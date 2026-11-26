"""Verificação de paridade contra «oco»: candidatos a stub no código e requisitos entregues sem teste.

Subcomandos: `stubs` (padrões de código oco em arquivos do produto), `sem-teste` (requisitos do catálogo com cenário sem teste)
e `ligar` (grava no catálogo as ligações que os planos declaram no bloco `**Catálogo:**`; dry-run por padrão).
Sempre consultivo: candidato não é veredito, quem decide é o revisor.
Saída: 0 = nada a conferir, 11 = há itens, 2 = uso inválido (argumento errado ou JSON ilegível; mensagem no stderr).
Só biblioteca padrão.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SAIDA_OK = 0
SAIDA_ITENS = 11
SAIDA_USO = 2

# Padrões de componente «oco»: existe, mas não recebe dados nem faz nada. Cada match é só um candidato.
PADROES_STUB = {
    "retorno_nulo": r"return\s+null\b",
    "lista_vazia_em_prop": r"\b(dataSource|data|options|items|columns)=\{\s*\[\s*\]\s*\}",
    "handler_vazio": r"=\{\s*\(\)\s*=>\s*\{\s*\}\s*\}",
    "pendencia": r"\b(TODO|FIXME|XXX)\b",
    "nao_implementado": r"not implemented|não implementado",
}
# Só `nao_implementado` ignora caixa («Not implemented» em mensagem de erro); os demais casam literalmente.
_COMPILADOS = {nome: re.compile(regex, re.IGNORECASE if nome == "nao_implementado" else 0)
               for nome, regex in PADROES_STUB.items()}


class ErroDeUso(Exception):
    """Entrada inválida (arquivo ausente, JSON ilegível, commit inexistente): vira saída 2."""


def _lista(valor):
    return valor if isinstance(valor, list) else []


def _ids(valor):
    """Ids (strings) de uma lista de ids; valor de tipo errado vira lista vazia."""
    return [v for v in _lista(valor) if isinstance(v, str)]


def _registros(catalogo, chave):
    """Registros-objeto com `id` string de uma seção do catálogo; o resto é ignorado."""
    if not isinstance(catalogo, dict):
        return []
    return [r for r in _lista(catalogo.get(chave)) if isinstance(r, dict) and isinstance(r.get("id"), str)]


def _ordenado_unico(valores):
    return sorted(set(valores))


def candidatos_stub(raiz, arquivos):
    """Candidatos a stub em `arquivos` (caminhos relativos a `raiz`); ausentes, fora da raiz e binários são pulados."""
    raiz = Path(raiz).resolve()
    candidatos = []
    for relativo in arquivos:
        caminho = (raiz / relativo).resolve()
        try:
            nome = caminho.relative_to(raiz).as_posix()
        except ValueError:
            continue  # fora da raiz do produto
        if not caminho.is_file():
            continue
        try:
            linhas = caminho.read_text(encoding="utf-8").splitlines()
        except (OSError, ValueError):  # ValueError cobre UnicodeDecodeError (binário)
            continue
        for numero, linha in enumerate(linhas, start=1):
            for padrao, regex in _COMPILADOS.items():
                if regex.search(linha):
                    candidatos.append({"arquivo": nome, "linha": numero, "padrao": padrao, "texto": linha.strip()})
    return candidatos


# O schema do catálogo só exige `id` em `tasks[]`; o estado de entrega é um campo `status` opcional na tarefa.
STATUS_ENTREGUE = {"done", "delivered", "completed", "entregue", "concluida", "concluída"}


def _tarefas_entregues(catalogo, entregues):
    """Ids das tarefas entregues: `entregues` informadas (ids do ledger do plano) e `tasks[].status` de entrega no catálogo."""
    ids = set(_ids(entregues))
    for tarefa in _registros(catalogo, "tasks"):
        status = tarefa.get("status")
        if isinstance(status, str) and status.strip().lower() in STATUS_ENTREGUE:
            ids.add(tarefa["id"])
    return ids


def estado_de_tarefas_conhecido(catalogo, entregues):
    """Há de onde saber se uma tarefa foi entregue: `entregues` informadas ou alguma tarefa do catálogo com `status`."""
    return entregues is not None or any(isinstance(t.get("status"), str) for t in _registros(catalogo, "tasks"))


def _tem_tarefas(catalogo):
    return any(_ids(r.get("task_ids")) for chave in ("requirements", "differences") for r in _registros(catalogo, chave))


def requisitos_sem_teste(catalogo, todos=False, entregues=None):
    """Requisitos com cenário sem teste em `tests[].scenario_ids`; `cenarios` traz só os cenários que faltam.

    Por padrão só os entregues: com alguma tarefa entregue em `task_ids` do requisito ou de uma diferença ligada a ele.
    Tarefa planejada não conta (o linkage exige `task_ids` em toda diferença). Entregue = `tasks[].status` de entrega no
    catálogo ou id em `entregues`; sem nenhuma das duas fontes nada é conhecido como entregue.
    """
    requisitos = _registros(catalogo, "requirements")
    diferencas = _registros(catalogo, "differences")
    cenarios = _registros(catalogo, "scenarios")
    feitas = _tarefas_entregues(catalogo, entregues)
    testados = set()
    for teste in _lista(catalogo.get("tests")) if isinstance(catalogo, dict) else []:
        if isinstance(teste, dict):
            testados.update(_ids(teste.get("scenario_ids")))

    resultado = []
    for req in requisitos:
        rid = req["id"]
        ligadas = {d["id"]: d for d in diferencas
                   if d["id"] in _ids(req.get("difference_ids")) or rid in _ids(d.get("requirement_ids"))}
        tarefas = set(_ids(req.get("task_ids"))).union(*(_ids(d.get("task_ids")) for d in ligadas.values()))
        if not todos and not tarefas & feitas:
            continue
        do_requisito = _ids(req.get("scenario_ids")) + [c["id"] for c in cenarios if rid in _ids(c.get("requirement_ids"))]
        sem_teste = [c for c in do_requisito if c not in testados]
        if do_requisito and not sem_teste:
            continue
        resultado.append({
            "requisito": rid,
            "diferencas": _ordenado_unico(ligadas),
            "cenarios": _ordenado_unico(sem_teste),
            "superficies": _ordenado_unico(d["surface_id"] for d in ligadas.values() if isinstance(d.get("surface_id"), str)),
        })
    return resultado


def linhas_conferencia(itens, catalogo):
    """Lista de conferência manual: uma linha por requisito, «tela (superfície) · requisito · o que conferir: cenários X»."""
    nomes = {}
    for sup in _registros(catalogo, "surfaces"):
        nome = next((sup[k] for k in ("name", "title", "label") if isinstance(sup.get(k), str)), None)
        if nome:
            nomes[sup["id"]] = nome
    linhas = []
    for item in itens:
        telas = ", ".join(f"{nomes[s]} ({s})" if s in nomes else s for s in item["superficies"]) or "(sem superfície)"
        cenarios = ", ".join(item["cenarios"]) or "nenhum cenário ligado"
        linhas.append(f"- [ ] {telas} · {item['requisito']} · o que conferir: cenários {cenarios}")
    return linhas


def _ler_json(caminho):
    try:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError) as erro:  # ValueError cobre JSON inválido e UnicodeDecodeError
        raise ErroDeUso(f"{caminho}: {erro}") from erro
    if not isinstance(dados, dict):
        raise ErroDeUso(f"{caminho}: o conteúdo precisa ser um objeto JSON")
    return dados


def _arquivos_desde(raiz, commit):
    """Arquivos alterados entre `commit` e HEAD, relativos a `raiz` (que pode ser subpasta do repositório), que ainda existem."""
    # `--relative` com cwd=raiz: caminhos relativos à raiz e arquivos fora dela excluídos.
    cmd = ["git", "-c", "core.quotePath=false", "--literal-pathspecs", "diff", "--name-only", "-z", "--relative",
           commit, "HEAD", "--"]
    try:
        proc = subprocess.run(cmd, cwd=raiz, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as erro:
        detalhe = erro.stderr.decode("utf-8", "replace").strip() if isinstance(erro, subprocess.CalledProcessError) else str(erro)
        raise ErroDeUso(f"git diff {commit}..HEAD em {raiz}: {detalhe}") from erro
    nomes = proc.stdout.decode("utf-8", "replace").split("\0")
    return [n for n in nomes if n and (Path(raiz) / n).is_file()]


def _imprimir_json(dados):
    print(json.dumps(dados, ensure_ascii=False, indent=2))


def _cmd_stubs(args):
    raiz = Path(args.raiz)
    if not raiz.is_dir():
        raise ErroDeUso(f"{args.raiz}: não é um diretório")
    arquivos = args.arquivos if args.arquivos else _arquivos_desde(raiz, args.desde)
    candidatos = candidatos_stub(raiz, arquivos)
    if args.formato == "md":
        for c in candidatos:
            print(f"- [ ] {c['arquivo']}:{c['linha']} · {c['padrao']} · {c['texto']}")
    else:
        _imprimir_json(candidatos)
    return SAIDA_ITENS if candidatos else SAIDA_OK


def _cmd_sem_teste(args):
    catalogo = _ler_json(args.catalogo)
    if args.entregues is not None and not args.entregues:
        raise ErroDeUso("--entregues sem ids: informe as tarefas entregues (T-1 T-2 ...) ou omita a opção.")
    if not args.todos and _tem_tarefas(catalogo) and not estado_de_tarefas_conhecido(catalogo, args.entregues):
        raise ErroDeUso(
            f"{args.catalogo}: nenhuma tarefa tem `status` e nada foi informado em --entregues; "
            "sem saber o que foi entregue a lista sairia vazia. Informe --entregues T-1 T-2 ... ou use --todos.")
    itens = requisitos_sem_teste(catalogo, todos=args.todos, entregues=args.entregues)
    if args.formato == "md":
        for linha in linhas_conferencia(itens, catalogo):
            print(linha)
    else:
        _imprimir_json(itens)
    return SAIDA_ITENS if itens else SAIDA_OK

# ---------------------------------------------------------------------------------------------------------------------
# ligar: bloco `**Catálogo:**` dos planos -> tasks[], task_ids, requirement_ids, plan_owners (e tests[] na entrega)
# ---------------------------------------------------------------------------------------------------------------------
PASTA_PLANOS = "docs/superpowers/plans"
COLECOES_ACEITAS = ("differences", "requirements", "scenarios")
STATUS_PLANEJADA = "planejada"
STATUS_ENTREGUE_NOVO = "entregue"
_RE_CERCA_ABRE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
_RE_CERCA_FECHA = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*$")
_RE_TITULO = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_RE_TAREFA = re.compile(r"^Task\s+(\d+)\s*[:：.—–-]\s*(.*)$")
_RE_BLOCO = re.compile(r"^\s*\*\*Cat[áa]logo(?::\*\*|\*\*:)\s*(.*?)\s*$", re.IGNORECASE)
_RE_TESTE = re.compile(r"^\s*[-*]\s*Tests?\s*:\s*(.+?)\s*$", re.IGNORECASE)
_RE_LEDGER_CABECALHO = re.compile(r"^#\s*SDD ledger\s*[—–-]+\s*plan:\s*(.+?)\s*$", re.IGNORECASE)
_RE_LEDGER_COMPLETA = re.compile(r"^\s*(?:[-*+]\s+)?(?:\[[ xX]\]\s*)?Task\s+(\d+)\s*:\s*complete\b", re.IGNORECASE)
_NENHUM = {"nenhum", "nenhuma", "none"}


def _nome_arquivo(caminho):
    """Nome do arquivo de um caminho com `/` ou `\\`; é com ele que planos e ledgers são comparados."""
    return str(caminho).replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]


def _stem(nome):
    return nome[:-3] if nome.lower().endswith(".md") else nome


def _parece_caminho(ficha):
    """Ficha com cara de caminho de arquivo: tem `/` ou termina em extensão; opção de linha de comando não é caminho."""
    return bool(ficha) and not ficha.startswith("-") and ("/" in ficha or re.search(r"\.[A-Za-z0-9]+$", ficha) is not None)


def _limpar_ficha(ficha):
    ficha = ficha.strip().strip("\"'(),;").split("::")[0].rstrip(".:")  # «tests/a.ts.» e «tests/a.ts:» (fim de frase)
    return re.sub(r":\d+(-\d+)?$", "", ficha).rstrip(".:").strip()


def _caminho_de_teste(texto):
    """Caminhos de teste de uma linha `- Test:`. Só conta ficha com cara de caminho (`/` ou extensão de arquivo).

    Entre crases valem todas as fichas-caminho de cada trecho (`pytest tests/x.py` dá `tests/x.py`); sem crases, a 1ª ficha-caminho
    de cada item separado por vírgula. Sufixos `:10-20` e `::teste` saem.
    """
    entre_crases = re.findall(r"`([^`]+)`", texto)
    caminhos = []

    def somar(ficha):
        ficha = _limpar_ficha(ficha)
        if _parece_caminho(ficha) and ficha not in caminhos:
            caminhos.append(ficha)
            return True
        return False

    if entre_crases:
        for trecho in entre_crases:
            for ficha in trecho.split():
                somar(ficha)
    else:
        for item in texto.split(","):
            for ficha in item.split():
                if somar(ficha):
                    break
    return caminhos


def _ids_do_bloco(valor):
    """(ids, nenhum): ids do bloco `**Catálogo:**` (sem crases nem comentário entre parênteses) e se declarou «nenhum»."""
    valor = re.sub(r"\([^)]*\)", " ", valor.replace("`", ""))
    fichas = [f.strip().rstrip(".") for f in re.split(r"[,;\s]+", valor) if f.strip().rstrip(".")]
    nenhum = any(f.lower() in _NENHUM for f in fichas)
    return [f for f in fichas if f.lower() not in _NENHUM], nenhum


def ler_plano(caminho):
    """Tarefas de um plano: `{nome, stem, tarefas: [{numero, titulo, ids, nenhum, tem_bloco, testes}]}`; sem `Task N` é erro de uso."""
    caminho = Path(caminho)
    try:
        texto = caminho.read_text(encoding="utf-8-sig")
    except (OSError, ValueError) as erro:
        raise ErroDeUso(f"{caminho}: {erro}") from erro
    nome = caminho.name
    secoes = []  # [nivel, numero, titulo, linhas]
    atual = None
    cerca = None  # (caractere, tamanho) da cerca aberta, como no CommonMark
    for linha in texto.splitlines():
        if cerca is not None:
            fecha = _RE_CERCA_FECHA.match(linha)
            if fecha and fecha.group(1)[0] == cerca[0] and len(fecha.group(1)) >= cerca[1]:
                cerca = None
            if atual is not None:
                atual[3].append((linha, True))
            continue
        abre = _RE_CERCA_ABRE.match(linha)
        if abre and not (abre.group(1)[0] == "`" and "`" in abre.group(2)):
            cerca = (abre.group(1)[0], len(abre.group(1)))
            if atual is not None:
                atual[3].append((linha, True))
            continue
        em_cerca = False
        titulo = None if em_cerca else _RE_TITULO.match(linha)
        if titulo:
            nivel = len(titulo.group(1))
            tarefa = _RE_TAREFA.match(titulo.group(2)) if nivel in (2, 3) else None
            if tarefa:
                atual = [nivel, int(tarefa.group(1)), tarefa.group(2).strip(), []]
                secoes.append(atual)
                continue
            if atual is not None and nivel <= atual[0]:
                atual = None
                continue
        if atual is not None:
            atual[3].append((linha, em_cerca))
    if not secoes:
        raise ErroDeUso(f"{caminho}: nenhuma tarefa «Task N:» (título de nível 2 ou 3) no plano")
    numeros = [s[1] for s in secoes]
    repetidos = sorted({n for n in numeros if numeros.count(n) > 1})
    if repetidos:
        raise ErroDeUso(f"{caminho}: «Task {repetidos[0]}» aparece mais de uma vez no plano")
    tarefas = []
    for _nivel, numero, titulo, linhas in secoes:
        ids, nenhum, tem_bloco, testes = [], False, False, []
        for linha, na_cerca in linhas:
            if na_cerca:
                continue
            bloco = _RE_BLOCO.match(linha)
            if bloco:
                tem_bloco = True
                achados, so_nenhum = _ids_do_bloco(bloco.group(1))
                nenhum = nenhum or so_nenhum
                ids.extend(i for i in achados if i not in ids)
                continue
            teste = _RE_TESTE.match(linha)
            if teste:
                testes.extend(c for c in _caminho_de_teste(teste.group(1)) if c not in testes)
        tarefas.append({"numero": numero, "titulo": titulo, "ids": ids, "nenhum": nenhum, "tem_bloco": tem_bloco, "testes": testes})
    return {"nome": nome, "stem": _stem(nome), "tarefas": tarefas}


def ler_ledger(texto_arg, planos):
    """Interpreta `PLANO=progress.md`: devolve (nome do plano, números das tarefas `complete`); ledger de outro plano é erro de uso."""
    posicoes = [i for i, c in enumerate(texto_arg) if c == "="]
    if not posicoes:
        raise ErroDeUso(f"--ledger {texto_arg!r}: use PLANO=progress.md")
    nomes = {p["nome"] for p in planos}
    escolhido = next(((texto_arg[:i], texto_arg[i + 1:]) for i in posicoes if _nome_arquivo(texto_arg[:i]) in nomes), None)
    if escolhido is None:
        raise ErroDeUso(f"--ledger {texto_arg!r}: o plano à esquerda do «=» não está em --planos")
    plano, ledger = escolhido
    try:
        linhas = Path(ledger).read_text(encoding="utf-8-sig").splitlines()
    except (OSError, ValueError) as erro:
        raise ErroDeUso(f"{ledger}: {erro}") from erro
    cabecalho = _RE_LEDGER_CABECALHO.match(linhas[0]) if linhas else None
    if not cabecalho:
        raise ErroDeUso(f"{ledger}: a 1ª linha precisa ser «# SDD ledger — plan: <caminho>»")
    if _nome_arquivo(cabecalho.group(1)) != _nome_arquivo(plano):
        raise ErroDeUso(f"{ledger}: o ledger é do plano {_nome_arquivo(cabecalho.group(1))}, não de {_nome_arquivo(plano)}")
    completas = {int(m.group(1)) for linha in linhas[1:] for m in [_RE_LEDGER_COMPLETA.match(linha)] if m}
    return _nome_arquivo(plano), completas


def _eh_visual(cenario):
    """Cenário com dimensão `visual`; `dimensions` aceita strings e objetos `{id}`."""
    for dimensao in _lista(cenario.get("dimensions")):
        valor = dimensao.get("id") if isinstance(dimensao, dict) else dimensao
        if isinstance(valor, str) and valor.strip().lower() == "visual":
            return True
    return False


def _nome_do_plano_da_tarefa(tarefa):
    plano = tarefa.get("plan")
    return _nome_arquivo(plano) if isinstance(plano, str) and plano.strip() else None


def _colecao_do_id(catalogo, ident):
    """Coleção de nível raiz (lista de objetos) em que o id aparece, ou None."""
    if isinstance(catalogo, dict):
        for chave, valor in catalogo.items():
            if isinstance(valor, list) and any(isinstance(r, dict) and r.get("id") == ident for r in valor):
                return chave
    return None


def _fechamento(catalogo, ids_do_bloco):
    """Fechamento do bloco, só descendo: DF -> seus REQ -> seus SC. Devolve (DFs, REQs, SCs) na ordem do catálogo."""
    por_id = {chave: {r["id"]: r for r in _registros(catalogo, chave)} for chave in COLECOES_ACEITAS}
    dfs = {i for i in ids_do_bloco if i in por_id["differences"]}
    reqs = {i for i in ids_do_bloco if i in por_id["requirements"]}
    scs = {i for i in ids_do_bloco if i in por_id["scenarios"]}
    for df in dfs:
        reqs.update(r for r in _ids(por_id["differences"][df].get("requirement_ids")) if r in por_id["requirements"])
    for req in reqs:
        scs.update(s for s in _ids(por_id["requirements"][req].get("scenario_ids")) if s in por_id["scenarios"])
    ordem = lambda chave, conjunto: [i for i in por_id[chave] if i in conjunto]
    return ordem("differences", dfs), ordem("requirements", reqs), ordem("scenarios", scs)


def _sem_df_no_bloco(catalogo, ids_do_bloco, dfs_do_bloco):
    """REQ e SC listados no bloco que nenhuma DF listada no mesmo bloco alcança (o fechamento só desce)."""
    diferencas = {r["id"]: r for r in _registros(catalogo, "differences")}
    requisitos = {r["id"]: r for r in _registros(catalogo, "requirements")}
    alcancados_req = {r for d in dfs_do_bloco for r in _ids(diferencas[d].get("requirement_ids"))}
    alcancados_sc = {s for r in alcancados_req if r in requisitos for s in _ids(requisitos[r].get("scenario_ids"))}
    avisos = []
    for ident in ids_do_bloco:
        if ident in requisitos and ident not in alcancados_req:
            avisos.append({"codigo": "REQ_SEM_DF", "ref": ident})
        elif ident in {r["id"] for r in _registros(catalogo, "scenarios")} and ident not in alcancados_sc:
            avisos.append({"codigo": "SC_SEM_DF", "ref": ident})
    return avisos


def calcular_ligacao(catalogo, planos, entregues=None, raiz=None):
    """Aplica os blocos dos `planos` a uma cópia do catálogo. Devolve (catalogo novo, relatório); não grava nada.

    `entregues`: {nome do plano: {números de tarefa completas}} vindo dos ledgers. `raiz`: onde procurar os arquivos de teste.
    """
    entregues = entregues or {}
    novo = copy.deepcopy(catalogo)
    bloqueantes, avisos = [], []
    bloqueio = lambda codigo, ref, detalhe="": bloqueantes.append({"codigo": codigo, "ref": ref, "detalhe": detalhe})
    nomes = {p["nome"] for p in planos}
    stems = {p["stem"]: p for p in planos}
    diferencas = {r["id"]: r for r in _registros(novo, "differences")}
    requisitos = {r["id"]: r for r in _registros(novo, "requirements")}
    cenarios = {r["id"]: r for r in _registros(novo, "scenarios")}
    if not isinstance(novo.get("tasks"), list):
        novo["tasks"] = []
    if not isinstance(novo.get("tests"), list):
        novo["tests"] = []

    # 1. Tarefas existentes dos planos passados: recalculadas. As de outros planos e as sem `plan` ficam como estão.
    antigas = {t["id"]: t for t in _registros(novo, "tasks") if _nome_do_plano_da_tarefa(t) in nomes}
    padrao_gerado = re.compile(r"^(?:%s)/T\d+$" % "|".join(re.escape(s) for s in stems)) if stems else None
    ids_de_outros = {}  # tarefas de plano não passado: id -> nome do plano
    for t in _registros(novo, "tasks"):
        dono = _nome_do_plano_da_tarefa(t)
        if dono and dono not in nomes:
            ids_de_outros[t["id"]] = _stem(dono)

    for plano in planos:
        existentes = {t["numero"] for t in plano["tarefas"]}
        for numero in sorted(entregues.get(plano["nome"], set()) - existentes):
            avisos.append({"codigo": "LEDGER_TAREFA_INEXISTENTE", "ref": f"{plano['stem']}/T{numero}",
                           "detalhe": f"o ledger marca «Task {numero}: complete», mas o plano não tem essa tarefa"})

    # 2. Leitura dos blocos: o que cada tarefa quer ligar.
    pedidas = []  # tarefas com entrega no catálogo
    todas_as_ids_do_catalogo = {r["id"] for v in novo.values() if isinstance(v, list) for r in v if isinstance(r, dict) and isinstance(r.get("id"), str)}
    for plano in planos:
        for tarefa in plano["tarefas"]:
            tid = f"{plano['stem']}/T{tarefa['numero']}"
            tarefa["id"] = tid
            if not tarefa["tem_bloco"]:
                bloqueio("TAREFA_SEM_BLOCO", tid, f"{plano['nome']}: «Task {tarefa['numero']}» sem a linha «**Catálogo:**»; use «nenhum» se a tarefa não entrega nada no catálogo")
                continue
            if tarefa["nenhum"] and tarefa["ids"]:
                bloqueio("NENHUM_MISTURADO", tid, "«nenhum» não pode vir junto de ids")
                continue
            if tarefa["nenhum"]:
                continue
            if not tarefa["ids"]:
                bloqueio("BLOCO_VAZIO", tid, "«**Catálogo:**» sem ids")
                continue
            validos = []
            for ident in tarefa["ids"]:
                if ident in diferencas and diferencas[ident].get("disposition"):
                    bloqueio("DISPOSITION_NO_BLOCO", tid, f"{ident} tem disposition; exceção aprovada não recebe tarefa (quem muda isso é o usuário)")
                elif ident in diferencas or ident in requisitos or ident in cenarios:
                    validos.append(ident)
                else:
                    colecao = _colecao_do_id(novo, ident)
                    if colecao:
                        bloqueio("COLECAO_NAO_ACEITA", tid, f"{ident} é de «{colecao}»; só differences, requirements e scenarios")
                    else:
                        bloqueio("ID_INEXISTENTE", tid, f"{ident} não existe no catálogo")
            dfs, reqs, scs = _fechamento(novo, validos)
            dfs = [d for d in dfs if not diferencas[d].get("disposition")]
            avisos.extend({**a, "tarefa": tid} for a in _sem_df_no_bloco(novo, validos, dfs))
            if tid in todas_as_ids_do_catalogo and tid not in antigas:
                bloqueio("ID_COLIDE", tid, "o id gerado já existe no catálogo em outro registro")
            visuais = [s for s in scs if _eh_visual(cenarios[s])]
            funcionais = [s for s in scs if s not in visuais]
            if funcionais and not tarefa["testes"]:
                bloqueio("TESTE_SEM_CAMINHO", tid, "a tarefa tem cenário funcional e nenhuma linha «- Test: `caminho`» no plano")
            pedidas.append({
                "id": tid, "plano": plano, "tarefa": tarefa, "bloco": validos, "dfs": dfs, "reqs": reqs, "scs": scs,
                "visuais": visuais, "funcionais": funcionais,
            })

    # 3. Tarefa já entregue que sumiu do plano relido.
    gerados = {p["id"] for p in pedidas}
    for tid, antiga in antigas.items():
        status = antiga.get("status")
        entregue = isinstance(status, str) and status.strip().lower() in STATUS_ENTREGUE
        if entregue and tid not in gerados:
            bloqueio("ENTREGUE_SUMIDA", tid, "a tarefa já entregue não está mais no plano com bloco do catálogo (renumeração?)")

    # 4. Dupla posse: entre os planos passados e contra tarefas de outros planos já gravadas no catálogo.
    donos = {}  # id -> {plano}
    for p in pedidas:
        for ident in p["dfs"] + p["reqs"] + p["scs"]:
            donos.setdefault(ident, set()).add(p["plano"]["nome"])
    for ident, quem in sorted(donos.items()):
        if len(quem) > 1:
            bloqueio("DUPLA_POSSE", ident, "no bloco de mais de um plano: " + ", ".join(sorted(quem)))
            continue
        meu = next(iter(quem))
        externos = set()
        registro = diferencas.get(ident) or requisitos.get(ident)
        if registro is not None:
            externos.update(ids_de_outros[t] for t in _ids(registro.get("task_ids")) if t in ids_de_outros)
        else:
            externos.update(ids_de_outros[t["id"]] for t in _registros(novo, "tasks") if t["id"] in ids_de_outros and ident in _ids(t.get("scenario_ids")))
            externos.update(o for o in (_stem(_nome_arquivo(x)) for x in _ids(cenarios[ident].get("plan_owners"))) if o not in stems)
        if externos:
            bloqueio("DUPLA_POSSE", ident, f"o plano {meu} quer ligar, mas já pertence a: " + ", ".join(sorted(externos)))

    # 5. Aplica: tasks[], task_ids, plan_owners, tests[].
    meus_ids = set(antigas) | gerados | {i for r in list(diferencas.values()) + list(requisitos.values()) for i in _ids(r.get("task_ids")) if padrao_gerado and padrao_gerado.match(i)}
    removidas = [t for t in antigas if t not in gerados]
    por_id_tarefa = {t["id"]: t for t in _registros(novo, "tasks")}
    resultado_tarefas = []
    for p in pedidas:
        tid, plano, tarefa = p["id"], p["plano"], p["tarefa"]
        existente = por_id_tarefa.get(tid) if tid in antigas else None
        completas = entregues.get(plano["nome"], set())
        status_antigo = existente.get("status") if existente else None
        antigo_entregue = isinstance(status_antigo, str) and status_antigo.strip().lower() in STATUS_ENTREGUE
        if antigo_entregue:
            status = status_antigo
        elif tarefa["numero"] in completas:
            status = STATUS_ENTREGUE_NOVO
        else:
            status = status_antigo if isinstance(status_antigo, str) and status_antigo.strip() else STATUS_PLANEJADA
        entregue = isinstance(status, str) and status.strip().lower() in STATUS_ENTREGUE
        if existente is None:
            registro = {"id": tid, "plan": f"{PASTA_PLANOS}/{plano['nome']}", "title": tarefa["titulo"],
                        "requirement_ids": p["reqs"], "scenario_ids": p["scs"], "status": status}
            novo["tasks"].append(registro)
            acao = "nova"
        else:
            antes = json.dumps(existente, sort_keys=True)
            existente.update({"plan": f"{PASTA_PLANOS}/{plano['nome']}", "title": tarefa["titulo"],
                              "requirement_ids": p["reqs"], "scenario_ids": p["scs"], "status": status})
            acao = "igual" if json.dumps(existente, sort_keys=True) == antes else "atualizada"
        # tests[] já gravados desta tarefa: sai o cenário que ela não tem mais; teste sem cenário sai (vale sem --raiz).
        mantidos = []
        for teste in novo["tests"]:
            if isinstance(teste, dict) and teste.get("task_id") == tid and isinstance(teste.get("scenario_ids"), list):
                restantes = [c for c in teste["scenario_ids"] if c in p["scs"]]
                if restantes != teste["scenario_ids"]:
                    if not restantes:
                        continue
                    teste["scenario_ids"] = restantes
            mantidos.append(teste)
        novo["tests"] = mantidos
        # tests[] novos: só na entrega, com a raiz, e só cenários funcionais.
        a_gravar, sem_arquivo = [], []
        if entregue and raiz is not None and p["funcionais"]:
            for caminho in tarefa["testes"]:
                destino = (Path(raiz) / caminho).resolve()
                try:
                    relativo = destino.relative_to(Path(raiz).resolve()).as_posix()
                except ValueError:
                    sem_arquivo.append(caminho)
                    continue
                if not destino.is_file():
                    sem_arquivo.append(caminho)
                    continue
                teste_id = f"{tid}:{relativo}"
                a_gravar.append(teste_id)
                atual = next((t for t in novo["tests"] if isinstance(t, dict) and t.get("id") == teste_id), None)
                if atual is None:
                    novo["tests"].append({"id": teste_id, "task_id": tid, "scenario_ids": list(p["funcionais"]), "file": relativo})
                else:
                    atual.update({"task_id": tid, "scenario_ids": list(p["funcionais"]), "file": relativo})
        p.update({"acao": acao, "status": status, "entregue": entregue, "testes_a_gravar": a_gravar, "testes_sem_arquivo": sem_arquivo})
        resultado_tarefas.append(p)

    # task_ids de DF e REQ, plan_owners dos cenários
    donas = {}  # id de DF/REQ/SC -> [ids de tarefa] na ordem dos planos
    for p in pedidas:
        for ident in p["dfs"] + p["reqs"] + p["scs"]:
            donas.setdefault(ident, []).append(p["id"])
    for registros in (diferencas, requisitos):
        for ident, registro in registros.items():
            atuais = _ids(registro.get("task_ids")) if isinstance(registro.get("task_ids"), list) else []
            desejados = donas.get(ident, [])
            if not any(t in meus_ids for t in atuais) and not desejados:
                continue
            lista = [t for t in atuais if t not in meus_ids or t in desejados]
            lista += [t for t in desejados if t not in lista]
            registro["task_ids"] = lista
    for ident, cenario in cenarios.items():
        quem = {pedido["plano"]["stem"] for pedido in pedidas if ident in pedido["scs"]}
        atuais = [o for o in _lista(cenario.get("plan_owners")) if isinstance(o, str)]
        mantidos = [o for o in atuais if o not in stems or o in quem]
        lista = mantidos + sorted(q for q in quem if q not in mantidos)
        if lista != atuais:
            if lista:
                cenario["plan_owners"] = lista
            else:
                cenario.pop("plan_owners", None)
    if removidas:
        novo["tasks"] = [t for t in novo["tasks"] if not (isinstance(t, dict) and t.get("id") in removidas)]
        novo["tests"] = [t for t in novo["tests"] if not (isinstance(t, dict) and t.get("task_id") in removidas)]

    # 6. Pendências do catálogo inteiro, já com o que foi ligado; DF com disposition fica de fora.
    pendencias = [{"codigo": "DF_SEM_TAREFA", "ref": d["id"]} for d in _registros(novo, "differences") if not d.get("disposition") and not _ids(d.get("task_ids"))]
    pendencias += [{"codigo": "REQ_SEM_TAREFA", "ref": r["id"]} for r in _registros(novo, "requirements") if not _ids(r.get("task_ids"))]

    testados = {s for t in novo["tests"] if isinstance(t, dict) for s in _ids(t.get("scenario_ids"))}
    visuais_pendentes = [{"tarefa": p["id"], "cenarios": p["visuais"]} for p in resultado_tarefas if p["visuais"]]
    faltas_funcionais = [{"tarefa": p["id"], "cenarios": [s for s in p["funcionais"] if s not in testados]} for p in resultado_tarefas
                         if p["entregue"] and any(s not in testados for s in p["funcionais"])]
    for aviso in ({"codigo": "TESTE_SEM_ARQUIVO", "tarefa": p["id"], "ref": c} for p in resultado_tarefas for c in p["testes_sem_arquivo"]):
        avisos.append(aviso)
    relatorio = {
        "gravado": False,
        "planos": [],
        "bloqueantes": bloqueantes,
        "pendencias": pendencias,
        "avisos": avisos,
        "visuais_pendentes": visuais_pendentes,
        "faltas_funcionais": faltas_funcionais,
    }
    for plano in planos:
        itens = []
        for tarefa in plano["tarefas"]:
            tid = tarefa["id"]
            pedido = next((p for p in resultado_tarefas if p["id"] == tid), None)
            item = {"id": tid, "titulo": tarefa["titulo"], "numero": tarefa["numero"]}
            if pedido is None:
                item["catalogo"] = "nenhum" if tarefa["nenhum"] else "sem bloco" if not tarefa["tem_bloco"] else "inválido"
            else:
                fechado = [i for i in pedido["dfs"] + pedido["reqs"] + pedido["scs"] if i not in pedido["bloco"]]
                item.update({"acao": pedido["acao"], "status": pedido["status"], "bloco": pedido["bloco"], "fechado_alem_do_bloco": fechado,
                             "diferencas": pedido["dfs"], "requisitos": pedido["reqs"], "cenarios": pedido["scs"],
                             "testes_no_plano": tarefa["testes"], "testes_a_gravar": pedido["testes_a_gravar"]})
            itens.append(item)
        relatorio["planos"].append({"plano": plano["nome"], "tarefas": itens})
    return novo, relatorio


def _formato_do_arquivo(texto):
    """(indentação, ensure_ascii, quebra de linha, \\n final) do JSON original, para regravar sem reformatar."""
    achado = re.search(r"\n([ \t]+)\"", texto)
    indent = ("\t" if achado.group(1).startswith("\t") else len(achado.group(1))) if achado else 2
    ascii_puro = bool(re.search(r"\\u[0-9a-fA-F]{4}", texto)) and texto.isascii()
    return indent, ascii_puro, "\r\n" if "\r\n" in texto else "\n", texto.endswith("\n")


def _gravar_catalogo(caminho, original, catalogo):
    indent, ascii_puro, quebra, final = _formato_do_arquivo(original)
    texto = json.dumps(catalogo, ensure_ascii=ascii_puro, indent=indent)
    if quebra != "\n":
        texto = texto.replace("\n", quebra)
    if final:
        texto += quebra
    if texto == original:
        return False
    caminho = Path(caminho)
    temporario = caminho.with_name(caminho.name + ".tmp")
    try:
        temporario.write_bytes(texto.encode("utf-8"))
        os.replace(temporario, caminho)
    except OSError as erro:
        try:
            temporario.unlink()
        except OSError:
            pass
        raise ErroDeUso(f"{caminho}: não foi possível gravar o catálogo: {erro}") from erro
    return True


def _linhas_ligacao(relatorio):
    linhas = []
    for plano in relatorio["planos"]:
        linhas.append(f"## {plano['plano']}")
        for t in plano["tarefas"]:
            if "acao" not in t:
                linhas.append(f"- {t['id']} · {t['titulo']} · catálogo: {t['catalogo']}")
                continue
            extra = f" · fechado além do bloco: {', '.join(t['fechado_alem_do_bloco'])}" if t["fechado_alem_do_bloco"] else ""
            linhas.append(f"- {t['id']} · {t['titulo']} · {t['acao']} · {t['status']} · DF {', '.join(t['diferencas']) or '-'} · "
                          f"REQ {', '.join(t['requisitos']) or '-'} · SC {', '.join(t['cenarios']) or '-'}{extra}")
    for chave, rotulo in (("bloqueantes", "Bloqueantes"), ("pendencias", "Pendências"), ("avisos", "Avisos")):
        if relatorio[chave]:
            linhas.append(f"## {rotulo}")
            linhas.extend("- " + " · ".join(str(v) for v in item.values() if v) for item in relatorio[chave])
    if relatorio["visuais_pendentes"]:
        linhas.append("## Visuais pendentes (conferência manual)")
        linhas.extend(f"- {i['tarefa']} · {', '.join(i['cenarios'])}" for i in relatorio["visuais_pendentes"])
    if relatorio["faltas_funcionais"]:
        linhas.append("## Entregues sem teste funcional")
        linhas.extend(f"- {i['tarefa']} · {', '.join(i['cenarios'])}" for i in relatorio["faltas_funcionais"])
    return linhas


def _cmd_ligar(args):
    caminho = Path(args.catalogo)
    try:
        original = caminho.read_bytes().decode("utf-8")
    except (OSError, ValueError) as erro:
        raise ErroDeUso(f"{args.catalogo}: {erro}") from erro
    catalogo = _ler_json(args.catalogo)
    if args.raiz is not None and not Path(args.raiz).is_dir():
        raise ErroDeUso(f"{args.raiz}: não é um diretório")
    planos = [ler_plano(p) for p in args.planos]
    nomes = [p["nome"] for p in planos]
    if len(set(nomes)) != len(nomes):
        raise ErroDeUso("dois planos com o mesmo nome de arquivo em --planos; o nome identifica o plano no catálogo")
    entregues = {}
    for texto in args.ledger or []:
        nome, completas = ler_ledger(texto, planos)
        entregues.setdefault(nome, set()).update(completas)
    novo, relatorio = calcular_ligacao(catalogo, planos, entregues, args.raiz)
    if args.gravar and not relatorio["bloqueantes"]:
        relatorio["gravado"] = _gravar_catalogo(caminho, original, novo)
    elif args.gravar:
        print("erro: há bloqueantes; nada foi gravado.", file=sys.stderr)
    if args.formato == "md":
        for linha in _linhas_ligacao(relatorio):
            print(linha)
    else:
        _imprimir_json(relatorio)
    return SAIDA_ITENS if relatorio["bloqueantes"] or relatorio["pendencias"] else SAIDA_OK


def _parser():
    parser = argparse.ArgumentParser(prog="verificacao.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("stubs", help="candidatos a código oco nos arquivos do plano ou alterados desde um commit")
    p.add_argument("--raiz", required=True, help="raiz do produto")
    origem = p.add_mutually_exclusive_group(required=True)
    origem.add_argument("--arquivos", nargs="+", metavar="F", help="arquivos relativos à raiz")
    origem.add_argument("--desde", metavar="COMMIT", help="arquivos alterados entre COMMIT e HEAD")
    p.add_argument("--formato", choices=("json", "md"), default="json")
    p.set_defaults(func=_cmd_stubs)

    p = sub.add_parser("sem-teste", help="requisitos do catálogo sem teste para nenhum cenário")
    p.add_argument("--catalogo", required=True)
    p.add_argument("--todos", action="store_true", help="inclui requisitos ainda não entregues")
    p.add_argument("--entregues", nargs="*", metavar="T", help="ids das tarefas já entregues (ledger do plano), além de tasks[].status")
    p.add_argument("--formato", choices=("json", "md"), default="json")
    p.set_defaults(func=_cmd_sem_teste)

    p = sub.add_parser("ligar", help="grava no catálogo as ligações declaradas no bloco «**Catálogo:**» dos planos (dry-run por padrão)")
    p.add_argument("--catalogo", required=True)
    p.add_argument("--planos", nargs="+", required=True, metavar="PLANO.md")
    p.add_argument("--ledger", action="append", metavar="PLANO=progress.md", help="ledger do SDD de um plano: marca «entregue» as tarefas «Task N: complete»")
    p.add_argument("--raiz", help="raiz do produto: com ela, tarefa entregue grava tests[] dos arquivos «- Test:» que existem")
    p.add_argument("--gravar", action="store_true", help="escreve o catálogo (sem isto só mostra); não grava havendo bloqueantes")
    p.add_argument("--formato", choices=("json", "md"), default="json")
    p.set_defaults(func=_cmd_ligar)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)  # erro de uso do argparse sai com 2
    if hasattr(sys.stdout, "reconfigure"):  # caminhos fora da code page legada (Windows) não quebram o print
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        return args.func(args)
    except ErroDeUso as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return SAIDA_USO


if __name__ == "__main__":
    sys.exit(main())
