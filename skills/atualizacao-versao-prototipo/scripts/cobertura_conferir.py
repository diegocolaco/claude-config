"""Conferências de cobertura da atualização de versão do protótipo: rastreio dos trechos, omissões, unidades de descoberta e achados.

Funções puras sobre dicionários (mapa, rastreio, catálogo, unidades); só `conferir_achados` lê o arquivo de achados de uma unidade.
Os códigos de saída ficam em `cobertura.py`. Só biblioteca padrão.
"""
import json
from math import ceil
from pathlib import Path
import re

SEM_IMPACTO = "SEM_IMPACTO"
NAO_INVESTIGADO = "NAO_INVESTIGADO"


def _lista(catalogo, chave):
    """Itens (dicts) do catálogo; chave ausente, nula ou de outro tipo vale lista vazia."""
    itens = catalogo.get(chave)
    if not isinstance(itens, list):
        return []
    return [item for item in itens if isinstance(item, dict)]


def _ids(itens):
    """IDs textuais dos itens (ids de outro tipo são ignorados, pois não casam com destino/local)."""
    return {item["id"] for item in itens if isinstance(item.get("id"), str)}


def _locais_nao_investigados(catalogo):
    """IDs de regiões e estados do catálogo com `discovery_status == NAO_INVESTIGADO`."""
    return _ids([
        item
        for chave in ("regions", "states")
        for item in _lista(catalogo, chave)
        if item.get("discovery_status") == NAO_INVESTIGADO
    ])


def _ids_do_mapa(mapa):
    """IDs dos trechos do mapa; o mapa é o lado obrigatório da cobertura e por isso é estrito (ValueError)."""
    trechos = mapa.get("trechos") if isinstance(mapa, dict) else None
    if not isinstance(trechos, list):
        raise ValueError("Mapa inválido: 'trechos' ausente ou não é uma lista.")
    ids = set()
    for posicao, trecho in enumerate(trechos):
        if not isinstance(trecho, dict) or not isinstance(trecho.get("id"), str):
            raise ValueError(f"Mapa inválido: o trecho na posição {posicao} não é um objeto com 'id' textual.")
        ids.add(trecho["id"])
    return ids


def _mesmo_commit(a, b):
    """Mesmo commit, aceitando SHA abreviado (7 caracteres ou mais) de um dos lados."""
    a, b = a.strip().lower(), b.strip().lower()
    return len(min(a, b, key=len)) >= 7 and (a.startswith(b) or b.startswith(a))


def _conferir_identidade(mapa, catalogo, atuais):
    """Achados de identidade do mapa: ele precisa corresponder às versões que o rastreio está fechando.

    Com `atuais` (SHA de `vigente` e `candidata` lidos agora no repositório): `MAPA_DESATUALIZADO` se algum difere do gravado
    no mapa (a branch andou depois dele). Sem `atuais`: `MAPA_OUTRA_VERSAO` se a `reference.version` do catálogo não é a
    `candidata_sha` do mapa (a skill grava a versão da candidata no catálogo). Mapa sem os SHAs
    (gerado antes deles) ou catálogo sem `reference.version` não têm o que comparar e passam.
    """
    achados = []
    if atuais is not None:
        for ref in ("vigente", "candidata"):
            gravado, atual = mapa.get(f"{ref}_sha"), atuais.get(ref)
            if isinstance(gravado, str) and isinstance(atual, str) and gravado and not _mesmo_commit(gravado, atual):
                achados.append({"codigo": "MAPA_DESATUALIZADO", "ref": ref, "gravado": gravado, "atual": atual})
        return achados
    referencia = catalogo.get("reference")
    versao = referencia.get("version") if isinstance(referencia, dict) else None
    candidata = mapa.get("candidata_sha")
    if isinstance(versao, str) and versao.strip() and isinstance(candidata, str) and candidata:
        if not _mesmo_commit(versao, candidata):
            achados.append({"codigo": "MAPA_OUTRA_VERSAO", "reference_version": versao, "candidata_sha": candidata})
    return achados


def conferir_rastreio(mapa, rastreio, catalogo, atuais=None, cruzamentos=None):
    """Confere que cada trecho do mapa tem destino válido na tabela de rastreio.

    `atuais` ({"vigente": sha, "candidata": sha}, lido do repositório) liga o mapa ao estado atual das refs; veja `_conferir_identidade`.
    Destino válido: `DF-…` existente em `catalogo['differences']`; `SEM_IMPACTO` com `motivo`;
    `NAO_INVESTIGADO` com `local` apontando região/estado do catálogo marcado como NAO_INVESTIGADO.
    `com_destino` conta só os destinos válidos; o que falta para `total` está em `faltantes`, `ids_inexistentes`, `sem_motivo`
    e `local_invalido`. Mapa malformado levanta ValueError. Trechos do rastreio que não existem no mapa (`desconhecidos`) reprovam: rastreio de outra versão não passa.
    Com `cruzamentos` (saída do `cruzar`), o resultado ganha `suspeitas_sem_destino` (suspeita forte sem diferença
    `INCONSISTENCIA-PROTO` com a assinatura em `cruzamento`) e `identidade` acusa `CRUZAMENTO_OUTRA_VERSAO`; os dois reprovam.
    Sem `cruzamentos`, o resultado é o de sempre: a chave nova não aparece.
    """
    ids_mapa = _ids_do_mapa(mapa)
    entradas = rastreio.get("trechos")
    if not isinstance(entradas, dict):
        entradas = {}
    diferencas = _ids(_lista(catalogo, "differences"))
    locais = _locais_nao_investigados(catalogo)

    faltantes, sem_motivo, local_invalido = [], [], []
    inexistentes = {}
    com_destino = 0
    for trecho in sorted(ids_mapa):
        entrada = entradas.get(trecho)
        destino = entrada.get("destino") if isinstance(entrada, dict) else None
        if not isinstance(destino, str):
            faltantes.append(trecho)
        elif destino == SEM_IMPACTO:
            motivo = entrada.get("motivo")
            if isinstance(motivo, str) and motivo.strip():
                com_destino += 1
            else:
                sem_motivo.append(trecho)
        elif destino == NAO_INVESTIGADO:
            local = entrada.get("local")
            if isinstance(local, str) and local in locais:
                com_destino += 1
            else:
                local_invalido.append(trecho)
        elif destino.startswith("DF-"):
            if destino in diferencas:
                com_destino += 1
            else:
                inexistentes.setdefault(destino, []).append(trecho)
        else:
            faltantes.append(trecho)  # destino fora do vocabulário não cobre o trecho

    desconhecidos = sorted(set(entradas) - ids_mapa)
    ids_inexistentes = [{"id": i, "trechos": sorted(ts)} for i, ts in sorted(inexistentes.items())]
    identidade = _conferir_identidade(mapa, catalogo, atuais)
    sem_destino = None
    if cruzamentos is not None:
        sem_destino = _suspeitas_sem_destino(cruzamentos, catalogo)
        identidade += _conferir_cruzamento(mapa, cruzamentos)
    ok = not (faltantes or desconhecidos or ids_inexistentes or sem_motivo or local_invalido or identidade or sem_destino)
    resultado = {
        "ok": ok,
        "identidade": identidade,
        "total": len(ids_mapa),
        "com_destino": com_destino,
        "faltantes": faltantes,
        "desconhecidos": desconhecidos,
        "ids_inexistentes": ids_inexistentes,
        "sem_motivo": sem_motivo,
        "local_invalido": local_invalido,
    }
    if sem_destino is not None:
        resultado["suspeitas_sem_destino"] = sem_destino
    return resultado


def _suspeitas_fortes(cruzamentos):
    """Suspeitas fortes (`id` e `assinatura` textuais) do `cruzamentos.json`; formato inesperado levanta ValueError."""
    suspeitas = cruzamentos.get("suspeitas")
    if not isinstance(suspeitas, list):
        raise ValueError("Cruzamentos inválidos: 'suspeitas' ausente ou não é uma lista.")
    fortes = []
    for posicao, s in enumerate(suspeitas):
        if not isinstance(s, dict) or not isinstance(s.get("id"), str) or not isinstance(s.get("assinatura"), str):
            raise ValueError(f"Cruzamentos inválidos: a suspeita na posição {posicao} não tem 'id' e 'assinatura' textuais.")
        if s.get("forca", "forte") == "forte":
            fortes.append(s)
    return fortes


def _suspeitas_sem_destino(cruzamentos, catalogo):
    """Suspeitas fortes sem diferença `INCONSISTENCIA-PROTO` cujo `cruzamento` (texto ou lista) traga a assinatura."""
    registradas = set()
    for diferenca in _lista(catalogo, "differences"):
        if diferenca.get("classe") != "INCONSISTENCIA-PROTO":
            continue
        cruzamento = diferenca.get("cruzamento")
        registradas.update([cruzamento] if isinstance(cruzamento, str) else _textos(cruzamento))
    return [{"id": s["id"], "assinatura": s["assinatura"]} for s in _suspeitas_fortes(cruzamentos)
            if s["assinatura"] not in registradas]


def _conferir_cruzamento(mapa, cruzamentos):
    """`CRUZAMENTO_OUTRA_VERSAO` se o `candidata` do cruzamento não é a `candidata_sha` do mapa (sem a SHA, nada a comparar)."""
    candidata_mapa, candidata = mapa.get("candidata_sha"), cruzamentos.get("candidata")
    if not (isinstance(candidata_mapa, str) and candidata_mapa):
        return []
    if isinstance(candidata, str) and candidata and _mesmo_commit(candidata, candidata_mapa):
        return []
    return [{"codigo": "CRUZAMENTO_OUTRA_VERSAO", "cruzamento_candidata": candidata, "candidata_sha": candidata_mapa}]


def listar_omissoes(antes, depois):
    """Diferenças presentes em `depois` e ausentes em `antes` (informativo: `ok` é sempre True)."""
    conhecidas = _ids(_lista(antes, "differences"))
    omissoes = [
        {"id": d.get("id"), "surface_id": d.get("surface_id")}
        for d in _lista(depois, "differences")
        if d.get("id") not in conhecidas
    ]
    omissoes.sort(key=lambda o: str(o["id"]))
    return {"ok": True, "omissoes": omissoes}


def _lista_ou_nenhum(itens):
    return ", ".join(str(i) for i in itens) or "nenhum"


def resumir_cobertura(mapa, rastreio, catalogo, antes=None, itens_omitidos=None, telas_relidas=None, cruzamentos=None, caminho=""):
    """Números do resumo da descoberta, contados dos arquivos, e a linha de cobertura pronta para copiar.

    `ok` é falso com pendência no rastreio ou tela nova sem releitura. `telas_relidas` None quer dizer que a leitura cega
    não foi informada: a linha diz isso, em vez de dar a entender que houve. Mapa malformado levanta ValueError.
    """
    conferencia = conferir_rastreio(mapa, rastreio, catalogo, None, cruzamentos)
    destinos = [e.get("destino") for e in (rastreio.get("trechos") or {}).values() if isinstance(e, dict)]
    trechos = {
        "total": conferencia["total"], "com_destino": conferencia["com_destino"],
        "em_diferencas": sum(1 for d in destinos if isinstance(d, str) and d.startswith("DF-")),
        "sem_impacto": destinos.count(SEM_IMPACTO), "nao_investigado": destinos.count(NAO_INVESTIGADO),
    }
    regioes = sum(1 for chave in ("regions", "states") for item in _lista(catalogo, chave)
                  if item.get("discovery_status") == NAO_INVESTIGADO)
    resumo_catalogo = {"diferencas": len(_lista(catalogo, "differences")), "regioes_nao_investigadas": regioes}
    pendentes = [*conferencia["faltantes"], *(t for i in conferencia["ids_inexistentes"] for t in i["trechos"]),
                 *conferencia["sem_motivo"], *conferencia["local_invalido"]]

    novas = sorted(t["id"] for t in _lista(mapa, "telas") if t.get("nova") is True and t.get("removida") is not True)
    leitura = None
    if telas_relidas is None:
        texto_leitura = "leitura cega: não informada"
    else:
        relidas = sorted(set(telas_relidas))
        faltando = sorted(set(novas) - set(relidas))
        leitura = {"telas_relidas": relidas, "total_telas": len(_lista(mapa, "telas")), "novas_sem_releitura": faltando}
        texto_leitura = (f"leitura cega: {len(relidas)}/{leitura['total_telas']} telas, "
                         f"novas sem releitura: {_lista_ou_nenhum(faltando)}")

    por_tela = {t: len(v) for t, v in sorted((itens_omitidos or {}).items()) if isinstance(v, list) and v}
    ids_omissoes = [o["id"] for o in listar_omissoes(antes, catalogo)["omissoes"]] if antes is not None else []
    omissoes = {"diferencas": ids_omissoes, "itens_por_tela": por_tela, "total_itens": sum(por_tela.values())}
    texto_omissoes = (f"omissões da leitura cega: {omissoes['total_itens']} itens em {len(por_tela)} telas, "
                      f"{len(ids_omissoes)} diferenças ({_lista_ou_nenhum(ids_omissoes)})")

    resumo_cruzamento = (cruzamentos or {}).get("resumo") or {}
    fortes = [d.get("id") for d in _lista(catalogo, "differences") if d.get("classe") == "INCONSISTENCIA-PROTO"]
    avisos = _textos((cruzamentos or {}).get("avisos"))
    texto_cruzamento = (f"cruzamento: {resumo_cruzamento.get('fortes', 0)} fortes ({_lista_ou_nenhum(fortes)}), "
                        f"{resumo_cruzamento.get('fracas', 0)} fracas, {resumo_cruzamento.get('preexistentes', 0)} preexistentes; "
                        f"avisos do cruzamento: {_lista_ou_nenhum(avisos)}") if cruzamentos else "cruzamento: não informado"

    linha = (f"Cobertura: {trechos['com_destino']}/{trechos['total']} trechos com destino válido "
             f"({trechos['em_diferencas']} em diferenças, {trechos['sem_impacto']} SEM_IMPACTO, "
             f"{trechos['nao_investigado']} NAO_INVESTIGADO em {regioes} regiões); "
             f"pendentes: {_lista_ou_nenhum(pendentes)}; diferenças no catálogo: {resumo_catalogo['diferencas']}; "
             f"{texto_leitura}; {texto_omissoes}; caminho: {caminho or 'não informado'}; {texto_cruzamento}")
    ok = conferencia["ok"] and not (leitura and leitura["novas_sem_releitura"])
    return {"ok": ok, "linha": linha, "trechos": trechos, "catalogo": resumo_catalogo, "pendentes": pendentes,
            "leitura_cega": leitura, "omissoes": omissoes}


# ---------------------------------------------------------------------------
# Unidades de descoberta (fase 2): quebra do mapa em fatias que cabem no orçamento de um agente.
# ---------------------------------------------------------------------------

DIFERENCA = "DIFERENCA"
DESTINOS_ACHADOS = (DIFERENCA, SEM_IMPACTO, NAO_INVESTIGADO)
CAMPOS_PROPOSTA = ("tela", "regiao", "antes", "agora", "fonte_prototipo", "fonte_produto", "trechos")
# Sem o tamanho do arquivo no mapa, trecho sem tela é estimado pela regra do mapa (~10 tokens por linha, vezes 2).
TOKENS_POR_LINHA = 20
TOKENS_TRECHO_SEM_LINHAS = 100
# Trechos de idiomas fora da referência não vão a agente: o comando `idiomas` os compara por script.
UNIDADE_IDIOMAS = "U-IDIOMAS"
IDIOMA_NO_CAMINHO = re.compile(r"(?:^|/)(?:locales?|i18n|lang|translations?)/([a-z]{2}(?:[-_][A-Za-z]{2})?)(?:/|\.[a-z]+$)")


def idioma_do_caminho(caminho):
    """Idioma de um arquivo de locale, normalizado (`src/locales/pt-BR/menu.ts` -> `pt-br`); outro arquivo vale None."""
    achado = IDIOMA_NO_CAMINHO.search(caminho or "")
    return achado.group(1).lower().replace("_", "-") if achado else None


def _trechos_de_outros_idiomas(trechos_do_mapa, referencia):
    """Trechos de locale fora da `referencia`; sem a referência entre os trechos, nada se separa (ninguém a leria)."""
    if not _texto_preenchido(referencia):
        return set()
    alvo = referencia.lower().replace("_", "-")
    idiomas = {id_: idioma_do_caminho(_arquivo_de(t)) for id_, t in trechos_do_mapa.items()}
    if alvo not in idiomas.values():
        return set()
    return {id_ for id_, idioma in idiomas.items() if idioma and idioma != alvo}


def _e_unidade_de_idiomas(unidade, trechos_do_mapa):
    """Só a unidade sem agente, sem telas e só com trechos de outros idiomas escapa do orçamento."""
    if unidade.get("id") != UNIDADE_IDIOMAS or unidade.get("sem_agente") is not True or _textos(unidade.get("telas")):
        return False
    proprios = _textos(unidade.get("trechos"))
    outros = _trechos_de_outros_idiomas(trechos_do_mapa, unidade.get("referencia"))
    return bool(proprios) and all(t in outros for t in proprios)


def _numero(valor):
    """Número finito não negativo; qualquer outra coisa (texto, booleano, nulo) vale 0."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor != valor or valor < 0:
        return 0.0
    return float(valor)


def _textos(valor):
    """Itens textuais de uma lista; valor que não é lista vale lista vazia."""
    return [item for item in valor if isinstance(item, str)] if isinstance(valor, list) else []


def _texto_preenchido(valor):
    return isinstance(valor, str) and bool(valor.strip())


def _arquivo_de(item, chave="arquivo"):
    """Caminho textual do item (trecho, tela ou arquivo do mapa); ausente ou de outro tipo vale ''."""
    valor = item.get(chave)
    return valor if isinstance(valor, str) else ""


def _prefixo_da_rota(tela):
    """Primeira parte da rota (`/pedidos/:id` -> `pedidos`), usada para manter telas vizinhas na mesma unidade."""
    rota = tela.get("rota")
    return rota.strip("/").split("/")[0] if isinstance(rota, str) else ""


def _peso_do_trecho(trecho):
    linhas = trecho.get("linhas")
    if (isinstance(linhas, list) and len(linhas) == 2 and all(isinstance(n, int) and not isinstance(n, bool) for n in linhas)
            and linhas[1] >= linhas[0]):
        return float((linhas[1] - linhas[0] + 1) * TOKENS_POR_LINHA)
    return float(TOKENS_TRECHO_SEM_LINHAS)


def _tokens_dos_arquivos(mapa):
    """Caminho -> tokens para ler o arquivo inteiro (`tokens_estimados` dos `arquivos` do mapa), quando informado."""
    tokens = {}
    for item in _lista(mapa, "arquivos"):
        valor = _numero(item.get("tokens_estimados"))
        if valor > 0 and _arquivo_de(item, "caminho"):
            tokens[item["caminho"]] = valor
    return tokens


def _peso_dos_soltos(trechos, tokens, orcamento, pagos=frozenset()):
    """Peso de trechos sem tela: por arquivo, o arquivo inteiro se couber no orçamento, senão as linhas alteradas.

    O agente precisa ler o arquivo para entender a região alterada; a mesma regra do `peso_sem_tela` do mapa.
    Arquivo em `pagos` (o `arquivo` de uma tela da unidade, cujo peso já o contém) soma só as linhas dos soltos.
    """
    por_arquivo = {}
    for trecho in trechos:
        por_arquivo.setdefault(_arquivo_de(trecho), []).append(trecho)
    total = 0.0
    for arquivo, itens in por_arquivo.items():
        inteiro = None if arquivo in pagos else tokens.get(arquivo)
        total += inteiro if inteiro is not None and inteiro <= orcamento else sum(_peso_do_trecho(t) for t in itens)
    return total


def _orcamento_valido(orcamento):
    return isinstance(orcamento, int) and not isinstance(orcamento, bool) and orcamento > 0


def _componentes(telas, mapa):
    """Telas ligadas pelo mesmo compartilhado ou acoplamento, em uniões (listas ordenadas de ids)."""
    pai = {i: i for i in telas}

    def raiz(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    for chave in ("compartilhados", "acoplamentos"):
        for item in _lista(mapa, chave):
            ligadas = sorted(set(i for i in _textos(item.get("telas")) if i in telas))
            for outra in ligadas[1:]:
                pai[raiz(outra)] = raiz(ligadas[0])
    grupos = {}
    for i in sorted(telas):
        grupos.setdefault(raiz(i), []).append(i)
    return list(grupos.values())


def _grupos_de_telas(telas, mapa, orcamento):
    """Grupos indivisíveis de telas: a componente acoplada inteira se couber; senão por prefixo de rota; senão tela a tela."""
    peso = lambda ids: sum(_numero(telas[i].get("peso")) for i in ids)  # noqa: E731
    grupos = []
    for componente in _componentes(telas, mapa):
        if len(componente) == 1 or peso(componente) <= orcamento:
            grupos.append(componente)
            continue
        por_prefixo = {}
        for i in componente:
            por_prefixo.setdefault(_prefixo_da_rota(telas[i]), []).append(i)
        for ids in por_prefixo.values():
            if len(ids) == 1 or peso(ids) <= orcamento:
                grupos.append(ids)
            else:
                grupos.extend([i] for i in ids)
    grupos.sort(key=lambda ids: (_prefixo_da_rota(telas[ids[0]]), ids[0]))
    return grupos


def _empacotar(atomos, orcamento):
    """Enche unidades em ordem (next-fit) até `orcamento`; átomo acima do orçamento fica sozinho. Átomo = (ids, peso)."""
    unidades, atual, peso_atual = [], None, 0.0
    for ids, peso in atomos:
        if peso > orcamento:
            unidades.append(([*ids], peso))
            atual = None
        elif atual is not None and peso_atual + peso <= orcamento:
            atual.extend(ids)
            peso_atual += peso
            unidades[-1] = (atual, peso_atual)
        else:
            atual, peso_atual = [*ids], peso
            unidades.append((atual, peso_atual))
    return unidades


def _usuarios_dos_trechos(mapa, telas, ids_mapa, trechos_do_mapa):
    """Quem usa cada trecho: `(proprios, usuarios)`.

    `proprios`: trecho -> tela que o lista em `trechos` (com empate, a de menor id, para independer da ordem do mapa).
    `usuarios`: trecho -> telas que o usam, incluindo a dona: compartilhado, acoplamento e dependência alterada.
    """
    por_arquivo = {}
    for id_, trecho in trechos_do_mapa.items():
        por_arquivo.setdefault(_arquivo_de(trecho), []).append(id_)
    proprios, usuarios = {}, {}
    for id_tela in sorted(telas):
        tela = telas[id_tela]
        for trecho in _textos(tela.get("trechos")):
            if trecho in ids_mapa:
                proprios.setdefault(trecho, id_tela)
        dependencias = set(_textos(tela.get("dependencias")))
        for arquivo in _textos(tela.get("afetada_por")):
            if arquivo in dependencias:
                for trecho in por_arquivo.get(arquivo, []):
                    usuarios.setdefault(trecho, set()).add(id_tela)
    for chave in ("compartilhados", "acoplamentos"):
        for item in _lista(mapa, chave):
            donas = [i for i in _textos(item.get("telas")) if i in telas]
            for trecho in _textos(item.get("trechos")):
                if trecho in ids_mapa:
                    usuarios.setdefault(trecho, set()).update(donas)
    for trecho, dona in proprios.items():
        usuarios.setdefault(trecho, set()).add(dona)
    return proprios, usuarios


def propor_unidades(mapa, orcamento, referencia=None):
    """Propõe unidades de descoberta que cobrem cada trecho do mapa uma única vez, cada uma até `orcamento` de peso.

    Guloso e determinístico. Telas ligadas pelo mesmo compartilhado/acoplamento ficam juntas (`U-NN`); se a componente
    passa do orçamento, divide-se por primeira parte da rota e, em último caso, tela a tela. Unidade = telas inteiras
    (peso = soma do `peso` das telas) com `trechos` próprios: os da tela, os de compartilhados/acoplamentos e os de
    dependência alterada usada por ela. Trecho usado por telas de várias unidades fica com a primeira unidade; as
    demais o listam em `contexto` (leitura apenas). Trechos sem tela vão para `U-COMP-NN`, por arquivo e depois por
    trecho (nunca se divide um trecho), com peso pelo tamanho do arquivo (`tokens_estimados` em `arquivos`, se couber no
    orçamento) ou, na falta dele, pelas linhas alteradas.

    Tela sozinha acima do orçamento fica em unidade com `dividir_por_regiao: true` e `regioes: []`; o orquestrador
    preenche as regiões depois. Por isso uma proposta nova com tela grande NÃO passa em `conferir_unidades` até
    que `regioes` seja preenchido.
    Com `referencia` (ex.: `pt-BR`), os trechos de locale dos demais idiomas ficam fora das outras unidades, inclusive de
    `contexto`, numa `U-IDIOMAS` com `sem_agente: true`: quem os destina é o comando `idiomas`.
    Mapa malformado ou orçamento inválido levantam ValueError.
    """
    ids_mapa = _ids_do_mapa(mapa)
    if not _orcamento_valido(orcamento):
        raise ValueError(f"Orçamento inválido: {orcamento!r} (esperado inteiro positivo).")
    telas = {}
    for tela in _lista(mapa, "telas"):
        if isinstance(tela.get("id"), str):
            telas.setdefault(tela["id"], tela)
    trechos_do_mapa = {t["id"]: t for t in _lista(mapa, "trechos")}
    outros_idiomas = _trechos_de_outros_idiomas(trechos_do_mapa, referencia)
    lidos = ids_mapa - outros_idiomas

    grupos = _grupos_de_telas(telas, mapa, orcamento)
    pacotes = _empacotar([(ids, sum(_numero(telas[i].get("peso")) for i in ids)) for ids in grupos], orcamento)
    unidades = []
    for n, (ids, peso) in enumerate(pacotes, 1):
        unidade = {"id": f"U-{n:02d}", "telas": ids, "regioes": [], "trechos": [], "peso": float(peso)}
        if peso > orcamento:
            unidade["dividir_por_regiao"] = True
        unidades.append(unidade)
    unidade_da_tela = {i: u for u in unidades for i in u["telas"]}

    # O dono vem da tela (trecho próprio) ou da primeira unidade, em ordem numérica, que o usa.
    proprios, usuarios = _usuarios_dos_trechos(mapa, telas, lidos, trechos_do_mapa)
    posicao = {u["id"]: n for n, u in enumerate(unidades)}
    donos = {}
    for trecho in sorted(lidos):
        if trecho in proprios:
            donos[trecho] = unidade_da_tela[proprios[trecho]]["id"]
        elif usuarios.get(trecho):
            donos[trecho] = min((unidade_da_tela[i]["id"] for i in usuarios[trecho]), key=posicao.get)
    por_id = {u["id"]: u for u in unidades}
    for trecho, dono in donos.items():
        por_id[dono]["trechos"].append(trecho)
        for id_tela in usuarios.get(trecho, ()):
            outra = unidade_da_tela[id_tela]
            if outra["id"] != dono and trecho not in outra.setdefault("contexto", []):
                outra["contexto"].append(trecho)
    for unidade in unidades:
        unidade["trechos"].sort()
        if "contexto" in unidade:
            unidade["contexto"].sort()

    # Trechos sem tela: unidades de código compartilhado/solto, agrupadas por arquivo.
    soltos = {}
    for trecho in sorted(lidos - set(donos)):
        soltos.setdefault(_arquivo_de(trechos_do_mapa[trecho]), []).append(trecho)
    atomos, tokens = [], _tokens_dos_arquivos(mapa)
    for arquivo in sorted(soltos):  # a unidade de soltos não tem tela: nenhum arquivo vem já pago
        peso = _peso_dos_soltos([trechos_do_mapa[t] for t in soltos[arquivo]], tokens, orcamento)
        if peso <= orcamento:
            atomos.append((soltos[arquivo], peso))
        else:
            atomos.extend(([t], _peso_do_trecho(trechos_do_mapa[t])) for t in soltos[arquivo])
    for n, (ids, peso) in enumerate(_empacotar(atomos, orcamento), 1):
        unidades.append({"id": f"U-COMP-{n:02d}", "telas": [], "regioes": [], "trechos": sorted(ids), "peso": float(peso)})
    if outros_idiomas:
        peso = _peso_dos_soltos([trechos_do_mapa[t] for t in outros_idiomas], tokens, orcamento)
        unidades.append({"id": UNIDADE_IDIOMAS, "telas": [], "regioes": [], "trechos": sorted(outros_idiomas), "peso": float(peso),
                         "sem_agente": True, "referencia": referencia})
    return {"orcamento": orcamento, "unidades": unidades}


def fatiar_unidades(mapa, unidades):
    """Por unidade com agente, só o que o brief dela precisa do mapa: os dados das telas e o status dos trechos em posse."""
    status = {t["id"]: t.get("status") for t in mapa.get("trechos", [])}
    telas = {t["id"]: t for t in mapa.get("telas", [])}
    fatias = {}
    for unidade in unidades.get("unidades", []):
        if unidade.get("sem_agente"):
            continue
        fatias[unidade["id"]] = {
            "unidade": unidade,
            "telas": [telas[i] for i in unidade.get("telas", []) if i in telas],
            "status_trechos": {i: status[i] for i in unidade.get("trechos", []) if i in status},
        }
    return fatias


def _unidades_validas(unidades):
    """Unidades (dicts) de um documento de unidades; formato inesperado vale lista vazia."""
    return _lista(unidades, "unidades") if isinstance(unidades, dict) else []


def conferir_unidades(mapa, unidades, orcamento=None):
    """Confere que as unidades cobrem o mapa: todo trecho e toda tela em exatamente uma unidade, cada unidade dentro do orçamento.

    `trechos` é posse (cada trecho em uma só unidade); `contexto` é leitura e não conta como posse, mas ids dele
    ausentes do mapa também entram em `desconhecidos`. `telas_sem_unidade`, `telas_duplicadas`, `telas_desconhecidas`
    e `unidades_duplicadas` (ids de unidade repetidos) também reprovam.
    O orçamento é o argumento `orcamento` ou, na falta dele, o `orcamento` do mapa; o `orcamento` do arquivo de
    unidades é ignorado na conferência (senão um arquivo editado se aprovaria) e, se diferir, aparece como
    `orcamento_divergente: true`, sem reprovar.
    O peso é recalculado do mapa: peso das telas da unidade mais a estimativa de cada trecho que ela possui
    e nenhuma de suas telas usa (trecho de outra tela, ou de unidade sem tela), pelo tamanho do arquivo ou, se não couber
    no orçamento ou faltar no mapa, pelas linhas alteradas. Unidade `dividir_por_regiao` só escapa de
    `acima_do_orcamento` se tiver uma única tela e ao menos `ceil(peso / orçamento)` regiões distintas em `regioes`;
    proposta nova com tela grande, portanto, não é ok até o orquestrador preencher as regiões. A `U-IDIOMAS` não vai a
    agente e não conta no orçamento, desde que traga só trechos de outros idiomas.
    Mapa malformado levanta ValueError; unidades malformadas viram achados (nunca exceção).
    """
    ids_mapa = _ids_do_mapa(mapa)
    telas = {}
    for tela in _lista(mapa, "telas"):
        if isinstance(tela.get("id"), str):
            telas.setdefault(tela["id"], tela)
    trechos_do_mapa = {t["id"]: t for t in _lista(mapa, "trechos")}
    _, usuarios = _usuarios_dos_trechos(mapa, telas, ids_mapa, trechos_do_mapa)
    tokens = _tokens_dos_arquivos(mapa)
    if not _orcamento_valido(orcamento):
        orcamento = mapa.get("orcamento")
    declarado = unidades.get("orcamento") if isinstance(unidades, dict) else None
    divergente = declarado is not None and declarado != orcamento
    validas = _unidades_validas(unidades)

    posses, usos_de_tela, ids_de_unidade = {}, {}, {}
    contexto, cobertos, telas_desconhecidas, acima = set(), set(), set(), []
    for unidade in validas:
        if isinstance(unidade.get("id"), str):
            ids_de_unidade[unidade["id"]] = ids_de_unidade.get(unidade["id"], 0) + 1
        proprios = _textos(unidade.get("trechos"))
        for trecho in proprios:
            posses[trecho] = posses.get(trecho, 0) + 1
        contexto.update(_textos(unidade.get("contexto")))
        cobertos.update(_arquivo_de(trechos_do_mapa[t]) for t in proprios if t in trechos_do_mapa)
        ids_telas = _textos(unidade.get("telas"))
        for i in ids_telas:
            usos_de_tela[i] = usos_de_tela.get(i, 0) + 1
        telas_desconhecidas.update(i for i in ids_telas if i not in telas)
        conhecidas = {i for i in ids_telas if i in telas}
        cobertos.update(_arquivo_de(telas[i]) for i in conhecidas)
        peso = sum(_numero(telas[i].get("peso")) for i in conhecidas)
        peso += _peso_dos_soltos(
            [trechos_do_mapa[t] for t in set(proprios) if t in trechos_do_mapa and not (usuarios.get(t, set()) & conhecidas)],
            tokens, orcamento if _orcamento_valido(orcamento) else 0,
            {_arquivo_de(telas[i]) for i in conhecidas},
        )
        regioes = {r.strip() for r in _textos(unidade.get("regioes")) if r.strip()}
        # Só escapa do orçamento a tela única dividida em regiões o bastante: uma região por orçamento de peso.
        dividida = (unidade.get("dividir_por_regiao") is True and len(ids_telas) == 1
                    and _orcamento_valido(orcamento) and len(regioes) >= ceil(peso / orcamento))
        if (_orcamento_valido(orcamento) and peso > orcamento and not dividida
                and not _e_unidade_de_idiomas(unidade, trechos_do_mapa)):
            acima.append(unidade["id"] if isinstance(unidade.get("id"), str) else "?")

    arquivos = {_arquivo_de(a, "caminho") for a in _lista(mapa, "arquivos")} | {_arquivo_de(t) for t in trechos_do_mapa.values()}
    resultado = {
        "arquivos_sem_unidade": sorted(a for a in arquivos if a and a not in cobertos),
        "trechos_sem_unidade": sorted(ids_mapa - set(posses)),
        "trechos_duplicados": sorted(t for t, n in posses.items() if n > 1),
        "acima_do_orcamento": sorted(acima),
        "desconhecidos": sorted((set(posses) | contexto) - ids_mapa),
        "telas_sem_unidade": sorted(set(telas) - set(usos_de_tela)),
        "telas_duplicadas": sorted(i for i, n in usos_de_tela.items() if n > 1 and i in telas),
        "telas_desconhecidas": sorted(telas_desconhecidas),
        "unidades_duplicadas": sorted(i for i, n in ids_de_unidade.items() if n > 1),
    }
    return {"ok": not any(resultado.values()), **resultado, "orcamento_divergente": divergente}


def _problemas_de_proposta(posicao, proposta, conhecidos):
    """Problemas de uma proposta: campos obrigatórios e trechos fora da unidade. Devolve (ref, problemas)."""
    proposta = proposta if isinstance(proposta, dict) else {}
    ref = proposta.get("ref") if _texto_preenchido(proposta.get("ref")) else f"#{posicao}"
    problemas = []
    for campo in CAMPOS_PROPOSTA:
        valor = proposta.get(campo)
        if campo == "trechos":
            preenchido = bool(_textos(valor))
        else:
            preenchido = _texto_preenchido(valor)
        if not preenchido:
            problemas.append(f"CAMPO_FALTANTE:{ref}:{campo}")
    problemas.extend(f"TRECHO_DESCONHECIDO:{t}" for t in _textos(proposta.get("trechos")) if t not in conhecidos)
    return ref, problemas


def _unidade_por_id(unidades, unidade_id):
    unidade = next((u for u in _unidades_validas(unidades) if u.get("id") == unidade_id), None)
    if unidade is None:
        raise ValueError(f"Unidade {unidade_id!r} não existe no arquivo de unidades.")
    return unidade


def _ler_achados(caminho):
    """`(achados, problema)`: o objeto do arquivo, ou `None` e `ARQUIVO_AUSENTE`/`JSON_INVALIDO`."""
    try:
        achados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except OSError:
        return None, "ARQUIVO_AUSENTE"
    except (ValueError, RecursionError):  # JSON inválido, UnicodeDecodeError e aninhamento profundo demais
        return None, "JSON_INVALIDO"
    return (achados, None) if isinstance(achados, dict) else (None, "JSON_INVALIDO")


def _problemas_do_arquivo(unidade, achados, completo=True):
    """`(problemas, destinos)` de um objeto de achados: `destinos` é trecho -> destino dos trechos sem problema.

    `completo`: todo trecho da unidade precisa de destino neste arquivo; sem isso (arquivo de uma região) só se confere o que ele traz.
    """
    proprios = set(_textos(unidade.get("trechos")))
    citaveis = proprios | set(_textos(unidade.get("contexto")))
    problemas = set()
    status = achados.get("status")
    if status == "FALHA":
        problemas.add("FALHA_DECLARADA")
    elif status != "OK":
        problemas.add("STATUS_INVALIDO")
    declarada = achados.get("unidade")
    if declarada is not None and declarada != unidade.get("id"):
        problemas.add(f"UNIDADE_DIVERGENTE:{declarada}")

    propostas = achados.get("propostas")
    refs = {}  # ref -> trechos que as propostas com esse ref citam
    for posicao, proposta in enumerate(propostas if isinstance(propostas, list) else []):
        ref, achadas = _problemas_de_proposta(posicao, proposta, citaveis)
        problemas.update(achadas)
        if isinstance(proposta, dict) and _texto_preenchido(proposta.get("ref")):
            refs.setdefault(ref, set()).update(_textos(proposta.get("trechos")))

    entradas = achados.get("trechos")
    entradas = entradas if isinstance(entradas, dict) else {}
    problemas.update(f"TRECHO_DESCONHECIDO:{t}" for t in entradas if t not in proprios)
    destinos = {}
    for trecho in sorted(proprios if completo else proprios & set(entradas)):
        entrada = entradas.get(trecho)
        destino = entrada.get("destino") if isinstance(entrada, dict) else None
        if destino not in DESTINOS_ACHADOS:
            problemas.add(f"TRECHO_SEM_DESTINO:{trecho}")
        elif destino == DIFERENCA:
            ref = entrada.get("proposta")
            if not (isinstance(ref, str) and ref in refs):
                problemas.add(f"PROPOSTA_AUSENTE:{ref if _texto_preenchido(ref) else trecho}")
            elif trecho not in refs[ref]:
                problemas.add(f"PROPOSTA_SEM_TRECHO:{trecho}")
            else:
                destinos[trecho] = destino
        elif not _texto_preenchido(entrada.get("motivo")):
            problemas.add(f"MOTIVO_FALTANTE:{trecho}")
        else:
            destinos[trecho] = destino
    return problemas, destinos


def conferir_achados(unidades, unidade_id, caminho):
    """Confere o arquivo de achados de uma unidade antes de integrá-lo ao catálogo.

    Devolve `{"ok", "unidade", "problemas"}` com códigos ordenados e sem repetição: `ARQUIVO_AUSENTE`, `JSON_INVALIDO`,
    `FALHA_DECLARADA`, `STATUS_INVALIDO` (`status` deve ser "OK" ou "FALHA"), `UNIDADE_DIVERGENTE:<id>` (o arquivo declara outra unidade), `TRECHO_SEM_DESTINO:<id>`,
    `TRECHO_DESCONHECIDO:<id>` (trecho que não é da unidade, nem como `contexto` quando citado por uma proposta),
    `PROPOSTA_SEM_TRECHO:<id>` (a proposta apontada não lista o trecho em `trechos`),
    `PROPOSTA_AUSENTE:<ref>` (sem `proposta` informada, o `<ref>` é o id do trecho), `CAMPO_FALTANTE:<ref>:<campo>`
    (proposta sem `ref` textual usa `#<posição>`) e `MOTIVO_FALTANTE:<id>`.
    `unidade_id` inexistente em `unidades` levanta ValueError.
    """
    unidade = _unidade_por_id(unidades, unidade_id)
    resultado = {"ok": False, "unidade": unidade_id, "problemas": []}
    achados, problema = _ler_achados(caminho)
    if problema:
        resultado["problemas"] = [problema]
        return resultado
    problemas, _ = _problemas_do_arquivo(unidade, achados)
    resultado["problemas"] = sorted(problemas)
    resultado["ok"] = not problemas
    return resultado


def conferir_achados_por_regiao(unidades, unidade_id, arquivos):
    """Confere os achados de uma unidade dividida por região: `arquivos` é {região: caminho}, um arquivo por região.

    Cada arquivo é conferido como em `conferir_achados`, mas só pelo que traz (a região não precisa cobrir a unidade), e o
    problema leva `@<região>` no fim. A cobertura é a união: todo trecho da unidade precisa de destino em ao menos um
    arquivo (`TRECHO_SEM_DESTINO:<id>`), e o mesmo trecho com destinos diferentes em duas regiões é `DESTINO_DIVERGENTE:<id>`.
    Também `REGIAO_DESCONHECIDA:<r>` (não está em `regioes` da unidade), `REGIAO_SEM_ARQUIVO:<r>` (região da unidade sem arquivo)
    e `REGIAO_DIVERGENTE:<declarada>@<r>` (o arquivo declara outra `regiao`).
    `unidade_id` inexistente levanta ValueError.
    """
    unidade = _unidade_por_id(unidades, unidade_id)
    declaradas = {r.strip() for r in _textos(unidade.get("regioes")) if r.strip()}
    problemas, destinos = set(), {}
    problemas.update(f"REGIAO_DESCONHECIDA:{r}" for r in arquivos if r not in declaradas)
    problemas.update(f"REGIAO_SEM_ARQUIVO:{r}" for r in declaradas if r not in arquivos)
    for regiao in sorted(arquivos):
        achados, problema = _ler_achados(arquivos[regiao])
        if problema:
            problemas.add(f"{problema}@{regiao}")
            continue
        achadas, uteis = _problemas_do_arquivo(unidade, achados, completo=False)
        declarada = achados.get("regiao")
        if declarada is not None and declarada != regiao:
            achadas.add(f"REGIAO_DIVERGENTE:{declarada}")
        problemas.update(f"{p}@{regiao}" for p in achadas)
        for trecho, destino in uteis.items():
            destinos.setdefault(trecho, set()).add(destino)
    problemas.update(f"DESTINO_DIVERGENTE:{t}" for t, ds in destinos.items() if len(ds) > 1)
    problemas.update(f"TRECHO_SEM_DESTINO:{t}" for t in _textos(unidade.get("trechos")) if t not in destinos)
    return {"ok": not problemas, "unidade": unidade_id, "regioes": sorted(arquivos), "problemas": sorted(problemas)}
