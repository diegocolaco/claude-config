"""Mapa de cobertura da atualização de versão do protótipo: corta o diff entre duas versões em trechos.

Cada trecho tem um `id` determinístico, usado depois para conferir que a descoberta cobriu o diff inteiro.
Só biblioteca padrão; o git é chamado por subprocess.
"""
from fnmatch import fnmatchcase
import json
from math import ceil
from pathlib import Path
import posixpath
import re
import subprocess
from types import SimpleNamespace

# Opções globais: caminhos sem aspas (acentos, espaços) e pathspec literal (sem curingas).
GIT = ["git", "-c", "core.quotePath=false", "--literal-pathspecs"]
# Chave de objeto: sem aspas, ou com o mesmo par de aspas dos dois lados (`'Atenção: x',` é valor, não a chave `Atenção`).
CHAVE = re.compile(r"""^\s*(['"]?)([\w.\-]+)\1\s*:""")
# Linha puramente estrutural (invólucro de locale): vazia, `{`, `}`, `],`, `export default {`...
ESTRUTURAL = re.compile(r"^\s*(export\s+default\s*)?[\[\]{}(),;]*\s*$")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

# Orçamento de tokens de um agente (~50% do contexto; ponto de partida do spec 6.2, calibrável).
ORCAMENTO_PADRAO = 60_000
# Pesos que somam ao multiplicador (1.0 + sinais) de cada tela; `max_trechos` limita o sinal por trecho.
PESOS = {
    "nova": 0.5, "por_trecho": 0.05, "max_trechos": 20, "compartilhado": 0.3,
    "formulario": 0.3, "permissao": 0.3, "acoplamento": 0.2,
}
# Metadado do processo gravado na candidata (não é conteúdo do protótipo): fora do mapa, listado em `ignorados`.
PREFIXOS_IGNORADOS = (".squad/",)
# Lockfiles (nome-base em qualquer pasta) e pastas de binários do yarn: derivados, cada um é um trecho só (`<caminho>#arquivo`).
LOCKFILES = frozenset((
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock", "bun.lockb", "deno.lock",
    "composer.lock", "Pipfile.lock", "packages.lock.json", "flake.lock", "poetry.lock", "uv.lock", "Cargo.lock",
    "Gemfile.lock", "go.sum", "pubspec.lock", "Podfile.lock", "mix.lock", "gradle.lockfile", ".pnp.cjs", ".pnp.loader.mjs",
))
PREFIXOS_LOCKFILE = (".yarn/releases/", ".yarn/cache/")
EXTENSOES = (".tsx", ".ts", ".jsx", ".js")
# Alias de import quando o preset não declara `aliases` (`@/x` -> `src/x`).
ALIASES_PADRAO = {"@/": "src/"}
IMPORT_DECL = re.compile(r"""import\s+(?:type\s+)?([^;'"]*?)\s*from\s*['"]([^'"]+)['"]""", re.S)
IMPORT_LAZY = re.compile(r"""(\w+)\s*=\s*(?:React\.)?lazy\(\s*\(\)\s*=>\s*import\(\s*['"]([^'"]+)['"]""")
TAG_JSX = re.compile(r"<\s*([A-Z][\w.]*)")
# Arquivo de página/tela: sinal de que deveria haver rota reconhecida.
PAGINA = re.compile(r"(?:^|/)(?:pages|views|screens|telas)/.+\.(?:tsx|jsx|ts|js)$")
# Estimativa de leitura de trecho sem tela (a mesma regra de `cobertura_conferir`: ~10 tokens por linha, vezes 2).
TOKENS_POR_LINHA = 20
TOKENS_TRECHO_SEM_LINHAS = 100
FORMULARIO = re.compile(r"<Form\b|useForm\b")
# `controle` não é permissão: minúsculas só no começo de palavra; capitalizadas, em fronteira camelCase.
PERMISSAO = re.compile(
    r"(?<![A-Za-z])(?:access|permission|role|perfil|escopo|unidade|vendedor)"
    r"|(?<=[a-z0-9_.])(?:Access|Permission|Role|Perfil|Escopo|Unidade|Vendedor)"
)
# Chaves genéricas demais para acoplar telas (aparecem em qualquer arquivo).
CHAVES_GENERICAS = {"path", "component", "name", "default", "title", "label", "value", "type", "props", "style"}


# --- Presets de rotas -------------------------------------------------------------------------------------------
# O código traz três estratégias de leitura (`objeto-config`, `jsx`, `arquivos`); o que muda de uma convenção para
# outra da mesma família (caminhos, nomes de chave, separadores) vem de um preset JSON em `rotas/` ou de `--rotas`.
ESTRATEGIAS = ("objeto-config", "jsx", "arquivos")
PASTA_PRESETS = Path(__file__).resolve().parent / "rotas"
NUNCA = re.compile(r"(?!)")  # nunca casa: recurso opcional do preset que não foi declarado


class PresetInvalido(ValueError):
    """Preset de rotas ilegível ou inválido; a mensagem nomeia o arquivo e o campo."""


def _motivo_ere(padrao):
    """Por que `padrao` não serve ao `git grep -E` (None se serve): construto só de Python, que o git lê como outra coisa.

    O git entende o ERE do POSIX com as extensões do GNU (`\\b`, `\\w`, `\\s`, classes `[[:alpha:]]`); não entende grupo
    `(?...)` (sem lookahead, lookbehind nem grupo sem captura), `\\d`, `\\D` e quantificador não ávido (`+?`, `*?`).
    """
    i, n, classe = 0, len(padrao), False
    while i < n:
        c = padrao[i]
        if c == "\\":
            if padrao[i + 1:i + 2] in ("d", "D"):
                return "«\\d» não existe no ERE (use [0-9])"
            i += 2
            continue
        if classe:
            if c == "[" and padrao[i + 1:i + 2] == ":":
                fim = padrao.find(":]", i + 2)
                i = n if fim < 0 else fim + 2
                continue
            classe = c != "]"
        elif c == "[":
            classe = True
            i += 1
            if padrao[i:i + 1] == "^":
                i += 1
            if padrao[i:i + 1] == "]":
                i += 1
            continue
        elif c == "(" and padrao[i + 1:i + 2] == "?":
            return "grupo «(?...)» não existe no ERE (sem lookahead, lookbehind nem grupo sem captura; use «(...)»)"
        elif c in "*+?}" and padrao[i + 1:i + 2] == "?":
            return "quantificador não ávido não existe no ERE"
        i += 1
    return None


def _ere_literal(texto):
    """`texto` escapado para o `git grep -E`: casa o próprio texto."""
    return re.sub(r"([.^$*+?()\[\]{}|\\])", r"\\\1", texto)


_ESQUEMA_COMUM = [
    ("nome", "texto", True), ("rotulo", "texto", True), ("estrategia", "texto", True), ("descricao", "texto", False),
    ("prioridade", "inteiro", False),
    ("marcas", [("arquivos", "textos", False), ("conteudo", "ere", False)], True),
    ("aliases", "mapa", False),
]
_ESQUEMAS = {
    "objeto-config": _ESQUEMA_COMUM + [
        ("arquivos", "textos", True),
        ("chaves", [("caminho", "texto", True), ("componente", "texto", True), ("filhas", "texto", True)], True),
        ("pasta_componentes", "texto", True),
    ],
    "jsx": _ESQUEMA_COMUM + [
        ("arquivos", "textos", True), ("tag", "texto", True),
        ("atributos", [(c, "texto", True) for c in ("caminho", "elemento", "componente", "indice", "lazy", "filhas")], True),
        ("listas", "listas", True), ("nao_tela", "textos", False),
    ],
    "arquivos": _ESQUEMA_COMUM + [
        ("pasta", "texto", True), ("extensoes", "extensoes", True),
        ("config", [("arquivo", "texto", True), ("chave_pasta", "texto", True)], False),
        ("gerado", "texto", False), ("marca_da_pasta", "regex", False),
        ("segmento", [
            ("separador", "caractere", True), ("sem_caminho", "texto", True), ("sem_aninhamento", "texto", True),
            ("ignorado", "texto", True), ("grupo", "par", True), ("layout", "texto", True), ("raiz", "texto", True),
            ("indice", "texto", True), ("sufixo_lazy", "texto", True), ("parametro", "texto", True),
            ("nao_rota", "textos", False),
        ], True),
        ("chaves", [
            ("componente", "texto", True), ("servidor", "texto", False), ("caminho", "texto", False),
            ("id", "texto", False), ("pai", "texto", False),
        ], True),
        ("lazy_funcao", "texto", False), ("outlet", "texto", False), ("criador", "texto", False),
    ],
}


def _campo(prefixo, nome):
    return f"{prefixo}.{nome}" if prefixo else nome


def _checar_valor(valor, tipo, campo, origem):
    """Levanta `PresetInvalido` nomeando `campo` se `valor` não for do `tipo`."""
    def falha(motivo):
        return PresetInvalido(f"{origem}: campo «{campo}» {motivo}")

    def texto(v):
        return isinstance(v, str) and v != ""

    def regex(v):
        if not texto(v):
            return False
        try:
            re.compile(v)
        except re.error as erro:
            raise falha(f"tem expressão regular inválida ({erro})") from erro
        return True

    if tipo == "texto" and not texto(valor):
        raise falha("deve ser um texto não vazio")
    if tipo == "caractere" and not (texto(valor) and len(valor) == 1):
        raise falha("deve ser um único caractere")
    if tipo == "inteiro" and (isinstance(valor, bool) or not isinstance(valor, int)):
        raise falha("deve ser um número inteiro")
    if tipo in ("regex", "ere") and not regex(valor):
        raise falha("deve ser uma expressão regular (texto não vazio)")
    if tipo == "ere" and _motivo_ere(valor):
        raise falha(f"usa construto que o git grep -E não entende: {_motivo_ere(valor)}")
    if tipo in ("textos", "extensoes", "listas"):
        if not isinstance(valor, list) or not valor:
            raise falha("deve ser uma lista não vazia")
        for item in valor:
            if tipo == "listas":
                if not regex(item):
                    raise falha("deve ser uma lista de expressões regulares")
                if not item.endswith("\\["):
                    raise falha(f"tem expressão que não termina em «\\[» (o abre-colchete da lista de rotas): {item!r}")
            elif not texto(item):
                raise falha("deve ser uma lista de textos não vazios")
            elif tipo == "extensoes" and not item.startswith("."):
                raise falha(f"tem extensão sem ponto inicial: {item!r}")
    if tipo == "par" and not (isinstance(valor, list) and len(valor) == 2 and all(texto(v) for v in valor)):
        raise falha("deve ser uma lista de dois textos não vazios")
    if tipo == "mapa":
        if not isinstance(valor, dict) or not all(texto(k) and texto(v) for k, v in valor.items()):
            raise falha("deve ser um objeto de textos não vazios")


def _checar_objeto(dados, esquema, prefixo, origem):
    if not isinstance(dados, dict):
        raise PresetInvalido(f"{origem}: campo «{prefixo or '(raiz)'}» deve ser um objeto, não {type(dados).__name__}")
    conhecidos = {nome for nome, _, _ in esquema}
    for chave in dados:
        if chave not in conhecidos:
            raise PresetInvalido(f"{origem}: campo «{_campo(prefixo, chave)}» desconhecido")
    for nome, tipo, obrigatorio in esquema:
        campo = _campo(prefixo, nome)
        if nome not in dados:
            if obrigatorio:
                raise PresetInvalido(f"{origem}: campo «{campo}» obrigatório ausente")
            continue
        if isinstance(tipo, list):
            _checar_objeto(dados[nome], tipo, campo, origem)
        else:
            _checar_valor(dados[nome], tipo, campo, origem)


def _barras(valor):
    """Caminho do preset com `/` (a barra invertida é normalizada), sem `./`, `//` nem `/` final: `./app//routes/` -> `app/routes`."""
    return posixpath.normpath(valor.replace("\\", "/"))


def _prefixo(valor):
    """Valor de alias: com `/` e sem `./` inicial; a barra final fica (`src/` + o resto do import)."""
    valor = valor.replace("\\", "/")
    while valor.startswith("./"):
        valor = valor[2:]
    return valor


def _compilar_objeto_config(p):
    c = p["chaves"]
    return SimpleNamespace(
        caminho=re.compile(rf"""\b{re.escape(c['caminho'])}\s*:\s*['"]([^'"]*)['"]"""),
        componente=re.compile(rf"""\b{re.escape(c['componente'])}\s*:\s*['"]([^'"]+)['"]"""),
        filhas=re.compile(rf"\b{re.escape(c['filhas'])}\s*:\s*$"),
    )


def _compilar_jsx(p):
    a, tag, e = p["atributos"], re.escape(p["tag"]), re.escape
    return SimpleNamespace(
        nome_caminho=a["caminho"],
        # `<Route ...>`: o parser lê a tag por contagem de chaves e aspas (atributos em qualquer ordem).
        route_abre=re.compile(rf"<{tag}(?=[\s/>])"),
        route_token=re.compile(rf"<{tag}(?=[\s/>])|</{tag}\s*>"),
        path=re.compile(rf"""\b{e(a['caminho'])}\s*=\s*(?:"([^"]*)"|'([^']*)')"""),
        # `path={"/x"}`, `path={'/x'}` e `path={`/x`}`: o template literal só vale sem `${}`.
        path_em_chaves=re.compile(
            rf"""\b{e(a['caminho'])}\s*=\s*\{{\s*(?:"([^"]*)"|'([^']*)'|`((?:(?!\$\{{)[^`])*)`)\s*\}}"""),
        # `path={` logo antes de uma chave no nível da tag: o que sobrou depois dos literais é interpolação ou expressão.
        path_antes_da_chave=re.compile(rf"\b{e(a['caminho'])}\s*=\s*$"),
        indice=re.compile(rf"(?<![\w.=-]){e(a['indice'])}(?![\w=-])"),
        elemento=re.compile(rf"\b{e(a['elemento'])}\s*=\s*\{{"),
        componente=re.compile(rf"\b{e(a['componente'])}\s*=\s*\{{\s*(\w+)\s*\}}"),
        # Propriedades de um objeto de rota (`createBrowserRouter`...), lidas de forma independente.
        obj_caminho=re.compile(rf"""\b{e(a['caminho'])}\s*:\s*['"]([^'"]*)['"]"""),
        filhas=re.compile(rf"\b{e(a['filhas'])}\s*:\s*$"),
        obj_indice=re.compile(rf"\b{e(a['indice'])}\s*:\s*true\b"),
        obj_elemento=re.compile(rf"\b{e(a['elemento'])}\s*:\s*(.*?)(?:,\s*[A-Za-z_]\w*\s*:|$)", re.S),
        obj_componente=re.compile(rf"\b{e(a['componente'])}\s*:\s*(\w+)"),
        obj_lazy=re.compile(rf"""\b{e(a['lazy'])}\s*:\s*\(\s*\)\s*=>\s*import\(\s*['"]([^'"]+)['"]"""),
        listas=re.compile("|".join(f"(?:{x})" for x in p["listas"])),
        nao_tela=set(p.get("nao_tela", [])),
    )


def _compilar_arquivos(p):
    s, c, e = p["segmento"], p["chaves"], re.escape
    cod = bool(p.get("criador"))
    extensoes = tuple(p["extensoes"])
    gerado = None
    if p.get("gerado"):
        gerado = re.compile(rf"(?:^|/){e(p['gerado'])}\.(?:{'|'.join(e(x[1:]) for x in extensoes)})$")
    return SimpleNamespace(
        extensoes=extensoes, gerado=gerado,
        marca_da_pasta=re.compile(p["marca_da_pasta"]) if p.get("marca_da_pasta") else None,
        componente=re.compile(rf"\b{e(c['componente'])}\s*:\s*(\w+)"),
        com_componente=re.compile(rf"\b{e(c['componente'])}\s*:"),
        servidor=re.compile(rf"\b{e(c['servidor'])}\s*:") if c.get("servidor") else NUNCA,
        lazy=(re.compile(rf"""\b{e(p['lazy_funcao'])}\(\s*\(\)\s*=>\s*import\(\s*['"]([^'"]+)['"]""")
              if p.get("lazy_funcao") else NUNCA),
        outlet=re.compile(rf"\b{e(p['outlet'])}\b") if p.get("outlet") else NUNCA,
        criador=_ere_literal(p["criador"]) if cod else None,
        definicao=re.compile(rf"\b(?:const|let|var)\s+(\w+)\s*(?::[^=]+)?=\s*{e(p['criador'])}\b") if cod else None,
        pai=re.compile(rf"\b{e(c['pai'])}\s*:\s*\(\)\s*=>\s*(\w+)") if cod else None,
        path=re.compile(rf"""\b{e(c['caminho'])}\s*:\s*(?:'([^']*)'|"([^"]*)"|`((?:(?!\$\{{)[^`])*)`)""") if cod else None,
        id=re.compile(rf"""\b{e(c['id'])}\s*:\s*['"`]""") if cod else None,
        separadores=re.compile("[/" + e(s["separador"]) + "]"),
        nao_rota=tuple(s.get("nao_rota", [])),
    )


_COMPILADORES = {"objeto-config": _compilar_objeto_config, "jsx": _compilar_jsx, "arquivos": _compilar_arquivos}


def validar_preset(dados, origem, nome_origem="skill"):
    """Valida o preset (estratégia, campos obrigatórios e tipos) e devolve-o pronto: defaults, `/` e regex compiladas."""
    if not isinstance(dados, dict):
        raise PresetInvalido(f"{origem}: o preset deve ser um objeto JSON, não {type(dados).__name__}")
    estrategia = dados.get("estrategia")
    if estrategia is None:
        raise PresetInvalido(f"{origem}: campo «estrategia» obrigatório ausente")
    if estrategia not in ESTRATEGIAS:
        raise PresetInvalido(
            f"{origem}: campo «estrategia» desconhecido ({estrategia!r}); esperado um de: {', '.join(ESTRATEGIAS)}")
    _checar_objeto(dados, _ESQUEMAS[estrategia], "", origem)
    marcas = dados["marcas"]
    if not marcas.get("arquivos") and not marcas.get("conteudo"):
        raise PresetInvalido(f"{origem}: campo «marcas» precisa de «arquivos» ou «conteudo»")
    if estrategia == "arquivos" and dados.get("criador"):
        for chave in ("caminho", "id", "pai"):
            if not dados["chaves"].get(chave):
                raise PresetInvalido(f"{origem}: campo «chaves.{chave}» obrigatório quando «criador» existe")
    preset = json.loads(json.dumps(dados))
    preset.setdefault("prioridade", 100)
    preset["aliases"] = {k.replace("\\", "/"): _prefixo(v) for k, v in preset.get("aliases", ALIASES_PADRAO).items()}
    if preset["marcas"].get("arquivos"):
        preset["marcas"]["arquivos"] = [_barras(a) for a in preset["marcas"]["arquivos"]]
    for campo in ("arquivos", "pasta", "pasta_componentes"):
        if campo in preset:
            preset[campo] = ([_barras(a) for a in preset[campo]] if isinstance(preset[campo], list)
                             else _barras(preset[campo]))
    if "config" in preset:
        preset["config"]["arquivo"] = _barras(preset["config"]["arquivo"])
    preset["_origem"] = nome_origem
    preset["_r"] = _COMPILADORES[estrategia](preset)
    return preset


def carregar_preset(caminho, nome_origem=None):
    """Lê e valida um preset JSON; `nome_origem` (padrão: o caminho) é o que o mapa registra."""
    try:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError) as erro:  # ValueError cobre JSON inválido e UnicodeDecodeError
        raise PresetInvalido(f"Não foi possível ler o preset {caminho}: {erro}") from erro
    return validar_preset(dados, str(caminho), str(caminho) if nome_origem is None else nome_origem)


_PRESETS_DA_SKILL = None


def presets_da_skill():
    """Presets da skill (`scripts/rotas/*.json`), validados e na ordem de precedência (`prioridade`, depois `nome`)."""
    global _PRESETS_DA_SKILL
    if _PRESETS_DA_SKILL is None:
        presets = [carregar_preset(c, "skill") for c in sorted(PASTA_PRESETS.glob("*.json"))]
        _PRESETS_DA_SKILL = sorted(presets, key=lambda p: (p["prioridade"], p["nome"]))
    return _PRESETS_DA_SKILL


def _gerados(presets):
    """[(regex, rótulo)] dos arquivos de rotas gerados que os presets declaram (fora do mapa)."""
    return [(p["_r"].gerado, p["rotulo"]) for p in presets if p["estrategia"] == "arquivos" and p["_r"].gerado]


def _arquivos_do_preset(leitor, preset):
    """Arquivos da revisão que casam com os padrões `arquivos` do preset, na ordem dos padrões."""
    achados = []
    for padrao in preset["arquivos"]:
        achados.extend(c for c in sorted(leitor.caminhos) if fnmatchcase(c, padrao) and c not in achados)
    return achados


def _casa_marcas(leitor, preset):
    """Detecção: o preset vale na revisão se algum arquivo casa com `marcas.arquivos` ou algum código com `marcas.conteudo`."""
    marcas = preset["marcas"]
    if any(fnmatchcase(c, g) for g in marcas.get("arquivos", ()) for c in leitor.caminhos):
        return True
    extensoes = preset["_r"].extensoes if preset["estrategia"] == "arquivos" else EXTENSOES
    return bool(marcas.get("conteudo")) and bool(leitor.buscar(marcas["conteudo"], extensoes))



def _git(repo, *args):
    """Executa o git em `repo` e devolve a saída como texto UTF-8."""
    resultado = subprocess.run(
        GIT + list(args), cwd=repo, check=True, capture_output=True,
    )
    return resultado.stdout.decode("utf-8", errors="replace")


def arvore_vazia(repo):
    """Hash completo da árvore vazia do repositório (SHA-1 ou SHA-256); não grava objeto: é a vigente da primeira sincronização."""
    resultado = subprocess.run(GIT + ["hash-object", "-t", "tree", "--stdin"], cwd=repo, input=b"", check=True, capture_output=True)
    return resultado.stdout.decode("utf-8", errors="replace").strip()


def resolver_sha(repo, ref):
    """SHA do commit para o qual `ref` (branch, tag ou commit) aponta agora; a árvore vazia vale como ela mesma.

    Nenhuma outra árvore é aceita: o erro do git do commit é relançado.
    """
    try:
        return _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").strip()
    except subprocess.CalledProcessError:
        try:
            arvore = _git(repo, "rev-parse", "--verify", f"{ref}^{{tree}}").strip()
        except subprocess.CalledProcessError:
            arvore = None
        if arvore is not None and arvore == arvore_vazia(repo):
            return arvore
        raise


def _status_nome(codigo):
    """Reduz o código do git (`R100`, `T`...) a `A`, `M`, `D` ou `R`."""
    letra = codigo[:1]
    if letra in ("A", "D", "R"):
        return letra
    if letra == "C":
        return "A"
    return "M"


def _ignorado(caminho, gerados):
    return caminho.startswith(PREFIXOS_IGNORADOS) or any(regex.search(caminho) for regex, _ in gerados)


def arquivos_alterados(repo, vigente, candidata, gerados=None):
    """Lista os arquivos alterados entre `vigente` e `candidata`, ordenados por caminho.

    Cada item tem `caminho`, `status` (A, M, D ou R), `origem` (só em R) e `binario`.
    Caminhos sob `PREFIXOS_IGNORADOS` (metadados do processo) e os arquivos de rotas gerados que os presets declaram
    (`routeTree.gen.ts` do TanStack; `gerados` padrão: os dos presets da skill) ficam de fora.
    """
    gerados = _gerados(presets_da_skill()) if gerados is None else gerados
    return [a for a in _alterados_todos(repo, vigente, candidata) if not _ignorado(a["caminho"], gerados)]


def arquivos_ignorados(repo, vigente, candidata, gerados=None):
    """Caminhos alterados sob `PREFIXOS_IGNORADOS` ou de rotas geradas dos presets, ordenados."""
    gerados = _gerados(presets_da_skill()) if gerados is None else gerados
    return [a["caminho"] for a in _alterados_todos(repo, vigente, candidata) if _ignorado(a["caminho"], gerados)]


def _alterados_todos(repo, vigente, candidata):
    repo = Path(repo)
    campos = _git(repo, "diff", "--name-status", "-M", "-z", vigente, candidata, "--").split("\0")
    itens = {}
    i = 0
    while i < len(campos) and campos[i]:
        status = _status_nome(campos[i])
        if campos[i][:1] in ("R", "C"):
            origem, caminho = campos[i + 1], campos[i + 2]
            i += 3
        else:
            origem, caminho = None, campos[i + 1]
            i += 2
        item = {"caminho": caminho, "status": status, "binario": False}
        if status == "R":
            item["origem"] = origem
        itens[caminho] = item

    # numstat marca binário com `-\t-`; em renomeação o caminho vem em campos separados.
    partes = _git(repo, "diff", "--numstat", "-M", "-z", vigente, candidata, "--").split("\0")
    i = 0
    while i < len(partes) and partes[i]:
        adicionadas, _, resto = partes[i].partition("\t")
        removidas, _, caminho = resto.partition("\t")
        if caminho == "":
            caminho = partes[i + 2]
            i += 3
        else:
            i += 1
        if caminho in itens:
            itens[caminho]["binario"] = adicionadas == "-" and removidas == "-"
    return [itens[c] for c in sorted(itens)]


def e_lockfile(caminho):
    """Lockfile (ou binário versionado do yarn): lido como um trecho só, nunca cortado por linhas nem por chave."""
    return (posixpath.basename(caminho) in LOCKFILES
            or any(caminho.startswith(p) or f"/{p}" in caminho for p in PREFIXOS_LOCKFILE))


def _arquivo_de_chave(caminho):
    """Locale, i18n e JSON são cortados por chave, não por linhas."""
    minusculo = caminho.lower()
    return "locale" in minusculo or "i18n" in minusculo or minusculo.endswith(".json")


def _trecho(arquivo, status, tipo, linhas=None, chave=None, id_=None):
    if id_ is None:
        if tipo == "arquivo":
            id_ = f"{arquivo}#arquivo"
        elif tipo == "chave":
            id_ = f"{arquivo}#{chave}"
        else:
            id_ = f"{arquivo}#L{linhas[0]}-{linhas[1]}"
    return {"id": id_, "arquivo": arquivo, "tipo": tipo, "linhas": linhas, "chave": chave, "status": status}


def _hunks(diff):
    """Extrai os hunks do `-U0`: cabeçalho numérico e as linhas `+`/`-` com seus números."""
    hunks = []
    atual = None
    for linha in diff.split("\n"):
        m = HUNK.match(linha)
        if m:
            antigo_ini, antigo_n, novo_ini, novo_n = m.groups()
            atual = {
                "antigo": (int(antigo_ini), 1 if antigo_n is None else int(antigo_n)),
                "novo": (int(novo_ini), 1 if novo_n is None else int(novo_n)),
                "linhas": [],
            }
            hunks.append(atual)
            novo_atual = int(novo_ini)
            continue
        if atual is None or not linha or linha[0] not in "+-":
            continue
        if linha[0] == "+":
            atual["linhas"].append(("+", linha[1:], novo_atual))
            novo_atual += 1
        else:
            atual["linhas"].append(("-", linha[1:], None))
    return hunks


def _trecho_de_linhas(arquivo, status, hunk):
    antigo_ini, antigo_n = hunk["antigo"]
    novo_ini, novo_n = hunk["novo"]
    if novo_n == 0:
        # Remoção pura: o lado novo não tem linhas; o id usa o lado antigo para não colidir.
        return _trecho(arquivo, status, "linhas", None, id_=f"{arquivo}#del:L{antigo_ini}-{antigo_ini + antigo_n - 1}")
    return _trecho(arquivo, status, "linhas", [novo_ini, novo_ini + novo_n - 1])


def _trechos_do_arquivo(repo, vigente, candidata, alterado):
    arquivo, status = alterado["caminho"], alterado["status"]
    if e_lockfile(arquivo):
        return [_trecho(arquivo, status, "arquivo")]
    # Só binário e removido são trecho único; adicionado de texto passa pelo hunk `@@ -0,0 +1,N @@`.
    if status == "D" or alterado["binario"]:
        return [_trecho(arquivo, status, "arquivo")]
    pathspec = [alterado["origem"], arquivo] if status == "R" else [arquivo]
    diff = _git(repo, "diff", "-U0", "--no-color", "--no-ext-diff", "-M", vigente, candidata, "--", *pathspec)
    por_chave = _arquivo_de_chave(arquivo)
    trechos = []
    for hunk in _hunks(diff):
        sem_chave = not por_chave
        if por_chave:
            for sinal, texto, numero in hunk["linhas"]:
                m = CHAVE.match(texto)
                if not m:
                    # Em arquivo de chave adicionado, só o invólucro estrutural não vira trecho.
                    if not (status == "A" and ESTRUTURAL.match(texto)):
                        sem_chave = True
                    continue
                chave = m.group(2)
                existente = next((t for t in trechos if t["id"] == f"{arquivo}#{chave}"), None)
                if existente is None:
                    existente = _trecho(arquivo, status, "chave", None, chave)
                    trechos.append(existente)
                if sinal == "+":
                    ini = existente["linhas"][0] if existente["linhas"] else numero
                    existente["linhas"] = [ini, numero]
        if sem_chave:
            trechos.append(_trecho_de_linhas(arquivo, status, hunk))
    # Sem hunks (renomeação pura, modo alterado, arquivo adicionado vazio): o arquivo inteiro é um trecho.
    return trechos or [_trecho(arquivo, status, "arquivo")]


def listar_trechos(repo, vigente, candidata, gerados=None):
    """Corta o diff `vigente..candidata` em trechos, ordenados e sem ids repetidos."""
    repo = Path(repo)
    por_id = {}
    for alterado in arquivos_alterados(repo, vigente, candidata, gerados):
        for trecho in _trechos_do_arquivo(repo, vigente, candidata, alterado):
            por_id.setdefault(trecho["id"], trecho)
    return [por_id[i] for i in sorted(por_id)]


class _Leitor:
    """Lê arquivos de uma revisão com `git ls-tree`/`git show`, sem checkout e com cache."""

    def __init__(self, repo, rev):
        self.repo, self.rev = repo, rev
        saida = _git(repo, "ls-tree", "-r", "--name-only", "-z", rev)
        self.caminhos = {c for c in saida.split("\0") if c}
        self._cache = {}
        self._buscas = {}
        # Aliases de import (`@/` -> `src/`): os dos presets em uso, definidos por `_rotas`.
        self.aliases = dict(ALIASES_PADRAO)

    def existe(self, caminho):
        return caminho in self.caminhos

    def bytes_de(self, caminho):
        if caminho not in self._cache:
            conteudo = None
            if caminho in self.caminhos:
                r = subprocess.run(GIT + ["show", f"{self.rev}:{caminho}"], cwd=self.repo, capture_output=True)
                conteudo = r.stdout if r.returncode == 0 else None
            self._cache[caminho] = conteudo
        return self._cache[caminho]

    def texto(self, caminho):
        conteudo = self.bytes_de(caminho)
        return None if conteudo is None else conteudo.decode("utf-8", errors="replace")

    def buscar(self, padrao, extensoes=EXTENSOES):
        """Caminhos de código (`extensoes`) da revisão cujo conteúdo casa com `padrao` (ERE), por um só `git grep`."""
        chave = (padrao, tuple(extensoes))
        if chave not in self._buscas:
            r = subprocess.run(GIT + ["grep", "-l", "-z", "-E", "-e", padrao, self.rev, "--"], cwd=self.repo, capture_output=True)
            if r.returncode not in (0, 1):
                detalhe = r.stderr.decode("utf-8", errors="replace").strip()
                raise PresetInvalido(
                    f"git grep falhou (código {r.returncode}) em {self.rev} com a expressão {padrao!r}: {detalhe or 'sem mensagem'}")
            achados = []
            if r.returncode == 0:
                prefixo = f"{self.rev}:"
                brutos = (c.decode("utf-8", errors="replace") for c in r.stdout.split(b"\0") if c)
                achados = sorted(c[len(prefixo):] for c in brutos if c.startswith(prefixo) and c.endswith(tuple(extensoes)))
            self._buscas[chave] = achados
        return self._buscas[chave]


def _resolver(leitor, base):
    """Acha o arquivo de `base` (sem extensão ou com) na revisão: `base`, `base.tsx`..., `base/index.tsx`..."""
    base = posixpath.normpath(base)
    candidatos = [base] + [base + e for e in EXTENSOES] + [f"{base}/index{e}" for e in EXTENSOES]
    return next((c for c in candidatos if leitor.existe(c)), None)


def _alias_de(leitor, especificador):
    """Alias de import que abre `especificador` (o mais longo), ou None."""
    return max((a for a in leitor.aliases if especificador.startswith(a)), key=len, default=None)


def _import_local(leitor, especificador):
    """O import aponta para um arquivo do projeto: relativo (`./`, `../`) ou por alias."""
    return especificador.startswith(("./", "../")) or _alias_de(leitor, especificador) is not None


def _resolver_import(leitor, origem, especificador):
    alias = _alias_de(leitor, especificador)
    if alias is not None:
        base = leitor.aliases[alias] + especificador[len(alias):]
    else:
        base = posixpath.join(posixpath.dirname(origem), especificador)
    return _resolver(leitor, base)


def _abre_string(texto, i):
    """A aspa em `texto[i]` abre uma string. Aspa simples ou dupla colada a letra, dígito, `)` ou `]` é o apóstrofo do texto
    JSX («Don't»), não abre; a crase sempre abre. Regra única de aspa: `_sem_comentarios`, `_fim_do_bloco`, `_fim_da_tag` e a
    estrutura do cruzamento usam esta função."""
    return texto[i] == "`" or i == 0 or not (texto[i - 1].isalnum() or texto[i - 1] in ")]")


def _sem_comentarios(texto):
    """Troca comentários `//` e `/* */` por espaços (mantém quebras de linha), sem mexer em strings."""
    saida, i, aspa = [], 0, None
    while i < len(texto):
        c, dois = texto[i], texto[i:i + 2]
        if aspa:
            saida.append(c)
            if c == "\\" and i + 1 < len(texto):
                saida.append(texto[i + 1])
                i += 1
            elif c == aspa:
                aspa = None
        elif c in "'\"`" and _abre_string(texto, i):
            aspa = c
            saida.append(c)
        elif dois == "//":
            while i < len(texto) and texto[i] != "\n":
                i += 1
            continue
        elif dois == "/*":
            fim = texto.find("*/", i + 2)
            fim = len(texto) if fim < 0 else fim + 2
            saida.append("".join("\n" if x == "\n" else " " for x in texto[i:fim]))
            i = fim
            continue
        else:
            saida.append(c)
        i += 1
    return "".join(saida)


def _fim_do_bloco(texto, ini):
    """Índice do fecho que casa com o abre em `texto[ini]` (`{`, `[` ou `(`), respeitando strings."""
    pares = {"{": "}", "[": "]", "(": ")"}
    pilha, i, aspa = [], ini, None
    while i < len(texto):
        c = texto[i]
        if aspa:
            if c == "\\":
                i += 1
            elif c == aspa:
                aspa = None
        elif c in "'\"`" and _abre_string(texto, i):
            aspa = c
        elif c in pares:
            pilha.append(pares[c])
        elif c in ")}]" and pilha:
            pilha.pop()
            if not pilha:
                return i
        i += 1
    return len(texto) - 1


def _juntar_rota(pai, caminho, indice=False):
    """Rota de um objeto/tag: `caminho` absoluto vale sozinho, relativo junta ao do pai; sem caminho vale o do pai."""
    if not caminho:
        return pai or ("/" if indice else "")
    if caminho.startswith("/") or not pai:
        return caminho
    return pai.rstrip("/") + "/" + caminho


def _rotas_objetos(texto, pai, caminho_re, filhas_re, componente_de, indice_de=None, manter_parenteses=False):
    """Lê uma lista de objetos de rota de forma estrutural: [(rota, referência)] de objetos com componente.

    Cada `{...}` é lido por contagem de chaves; a lista de filhas (`filhas_re`) é recursiva e o caminho (`caminho_re`) relativo
    de uma filha se junta ao do pai. Objeto com filhas não é tela, mesmo com componente (layout).
    `componente_de(plana)` devolve a referência do componente (pode ser None se não resolvida) ou False se não houver.
    """
    rotas, i = [], 0
    while True:
        ini = texto.find("{", i)
        if ini < 0:
            return rotas
        fim = _fim_do_bloco(texto, ini)
        corpo = texto[ini + 1:fim]
        i = fim + 1
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
                fecho = _fim_do_bloco(corpo, j)
                if c == "[" and filhas_re.search("".join(plana)):
                    filhas = corpo[j + 1:fecho]
                plana.append(corpo[j:fecho + 1] if c == "(" and manter_parenteses else " ")
                j = fecho
            else:
                plana.append(c)
            j += 1
        plana = "".join(plana)
        m_path = caminho_re.search(plana)
        rota = _juntar_rota(pai, m_path.group(1) if m_path else None, bool(indice_de and indice_de(plana)))
        if filhas is not None:
            rotas.extend(_rotas_objetos(filhas, rota, caminho_re, filhas_re, componente_de, indice_de, manter_parenteses))
            continue
        referencia = componente_de(plana)
        if referencia is not False and rota:
            rotas.append((rota, referencia))


def _rotas_objeto_config(texto, r, pai=""):
    """Rotas de uma lista de objetos de configuração (Umi): [(rota, componente)] dos objetos com componente."""
    def componente(plana):
        m = r.componente.search(plana)
        return m.group(1) if m else False
    return _rotas_objetos(texto, pai, r.caminho, r.filhas, componente)


def _importados(texto):
    """Nome local -> especificador, de imports default, nomeados (`A as B`) e `lazy(() => import(...))`."""
    nomes = {}
    for clausula, especificador in IMPORT_DECL.findall(texto):
        nomeados = re.search(r"\{([^}]*)\}", clausula)
        if nomeados:
            for item in nomeados.group(1).split(","):
                partes = item.strip().removeprefix("type ").split(" as ")
                if partes[-1].strip():
                    nomes[partes[-1].strip()] = especificador
        padrao = re.match(r"\s*(\w+)\s*(?:,|$)", clausula)
        if padrao:
            nomes[padrao.group(1)] = especificador
    nomes.update(IMPORT_LAZY.findall(texto))
    return nomes


def _sem_chaves(texto):
    """Troca cada `{...}` (valor de prop) por um espaço."""
    saida, i = [], 0
    while i < len(texto):
        if texto[i] == "{":
            i = _fim_do_bloco(texto, i) + 1
            saida.append(" ")
        else:
            saida.append(texto[i])
            i += 1
    return "".join(saida)


def _nome_da_pagina(elemento, nao_tela):
    """Componente de página dentro de um elemento JSX: ignora `nao_tela` (`Navigate`, `Outlet`), props `={...}` e invólucros com filhos."""
    limpo = _sem_chaves(elemento)
    # `<B></B>` (fechamento explícito, sem filhos) é o próprio componente, não um invólucro.
    limpo = re.sub(r"<\s*([A-Z][\w.]*)((?:\s[^<>]*)?)>\s*</\s*\1\s*>", r"<\1\2/>", limpo)
    nomes = [n for n in TAG_JSX.findall(limpo)
             if n not in nao_tela and not re.search(rf"</\s*{re.escape(n)}\s*>", limpo)]
    return nomes[0] if nomes else None


def _fim_da_tag(texto, i):
    """Índice do `>` que fecha a tag aberta antes de `i` e se ela é auto-fechada (`/>`); respeita aspas e chaves."""
    aspa = None
    while i < len(texto):
        c = texto[i]
        if aspa:
            if c == aspa:
                aspa = None
        elif c in "'\"`" and _abre_string(texto, i):
            aspa = c
        elif c == "{":
            i = _fim_do_bloco(texto, i)
        elif c == ">":
            return i, texto[:i].rstrip().endswith("/")
        i += 1
    return len(texto), False


def _fecho_route(texto, i, token):
    """Posição `(início, fim)` do `</Route>` que casa com o `<Route>` aberto antes de `i` (`token` acha abertura e fecho)."""
    profundidade, pos = 1, i
    while True:
        m = token.search(texto, pos)
        if m is None:
            return len(texto), len(texto)
        if m.group(0).startswith("</"):
            profundidade -= 1
            if profundidade == 0:
                return m.start(), m.end()
            pos = m.end()
        else:
            fim, auto = _fim_da_tag(texto, m.end())
            if not auto:
                profundidade += 1
            pos = fim + 1


def _path_literal_em_chaves(m, nome):
    """`path={"/x"}` -> `path="/x"` (aspas simples se o valor tem aspas duplas); `nome` é o atributo do caminho."""
    valor = next(g for g in m.groups() if g is not None)
    return f"{nome}='{valor}'" if '"' in valor else f'{nome}="{valor}"'


def _path_dinamico(cab, antes_da_chave):
    """O `<Route>` tem `path={...}` não literal entre os atributos da própria tag (nunca dentro de `element={...}` e afins)."""
    i, aspa = 0, None
    while i < len(cab):
        c = cab[i]
        if aspa:
            if c == aspa:
                aspa = None
        elif c in "'\"":
            aspa = c
        elif c == "{":
            if antes_da_chave.search(cab[:i]):
                return True
            i = _fim_do_bloco(cab, i)
        i += 1
    return False


def _rotas_jsx(texto, importados, r, pai="", dinamicas=None, deslocamento=0):
    """Rotas de tags `<Route>`: [(rota, especificador)]. Atributos em qualquer ordem; filhas relativas se juntam ao pai.

    `<Route>` com `path` dinâmico (interpolação ou expressão) não vira rota, nem as filhas dele; se `dinamicas` for uma
    lista, recebe o deslocamento de cada uma dessas tags no texto inteiro (`deslocamento` é o de `texto` nele).
    """
    rotas, i = [], 0
    while True:
        m = r.route_abre.search(texto, i)
        if m is None:
            return rotas
        fim, auto = _fim_da_tag(texto, m.end())
        cab = r.path_em_chaves.sub(lambda achado: _path_literal_em_chaves(achado, r.nome_caminho), texto[m.end():fim])
        i = fim + 1
        filhas = None
        if not auto:
            ini_fecho, i = _fecho_route(texto, i, r.route_token)
            filhas = texto[fim + 1:ini_fecho]
        if _path_dinamico(cab, r.path_antes_da_chave):
            if dinamicas is not None:
                dinamicas.append(deslocamento + m.start())
            continue
        plano = _sem_chaves(cab)
        m_path = r.path.search(plano)
        caminho = (m_path.group(1) if m_path.group(1) is not None else m_path.group(2)) if m_path else None
        rota = _juntar_rota(pai, caminho, bool(r.indice.search(plano)))
        if filhas is not None:
            rotas.extend(_rotas_jsx(filhas, importados, r, rota, dinamicas, deslocamento + fim + 1))
            continue
        m_comp, m_elem = r.componente.search(cab), r.elemento.search(cab)
        nome = m_comp.group(1) if m_comp else None
        if nome is None and m_elem:
            ini = m_elem.end() - 1
            nome = _nome_da_pagina(cab[ini + 1:_fim_do_bloco(cab, ini)], r.nao_tela)
        if nome is not None and rota:
            rotas.append((rota, importados.get(nome)))


def _rotas_objetos_react(texto, importados, r):
    """Rotas de listas de objetos `{ path, element, children }` (`createBrowserRouter`, `useRoutes`...): [(rota, especificador)]."""
    def componente(plana):
        m = r.obj_lazy.search(plana)
        if m:
            return m.group(1)
        m = r.obj_componente.search(plana)
        nome = m.group(1) if m else None
        if nome is None:
            m = r.obj_elemento.search(plana)
            nome = _nome_da_pagina(m.group(1), r.nao_tela) if m else None
        return False if nome is None else importados.get(nome)

    rotas = []
    for m in r.listas.finditer(texto):
        ini = m.end() - 1
        rotas.extend(_rotas_objetos(
            texto[ini + 1:_fim_do_bloco(texto, ini)], "", r.obj_caminho, r.filhas, componente,
            lambda plana: r.obj_indice.search(plana), manter_parenteses=True))
    return rotas


def _config_do_preset(leitor, preset):
    """Arquivo de configuração do roteador na revisão (dict) ou None se o preset não tem ou ele não existe; `{}` se ilegível."""
    if "config" not in preset:
        return None
    texto = leitor.texto(preset["config"]["arquivo"])
    if texto is None:
        return None
    try:
        config = json.loads(texto)
    except ValueError:
        return {}
    return config if isinstance(config, dict) else {}


def _pasta_de_rotas(preset, config):
    pasta = config.get(preset["config"]["chave_pasta"]) if config else None
    return posixpath.normpath(pasta.replace("\\", "/")) if isinstance(pasta, str) and pasta.strip() else preset["pasta"]


def _parte_de_arquivo(relativo, preset):
    """Convenção de nome do roteamento por arquivo: `(id, lazy, layout)` do arquivo de rota, ou None se não for rota.

    `id` é a tupla de segmentos (pastas e o separador do nome separam segmentos; o nome de layout final some, o índice
    e os prefixos de sem-caminho, grupo e parâmetro ficam). Arquivo ou pasta com o prefixo de ignorado e arquivo que
    não é de código não são rotas.
    """
    r, s = preset["_r"], preset["segmento"]
    base = next((relativo[:-len(e)] for e in r.extensoes if relativo.endswith(e)), None)
    if base is None or base.endswith(r.nao_rota):
        return None
    lazy = base.endswith(s["sufixo_lazy"])
    if lazy:
        base = base[:-len(s["sufixo_lazy"])]
    partes = r.separadores.split(base)
    if not all(partes) or any(p.startswith(s["ignorado"]) for p in partes):
        return None
    layout = partes[-1] == s["layout"]
    if layout:
        partes = partes[:-1]
    return tuple(partes), lazy, layout


def _rota_do_id(partes, preset):
    """Caminho de URL de um id: sem-caminho e grupo não geram caminho, o sufixo sem-aninhamento cai, o índice final some.

    O parâmetro dinâmico (`$id`, `:id`...) sai com `$` na rota do mapa, qualquer que seja o prefixo do nome do arquivo.
    """
    s = preset["segmento"]
    sem_caminho, sem_aninhamento, (abre, fecha) = s["sem_caminho"], s["sem_aninhamento"], s["grupo"]
    if partes and partes[-1] == s["indice"]:
        partes = partes[:-1]

    def normal(p):
        if p.endswith(sem_aninhamento) and not p.startswith(sem_caminho):
            while p.endswith(sem_aninhamento):
                p = p[:-len(sem_aninhamento)]
        return "$" + p[len(s["parametro"]):] if p.startswith(s["parametro"]) else p

    segmentos = [normal(p) for p in partes if not p.startswith(sem_caminho) and not (p.startswith(abre) and p.endswith(fecha))]
    return "/" + "/".join(x for x in segmentos if x)


def _componente_de_rota(leitor, arquivo, texto, importados, preset):
    """Arquivo do componente de uma rota: o importado de outro arquivo do projeto, senão o próprio arquivo."""
    r = preset["_r"]
    lazy = r.lazy.search(texto)
    especificador = lazy.group(1) if lazy else None
    if especificador is None:
        m = r.componente.search(_sem_chaves_aninhadas(texto))
        especificador = importados.get(m.group(1)) if m else None
    if especificador and _import_local(leitor, especificador):
        return _resolver_import(leitor, arquivo, especificador) or arquivo
    return arquivo


def _sem_chaves_aninhadas(texto):
    """Só o objeto de opções do `createFileRoute(...)({ ... })`, sem os `{...}` internos (não lê `component` de dentro)."""
    m = re.search(r"\)\s*\(\s*\{", texto) or re.search(r"create\w*Route\w*\s*\(\s*\{", texto)
    if m is None:
        return texto
    ini = m.end() - 1
    return _sem_chaves(texto[ini + 1:_fim_do_bloco(texto, ini)])


def _so_servidor(texto, r):
    """Rota de servidor (`server: { handlers }`, ex.: `api.health.ts`) sem `component`: responde HTTP, não é tela."""
    opcoes = _sem_chaves_aninhadas(texto)
    return r.servidor.search(opcoes) is not None and r.com_componente.search(opcoes) is None


def _rotas_por_arquivo(leitor, preset):
    """Rotas por arquivo: lista de dicts `rota`, `arquivo`, `origem` (arquivo de rota) e `extras` (dependências da tela)."""
    r, s = preset["_r"], preset["segmento"]
    config = _config_do_preset(leitor, preset)
    pasta = _pasta_de_rotas(preset, config)
    prefixo = pasta + "/"
    candidatos, por_route = {}, set()
    for caminho in sorted(leitor.caminhos):
        if not caminho.startswith(prefixo):
            continue
        convencao = _parte_de_arquivo(caminho[len(prefixo):], preset)
        if convencao is not None:
            candidatos.setdefault(convencao[0], {})[convencao[1]] = caminho
            if convencao[2]:
                por_route.add(convencao[0])
    textos = {c: _sem_comentarios(leitor.texto(c) or "") for g in candidatos.values() for c in g.values()}
    # Sem arquivo de configuração, a pasta só vale se algum arquivo dela tiver a marca do roteador (`src/routes/` também
    # existe em apps de outros roteadores); preset sem `marca_da_pasta` vale a pasta sempre.
    if config is None and r.marca_da_pasta is not None and not any(r.marca_da_pasta.search(t) for t in textos.values()):
        return []

    raiz_id = (s["raiz"],)
    raiz = candidatos.get(raiz_id, {})
    grupos = {i: g for i, g in candidatos.items() if i != raiz_id}
    sem_caminho, (abre, fecha) = s["sem_caminho"], s["grupo"]
    layouts = {}
    for ident, grupo in grupos.items():
        arquivos = [grupo[k] for k in (False, True) if k in grupo]
        ultimo = ident[-1] if ident else s["layout"]
        filhas = any(len(o) > len(ident) and o[:len(ident)] == ident for o in grupos)
        texto = "\n".join(textos[c] for c in arquivos)
        sem_rota = (ident in por_route or not ident or ultimo.startswith(sem_caminho)
                    or (ultimo.startswith(abre) and ultimo.endswith(fecha)))
        layouts[ident] = sem_rota or (filhas and r.outlet.search(texto) is not None)

    rotas = []
    for ident in sorted(grupos, key=lambda i: (len(i), i)):
        if layouts[ident]:
            continue
        grupo = grupos[ident]
        arquivos = [grupo[k] for k in (False, True) if k in grupo]
        if all(_so_servidor(textos[c], r) for c in arquivos):
            continue
        dono = grupo.get(True) or grupo[False]
        componente = dono
        for caminho in [dono] + [c for c in arquivos if c != dono]:
            alvo = _componente_de_rota(leitor, caminho, textos[caminho], _importados(textos[caminho]), preset)
            if alvo != caminho:
                componente = alvo
                break
        extras = {c for c in arquivos if c != componente}
        extras.update(c for c in raiz.values())
        for corte in range(len(ident)):
            pai = grupos.get(ident[:corte])
            if pai is not None and layouts[ident[:corte]]:
                extras.update(pai.values())
        extras.discard(componente)
        rotas.append({"rota": _rota_do_id(ident, preset), "arquivo": componente, "origem": grupo.get(False) or grupo[True],
                      "extras": sorted(extras)})
    return rotas


def _juntar_caminhos(*caminhos):
    return "/" + "/".join(s for c in caminhos for s in c.strip("/").split("/") if s)


def _rotas_por_codigo(leitor, preset):
    """Rotas por código (`createRoute({ getParentRoute, path, component })`), com o caminho resolvido pelo pai."""
    r = preset["_r"]
    if r.criador is None:
        return []
    defs = {}
    for caminho in leitor.buscar(r.criador, r.extensoes):
        if r.gerado is not None and r.gerado.search(caminho):
            continue
        texto = _sem_comentarios(leitor.texto(caminho) or "")
        importados = _importados(texto)
        for m in r.definicao.finditer(texto):
            abre = texto.find("{", m.end())
            if abre < 0:
                continue
            bruto = texto[abre + 1:_fim_do_bloco(texto, abre)]
            corpo = _sem_chaves(bruto)
            pai = r.pai.search(corpo)
            if pai is None:
                # `createRoute` sem `getParentRoute` é de outra biblioteca (ex.: OpenAPI), não do roteador.
                continue
            path = r.path.search(corpo)
            lazy = r.lazy.search(bruto)
            componente = r.componente.search(corpo)
            defs[(caminho, m.group(1))] = {
                "pai": pai.group(1), "importados": importados,
                "path": next((g for g in path.groups() if g is not None), "") if path and not r.id.search(corpo) else "",
                "componente": lazy.group(1) if lazy else (importados.get(componente.group(1)) if componente else None),
                "abre": abre, "arquivo": caminho,
            }

    def achar_pai(d):
        if (d["arquivo"], d["pai"]) in defs:
            return defs[(d["arquivo"], d["pai"])]
        especificador = d["importados"].get(d["pai"])
        if especificador and _import_local(leitor, especificador):
            alvo = _resolver_import(leitor, d["arquivo"], especificador)
            return defs.get((alvo, d["pai"]))
        return None

    com_filhas = {id(achar_pai(d)) for d in defs.values() if achar_pai(d) is not None}
    rotas = []
    for d in sorted(defs.values(), key=lambda x: (x["arquivo"], x["abre"])):
        if id(d) in com_filhas:
            continue
        caminhos, ancestrais, atual, vistos = [], [], d, set()
        while atual is not None and id(atual) not in vistos:
            vistos.add(id(atual))
            caminhos.insert(0, atual["path"])
            ancestrais.append(atual["arquivo"])
            atual = achar_pai(atual)
        componente = d["componente"]
        arquivo = d["arquivo"]
        if componente and _import_local(leitor, componente):
            arquivo = _resolver_import(leitor, d["arquivo"], componente) or d["arquivo"]
        rotas.append({"rota": _juntar_caminhos(*caminhos), "arquivo": arquivo, "origem": d["arquivo"],
                      "extras": sorted(set(ancestrais) - {arquivo})})
    return rotas


def _rotas(leitor, fontes=None, dinamicas=None, extras=None, formatos=None, presets=None, aplicados=None):
    """Rotas da revisão: rota -> arquivo ou None, lidas pelos presets (Umi, React Router e TanStack Router na skill).

    Sem `presets`, usa os da skill e aplica as marcas de detecção de cada um à revisão; com `presets` (`--rotas`), usa só
    esses e pula a detecção. Na ordem de `prioridade` dos presets, a primeira rota repetida vale.
    Se `fontes` for um dict, recebe rota -> arquivo que a declara (onde um troca de componente aparece no diff).
    Se `dinamicas` for uma lista, recebe `(arquivo, linha)` de cada `<Route>` com `path` dinâmico, que não é lida.
    Se `extras` for um dict, recebe rota -> arquivos que a tela atravessa sem importar (layouts e arquivo de rota do TanStack).
    Se `formatos` for uma lista, recebe o rótulo de cada formato que deu ao menos uma rota.
    Se `aplicados` for uma lista, recebe `(preset, n)` de cada preset usado na revisão, com `n` rotas que ele deu ao mapa.
    """
    rotas = {}
    fontes = {} if fontes is None else fontes
    if presets is None:
        usados = [p for p in presets_da_skill() if _casa_marcas(leitor, p)]
    else:
        usados = sorted(presets, key=lambda p: (p["prioridade"], p["nome"]))
    contagem = {p["nome"]: 0 for p in usados}
    if usados:
        leitor.aliases = {a: v for p in usados for a, v in p["aliases"].items()}

    def registrar(rota, arquivo, origem, preset):
        if rota not in rotas:
            rotas[rota], fontes[rota] = arquivo, origem
            contagem[preset["nome"]] += 1
            if formatos is not None and preset["rotulo"] not in formatos:
                formatos.append(preset["rotulo"])
            return True
        return False

    por_arquivos = {p["nome"]: _rotas_por_arquivo(leitor, p) + _rotas_por_codigo(leitor, p)
                    for p in usados if p["estrategia"] == "arquivos"}
    # Arquivos de rota das estratégias por arquivo (`src/routes/index.tsx`, `src/router.tsx`) são tela e rotas por código
    # lidas à parte: o `jsx` não os lê de novo.
    reivindicados = {r["origem"] for lista in por_arquivos.values() for r in lista}
    for preset in usados:
        estrategia, r = preset["estrategia"], preset["_r"]
        if estrategia == "objeto-config":
            for caminho in _arquivos_do_preset(leitor, preset):
                texto = _sem_comentarios(leitor.texto(caminho) or "")
                inicio = texto.find("[")
                for rota, componente in _rotas_objeto_config(texto[inicio + 1:] if inicio >= 0 else "", r):
                    if _alias_de(leitor, componente) is not None or componente.startswith("../"):
                        arquivo = _resolver_import(leitor, caminho, componente)
                    else:
                        arquivo = _resolver(leitor, preset["pasta_componentes"] + "/" + componente.removeprefix("./"))
                    registrar(rota, arquivo, caminho, preset)
        elif estrategia == "jsx":
            for caminho in _arquivos_do_preset(leitor, preset):
                texto = leitor.texto(caminho)
                if texto is None or caminho in reivindicados:
                    continue
                texto = _sem_comentarios(texto)
                importados = _importados(texto)
                posicoes = []
                for rota, especificador in _rotas_jsx(texto, importados, r, dinamicas=posicoes) + _rotas_objetos_react(texto, importados, r):
                    arquivo = None
                    if especificador and _import_local(leitor, especificador):
                        arquivo = _resolver_import(leitor, caminho, especificador)
                    registrar(rota, arquivo, caminho, preset)
                if dinamicas is not None:
                    dinamicas.extend((caminho, texto.count("\n", 0, posicao) + 1) for posicao in posicoes)
        else:
            for item in por_arquivos[preset["nome"]]:
                if registrar(item["rota"], item["arquivo"], item["origem"], preset) and extras is not None:
                    extras[item["rota"]] = item["extras"]
    if aplicados is not None:
        aplicados.extend((p, contagem[p["nome"]]) for p in usados)
    return rotas


def _imports_locais(leitor):
    """Regex dos imports do projeto: relativos (`./`, `../`) e por alias (`@/`, do preset em uso)."""
    inicios = r"\.{1,2}/" + "".join("|" + re.escape(a) for a in sorted(leitor.aliases))
    return re.compile(rf"""(?:from\s+|import\s*\(?\s*)['"]((?:{inicios})[^'"]+)['"]""")


def _dependencias(leitor, arquivo):
    """Fecho transitivo dos imports relativos e por alias de `arquivo`, ordenado e sem o próprio arquivo."""
    vistos, pilha, imports = set(), [arquivo], _imports_locais(leitor)
    while pilha:
        atual = pilha.pop()
        for especificador in imports.findall(leitor.texto(atual) or ""):
            alvo = _resolver_import(leitor, atual, especificador)
            if alvo and alvo != arquivo and alvo not in vistos:
                vistos.add(alvo)
                pilha.append(alvo)
    return sorted(vistos)


def _slug_da_rota(rota):
    """`TL-` + rota em minúsculas; fora de [a-z0-9-] vira `-` (repetições colapsam) e `*` vira `curinga`."""
    corpo = re.sub(r"[^a-z0-9-]+", "-", rota.replace("*", "curinga").lower())
    return "TL-" + (re.sub(r"-+", "-", corpo).strip("-") or "raiz")


def _campos_de_rota(aplicados):
    """arquivo de rotas -> nome do campo do caminho (`chaves.caminho`), dos presets `objeto-config` em uso."""
    return {a: p["chaves"]["caminho"] for p, _ in aplicados if p["estrategia"] == "objeto-config" for a in p["arquivos"]}


def _tipo_acoplamento(caminho, campos_de_rota=None):
    """Tipo de acoplamento de um arquivo alterado pelo caminho, ou None se não for fonte de acoplamento.

    `campos_de_rota` (veja `_campos_de_rota`) diz quais arquivos o preset em uso lê como lista de rotas.
    """
    partes = caminho.lower().split("/")
    nomes = partes[:-1] + [partes[-1].rsplit(".", 1)[0]]
    if caminho in (campos_de_rota or {}) or ("config" in partes[:-1] and re.match(r"routes?$|router$", nomes[-1])):
        return "rota"
    if any(n in ("mock", "_mock", "mocks") for n in nomes):
        return "mock"
    if "locale" in caminho.lower() or "i18n" in caminho.lower():
        return "locale"
    if any(n.startswith(("theme", "tema")) for n in nomes):
        return "tema"
    if any(n in ("store", "stores") for n in nomes):
        return "store"
    if "config" in partes[:-1] or _arquivo_de_chave(caminho):
        return "config"
    return None


SEM_VALOR = re.compile(r"""^\s*(['"]?)([\w.\-]+)\1\s*:\s*$""")
REMOCAO = re.compile(r"#del:L(\d+)-(\d+)$")


def _chave_do_valor_seguinte(linhas, numero):
    """Chave cuja linha (`numero`, de 1) é a anterior à dada e só tem a chave, com o valor na linha seguinte (ant-design-pro)."""
    m = SEM_VALOR.match(linhas[numero - 2]) if 2 <= numero <= len(linhas) + 1 else None
    return m.group(2) if m else None


def _chaves_de_acoplamento(tipo, trechos, texto, texto_antigo=None, campo_de_rota="path"):
    """Chaves alteradas de um arquivo-fonte: chaves dos trechos `chave` e as chaves das linhas dos demais.

    Linha alterada que não é uma chave (`'Unidade de negócio',`) pode ser o valor de uma chave sem valor na linha anterior
    (`'p.centro':`); a chave vale. As linhas novas se leem em `texto`; a remoção pura (sem linhas no lado novo) se lê em
    `texto_antigo`, o lado em que ela existe. Em arquivo de rotas, a chave é o valor do campo `campo_de_rota` da linha.
    """
    rota_caminho = re.compile(rf"""(?<![\w.-]){re.escape(campo_de_rota)}['"]?\s*:\s*['"]([^'"]+)['"]""")
    chaves = {}
    novas = (texto or "").splitlines()
    antigas = (texto_antigo or "").splitlines()
    for t in trechos:
        if t["tipo"] == "chave":
            chaves.setdefault(t["chave"], []).append(t["id"])
        elif t["tipo"] == "linhas" and t["linhas"] and texto is not None:
            ini, fim = t["linhas"]
            for numero in range(ini, min(fim, len(novas)) + 1):
                linha = novas[numero - 1]
                if tipo == "rota":
                    m = rota_caminho.search(linha)
                    chave = m.group(1) if m else None
                else:
                    # Depois de uma chave sem valor (`'k':`), a linha é o valor, mesmo que pareça uma chave (`'Atenção: x',`).
                    chave = _chave_do_valor_seguinte(novas, numero)
                    if not chave and (m := CHAVE.match(linha)):
                        chave = m.group(2)
                if chave:
                    chaves.setdefault(chave, []).append(t["id"])
        elif t["tipo"] == "linhas" and tipo != "rota" and texto_antigo is not None:
            removida = REMOCAO.search(t["id"])
            if removida:
                for numero in range(int(removida.group(1)), min(int(removida.group(2)), len(antigas)) + 1):
                    chave = _chave_do_valor_seguinte(antigas, numero)
                    if chave:
                        chaves.setdefault(chave, []).append(t["id"])
    # Rota curta (`/`, `/x`) vale; chave de texto com menos de 3 caracteres é ruído.
    return {c: sorted(set(ids)) for c, ids in chaves.items()
            if (tipo == "rota" or len(c) >= 3) and c not in CHAVES_GENERICAS}


def _contem_chave(texto, chave):
    """Chave com ponto casa por trecho literal; sem ponto, só como palavra inteira (`status` não casa `statusX`)."""
    if "." in chave:
        return chave in texto
    return re.search(rf"(?<!\w){re.escape(chave)}(?!\w)", texto) is not None


def _peso_do_trecho(trecho):
    """Estimativa de leitura de um trecho pelas linhas alteradas (mesma regra de `cobertura_conferir`)."""
    linhas = trecho.get("linhas")
    if linhas:
        return float((linhas[1] - linhas[0] + 1) * TOKENS_POR_LINHA)
    return float(TOKENS_TRECHO_SEM_LINHAS)


def _peso_do_arquivo_solto(tokens, trechos, orcamento):
    """Peso dos trechos sem tela de um arquivo: o arquivo inteiro se couber no orçamento, senão as linhas alteradas."""
    if tokens is not None and 0 < tokens <= orcamento:
        return float(tokens)
    return sum(_peso_do_trecho(t) for t in trechos)


def _onde_procurar(presets):
    """Onde os presets procuram rotas, para o aviso de «nenhuma rota reconhecida»."""
    locais = [a for p in presets if p["estrategia"] != "arquivos" for a in p["arquivos"]]
    for p in presets:
        if p["estrategia"] == "arquivos":
            config = p.get("config")
            locais.append(f"{p['pasta']}/ ou {config['chave_pasta']} do {config['arquivo']} do {p['rotulo']}" if config
                          else f"{p['pasta']}/ do {p['rotulo']}")
    return ", ".join(locais)


def _presets_aplicados(aplicados_v, aplicados_c):
    """Presets de rotas do mapa (detectados ou impostos por `--rotas`): nome, origem (`skill` ou o caminho do `--rotas`),
    as revisões em que valeram e quantas rotas deram ao mapa em cada uma."""
    por_nome = {}
    for revisao, lista in (("vigente", aplicados_v), ("candidata", aplicados_c)):
        for p, n in lista:
            item = por_nome.setdefault(p["nome"], {"nome": p["nome"], "origem": p["_origem"], "revisoes": [], "rotas": {},
                                                   "_chave": (p["prioridade"], p["nome"])})
            item["revisoes"].append(revisao)
            item["rotas"][revisao] = n
    return [{k: v for k, v in item.items() if k != "_chave"} for item in sorted(por_nome.values(), key=lambda i: i["_chave"])]


def mapear(repo, vigente, candidata, orcamento=ORCAMENTO_PADRAO, rotas=None):
    """Mapeia telas, código compartilhado, acoplamentos por chave e peso da atualização `vigente` -> `candidata`.

    `rotas` é o caminho de um preset JSON de rotas: usa só ele e pula a detecção; sem ele, os presets da skill.
    Preset ilegível ou inválido levanta `PresetInvalido`.
    """
    repo = Path(repo)
    if rotas is not None and str(rotas) == "":
        raise PresetInvalido("--rotas vazio: informe o caminho do preset JSON")
    explicito = [carregar_preset(rotas)] if rotas is not None else None
    candidatos = explicito or presets_da_skill()
    gerados = _gerados(candidatos)
    arquivos = arquivos_alterados(repo, vigente, candidata, gerados)
    trechos = listar_trechos(repo, vigente, candidata, gerados)
    alterados = {a["caminho"] for a in arquivos}
    trechos_de = {}
    for t in trechos:
        trechos_de.setdefault(t["arquivo"], []).append(t)
    leitor_v, leitor_c = _Leitor(repo, vigente), _Leitor(repo, candidata)
    fontes_c = {}
    dinamicas = []
    extras_v, extras_c, formatos = {}, {}, []
    aplicados_v, aplicados_c = [], []
    rotas_v = _rotas(leitor_v, extras=extras_v, presets=explicito, aplicados=aplicados_v)
    rotas_c = _rotas(leitor_c, fontes_c, dinamicas, extras_c, formatos, presets=explicito, aplicados=aplicados_c)
    for a in arquivos:
        # Custo de ler o arquivo inteiro (lado novo; o vigente se foi removido). Binário não entra.
        conteudo = None if a["binario"] else (leitor_v if a["status"] == "D" else leitor_c).bytes_de(a["caminho"])
        if conteudo is not None:
            a["tokens_estimados"] = ceil(len(conteudo) / 4) * 2
    avisos = []
    primeira = vigente == arvore_vazia(repo)
    if primeira:
        avisos.append("Primeira sincronização: vigente é a árvore vazia; toda tela entra como nova")
    ignorados = arquivos_ignorados(repo, vigente, candidata, gerados)
    metadados = [c for c in ignorados if c.startswith(PREFIXOS_IGNORADOS)]
    if metadados:
        avisos.append(f"{len(metadados)} arquivos de metadados do processo (.squad/) fora do mapa")
    for regex, rotulo in gerados:
        gerados_do_preset = [c for c in ignorados if c not in metadados and regex.search(c)]
        if gerados_do_preset:
            avisos.append(
                f"{len(gerados_do_preset)} arquivo(s) gerado(s) do {rotulo} ({', '.join(gerados_do_preset)}) fora do mapa: a "
                "mudança só reflete as rotas por arquivo; regerar com o roteador, sem leitura nem destino por trecho."
            )
    locks = [a["caminho"] for a in arquivos if e_lockfile(a["caminho"])]
    if locks:
        aviso = (f"{len(locks)} lockfile(s) lido(s) como um trecho só ({', '.join(locks)}): dependências diretas se leem no "
                 "package.json; confira à mão troca de versão de biblioteca de UI")
        if not any(posixpath.basename(c) == "package.json" for c in alterados):
            aviso += ". Sem mudança em nenhum package.json: só dependência transitiva"
        avisos.append(aviso)
    por_arquivo = {p["rotulo"] for p in candidatos if p["estrategia"] == "arquivos"}
    if por_arquivo.intersection(formatos) and len(formatos) > 1:
        avisos.append(
            f"Rotas de mais de um formato ({', '.join(formatos)}): o mapa usa as de todos, e a primeira rota repetida vale; "
            "confira que o protótipo não deixou rota de um formato antigo."
        )

    for arquivo, linha in dinamicas:
        avisos.append(f"Rota dinâmica em {arquivo}:{linha} (path com interpolação ou expressão): não foi lida; confira a tela à mão.")

    # Telas candidatas: (rota, arquivo, removida). A removida lê o lado vigente, pois o novo não a tem.
    brutas = []
    for rota, arquivo in rotas_c.items():
        if arquivo is not None:
            brutas.append((rota, arquivo, False))
        elif rotas_v.get(rota):
            brutas.append((rota, rotas_v[rota], True))
            avisos.append(f"Rota {rota} aponta para arquivo que não existe na candidata (tela removida: {rotas_v[rota]}).")
        else:
            brutas.append((rota, None, False))
            avisos.append(f"Rota {rota} sem arquivo de tela resolvido na candidata.")
    for rota, arquivo in rotas_v.items():
        if rota not in rotas_c and arquivo is not None:
            brutas.append((rota, arquivo, True))

    # Um arquivo atrás de várias rotas (ex.: 404) é uma tela só, na primeira rota; as demais viram aviso.
    unicas, extras = [], {}
    for rota, arquivo, removida in brutas:
        previa = next((b for b in unicas if arquivo is not None and b[1] == arquivo), None)
        if previa is None:
            unicas.append((rota, arquivo, removida))
        else:
            extras.setdefault(arquivo, [previa[0]]).append(rota)
    for arquivo, rotas in extras.items():
        avisos.append(f"Arquivo {arquivo} atende várias rotas ({', '.join(rotas)}): contado uma vez, na rota {rotas[0]}.")
    brutas = unicas

    telas = []
    for rota, arquivo, removida in brutas:
        leitor = leitor_v if removida else leitor_c
        dependencias = _dependencias(leitor, arquivo) if arquivo else []
        if arquivo:
            # Layouts e arquivo de rota do TanStack: a tela depende deles (e do que eles importam) sem importá-los.
            uniao = set(dependencias)
            for extra in (extras_v if removida else extras_c).get(rota, []):
                if extra != arquivo and leitor.existe(extra):
                    uniao.add(extra)
                    uniao.update(_dependencias(leitor, extra))
            dependencias = sorted(uniao - {arquivo})
        conteudo = [leitor.bytes_de(c) or b"" for c in ([arquivo] if arquivo else []) + dependencias]
        texto = "\n".join(c.decode("utf-8", errors="replace") for c in conteudo)
        nova = not removida and (rota not in rotas_v or (arquivo is not None and any(
            a["caminho"] == arquivo and a["status"] == "A" for a in arquivos)))
        telas.append({
            "id": _slug_da_rota(rota), "rota": rota, "arquivo": arquivo, "nova": nova, "removida": removida,
            "dependencias": dependencias, "trechos": [t["id"] for t in trechos_de.get(arquivo, [])],
            "tokens_estimados": ceil(sum(len(c) for c in conteudo) / 4) * 2,
            "_texto": texto, "afetada_por": sorted(d for d in dependencias if d in alterados),
            "acoplamentos": [],
        })
    usados = {}
    for tela in telas:
        n = usados.get(tela["id"], 0) + 1
        usados[tela["id"]] = n
        if n > 1:
            tela["id"] = f"{tela['id']}-{n}"

    # Acoplamentos: chaves alteradas em locale/config/tema/store/mock/rotas e as telas que as contêm.
    arquivos_de_tela = {t["arquivo"] for t in telas if t["arquivo"]}
    # Dado volumoso (mock gerado, config grande) só avisa: o trecho segue no mapa e precisa de destino.
    for a in arquivos:
        tokens = a.get("tokens_estimados")
        if tokens is not None and tokens > orcamento / 4 and a["caminho"] not in arquivos_de_tela and not e_lockfile(a["caminho"]):
            avisos.append(f"Arquivo volumoso {a['caminho']} ({tokens} tokens): dê destino pelo cabeçalho e pelas chaves, sem ler inteiro")
    campos_de_rota = _campos_de_rota(aplicados_v + aplicados_c)
    fontes = {}
    for caminho, itens in trechos_de.items():
        if e_lockfile(caminho):  # derivado: nada a acoplar, e ler o texto inteiro de um lockfile é custo à toa
            continue
        # Um arquivo de tela nunca é fonte de acoplamento (`pages/Store.tsx` não é um store).
        tipo = None if caminho in arquivos_de_tela else _tipo_acoplamento(caminho, campos_de_rota)
        if tipo is None:
            continue
        chaves = _chaves_de_acoplamento(tipo, itens, leitor_c.texto(caminho), leitor_v.texto(caminho),
                                        campos_de_rota.get(caminho, "path"))
        for chave, ids in chaves.items():
            fonte = fontes.setdefault((tipo, chave), {"arquivos": set(), "trechos": set()})
            fonte["arquivos"].add(caminho)
            fonte["trechos"].update(ids)
    # Rota que passa a renderizar outro componente: o diff está no arquivo de rotas, sem linha de `path`.
    for tela in telas:
        origem = fontes_c.get(tela["rota"])
        if (tela["removida"] or tela["nova"] or origem not in trechos_de or origem in arquivos_de_tela
                or tela["rota"] not in rotas_v or rotas_v[tela["rota"]] == tela["arquivo"]):
            continue
        fonte = fontes.setdefault(("rota", tela["rota"]), {"arquivos": set(), "trechos": set()})
        fonte["arquivos"].add(origem)
        fonte["trechos"].update(t["id"] for t in trechos_de[origem])
    acoplamentos = []
    for (tipo, chave), fonte in sorted(fontes.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if tipo == "rota":
            afetadas = [t for t in telas if t["rota"] == chave and not t["nova"] and not t["removida"]]
        else:
            afetadas = [t for t in telas if not t["removida"] and _contem_chave(t["_texto"], chave)]
        if not afetadas:
            continue
        for t in afetadas:
            t["acoplamentos"].append(chave)
            t["afetada_por"] = sorted(set(t["afetada_por"]) | (fonte["arquivos"] - {t["arquivo"]}))
        acoplamentos.append({
            "chave": chave, "tipo": tipo, "telas": sorted(t["id"] for t in afetadas), "trechos": sorted(fonte["trechos"]),
        })

    listadas = [t for t in telas if t["trechos"] or t["nova"] or t["removida"] or t["afetada_por"]]
    compartilhados = []
    for caminho in sorted(alterados - arquivos_de_tela):
        usam = sorted(t["id"] for t in listadas if caminho in t["dependencias"])
        if len(usam) >= 2:
            compartilhados.append({"arquivo": caminho, "telas": usam, "trechos": [t["id"] for t in trechos_de.get(caminho, [])]})
    arquivos_compartilhados = {c["arquivo"] for c in compartilhados}

    for tela in listadas:
        sinais = 0.0
        if tela["nova"]:
            sinais += PESOS["nova"]
        sinais += PESOS["por_trecho"] * min(len(tela["trechos"]), PESOS["max_trechos"])
        if arquivos_compartilhados.intersection(tela["dependencias"]):
            sinais += PESOS["compartilhado"]
        if FORMULARIO.search(tela["_texto"]):
            sinais += PESOS["formulario"]
        if PERMISSAO.search(tela["_texto"]):
            sinais += PESOS["permissao"]
        if tela["acoplamentos"]:
            sinais += PESOS["acoplamento"]
        tela["multiplicador"] = round(1.0 + sinais, 4)
        tela["peso"] = tela["tokens_estimados"] * tela["multiplicador"]
    for tela in telas:
        del tela["_texto"]
    listadas.sort(key=lambda t: t["id"])

    # Trechos sem tela (código solto, locale sem consumidor, rotas não reconhecidas): custo pelo tamanho do arquivo.
    com_tela = set()
    for tela in telas:
        com_tela.update(tela["trechos"])
        for arquivo in tela["afetada_por"]:
            if arquivo in tela["dependencias"]:
                com_tela.update(t["id"] for t in trechos_de.get(arquivo, []))
    for item in compartilhados + acoplamentos:
        com_tela.update(item["trechos"])
    soltos = {}
    for t in trechos:
        if t["id"] not in com_tela:
            soltos.setdefault(t["arquivo"], []).append(t)
    tokens_de = {a["caminho"]: a.get("tokens_estimados") for a in arquivos}
    peso_sem_tela = sum(_peso_do_arquivo_solto(tokens_de.get(c), ts, orcamento) for c, ts in soltos.items())
    # Na primeira sincronização a vigente é a árvore vazia: não ter rotas nela é o esperado, não um defeito do preset.
    sem_rotas = [nome for nome, lido in (("vigente", rotas_v), ("candidata", rotas_c)) if not lido and not (nome == "vigente" and primeira)]
    if sem_rotas and trechos:
        paginas = [a["caminho"] for a in arquivos if PAGINA.search(a["caminho"])]
        onde = " na " + " e na ".join(sem_rotas) if len(sem_rotas) == 1 else ""
        mudaram = f", mas {len(paginas)} arquivos de página/tela mudaram" if paginas else ""
        avisos.append(
            f"Nenhuma rota reconhecida{onde} ({_onde_procurar(candidatos)}){mudaram}: os trechos não se ligam a telas "
            "e o peso usa o tamanho dos arquivos."
        )
    if soltos:
        n = sum(len(ts) for ts in soltos.values())
        avisos.append(
            f"{n} trechos de {len(soltos)} arquivos não se ligam a nenhuma tela (peso estimado pelo tamanho dos "
            f"arquivos: {peso_sem_tela:.0f} tokens): leia como código compartilhado ou solto."
        )
    peso_total = sum(t["peso"] for t in listadas) + peso_sem_tela
    if peso_total > orcamento:
        avisos.append(f"Peso total {peso_total:.0f} excede o orçamento de {orcamento} tokens: dividir entre mais de um agente.")
    return {
        "vigente": vigente, "candidata": candidata, "vigente_sha": resolver_sha(repo, vigente),
        "candidata_sha": resolver_sha(repo, candidata), "orcamento": orcamento, "arquivos": arquivos, "trechos": trechos,
        "telas": listadas, "compartilhados": compartilhados, "acoplamentos": acoplamentos,
        "peso_total": peso_total, "peso_sem_tela": peso_sem_tela, "cabe_em_um_agente": peso_total <= orcamento, "avisos": avisos,
        "ignorados": ignorados, "presets_de_rotas": _presets_aplicados(aplicados_v, aplicados_c),
    }
