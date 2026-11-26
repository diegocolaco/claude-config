"""Inventário por tela: os arquivos e os componentes que cada tela da candidata usa, lidos do git.

O mapa diz o que mudou; este módulo diz do que cada tela é feita, para o plano reproduzi-la com os mesmos componentes do
protótipo. Parte do arquivo de cada tela do mapa (e dos arquivos de moldura informados) e segue os imports, os reexports e os
`import('literal')` dentro da própria revisão `candidata`: nunca lê o disco, porque o disco pode ter o que o git não tem
(`src/.umi`, gerado no build). Só biblioteca padrão; nada é gravado no repositório do protótipo e nenhum comando de
build, de pacote ou de rede é chamado.
"""
import json
from pathlib import Path
import posixpath
import re
import sys

sys.path.insert(0, str(Path(__file__).parent))

import cobertura_cruzar  # noqa: E402
import cobertura_mapa as cm  # noqa: E402

CODIGO = (".ts", ".tsx", ".js", ".jsx", ".mjs")
# Pacotes que toda tela usa e que não dizem nada sobre o desenho dela. Só estes: o resto entra, sem lista de bibliotecas.
PACOTES_FORA = frozenset(("react", "react-dom"))

_ANTES = r"(?<![\w.$])"
IMPORT_DECL = re.compile(_ANTES + r"""import\s+(type\s+)?([^;'"]*?)\s*from\s*(['"])([^'"\n]+)\3""", re.S)
IMPORT_EFEITO = re.compile(_ANTES + r"""import\s*(['"])([^'"\n]+)\1""")
EXPORT_DE = re.compile(
    _ANTES + r"""export\s+(type\s+)?(\*(?:\s*as\s+[\w$]+)?|\{[^}]*\})\s*from\s*(['"])([^'"\n]+)\3""", re.S)
# `export { A, B as C }` sem `from`: reexporta nomes que o próprio arquivo importou (barril escrito em duas etapas).
EXPORT_LOCAL = re.compile(_ANTES + r"""export\s+(type\s+)?\{([^}]*)\}(?!\s*from\b)""", re.S)
IMPORT_DINAMICO = re.compile(_ANTES + r"""import\s*\(""")
# `import('x')`, `import("x")` e a crase sem interpolação (`import(`./x`)`) são literais.
IMPORT_DINAMICO_LITERAL = re.compile(
    _ANTES + r"""import\s*\(\s*(?:(['"])([^'"\n]+)\1|`((?:(?!\$\{)[^`\n])*)`)\s*[,)]""")
# Tag de Web Component: minúscula, com hífen, colada ao `<` (`i<n-m` não casa: letra antes do `<`).
TAG_ELEMENTO = re.compile(r"(?<![\w)\]])<([a-z][a-z0-9]*(?:-[a-z][a-z0-9]*)+)(?![\w-])")


class _Registro:
    """Um import, um reexport (`export ... from`) ou um `import()` de um arquivo."""

    def __init__(self, especificador, genero, itens=(), padrao=False, estrela=False, efeito=False, tipo=False):
        self.especificador, self.genero = especificador, genero
        self.itens = list(itens)  # (nome no arquivo de origem do import/reexport, tipo?)
        self.padrao, self.estrela, self.efeito, self.tipo = padrao, estrela, efeito, tipo

    @property
    def todos(self):
        """Não dá para saber quais nomes do alvo servem: import padrão, `* as`, só por efeito, dinâmico, `export *`."""
        return self.padrao or self.estrela or self.efeito or self.genero == "dinamico"

    def nomes_de_pacote(self):
        """Nomes que o import grava no pacote externo: (nome, tipo?)."""
        nomes = list(self.itens)
        if self.padrao:
            nomes.append(("default", self.tipo))
        if self.estrela:
            nomes.append(("*", self.tipo))
        return nomes


def _itens_da_clausula(clausula, tipo_geral):
    """`React, { useState, type Foo as Bar }` -> (itens nomeados [(nome, tipo?)], padrão?, estrela?, locais).

    `locais` liga cada nome local ao que ele é no módulo de origem: {local: (nome original, tipo?)}."""
    itens, padrao, estrela, locais = [], False, False, {}
    chaves = re.search(r"\{([^}]*)\}", clausula)
    if chaves:
        for item in chaves.group(1).split(","):
            partes = item.split()
            if not partes:
                continue
            tipo = tipo_geral
            if partes[0] == "type" and len(partes) >= 2 and not (len(partes) == 3 and partes[1] == "as"):
                tipo, partes = True, partes[1:]
            itens.append((partes[0], tipo))
            locais[partes[2] if len(partes) >= 3 and partes[1] == "as" else partes[0]] = (partes[0], tipo)
    resto = re.sub(r"\{[^}]*\}", "", clausula)
    for parte in resto.split(","):
        parte = parte.strip()
        local = parte.split()[-1] if parte else ""
        if parte.startswith("*"):
            estrela = True
            locais[local] = ("*", tipo_geral)
        elif parte:
            padrao = True
            locais[local] = ("default", tipo_geral)
    return itens, padrao, estrela, locais


class _Analise:
    """O que um arquivo de código importa e reexporta, e se ele é um barril (só reexporta)."""

    def __init__(self, texto_sem_comentarios):
        texto = resto = texto_sem_comentarios
        self.registros = []
        locais = {}  # nome local -> (especificador, nome original, tipo?), dos imports do arquivo
        for m in IMPORT_DECL.finditer(texto):
            itens, padrao, estrela, ligados = _itens_da_clausula(m.group(2), bool(m.group(1)))
            locais.update({local: (m.group(4), original, tipo) for local, (original, tipo) in ligados.items()})
            self.registros.append(_Registro(m.group(4), "import", itens, padrao, estrela, tipo=bool(m.group(1))))
        for m in IMPORT_EFEITO.finditer(texto):
            self.registros.append(_Registro(m.group(2), "import", efeito=True))
        self.exports = {}  # nome exportado -> (especificador, nome original, tipo?)
        for m in EXPORT_DE.finditer(texto):
            tipo_geral, corpo, especificador = bool(m.group(1)), m.group(2), m.group(4)
            if corpo.startswith("*"):
                como = re.search(r"as\s+([\w$]+)", corpo)
                if como:  # `export * as ns from`: o nome `ns` leva o módulo inteiro
                    self.exports[como.group(1)] = (especificador, "*", tipo_geral)
                self.registros.append(_Registro(especificador, "export", estrela=True, tipo=tipo_geral))
                continue
            itens = []
            for item in corpo.strip("{} \n\t").split(","):
                partes = item.split()
                if not partes:
                    continue
                tipo = tipo_geral
                if partes[0] == "type" and len(partes) >= 2 and not (len(partes) == 3 and partes[1] == "as"):
                    tipo, partes = True, partes[1:]
                original = partes[0]
                exportado = partes[2] if len(partes) >= 3 and partes[1] == "as" else original
                itens.append((original, tipo))
                self.exports[exportado] = (especificador, original, tipo)
            self.registros.append(_Registro(especificador, "export", itens, tipo=tipo_geral))
        literais = set()
        for m in IMPORT_DINAMICO_LITERAL.finditer(texto):
            literais.add(m.start())
            self.registros.append(_Registro(m.group(2) or m.group(3), "dinamico"))
        self.dinamico_nao_literal = any(m.start() not in literais for m in IMPORT_DINAMICO.finditer(texto))
        so_reexporta = True
        for m in EXPORT_LOCAL.finditer(texto):
            for item in m.group(2).split(","):
                partes = item.split()
                if partes and partes[0] == "type" and len(partes) >= 2 and not (len(partes) == 3 and partes[1] == "as"):
                    partes = partes[1:]
                if not partes:
                    continue
                exportado = partes[2] if len(partes) >= 3 and partes[1] == "as" else partes[0]
                if partes[0] in locais:
                    self.exports[exportado] = locais[partes[0]]
                else:  # exporta algo declarado aqui: o arquivo tem código próprio
                    so_reexporta = False
        for padrao in (IMPORT_DECL, IMPORT_EFEITO, EXPORT_DE, EXPORT_LOCAL):
            resto = padrao.sub(" ", resto)
        self.barril = (so_reexporta and bool(self.exports or any(r.genero == "export" for r in self.registros))
                       and not re.sub(r"[\s;]+", "", resto))


def _sem_strings(texto):
    """Esvazia o conteúdo das strings (mantém aspas e quebras de linha): `'<dom-table'` numa string não é uso.

    String com aspa simples ou dupla não atravessa linha, para uma aspa solta no texto JSX não engolir o arquivo."""
    saida, i, aspa = [], 0, None
    while i < len(texto):
        c = texto[i]
        if aspa:
            if c == "\\" and i + 1 < len(texto):
                saida.append("  ")
                i += 2
                continue
            if c == aspa:
                aspa = None
                saida.append(c)
            elif c == "\n":
                if aspa != "`":
                    aspa = None
                saida.append(c)
            else:
                saida.append(" ")
        elif c in "'\"`" and cm._abre_string(texto, i):
            aspa = c
            saida.append(c)
        else:
            saida.append(c)
        i += 1
    return "".join(saida)


def _pacote(especificador):
    """Nome do pacote de um import externo: `antd/es/table` -> `antd`; `@ant-design/icons/lib/x` -> `@ant-design/icons`."""
    partes = especificador.split("/")
    return "/".join(partes[:2]) if especificador.startswith("@") and len(partes) >= 2 else partes[0]


class _Contexto:
    """Leitor da candidata com cache da análise de cada arquivo."""

    def __init__(self, leitor, bases=()):
        self.leitor = leitor
        self.bases = list(bases)  # `baseUrl` do tsconfig/jsconfig, relativos à raiz do repositório
        self._analises = {}
        self._elementos = {}

    def analise(self, arquivo):
        if arquivo not in self._analises:
            self._analises[arquivo] = _Analise(cm._sem_comentarios(self.leitor.texto(arquivo) or ""))
        return self._analises[arquivo]

    def elementos(self, arquivo):
        if arquivo not in self._elementos:
            texto = _sem_strings(cm._sem_comentarios(self.leitor.texto(arquivo) or ""))
            self._elementos[arquivo] = set(TAG_ELEMENTO.findall(texto))
        return self._elementos[arquivo]


class _Fechamento:
    """Fechamento de imports a partir de um arquivo de entrada, com filtro por símbolo nos barris."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.arquivos, self.barris, self.nao_resolvidos, self.avisos = set(), set(), set(), set()
        self.pacotes = {}  # pacote -> {"valores": set, "tipos": set}
        self._completos, self._pedidos, self._efeitos = set(), set(), set()
        self._pilha = []

    def percorrer(self, arquivo):
        self._pilha.append(("seguir", arquivo))
        while self._pilha:
            tarefa = self._pilha.pop()
            if tarefa[0] == "seguir":
                self._seguir(tarefa[1])
            elif tarefa[0] == "aresta":
                self._aresta(tarefa[1])
            else:
                self._pedir(*tarefa[1:])
        return self

    def _seguir(self, arquivo):
        """Entra no arquivo por inteiro: todos os imports dele valem."""
        if arquivo in self._completos:
            return
        self._completos.add(arquivo)
        self.arquivos.add(arquivo)
        if not arquivo.endswith(CODIGO):
            return
        analise = self.ctx.analise(arquivo)
        if analise.dinamico_nao_literal:
            self.avisos.add(f"{arquivo}: import dinâmico não literal (import(x)) não foi seguido")
        self._pilha.extend(("aresta", (arquivo, r)) for r in reversed(analise.registros))

    def _registrar_pacote(self, pacote, nomes):
        if pacote in PACOTES_FORA:
            return
        entrada = self.pacotes.setdefault(pacote, {"valores": set(), "tipos": set()})
        for nome, tipo in nomes:
            entrada["tipos" if tipo else "valores"].add(nome)

    def _aresta(self, par):
        origem, r = par
        especificador = r.especificador
        leitor = self.ctx.leitor
        if _e_local(leitor, especificador):
            alvo = _resolver_local(leitor, origem, especificador)
        elif especificador.startswith("@@/"):  # alias do Umi sem `paths` que o declare: `src/.umi` não está no git
            alvo = None
        elif especificador.startswith("node:"):  # módulo embutido do Node: não é componente
            return
        else:
            alvo = _resolver_por_base(leitor, self.ctx.bases, especificador)
            if alvo is None:
                if especificador.startswith(("~/", "#/")):
                    self.avisos.add(f"{origem}: import {especificador!r} parece alias, mas nenhum `paths` o declara; contado como pacote")
                self._registrar_pacote(_pacote(especificador), r.nomes_de_pacote())
                return
        if alvo is None:
            self.nao_resolvidos.add(especificador)
            return
        if not alvo.endswith(CODIGO):  # estilo, dado, imagem: entra na lista e não se segue
            self.arquivos.add(alvo)
            return
        if not self.ctx.analise(alvo).barril:
            self._pilha.append(("seguir", alvo))
            return
        self.arquivos.add(alvo)
        if r.todos:  # não dá para filtrar: segue o barril inteiro e sinaliza
            self.barris.add(alvo)
            self._pilha.append(("seguir", alvo))
        else:
            self._pilha.extend(("pedir", alvo, nome, tipo) for nome, tipo in reversed(r.itens))
            if alvo not in self._efeitos:  # `import './C'` do barril roda com qualquer símbolo pedido
                self._efeitos.add(alvo)
                self._pilha.extend(("aresta", (alvo, e)) for e in reversed(self.ctx.analise(alvo).registros) if e.efeito)

    def _pedir(self, barril, nome, tipo):
        """Um import pede `nome` do barril: segue só o arquivo de onde o barril o reexporta."""
        if (barril, nome, tipo) in self._pedidos:  # o mesmo nome pedido como tipo e como valor são dois usos
            return
        self._pedidos.add((barril, nome, tipo))
        achado = self.ctx.analise(barril).exports.get(nome)
        if achado is None:  # símbolo que o barril não declara (vem de `export *`, p. ex.): sem filtro
            self.barris.add(barril)
            self._pilha.append(("seguir", barril))
            return
        especificador, original, tipo_do_barril = achado
        tipo = tipo or tipo_do_barril
        if original == "*":
            registro = _Registro(especificador, "import", estrela=True, tipo=tipo)
        else:
            registro = _Registro(especificador, "import", [(original, tipo)])
        self._pilha.append(("aresta", (barril, registro)))


class MolduraAusente(ValueError):
    """`--moldura` aponta para arquivo que a candidata não tem (erro de quem chamou, não do mapa)."""


def _e_local(leitor, especificador):
    """Import do projeto: relativo (inclusive `.` e `..`) ou por alias."""
    return especificador in (".", "..") or cm._import_local(leitor, especificador)


def _resolver_por_base(leitor, bases, especificador):
    """Import sem alias que o `baseUrl` do tsconfig leva a um arquivo que existe na candidata; senão None (é pacote)."""
    for base in bases:
        alvo = cm._resolver(leitor, posixpath.join(base, especificador))
        if alvo is not None:
            return alvo
    return None


def _resolver_local(leitor, origem, especificador):
    """`cm._resolver_import` e, onde ele não acha, o que o mapa não conhece: `.mjs` e arquivo de tipos sem extensão
    (`./x` -> `x.mjs`, `x.d.ts`)."""
    alvo = cm._resolver_import(leitor, origem, especificador)
    if alvo is None:
        alias = cm._alias_de(leitor, especificador)
        base = (leitor.aliases[alias] + especificador[len(alias):] if alias is not None
                else posixpath.join(posixpath.dirname(origem), especificador))
        base = posixpath.normpath(base)
        alvo = next((c for c in (base + ".mjs", base + ".d.ts", base + "/index.mjs") if leitor.existe(c)), None)
    return alvo


def _arquivo_da_tela(tela):
    return tela.get("arquivo") if isinstance(tela, dict) else None


def _inventario_de(ctx, arquivo):
    """Inventário de um arquivo de entrada (tela ou moldura) na revisão do contexto."""
    f = _Fechamento(ctx).percorrer(arquivo)
    elementos = set()
    for a in f.arquivos:
        if a.endswith(CODIGO):
            elementos |= ctx.elementos(a)
    return {
        "arquivos": sorted(f.arquivos),
        "componentes": {p: {"valores": sorted(v["valores"]), "tipos": sorted(v["tipos"])} for p, v in sorted(f.pacotes.items())},
        "elementos": sorted(elementos),
        "barris": sorted(f.barris),
        "nao_resolvidos": sorted(f.nao_resolvidos),
    }, f.avisos


def _vazio():
    return {"arquivos": [], "componentes": {}, "elementos": [], "barris": [], "nao_resolvidos": []}


def _jsonc(texto):
    """JSON com comentários `//` e `/* */` e vírgula final, como o tsconfig aceita."""
    texto = cm._sem_comentarios(texto.lstrip("\ufeff"))
    saida, i, aspa = [], 0, False
    while i < len(texto):
        c = texto[i]
        if aspa:
            saida.append(c)
            if c == "\\" and i + 1 < len(texto):
                saida.append(texto[i + 1])
                i += 1
            elif c == '"':
                aspa = False
        elif c == '"':
            aspa = True
            saida.append(c)
        elif c == ",":
            resto = texto[i + 1:].lstrip()
            if resto[:1] not in ("}", "]"):
                saida.append(c)
        else:
            saida.append(c)
        i += 1
    return json.loads("".join(saida))


def _config_ts(leitor, caminho, avisos, vistos=()):
    """`baseUrl` e `paths` do `compilerOptions` de `caminho`, já relativos à raiz do repositório, seguindo `extends` relativo.

    Devolve {"base": pasta ou None, "paths": {chave: [alvos]}}; arquivo ilegível ou `extends` ausente viram aviso."""
    vazio = {"base": None, "paths": {}}
    if caminho in vistos:
        return vazio
    texto = leitor.texto(caminho)
    if texto is None:
        avisos.add(f"{caminho}: arquivo ausente na candidata (extends); aliases dele ignorados")
        return vazio
    try:
        dados = _jsonc(texto)
        if not isinstance(dados, dict):
            raise ValueError("a raiz não é um objeto")
    except ValueError as erro:
        avisos.add(f"{caminho}: JSON ilegível ({erro}); aliases dele ignorados")
        return vazio
    pasta = posixpath.dirname(caminho)
    herdado = vazio
    heranca = dados.get("extends")
    for pai in ([heranca] if isinstance(heranca, str) else heranca if isinstance(heranca, list) else []):
        if not isinstance(pai, str) or not pai.startswith(("./", "../")):
            continue  # pacote de configuração base (`@tsconfig/node`): não está no git
        alvo = posixpath.normpath(posixpath.join(pasta, pai))
        if not leitor.existe(alvo) and leitor.existe(alvo + ".json"):
            alvo += ".json"
        base_pai = _config_ts(leitor, alvo, avisos, (*vistos, caminho))
        herdado = {"base": base_pai["base"] or herdado["base"], "paths": base_pai["paths"] or herdado["paths"]}
    opcoes = dados.get("compilerOptions")
    opcoes = opcoes if isinstance(opcoes, dict) else {}
    base = herdado["base"]
    if isinstance(opcoes.get("baseUrl"), str):
        base = posixpath.normpath(posixpath.join(pasta, opcoes["baseUrl"]))
    paths = herdado["paths"]
    if isinstance(opcoes.get("paths"), dict):  # `paths` parte do `baseUrl`; sem ele, da pasta do arquivo que o declara
        raiz = base if base is not None else pasta
        paths = {}
        for chave, alvos in opcoes["paths"].items():
            alvo = alvos[0] if isinstance(alvos, list) and alvos and isinstance(alvos[0], str) else None
            if alvo is not None and alvo.endswith("*"):
                completo = posixpath.normpath(posixpath.join(raiz, alvo[:-1] or "."))
                paths[chave] = "" if completo == "." else completo + "/"
            else:
                paths[chave] = None
    return {"base": base, "paths": paths}


def _aliases_do_tsconfig(leitor, avisos):
    """(aliases `prefixo/` -> `pasta/`, bases) do `tsconfig.json` (ou, sem ele, `jsconfig.json`) da raiz da candidata."""
    for nome in ("tsconfig.json", "jsconfig.json"):
        if leitor.existe(nome):
            config = _config_ts(leitor, nome, avisos)
            break
    else:
        return {}, []
    aliases = {}
    for chave, prefixo in config["paths"].items():
        if chave.endswith("/*") and prefixo is not None:
            aliases[chave[:-1]] = prefixo
        else:
            avisos.add(f"{nome}: `paths` {chave!r} sem curinga final não é lido")
    return aliases, ([config["base"]] if config["base"] is not None else [])


def _aliases_da_revisao(leitor, mapa, avisos):
    """Prepara os aliases de import da revisão e devolve as bases (`baseUrl`) do tsconfig.

    Vêm do `tsconfig.json`/`jsconfig.json` (`paths`) e dos presets que o mapa usou (`--rotas`) ou, sem eles, dos detectados na
    revisão; o preset vale sobre o tsconfig, porque é o que o `mapear` e o `cruzar` usam. Só o inventário lê o tsconfig."""
    aliases, bases = _aliases_do_tsconfig(leitor, avisos)
    presets = cobertura_cruzar._presets_do_mapa(mapa)
    usados = sorted(presets, key=lambda p: (p["prioridade"], p["nome"])) if presets else [
        p for p in cm.presets_da_skill() if cm._casa_marcas(leitor, p)]
    de_preset = {a: v for p in usados for a, v in p["aliases"].items()}
    leitor.aliases = {**({} if usados else cm.ALIASES_PADRAO), **aliases, **de_preset}
    return bases


def inventariar(repo, mapa, molduras=()):
    """Inventário das telas do `mapa` e das `molduras` (arquivos de entrada que não são tela) na `candidata` do mapa.

    Levanta `ValueError` em entrada inválida (mapa sem `candidata` ou `telas`, moldura ausente da revisão) e deixa passar
    `subprocess.CalledProcessError` (commit inexistente) e `OSError` do git.
    """
    if not isinstance(mapa, dict) or not isinstance(mapa.get("telas"), list):
        raise ValueError("Mapa inválido: falta a lista 'telas'.")
    revisao = mapa.get("candidata_sha") if isinstance(mapa.get("candidata_sha"), str) and mapa.get("candidata_sha") else mapa.get("candidata")
    if not isinstance(revisao, str) or not revisao:
        raise ValueError("Mapa inválido: falta 'candidata'.")
    for tela in mapa["telas"]:
        if not isinstance(tela, dict) or not isinstance(tela.get("id"), str):
            raise ValueError("Mapa inválido: cada tela precisa ser um objeto com 'id'.")
    repo = Path(repo)
    sha = cm.resolver_sha(repo, revisao)
    leitor = cm._Leitor(repo, sha)
    entradas = []
    for m in molduras:
        caminho = posixpath.normpath(str(m).replace("\\", "/"))
        if not leitor.existe(caminho):
            raise MolduraAusente(f"--moldura {m}: o arquivo não existe na candidata {sha}.")
        entradas.append(caminho)
    avisos = set()
    ctx = _Contexto(leitor, _aliases_da_revisao(leitor, mapa, avisos))
    telas, saida_molduras = [], []
    for tela in sorted((t for t in mapa["telas"] if not t.get("removida")), key=lambda t: t["id"]):
        arquivo = _arquivo_da_tela(tela)
        if not isinstance(arquivo, str) or not leitor.existe(arquivo):
            avisos.add(f"Tela {tela['id']}: arquivo {arquivo!r} ausente na candidata; sem inventário")
            dados = _vazio()
        else:
            dados, avisos_do_arquivo = _inventario_de(ctx, arquivo)
            avisos |= avisos_do_arquivo
        telas.append({"id": tela["id"], "rota": tela.get("rota"), "arquivo": arquivo, **dados})
    for tela in mapa["telas"]:
        if tela.get("removida"):
            avisos.add(f"Tela {tela['id']}: removida na candidata; fora do inventário")
    for caminho in sorted(set(entradas)):
        dados, avisos_do_arquivo = _inventario_de(ctx, caminho)
        avisos |= avisos_do_arquivo
        saida_molduras.append({"arquivo": caminho, **dados})
    nomes = {}
    for item in telas + saida_molduras:
        for pacote, listas in item["componentes"].items():
            soma = nomes.setdefault(pacote, {"valores": set(), "tipos": set(), "telas": 0})
            soma["valores"].update(listas["valores"])
            soma["tipos"].update(listas["tipos"])
    for item in telas:
        for pacote in item["componentes"]:
            nomes[pacote]["telas"] += 1
    return {
        "versao": sha, "telas": telas, "molduras": saida_molduras,
        "global": {p: {"valores": len(s["valores"]), "tipos": len(s["tipos"]), "telas": s["telas"]} for p, s in sorted(nomes.items())},
        "avisos": sorted(avisos),
    }
