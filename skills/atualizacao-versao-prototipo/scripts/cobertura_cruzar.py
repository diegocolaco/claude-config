"""Cruzamento entre telas da candidata: guarda assimétrica (D1) e texto antigo intacto (D2).

A leitura por tela não compara telas entre si. Este módulo lê, por git (sem checkout, sem rodar o protótipo), todas as telas
da candidata e procura duas inconsistências que o diff sozinho não mostra:

- D1: a mesma coluna ou campo com guarda de permissão numa tela e sem guarda em outra, quando a assimetria é nova na versão;
- D2: um texto trocado (valor de chave do locale ou literal trocado no diff) com um literal antigo intacto no mesmo elemento.

Os dois são heurísticos: a saída é uma pergunta ao Diego, nunca um requisito. Só biblioteca padrão; nada é gravado.
"""
from bisect import bisect_right
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).parent))

import cobertura_conferir  # noqa: E402
import cobertura_mapa as cm  # noqa: E402

EXCLUIDOS = re.compile(
    r"(^|/)(node_modules|\.umi[\w-]*|components/ui|locales?|i18n|lang|services|integrations|mocks?|_mock|__tests__|tests?|e2e"
    r"|typings|types)(/|$)|\.(d|gen|test|spec|server|functions)\.\w+$")
GENERICAS = frozenset(
    "id key name nome title titulo label status tipo type data date value valor total desc descricao description createdAt "
    "updatedAt created_at updated_at acoes actions index length text content children".split())
AVISO_SEM_ROTA = "nenhuma rota reconhecida: arquivos lidos sem ligação a tela"
AVISO_SEM_LEITURA = "NENHUM_ARQUIVO_LIDO: {telas} telas reconhecidas e nenhum arquivo lido; o cruzamento não viu nada"
AVISO_TELA_SEM_LEITURA = "TELA_SEM_LEITURA: {arquivo} ({tela}, {versao}): arquivo da rota fora da leitura"

# ---------------------------------------------------------------------------------------------------------------------
# Estrutura do texto
# ---------------------------------------------------------------------------------------------------------------------


def _no_escopo(caminho):
    return caminho.startswith("src/") and caminho.endswith(cm.EXTENSOES) and not EXCLUIDOS.search(caminho)


FECHO = {"{": "}", "[": "]", "(": ")"}


def _estrutura(t):
    """Pares `{[(` -> fecho, intervalos de string (início -> fim) e o motivo de perda de estrutura (None se não houve).

    Pula strings pela regra de aspa de `cm._abre_string`; a crase sempre abre string. Perda de estrutura: string ou template
    aberto até o fim do arquivo (regex com crase, crase no texto JSX) ou delimitadores que não casam. O que vem depois do ponto
    de perda não é confiável. Resíduo aceito: crases em número par podem fechar por engano sem que nada seja detectado.
    """
    pares, pilha, strs, perda = {}, [], {}, None
    i, n = 0, len(t)
    while i < n:
        c = t[i]
        if c in "'\"`":
            if not cm._abre_string(t, i):
                i += 1
                continue
            k = i + 1
            while k < n and t[k] != c:
                if t[k] == "\\":
                    k += 1
                elif t[k] == "\n" and c != "`":
                    break
                k += 1
            if k >= n:
                perda = perda or ("template aberto até o fim do arquivo" if c == "`" else "string aberta até o fim do arquivo")
            strs[i] = min(k, n - 1)
            i = k + 1
            continue
        if c in "{[(":
            pilha.append(i)
        elif c in "}])":
            if not pilha or FECHO[t[pilha[-1]]] != c:
                perda = perda or "delimitadores desbalanceados"
            if pilha:
                pares[pilha.pop()] = i
        i += 1
    if pilha:
        perda = perda or "delimitadores desbalanceados"
    return pares, strs, perda


def _anterior(t, i):
    """Índice do caractere não branco antes de `i` (-1 se não houver)."""
    j = i - 1
    while j >= 0 and t[j] in " \t\r\n":
        j -= 1
    return j


def _corpo_de_funcao(t, a):
    """O `{` em `t[a]` é corpo de função: vem depois de `)` ou de `=>`."""
    if t[a] != "{":
        return False
    j = _anterior(t, a)
    return j >= 0 and (t[j] == ")" or t[max(j - 1, 0):j + 1] == "=>")


def _objeto_literal(t, a, sem_argumento=False):
    """O `{` em `t[a]` abre um objeto literal: vem depois de `(`, `[`, `,`, `:` ou `?` e não é corpo de função.

    Com `sem_argumento`, o objeto passado a uma chamada (`formatMessage({ id })`) não vale: ele não é um elemento da tela.
    """
    if t[a] != "{" or _corpo_de_funcao(t, a):
        return False
    j = _anterior(t, a)
    if j < 0 or t[j] not in "([,:?":
        return False
    if sem_argumento and t[j] == "(":
        k = _anterior(t, j)
        if k >= 0 and (t[k].isalnum() or t[k] in "_$)"):
            return False
    return True


class _Arquivo:
    """Texto de um arquivo sem comentários, com os pares de chaves e as linhas indexadas."""

    def __init__(self, texto):
        self.t = cm._sem_comentarios(texto)
        self.inicios = [0] + [m.end() for m in re.finditer("\n", self.t)]
        self.pares, self.strs, self.perda = _estrutura(self.t)
        self._rg = None
        self._access = None

    def linha(self, p):
        return bisect_right(self.inicios, p)

    def envolvem(self, p):
        """Pares que envolvem `p`, do mais interno para fora."""
        return sorted(((a, f) for a, f in self.pares.items() if a < p <= f), key=lambda x: -x[0])

    @property
    def rg(self):
        if self._rg is None:
            self._rg = _regex_guarda(self.t)
        return self._rg

    @property
    def spans_access(self):
        if self._access is None:
            self._access = _spans_access(self)
        return self._access


# ---------------------------------------------------------------------------------------------------------------------
# D1: guardas
# ---------------------------------------------------------------------------------------------------------------------

HOOK_ACESSO = re.compile(r"const\s*\{([^}]*)\}\s*=\s*useAccess\s*\(")
HOOK_AUTH = re.compile(
    r"const\s*\{([^}]*)\}\s*=\s*(?:useAuth|useSession|useUser|useCurrentUser|usePermissions?|useRoles?|useProfile)\w*\s*\(")
NOME_PAPEL = re.compile(r"^(?:role|roles|perfil|papel|permissions?|permissoes)$")
NOME_BOOLEANO = re.compile(r"^(?:is[A-Z]\w*|can[A-Z]\w*|has[A-Z]\w*)$")
FUNCOES_GUARDA = r"\b(?:hasRole|hasAnyRole|hasPermission|hasAccess|checkPermission|temPermissao|temPerfil)\s*\("
GUARDA_DA_TELA = re.compile(
    r"\b(?:useRequireRole|requireRole|useRequirePermission|requirePermission)\s*\(|<(?:RequireRole|RoleGuard|RequirePermission)\b")
PAPEL_NA_ROTA = re.compile(r"\b(?:role|roles|perfil|papel|permissions?|permissoes)\b")
OPERADOR = re.compile(r"&&|(?<!\?)\?(?![.?])")


def _nomes_desestruturados(m):
    nomes = []
    for parte in m.group(1).split(","):
        nome = parte.strip().split(":")[-1].strip().split("=")[0].strip()  # o alias vale
        if re.fullmatch(r"[A-Za-z_$][\w$]*", nome):
            nomes.append(nome)
    return nomes


def _regex_guarda(t):
    """Regex G do arquivo: o que conta como guarda de permissão neste arquivo (veja o brief, §2.4)."""
    solto = r"(?<![\w$.])" + "{}" + r"(?![\w$])"
    alternativas = [r"\baccess\??\.\w+", FUNCOES_GUARDA]
    for m in HOOK_ACESSO.finditer(t):
        alternativas += [solto.format(re.escape(n)) for n in _nomes_desestruturados(m)]
    for m in HOOK_AUTH.finditer(t):
        for n in _nomes_desestruturados(m):
            e = re.escape(n)
            if NOME_PAPEL.match(n):
                alternativas += [
                    rf"(?<![\w$.]){e}\s*[!=]==?\s*(['\"])[^'\"]*\1",
                    rf"(['\"])[^'\"]*\1\s*[!=]==?\s*{e}(?![\w$])",
                    rf"(?<![\w$.]){e}\??\.includes\([^)]*\)",
                ]
            elif NOME_BOOLEANO.match(n):
                alternativas.append(solto.format(e))
            else:  # objeto de sessão: user.role, profile.isAdmin
                alternativas.append(
                    rf"(?<![\w$.]){e}\??\.(?:role|roles|perfil|papel|permissions?|is[A-Z]\w*|can[A-Z]\w*)(?![\w$])")
    return re.compile("|".join(f"(?:{a})" for a in alternativas))


def _texto_da_guarda(m):
    return re.sub(r"\s+", " ", m.group(0)).strip()


def _spans_access(a):
    """Intervalos (início, fim, guarda) entre `<Access accessible={G}>` e o `</Access>` casado."""
    t, saida = a.t, []
    for m in re.finditer(r"<Access(?=[\s>])", t):
        fim, auto = cm._fim_da_tag(t, m.end())
        g = a.rg.search(t[m.end():fim])
        if not g or auto:
            continue
        profundidade, pos = 1, fim + 1
        for mm in re.finditer(r"<Access(?=[\s>])|</Access\s*>", t[pos:]):
            if mm.group(0).startswith("</"):
                profundidade -= 1
                if profundidade == 0:
                    saida.append((fim, pos + mm.start(), _texto_da_guarda(g)))
                    break
            else:
                profundidade += 1
    return saida


def _guarda_do_elemento(a, p, forma):
    """Guarda do elemento em `a.t[p]`: `(forma_da_guarda, texto)` ou None. A primeira que casar vale; nunca janela de linhas."""
    t, rg = a.t, a.rg
    for ini, fim, texto in a.spans_access:
        if ini <= p <= fim:
            return "Access", texto
    envolve = a.envolvem(p)
    if forma == "coluna":  # o menor objeto literal que contém a chave
        for ini, fim in envolve:
            if t[ini] == "{" and not _corpo_de_funcao(t, ini):
                if _objeto_literal(t, ini):
                    g = rg.search(t[ini:fim + 1])
                    if g:
                        return "propriedade", _texto_da_guarda(g)
                break
    q = p
    for nivel, (ini, fim) in enumerate(envolve):
        if nivel >= 8 or _corpo_de_funcao(t, ini):
            break
        segmento, i = [], ini + 1
        while i < q:
            if i in a.pares and a.pares[i] < q:
                segmento.append(" _ ")
                i = a.pares[i] + 1
                continue
            if i in a.strs and a.strs[i] < q:
                segmento.append(t[i:a.strs[i] + 1])
                i = a.strs[i] + 1
                continue
            if t[i] in ",;":
                segmento = []
            else:
                segmento.append(t[i])
            i += 1
        s = "".join(segmento)
        for g in rg.finditer(s):
            if OPERADOR.search(s[g.end():]):
                return "inclusao_condicional", _texto_da_guarda(g)
        q = ini
    return None


# ---------------------------------------------------------------------------------------------------------------------
# D1: elementos (coluna, campo e informação exibida)
# ---------------------------------------------------------------------------------------------------------------------

COLUNA = re.compile(r"""\b(?:dataIndex|accessorKey)\s*:\s*(?:(['"])([\w.$-]+)\1|\[([^\]]*)\])""")
TAG_CAMPO = re.compile(r"<(?:Form\.Item|FormItem|FormField|Controller|ProForm\w*)(?=[\s/>])")
NOME_ATRIBUTO = re.compile(
    r"""(?<![\w$.-])name\s*=\s*(?:"([^"]+)"|'([^']+)'|\{\s*(?:"([^"]+)"|'([^']+)'|\[([^\]]*)\])\s*\})""")
REGISTRO = re.compile(r"""\bregister\(\s*(['"])([\w.]+)\1""")
VALOR_CONTROLADO = re.compile(r"\b(?:value|checked)\s*=\s*\{\s*([A-Za-z_$][\w$]*)\??\.([A-Za-z_$][\w$]*)\s*(?:\?\?[^{}]*)?\}")
MEMBRO_JSX = re.compile(r"\{\s*([A-Za-z_$][\w$]*)\??\.([A-Za-z_$][\w$]*)\s*(?:\?\?[^{}\n]*)?\}")


def _ultimo_literal(lista):
    partes = re.findall(r"""['"]([\w$.-]+)['"]""", lista or "")
    return partes[-1] if partes else None


def _fora_de_chaves(texto):
    """Máscara das posições de `texto` dentro de `{...}` (o `name` de um atributo aninhado não é o do campo)."""
    dentro, i = set(), 0
    while i < len(texto):
        if texto[i] == "{":
            fim = cm._fim_do_bloco(texto, i)
            dentro.update(range(i + 1, fim))
            i = fim
        i += 1
    return dentro


def _elementos(t):
    """[(chave, posição, forma)] da informação mostrada ou editada: `coluna`, `campo` e `exibe`."""
    saida = []
    for m in COLUNA.finditer(t):
        k = m.group(2) or _ultimo_literal(m.group(3))
        if k:
            saida.append((k.split(".")[-1], m.start(), "coluna"))
    for m in TAG_CAMPO.finditer(t):
        fim, _ = cm._fim_da_tag(t, m.end())
        cabeca = t[m.end():fim]
        dentro = _fora_de_chaves(cabeca)
        for mn in NOME_ATRIBUTO.finditer(cabeca):
            if mn.start() in dentro:
                continue
            k = next((g for g in mn.groups()[:4] if g), None) or _ultimo_literal(mn.group(5))
            if k:  # a posição é a do atributo `name`, que é a linha que o Diego abre
                saida.append((k.split(".")[-1], m.end() + mn.start(), "campo"))
            break
    for m in REGISTRO.finditer(t):
        saida.append((m.group(2).split(".")[-1], m.start(), "campo"))
    for m in VALOR_CONTROLADO.finditer(t):
        saida.append((m.group(2), m.start(), "campo"))
    for m in MEMBRO_JSX.finditer(t):
        j = _anterior(t, m.start())
        if j < 0 or t[j] in "=(,[:?&|${!+" or t[max(j - 1, 0):j + 1] == "=>":
            continue
        if not (t[j] in ">}.)" or t[j].isalpha()):
            continue
        saida.append((m.group(2), m.start(), "exibe"))
    return saida


# ---------------------------------------------------------------------------------------------------------------------
# Revisão: rotas, telas e arquivos lidos
# ---------------------------------------------------------------------------------------------------------------------


def _acessos_do_preset(leitor, preset):
    """arquivo de componente -> `access` da rota em `config/routes.ts` (herdado do pai em `routes: [...]`), para o Umi."""
    r = preset["_r"]
    saida = {}

    def objetos(seg, herdado):
        i = 0
        while True:
            ini = seg.find("{", i)
            if ini < 0:
                return
            fim = cm._fim_do_bloco(seg, ini)
            corpo, i = seg[ini + 1:fim], fim + 1
            plana, filhas, j, aspa = [], None, 0, None
            while j < len(corpo):
                c = corpo[j]
                if aspa:
                    plana.append(c)
                    if c == "\\" and j + 1 < len(corpo):
                        plana.append(corpo[j + 1])
                        j += 1
                    elif c == aspa:
                        aspa = None
                elif c in "'\"`":
                    aspa = c
                    plana.append(c)
                elif c in "{[(":
                    fecho = cm._fim_do_bloco(corpo, j)
                    if c == "[" and r.filhas.search("".join(plana)):
                        filhas = corpo[j + 1:fecho]
                    plana.append(" ")
                    j = fecho
                else:
                    plana.append(c)
                j += 1
            plana = "".join(plana)
            m = re.search(r"""\baccess\s*:\s*['"](\w+)['"]""", plana)
            acesso = m.group(1) if m else herdado
            mc = r.componente.search(plana)
            if mc and acesso:
                yield mc.group(1), acesso
            if filhas is not None:
                yield from objetos(filhas, acesso)

    for caminho in cm._arquivos_do_preset(leitor, preset):
        texto = cm._sem_comentarios(leitor.texto(caminho) or "")
        inicio = texto.find("[")
        if inicio < 0:
            continue
        for componente, acesso in objetos(texto[inicio + 1:cm._fim_do_bloco(texto, inicio)], None):
            if cm._alias_de(leitor, componente) is not None or componente.startswith("../"):
                arquivo = cm._resolver_import(leitor, caminho, componente)
            else:
                arquivo = cm._resolver(leitor, preset["pasta_componentes"] + "/" + componente.removeprefix("./"))
            if arquivo:
                saida[arquivo] = acesso
    return saida


class _Revisao:
    """Uma revisão (SHA) do protótipo: rotas, telas, arquivos lidos e a guarda de tela, tudo por git."""

    def __init__(self, repo, rev, presets=None, ids_do_mapa=None):
        self.rev = rev
        self._ocorrencias = None
        self.leitor = cm._Leitor(repo, rev)
        extras, self.formatos, aplicados = {}, [], []
        self.rotas = cm._rotas(self.leitor, extras=extras, formatos=self.formatos, presets=presets, aplicados=aplicados)
        self._arquivos = {}
        self.acessos = {}
        for preset, _ in aplicados:
            if preset["estrategia"] == "objeto-config":
                self.acessos.update(_acessos_do_preset(self.leitor, preset))
        # Telas como o mapa as conta: um arquivo atrás de várias rotas é uma tela só, na primeira rota.
        self.telas, self.telas_do, usados, vistos = {}, {}, {}, set()
        self.de_rota = set()  # arquivos que uma rota liga (tela e layouts): sempre lidos, em qualquer pasta
        ids_do_mapa = ids_do_mapa or {}
        for rota, arquivo in self.rotas.items():
            if arquivo is not None:
                if arquivo in vistos:
                    continue
                vistos.add(arquivo)
            id_ = cm._slug_da_rota(rota)
            usados[id_] = usados.get(id_, 0) + 1
            if usados[id_] > 1:
                id_ = f"{id_}-{usados[id_]}"
            if arquivo is None:
                continue
            id_ = ids_do_mapa.get(arquivo, id_)
            ficheiros = {arquivo}
            ligados = [e for e in extras.get(rota, []) if e != arquivo and self.leitor.existe(e)]
            ficheiros.update(cm._dependencias(self.leitor, arquivo))
            for e in ligados:
                ficheiros.add(e)
                ficheiros.update(cm._dependencias(self.leitor, e))
            self.telas[id_] = {"rota": rota, "arquivo": arquivo, "extras": ligados}
            self.de_rota.update([arquivo] + ligados)
            for f in ficheiros:
                self.telas_do.setdefault(f, set()).add(id_)

    def arquivo(self, caminho):
        if caminho not in self._arquivos:
            self._arquivos[caminho] = _Arquivo(self.leitor.texto(caminho) or "")
        return self._arquivos[caminho]

    @property
    def perdidos(self):
        """arquivo lido -> motivo, dos arquivos de estrutura perdida (veja `_estrutura`): o que sai deles não é confiável."""
        return {c: self.arquivo(c).perda for c in self.escopo() if self.arquivo(c).perda}

    def escopo(self):
        """Arquivos lidos: com rota, as telas e os layouts (em qualquer pasta) e o que importam (em `src/`, fora de `EXCLUIDOS`).

        Sem rota, todos os de `src/`. `src/` e `EXCLUIDOS` filtram só o que não veio de uma rota.
        """
        if not self.telas:
            return sorted(c for c in self.leitor.caminhos if _no_escopo(c))
        return sorted(c for c in self.telas_do if _no_escopo(c) or (c in self.de_rota and c.endswith(cm.EXTENSOES)))

    def telas_sem_leitura(self):
        """[(tela, arquivo)] das telas cujo arquivo de rota ficou fora da leitura (extensão que o cruzamento não lê)."""
        lidos = set(self.escopo())
        return sorted((id_, t["arquivo"]) for id_, t in self.telas.items() if t["arquivo"] not in lidos)

    def guarda_direta(self, caminho):
        """Guarda de tela no próprio arquivo: `access` da rota, `useRequireRole`..., `beforeLoad` ou retorno antecipado."""
        if caminho in self.acessos:
            return True
        a = self.arquivo(caminho)
        if GUARDA_DA_TELA.search(a.t):
            return True
        for m in re.finditer(r"\bbeforeLoad\b", a.t):
            ini = a.t.find("{", m.end())
            if ini >= 0:
                bloco = a.t[ini:cm._fim_do_bloco(a.t, ini) + 1]
                if a.rg.search(bloco) or PAPEL_NA_ROTA.search(bloco):
                    return True
        return bool(re.search(r"if\s*\(\s*!\s*(?:" + a.rg.pattern + r")[^)]*\)\s*\{?\s*return\b", a.t))

    def tela_guardada(self, id_):
        tela = self.telas[id_]
        return any(self.guarda_direta(c) for c in [tela["arquivo"]] + tela["extras"])

    def arquivo_guardado(self, caminho):
        """Guarda de tela do arquivo. Componente que não é tela só a tem se todas as telas que o usam a têm."""
        if self.guarda_direta(caminho):
            return True
        telas = self.telas_do.get(caminho)
        return bool(telas) and all(self.tela_guardada(t) for t in telas)

    def ocorrencias(self):
        """chave -> arquivo -> [{linha, forma, guarda, texto, tela_guardada}] dos elementos dos arquivos lidos (calculado uma vez)."""
        if self._ocorrencias is not None:
            return self._ocorrencias
        indice = self._ocorrencias = {}
        for caminho in self.escopo():
            a = self.arquivo(caminho)
            guardado_na_tela = self.arquivo_guardado(caminho)
            for chave, p, forma in _elementos(a.t):
                g = _guarda_do_elemento(a, p, forma)
                indice.setdefault(chave, {}).setdefault(caminho, []).append({
                    "linha": a.linha(p), "forma": forma, "guarda": g[0] if g else None, "texto": g[1] if g else None,
                    "tela_guardada": guardado_na_tela})
        return indice


# ---------------------------------------------------------------------------------------------------------------------
# D1: classificação
# ---------------------------------------------------------------------------------------------------------------------


def _lados(por_arquivo):
    """G: arquivos com guarda de elemento; U: arquivos com elemento sem guarda de elemento nem de tela."""
    G = {f for f, os in por_arquivo.items() if any(o["guarda"] for o in os)}
    U = {f for f, os in por_arquivo.items() if any(not o["guarda"] and not o["tela_guardada"] for o in os)}
    return G, U


def _novidade(G_C, U_C, G_V, U_V, rev_c, rev_v, ren):
    """Linhas de `novidade` por arquivo: guarda nova, guarda removida, sem guarda e nova, tela nova."""
    linhas = []
    for f in sorted(G_C - G_V):
        linhas.append(f"guarda nova: {f}")
    for f in sorted(U_C - U_V):
        antes = ren.get(f, f)
        if f in G_V:
            linhas.append(f"guarda removida: {f}")
        elif antes not in rev_v.leitor.caminhos:
            linhas.append(f"sem guarda e nova: {f}")
        elif rev_c.telas_do.get(f, set()) - rev_v.telas_do.get(antes, set()):
            linhas.append(f"tela nova: {f}")
        else:
            linhas.append(f"sem guarda e nova: {f}")
    return linhas


def _frase_telas(itens):
    """`a`, `a e b`, `a, b e c`."""
    itens = list(itens)
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def _rotulo_de_local(telas, arquivo, linha):
    nome = arquivo.rsplit("/", 1)[-1]
    return f"{_frase_telas(telas) or arquivo} ({nome}:{linha})"


def _d1(rev_c, rev_v, ren):
    """Suspeitas fortes, fracas e preexistentes da guarda assimétrica."""
    ocorr_c, ocorr_v = rev_c.ocorrencias(), rev_v.ocorrencias()
    inv = {origem: novo for novo, origem in ren.items()}
    fortes, fracas, preexistentes = [], [], []
    sha7 = rev_c.rev[:7]
    for chave in sorted(ocorr_c):
        G_C, U_C = _lados(ocorr_c[chave])
        if not (G_C and U_C):
            continue
        G_V, U_V = _lados(ocorr_v.get(chave, {}))
        G_V, U_V = {inv.get(f, f) for f in G_V}, {inv.get(f, f) for f in U_V}
        if not ((G_C - G_V) | (U_C - U_V)):
            preexistentes.append(chave)
            continue

        def unidades(f):
            return rev_c.telas_do.get(f) or {f}
        telas_arquivos = sorted(set().union(*[rev_c.telas_do.get(f, set()) for f in G_C | U_C]))
        n_telas = len(telas_arquivos) or len(G_C | U_C)
        if chave in GENERICAS:
            fracas.append({"chave": chave, "motivo": "chave_generica", "telas": n_telas})
            continue
        telas_G = set().union(*[unidades(f) for f in G_C])
        if all(unidades(f) <= telas_G for f in U_C):
            fracas.append({"chave": chave, "motivo": "mesma_tela", "telas": n_telas})
            continue
        if any(f in rev_c.perdidos for f in G_C | U_C) or any(ren.get(f, f) in rev_v.perdidos for f in G_V | U_V):
            fracas.append({"chave": chave, "motivo": "estrutura_perdida", "telas": n_telas})
            continue
        com_guarda, sem_guarda = [], []
        for f in sorted(G_C | U_C):
            for o in ocorr_c[chave][f]:
                telas = sorted(rev_c.telas_do.get(f, set()))
                if o["guarda"]:
                    com_guarda.append({"arquivo": f, "linha": o["linha"], "telas": telas, "guarda": o["texto"], "forma": o["guarda"]})
                elif f in U_C and not o["tela_guardada"]:
                    sem_guarda.append({"arquivo": f, "linha": o["linha"], "telas": telas})
        guardas = sorted({c["guarda"] for c in com_guarda})
        locais_g = [_rotulo_de_local(c["telas"], c["arquivo"], c["linha"]) for c in com_guarda[:1]]
        telas_g = sorted({t for c in com_guarda for t in c["telas"]})
        locais_u = [_rotulo_de_local(s["telas"], s["arquivo"], s["linha"]) for s in sem_guarda]
        fortes.append({
            "detector": "D1", "assinatura": f"D1:{chave}@{sha7}", "forca": "forte", "chave": chave,
            "com_guarda": com_guarda, "sem_guarda": sem_guarda,
            "novidade": _novidade(G_C, U_C, G_V, U_V, rev_c, rev_v, ren),
            "telas": sorted({t for e in com_guarda + sem_guarda for t in e["telas"]}),
            "pergunta": (f"A chave «{chave}» tem guarda ({', '.join(guardas)}) em {_frase_telas(telas_g) or locais_g[0]} e aparece "
                         f"sem guarda em {_frase_telas(locais_u)}. A diferença é intencional?"),
        })
    return fortes, fracas, preexistentes


# ---------------------------------------------------------------------------------------------------------------------
# D2: textos de interface, locale e literais
# ---------------------------------------------------------------------------------------------------------------------

LETRAS = re.compile(r"[A-Za-zÀ-ÿ]{2}")
LITERAL = re.compile(r""""((?:[^"\\\n]|\\.)*)"|'((?:[^'\\\n]|\\.)*)'|`((?:[^`\\]|\\.)*)`|>([^<>{}]+)<""")
INTERPOLACAO = re.compile(r"\$\{[^{}]*\}")
CLASSE_TAILWIND = re.compile(r"^[a-z0-9:/\[\]._%!-]+$")
SO_IDENTIFICADOR = re.compile(r"^[\w.$/@:-]+$")
ANTES_DO_LITERAL = re.compile(
    r"(?:defaultMessage\s*[:=]\s*\{?\s*|\b(?:className|class|style|variant|size|type|key|id|href|to|src)\s*[:=]\s*\{?\s*"
    r"|\b(?:cn|clsx|cva|twMerge)\(\s*(?:[^()]*,\s*)?|\b(?:t|formatMessage|i18n\.t)\(\s*|from\s+|import\s*\(?\s*)$")
PARES_DE_LOCALE = re.compile(
    r"""(?:^|[,{\s])(['"]?)([\w.\-]+)\1\s*:\s*((?:(['"`])(?:\\.|(?!\4).)*?\4\s*\+?\s*)+)""", re.S)
PASTA_DE_LOCALE = re.compile(r"(^|/)(locales?|i18n|lang|translations?)/")


def _literais(t):
    """(texto, posição) dos literais de string, das partes dos templates e do texto JSX (`>…<`, aparado)."""
    for m in LITERAL.finditer(t):
        if m.group(3) is not None:  # template: cada parte entre interpolações
            inicio = m.start(3)
            partes, fim = [], 0
            for i in INTERPOLACAO.finditer(m.group(3)):
                partes.append((m.group(3)[fim:i.start()], inicio + fim))
                fim = i.end()
            partes.append((m.group(3)[fim:], inicio + fim))
            for s, p in partes:
                if s and LETRAS.search(s):
                    yield s, p
            continue
        s = next(g for g in m.groups() if g is not None)
        if m.group(4) is not None:
            s = s.strip()
        if s and LETRAS.search(s):
            yield s, m.start()


def _texto_de_interface(s):
    """Texto que o usuário lê: não é seletor CSS, caminho, URL, classe do Tailwind, chave nem identificador."""
    s2 = s.strip()
    if not LETRAS.search(s2):
        return False
    if re.search(r"[&{};<>]", s2) or s2.startswith((".", "#", "@", "/", "http", "--")):
        return False
    tokens = s2.split()
    if all(CLASSE_TAILWIND.match(x) for x in tokens) and any("-" in x or ":" in x for x in tokens):
        return False
    if len(tokens) == 1 and SO_IDENTIFICADOR.match(s2) and not (s2[0].isupper() or re.search(r"[À-ÿ]", s2)):
        return False
    return True


def _padrao_do_antigo(antigo):
    corpo = re.escape(antigo)
    if antigo[:1].isalpha():
        corpo = f"[{antigo[0].upper()}{antigo[0].lower()}]" + re.escape(antigo[1:])
    return re.compile(rf"(?<!\w){corpo}(?!\w)")


def _spans_jsx(t):
    """(início, fim, tag) de cada elemento JSX, da `<Tag` ao `</Tag>` casado ou ao `/>`; a tag exige não-palavra antes."""
    saida = []
    for m in re.finditer(r"<([A-Za-z][\w.]*)(?=[\s/>])", t):
        if m.start() > 0 and (t[m.start() - 1].isalnum() or t[m.start() - 1] == "_"):
            continue  # `useState<T>`
        nome = m.group(1)
        fim, auto = cm._fim_da_tag(t, m.end())
        if auto:
            saida.append((m.start(), fim, nome))
            continue
        profundidade = 1
        token = re.compile(rf"<{re.escape(nome)}(?=[\s/>])|</{re.escape(nome)}\s*>")
        for mm in token.finditer(t, fim + 1):
            if mm.group(0).startswith("</"):
                profundidade -= 1
                if profundidade == 0:
                    saida.append((m.start(), mm.end(), nome))
                    break
            elif not cm._fim_da_tag(t, mm.end())[1]:
                profundidade += 1
    return saida


def _escopo_do_uso(a, jsx, p, pai=False):
    """O menor elemento (JSX ou objeto literal) de até 40 linhas que contém o uso em `p`.

    Com `pai`, o uso é o texto filho de um elemento (`<Label>Cost</Label>`) e o escopo é o elemento que o contém: o rótulo
    e o `placeholder` do `<Input>` ao lado vivem no mesmo pai.
    """
    candidatos = [(fim - ini, ini, fim) for ini, fim, nome in jsx if ini <= p <= fim and nome not in ("FormattedMessage", "Trans")]
    candidatos += [(fim - ini, ini, fim) for ini, fim in a.pares.items()
                   if ini < p <= fim and _objeto_literal(a.t, ini, sem_argumento=True)]
    candidatos = [c for c in sorted(candidatos) if a.t.count("\n", c[1], c[2]) <= 40]
    if not candidatos:
        return None
    escolhido = candidatos[1] if pai and len(candidatos) > 1 else candidatos[0]
    return escolhido[1], escolhido[2]


def _padrao_do_idioma(idioma):
    corpo = "".join("[-_]?" if c in "-_" else re.escape(c) for c in idioma)
    return re.compile(corpo)


def _flat_json(dados, prefixo=""):
    saida = {}
    if isinstance(dados, dict):
        for k, v in dados.items():
            if isinstance(v, dict):
                saida.update(_flat_json(v, f"{prefixo}{k}."))
            elif isinstance(v, str):
                saida[f"{prefixo}{k}"] = v
    return saida


def _ler_locale(caminho, texto):
    """chave -> valor de um arquivo de locale: pares `chave: 'valor'` do TS/JS (valor na linha seguinte, `+`) ou JSON aninhado."""
    if caminho.endswith(".json"):
        try:
            return _flat_json(json.loads(texto))
        except ValueError:
            return {}
    saida = {}
    for m in PARES_DE_LOCALE.finditer(cm._sem_comentarios(texto)):
        partes = re.findall(r"""(['"`])((?:\\.|(?!\1).)*?)\1""", m.group(3), re.S)
        saida[m.group(2)] = "".join(p[1] for p in partes)
    return saida


def _locales(leitor, idioma):
    """(chave -> (valor, arquivo), arquivos do idioma, arquivos de locale de qualquer idioma)."""
    todos = sorted(c for c in leitor.caminhos if PASTA_DE_LOCALE.search(c) and c.endswith((".ts", ".js", ".json")))
    padrao = _padrao_do_idioma(idioma)
    do_idioma = [c for c in todos if padrao.search(c)]
    valores = {}
    for c in do_idioma:
        for k, v in _ler_locale(c, leitor.texto(c) or "").items():
            valores[k] = (v, c)
    return valores, do_idioma, todos


def _aviso_de_locale(do_idioma, todos, idioma):
    if do_idioma or not todos:
        return None
    idiomas = {m.group(0).lower().replace("_", "-") for c in todos for m in re.finditer(r"[a-z]{2}[-_]?[A-Z]{2}", c)}
    if len(idiomas) > 1:
        return f"locale de vários idiomas e nenhum do {idioma}"
    return f"nenhum locale do idioma {idioma}"


def _trocas_de_literal(repo, v, c, rev_c, alterados):
    """[(arquivo, antigo, novo, linha)] de literais trocados no diff, linha a linha, em arquivos do escopo."""
    saida = []
    for caminho in rev_c.escopo():
        a = alterados.get(caminho)
        if not a or a["status"] not in ("M", "R") or a["binario"]:
            continue
        pathspec = [a["origem"], caminho] if a["status"] == "R" else [caminho]
        diff = cm._git(rev_c.leitor.repo, "diff", "-U0", "--no-color", "--no-ext-diff", "-M", v, c, "--", *pathspec)
        for hunk in cm._hunks(diff):
            removidas = [x[1] for x in hunk["linhas"] if x[0] == "-"]
            adicionadas = [(x[1], x[2]) for x in hunk["linhas"] if x[0] == "+"]
            if len(removidas) != len(adicionadas):
                continue
            for velha, (nova, numero) in zip(removidas, adicionadas):
                lv, ln = [s for s, _ in _literais(velha)], [s for s, _ in _literais(nova)]
                if len(lv) != len(ln):
                    continue
                for antigo, novo in zip(lv, ln):
                    if antigo != novo and _texto_de_interface(antigo) and _texto_de_interface(novo) and antigo not in novo:
                        saida.append((caminho, antigo, novo, numero))
    return saida


def _d2(repo, mapa_v, mapa_c, rev_c, rev_v, idioma, alterados, ren):
    """Suspeitas fortes do texto antigo intacto, contagem das fracas e dados do formato."""
    valores_c, do_idioma, todos = _locales(rev_c.leitor, idioma)
    valores_v = {k: val for k, (val, _) in _locales(rev_v.leitor, idioma)[0].items()}
    avisos = []
    aviso = _aviso_de_locale(do_idioma, todos, idioma)
    if aviso:
        avisos.append(aviso)
    trocas_locale = sorted((k, valores_v[k], valor, arquivo) for k, (valor, arquivo) in valores_c.items()
                           if k in valores_v and valores_v[k] != valor and LETRAS.search(valores_v[k]))
    escopo = rev_c.escopo()
    trocas_literal = _trocas_de_literal(repo, mapa_v, mapa_c, rev_c, alterados)
    chaves_locale = set(valores_c)
    cache = {}

    def preparar(caminho):
        if caminho not in cache:
            a = rev_c.arquivo(caminho)
            origem_v = ren.get(caminho, caminho)
            texto_v = cm._sem_comentarios(rev_v.leitor.texto(origem_v) or "") if rev_v.leitor.existe(origem_v) else None
            cache[caminho] = (a, texto_v, list(_literais(a.t)), _spans_jsx(a.t))
        return cache[caminho]

    achados = []

    def varrer(caminho, antigo, novo, usos, origem, uso_rotulo, pai=False):
        a, texto_v, literais, jsx = preparar(caminho)
        if texto_v is None:
            return  # arquivo novo: nada era literal antigo
        escopos = [e for e in (_escopo_do_uso(a, jsx, u, pai) for u in usos) if e]
        padrao = _padrao_do_antigo(antigo)
        for s, p in literais:
            m = padrao.search(s)
            if not m or novo.lower() in s.lower() or s in chaves_locale or not _texto_de_interface(s):
                continue
            if ANTES_DO_LITERAL.search(a.t[max(0, p - 40):p]) or s not in texto_v:
                continue
            achados.append({
                "arquivo": caminho, "linha": a.linha(p), "literal": s, "antigo": antigo, "novo": novo, "origem": origem,
                "uso": uso_rotulo, "perdida": bool(a.perda),
                "forte": not a.perda and any(ini <= p <= fim for ini, fim in escopos),
                "molde": s[:m.start()] + "{antigo}" + s[m.end():]})

    for chave, antigo, novo, arquivo_locale in trocas_locale:
        busca = re.compile(rf"""(['"`]){re.escape(chave)}\1""")
        for caminho in escopo:
            a = rev_c.arquivo(caminho)
            usos = [m.start() for m in busca.finditer(a.t)]
            if usos:
                varrer(caminho, antigo, novo, usos, f"locale:{chave}", f"{caminho}:{a.linha(usos[0])}")
    for caminho, antigo, novo, numero in trocas_literal:
        a = rev_c.arquivo(caminho)
        if numero > len(a.inicios):
            continue
        ini = a.inicios[numero - 1]
        fim = a.inicios[numero] if numero < len(a.inicios) else len(a.t)
        p = ini + max(a.t[ini:fim].find(novo), 0)
        texto_filho = bool(re.search(r">\s*" + re.escape(novo) + r"\s*<", a.t[ini:fim]))
        varrer(caminho, antigo, novo, [p], f"literal:{caminho}:{numero}", f"{caminho}:{numero}", texto_filho)

    # Dedupe por (arquivo, linha, literal): a forte vence a fraca.
    unicos, vistos = [], set()
    for h in sorted(achados, key=lambda h: (not h["forte"], h["arquivo"], h["linha"], h["origem"], h["antigo"])):
        chave = (h["arquivo"], h["linha"], h["literal"])
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(h)
    grupos = {}
    for h in unicos:
        if h["forte"]:
            grupos.setdefault(h["molde"], []).append(h)
    fracas = {"D2_fora_do_elemento": sum(1 for h in unicos if not h["forte"] and not h["perdida"])}
    if any(h["perdida"] for h in unicos):  # só aparece quando houve: o formato de sempre não ganha chave
        fracas["D2_estrutura_perdida"] = sum(1 for h in unicos if h["perdida"])
    sha7 = rev_c.rev[:7]
    fortes = []
    for molde in sorted(grupos):
        ocorrencias = sorted(grupos[molde], key=lambda h: (h["arquivo"], h["linha"], h["literal"]))
        telas = sorted({t for h in ocorrencias for t in rev_c.telas_do.get(h["arquivo"], set())})
        exemplo = ocorrencias[0]
        origens = {h["origem"].split(":", 1)[0] for h in ocorrencias}
        como = "pela chave" if origens == {"locale"} else "no código" if origens == {"literal"} else "pela chave ou no código"
        n = len(ocorrencias)
        fortes.append({
            "detector": "D2", "assinatura": f"D2:{molde}@{sha7}", "forca": "forte", "molde": molde,
            "ocorrencias": [{k: h[k] for k in ("arquivo", "linha", "literal", "antigo", "novo", "origem", "uso")}
                            | {"telas": sorted(rev_c.telas_do.get(h["arquivo"], set()))} for h in ocorrencias],
            "telas": telas,
            "pergunta": (f"O texto mudou {como} (ex.: «{exemplo['antigo']}» → «{exemplo['novo']}»), mas {n} "
                         f"{'literal' if n == 1 else 'literais'} no mesmo elemento "
                         f"{'continua' if n == 1 else 'continuam'} com o texto antigo no molde «{molde}» em {len(telas)} "
                         f"{'tela' if len(telas) == 1 else 'telas'}. O protótipo deve trocar também "
                         f"{'esse literal' if n == 1 else 'esses literais'}, ou o texto antigo é intencional?"),
            "_locale": [(h["origem"][7:], valores_c.get(h["origem"][7:], (None, None))[1])
                        for h in ocorrencias if h["origem"].startswith("locale:")],
        })
    formato = {"locale": do_idioma, "trocas_locale": len(trocas_locale), "trocas_literal": len(trocas_literal)}
    return fortes, fracas, avisos, formato


# ---------------------------------------------------------------------------------------------------------------------
# Diferenças afetadas (catálogo) e unidades
# ---------------------------------------------------------------------------------------------------------------------


def _sem_linha(caminho):
    """`src/a.tsx:44` e `src/a.tsx:44-50` -> `src/a.tsx`."""
    return re.sub(r":\d+(?:[-,]\d+)*$", "", caminho.strip())


def _texto(valor):
    return valor if isinstance(valor, str) else ""


def _afeta_df(suspeita, catalogo, rev_c):
    """Diferenças do catálogo ligadas à suspeita por arquivo, rota ou chave de locale, com `cita_texto`."""
    superficies = {s["id"]: s for s in cobertura_conferir._lista(catalogo, "surfaces") if isinstance(s.get("id"), str)}
    if suspeita["detector"] == "D1":
        arquivos = {e["arquivo"] for e in suspeita["com_guarda"] + suspeita["sem_guarda"]}
        palavras = [suspeita["chave"]] + sorted({e["guarda"] for e in suspeita["com_guarda"]})
        palavras += sorted({e["guarda"].split(".")[-1] for e in suspeita["com_guarda"] if "." in e["guarda"]})
        chaves = set()
    else:
        arquivos = {o["arquivo"] for o in suspeita["ocorrencias"]}
        molde = suspeita["molde"].replace("{antigo}", "").strip()
        palavras = [molde] if len(molde) >= 4 else []
        palavras += sorted({o["antigo"] for o in suspeita["ocorrencias"]} | {o["novo"] for o in suspeita["ocorrencias"]})
        chaves = {(arq, chave) for chave, arq in suspeita["_locale"]}
    rotas = {rev_c.telas[t]["rota"] for t in suspeita["telas"] if t in rev_c.telas}
    saida = []
    for df in cobertura_conferir._lista(catalogo, "differences"):
        if not isinstance(df.get("id"), str):
            continue
        por = set()
        for parte in re.split(r"[;,]", _texto(df.get("fonte_prototipo"))):
            if parte.strip() and _sem_linha(parte) in arquivos:
                por.add("fonte_prototipo")
        trechos = df.get("trechos") if isinstance(df.get("trechos"), list) else []
        for trecho in (t for t in trechos if isinstance(t, str)):
            arquivo, _, chave = trecho.partition("#")
            if arquivo in arquivos:
                por.add("trechos")
            if chave and (arquivo, chave) in chaves:
                por.add("chave")
        ids = [df.get("surface_id")] + (df.get("surface_ids") if isinstance(df.get("surface_ids"), list) else [])
        for sid in (i for i in ids if isinstance(i, str)):
            s = superficies.get(sid)
            if s and (_texto(s.get("arquivo_prototipo")) in arquivos or _texto(s.get("rota")) in rotas):
                por.add("superficie")
        if por:
            texto = _texto(df.get("produto_precisa")) + "\n" + _texto(df.get("agora"))
            saida.append({"id": df["id"], "por": sorted(por), "cita_texto": any(p in texto for p in palavras if p)})
    return sorted(saida, key=lambda x: x["id"])


def _ligar_unidades(suspeita, unidades):
    ids_por_tela = {}
    for u in cobertura_conferir._unidades_validas(unidades):
        for t in cobertura_conferir._textos(u.get("telas")):
            ids_por_tela.setdefault(t, set()).add(u.get("id"))
    suspeita["unidades"] = sorted({i for t in suspeita["telas"] for i in ids_por_tela.get(t, ()) if isinstance(i, str)})
    suspeita["fora_do_mapa"] = sorted(t for t in suspeita["telas"] if t not in ids_por_tela)


# ---------------------------------------------------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------------------------------------------------


def _presets_do_mapa(mapa):
    """Presets impostos por `--rotas` na hora de mapear (origem diferente de `skill`); None se o mapa usou os da skill."""
    origens = []
    for item in mapa.get("presets_de_rotas") or []:
        origem = item.get("origem") if isinstance(item, dict) else None
        if isinstance(origem, str) and origem != "skill" and origem not in origens:
            origens.append(origem)
    return [cm.carregar_preset(o) for o in origens] or None


def cruzar(repo, mapa, catalogo=None, unidades=None, idioma="pt-BR"):
    """Procura D1 e D2 nas telas da candidata do `mapa`; devolve o documento de `cruzamentos.json`.

    Lê as revisões do mapa (`vigente_sha`/`candidata_sha`; sem eles, `vigente`/`candidata`) e confere com as refs de agora:
    `MAPA_DESATUALIZADO` fica em `identidade`. Só git de leitura; levanta `ValueError` em entrada inválida e deixa passar
    `subprocess.CalledProcessError` e `OSError` do git.
    """
    if not isinstance(mapa, dict) or not all(isinstance(mapa.get(r), str) and mapa[r] for r in ("vigente", "candidata")):
        raise ValueError("Mapa inválido: faltam 'vigente' e 'candidata'.")
    if catalogo is not None and not isinstance(catalogo, dict):
        raise ValueError("Catálogo inválido: o JSON deve ser um objeto.")
    if unidades is not None and not isinstance(unidades, dict):
        raise ValueError("Unidades inválidas: o JSON deve ser um objeto.")
    repo = Path(repo)
    atuais = {ref: cm.resolver_sha(repo, mapa[ref]) for ref in ("vigente", "candidata")}
    identidade = cobertura_conferir._conferir_identidade(mapa, {}, atuais)
    sha_v = mapa.get("vigente_sha") if isinstance(mapa.get("vigente_sha"), str) and mapa.get("vigente_sha") else mapa["vigente"]
    sha_c = mapa.get("candidata_sha") if isinstance(mapa.get("candidata_sha"), str) and mapa.get("candidata_sha") else mapa["candidata"]
    sha_v, sha_c = cm.resolver_sha(repo, sha_v), cm.resolver_sha(repo, sha_c)
    presets = _presets_do_mapa(mapa)
    gerados = cm._gerados(presets or cm.presets_da_skill())
    alterados = {a["caminho"]: a for a in cm.arquivos_alterados(repo, sha_v, sha_c, gerados)}
    ren = {c: a["origem"] for c, a in alterados.items() if a["status"] == "R"}

    ids_do_mapa = {t["arquivo"]: t["id"] for t in mapa.get("telas") or []
                   if isinstance(t, dict) and isinstance(t.get("arquivo"), str) and isinstance(t.get("id"), str)}
    rev_c = _Revisao(repo, sha_c, presets, ids_do_mapa)
    rev_v = _Revisao(repo, sha_v, presets)
    avisos = [] if rev_c.telas else [AVISO_SEM_ROTA]
    if rev_c.telas and not rev_c.escopo():
        avisos.append(AVISO_SEM_LEITURA.format(telas=len(rev_c.telas)))
    avisos += [AVISO_TELA_SEM_LEITURA.format(arquivo=arquivo, tela=tela, versao="candidata")
               for tela, arquivo in rev_c.telas_sem_leitura()]

    fortes_d1, fracas_d1, preexistentes_d1 = _d1(rev_c, rev_v, ren)
    fortes_d2, fracas_d2, avisos_d2, formato_d2 = _d2(repo, sha_v, sha_c, rev_c, rev_v, idioma, alterados, ren)
    avisos += avisos_d2
    avisos += sorted(f"ESTRUTURA_PERDIDA: {arquivo} ({versao}): {motivo}"
                     for versao, rev in (("candidata", rev_c), ("vigente", rev_v)) for arquivo, motivo in rev.perdidos.items())

    fortes = sorted(fortes_d1 + fortes_d2, key=lambda s: (s["detector"], s["assinatura"]))
    for n, s in enumerate(fortes, 1):
        s["id"] = f"S-{n:02d}"
        s["afeta_df"] = _afeta_df(s, catalogo, rev_c) if catalogo is not None else None
        if unidades is not None:
            _ligar_unidades(s, unidades)
        else:
            s["unidades"] = s["fora_do_mapa"] = None
        s.pop("_locale", None)
    ordem = ("id", "assinatura", "detector", "forca")
    fortes = [{**{k: s[k] for k in ordem}, **{k: v for k, v in s.items() if k not in ordem}} for s in fortes]

    lidos = rev_c.escopo()
    ocorr = [o for por in rev_c.ocorrencias().values() for os in por.values() for o in os]
    return {
        "vigente": sha_v, "candidata": sha_c, "identidade": identidade,
        "formato": {
            "rotas": rev_c.formatos, "locale": formato_d2["locale"], "arquivos_lidos": len(lidos), "telas": len(rev_c.telas),
            "elementos": len(ocorr), "com_guarda_de_elemento": sum(1 for o in ocorr if o["guarda"]),
            "com_guarda_de_tela": sum(1 for c in lidos if rev_c.arquivo_guardado(c)),
            "trocas_locale": formato_d2["trocas_locale"], "trocas_literal": formato_d2["trocas_literal"],
        },
        "suspeitas": fortes,
        "fracas": {"D1": fracas_d1, **fracas_d2},
        "preexistentes": {"D1": preexistentes_d1},
        "resumo": {"fortes": len(fortes), "fracas": len(fracas_d1) + sum(fracas_d2.values()), "preexistentes": len(preexistentes_d1)},
        "avisos": avisos,
    }
