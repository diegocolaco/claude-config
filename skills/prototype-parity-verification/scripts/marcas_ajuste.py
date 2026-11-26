#!/usr/bin/env python3
"""Checklist do ajuste numa tela pronta: o que o protótipo faz naquela região, e a prova de que nada foi pulado.

Por que existe: «conferir cada correção» sem dizer o que olhar deixa o resultado na mão do modelo, e citação correta não revela o que
o agente deixou de ler. O alvo aqui é a omissão: toda linha da checklist precisa de marca, e a marca precisa de evidência no produto.

uso:
  marcas_ajuste.py lista <catalogo.json> <pasta-fatos> <TL-id> <SC-id> [<SC-id> ...] --saida <checklist.json> [--superficie SF-x]
  marcas_ajuste.py confere <checklist.json> <marcas.json> <raiz-do-produto> [--catalogo <catalogo.json>] [--pasta-fatos <pasta>]

`lista` expande cada cenário pedido para todos os cenários da mesma região (`region_id`), para não escolher um recorte estreito, e junta:
os fatos desses cenários (`<pasta-fatos>/<TL-id>.json`, gravado pela passada de fatos com `--ao-lado`), todas as ausências da tela
(`<pasta-fatos>/ausencias/<TL-id>.json`, só as respostas NAO) e o padrão de biblioteca da tela (chave `biblioteca`). Cada linha tem
`id` estável, `texto`, `fonte` e `origem`; a checklist grava também o catálogo e a `pasta_fatos` (absolutos); fato com `imprecisao` vale pelo motivo, que vai no texto. Fato de outra região e `sem_cenario`
ficam fora, e a saída diz quantos. A tela sem arquivo de fatos sai 2: rode a passada de fatos nela. Checklist vazia sai 11 e apaga o
`--saida` que já existia, para não sobrar arquivo velho.

`confere` lê as marcas, uma lista de `{"id", "marca", "evidencia", "motivo"}`. Toda linha precisa de `cumpre`, `muda`, `diverge` ou
`nao_verificado`. `cumpre`, `muda` e `diverge` exigem `arquivo:linha` (ou `arquivo:ini-fim`) que exista na raiz do produto; `nao_verificado`
exige `motivo`. Evidência em arquivo binário, em `.git/` ou em `.squad/` é inválida (catálogo e fatos não provam o que o produto faz); as linhas
contam como num editor (`\n`). Sem nenhuma linha `muda`, não passa: a correção pedida não está ligada à checklist.
Linha sem marca, id inválido ou desconhecido, marca repetida ou evidência inválida saem listados, um a um; o resumo conta só marcas válidas.
O `confere` remonta a checklist a partir do catálogo e da pasta de fatos gravados (`--catalogo` e `--pasta-fatos` substituem os caminhos) e
compara com as linhas do arquivo: pega checklist encurtada ou velha por erro, mas não impede fraude deliberada, como trocar `cenarios_pedidos`.
Imprime o resumo em markdown e a situação de `tests[]` dos cenários da tela.

Limite: prova que nada foi pulado e que a evidência existe, não que a marca está certa; `nao_verificado` nunca conta como aprovado.
Sucesso vazio é erro: checklist sem linhas ou sem `muda` não sai 0.
Saída: 0 = ok, 11 = há itens a resolver, 2 = uso inválido (argumento errado, arquivo ausente, JSON ilegível ou checklist malformada; mensagem no stderr).
Só biblioteca padrão.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SAIDA_OK = 0
SAIDA_ITENS = 11
SAIDA_USO = 2

MARCAS = ("cumpre", "muda", "diverge", "nao_verificado")
USAM_EVIDENCIA = ("cumpre", "muda", "diverge")
PASTAS_SEM_PROVA = (".git", ".squad")
CHAVES_RESERVADAS = ("sem_cenario", "biblioteca")
# Mesmos nomes de matriz_variacoes.py (a passada de ausências numera as perguntas).
PERGUNTAS = {"A": "sessão e permissão", "1": "carregamento", "2": "falha", "3": "vazio", "4": "sucesso", "5": "efeito real",
             "6": "entrada", "7": "caminho do dado", "8": "navegação"}
EVIDENCIA = re.compile(r"^(?P<arquivo>.+):(?P<ini>\d+)(?:-(?P<fim>\d+))?$")


class ErroDeUso(Exception):
    """Entrada inválida: vira saída 2 com a mensagem no stderr."""


def _ler_json(caminho, o_que):
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except OSError as erro:
        raise ErroDeUso(f"{o_que}: não consegui abrir {caminho} ({erro.strerror})")
    except (UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise ErroDeUso(f"{o_que}: {caminho} não é JSON válido ({erro})")


def _celula(texto):
    return str(texto).replace("|", "\\|").replace("\n", " ")


def _id_da_linha(origem, texto, fonte):
    return "L-" + hashlib.sha1(f"{origem}\n{texto}\n{fonte}".encode("utf-8")).hexdigest()[:8]


def _linha(origem, texto, fonte, imprecisao=None):
    linha = {"id": _id_da_linha(origem, texto, fonte), "texto": texto, "fonte": fonte, "origem": origem}
    if imprecisao:
        linha["texto"] = f"{texto} [IMPRECISO: vale o motivo: {imprecisao}]"
        linha["imprecisao"] = imprecisao
    return linha


def _fatos_de(lista, onde):
    """Fatos `{texto, fonte, imprecisao?}` de uma lista do arquivo de fatos; forma errada vira erro de uso."""
    if not isinstance(lista, list) or any(not isinstance(x, dict) or not isinstance(x.get("texto"), str) or not x["texto"].strip() for x in lista):
        raise ErroDeUso(f"fatos: {onde} deveria ser uma lista de fatos com `texto`")
    return lista


def _numero(identificador):
    achado = re.search(r"\d+", identificador)
    return (int(achado.group()) if achado else 0, identificador)


def _registros(catalogo, chave):
    valor = catalogo.get(chave) if isinstance(catalogo, dict) else None
    return [r for r in valor if isinstance(r, dict) and isinstance(r.get("id"), str)] if isinstance(valor, list) else []


def _eh_visual(cenario):
    """Mesma regra de verificacao.py: dimensão `visual`, em string ou objeto `{id}`."""
    dimensoes = cenario.get("dimensions")
    for dimensao in dimensoes if isinstance(dimensoes, list) else []:
        valor = dimensao.get("id") if isinstance(dimensao, dict) else dimensao
        if isinstance(valor, str) and valor.strip().lower() == "visual":
            return True
    return False


def _cenarios_da_superficie(catalogo, superficie):
    regioes = {r["id"] for r in _registros(catalogo, "regions") if r.get("surface_id") == superficie}
    return [c for c in _registros(catalogo, "scenarios") if c.get("region_id") in regioes]


def _ausencias(pasta, tela):
    """Linhas das respostas NAO da passada de ausências; None quando a tela não tem o arquivo."""
    caminho = Path(pasta) / "ausencias" / f"{tela}.json"
    if not caminho.is_file():
        return None
    blocos = _ler_json(caminho, "ausências")
    if not isinstance(blocos, list) or any(not isinstance(b, dict) for b in blocos):
        raise ErroDeUso(f"ausências: {caminho} deveria ser a lista de alvos da passada de ausências")
    linhas = []
    for bloco in blocos:
        for item in bloco.get("itens") or []:
            if not isinstance(item, dict) or item.get("resposta") != "NAO" or not isinstance(item.get("texto"), str):
                continue
            tema = PERGUNTAS.get(str(item.get("pergunta")), "?")
            texto = f"Ausência ({tema}), {bloco.get('alvo') or 'tela'}: o protótipo não tem: {item['texto']}"
            linhas.append(_linha("ausencia", texto, str(item.get("fonte") or "")))
    return linhas


def montar_checklist(catalogo, pasta, tela, pedidos, superficie, caminho_catalogo):
    if not re.match(r"^TL-.+", tela):
        raise ErroDeUso(f"tela: esperava um id TL-<tela>, e veio {tela}")
    superficie = superficie or "SF-" + tela[3:]
    da_tela = _cenarios_da_superficie(catalogo, superficie)
    por_id = {c["id"]: c for c in _registros(catalogo, "scenarios")}
    regioes = {r["id"]: r for r in _registros(catalogo, "regions")}
    expandidos = []
    for sid in pedidos:
        cenario = por_id.get(sid)
        if cenario is None:
            raise ErroDeUso(f"cenário {sid} não está no catálogo")
        regiao = regioes.get(cenario.get("region_id"))
        if regiao is None or regiao.get("surface_id") != superficie:
            raise ErroDeUso(f"cenário {sid} não é da superfície {superficie} ({tela}); para moldura ou global, informe --superficie")
        for irmao in _cenarios_da_superficie(catalogo, superficie):
            if irmao.get("region_id") == cenario["region_id"] and irmao["id"] not in expandidos:
                expandidos.append(irmao["id"])
    expandidos.sort(key=_numero)

    arquivo = Path(pasta) / f"{tela}.json"
    if not arquivo.is_file():
        raise ErroDeUso(f"{tela} não tem {arquivo}: rode a passada de fatos nesta tela (descoberta-em-ondas) e grave com --ao-lado antes de ajustar")
    fatos = _ler_json(arquivo, "fatos")
    if not isinstance(fatos, dict):
        raise ErroDeUso(f"fatos: {arquivo} deveria ser um objeto com os fatos por cenário")

    linhas = []
    sem_fatos = []
    for sid in expandidos:
        daqui = _fatos_de(fatos.get(sid, []), sid)
        if not daqui:
            sem_fatos.append(sid)
        linhas += [_linha(f"fato:{sid}", x["texto"], str(x.get("fonte") or ""), x.get("imprecisao")) for x in daqui]
    ausencias = _ausencias(pasta, tela)
    linhas += ausencias or []
    for x in _fatos_de(fatos.get("biblioteca", []), "biblioteca"):
        linhas.append(_linha("biblioteca", x["texto"], str(x.get("fonte") or ""), x.get("imprecisao")))
    unicas = list({x["id"]: x for x in linhas}.values())

    fora_fatos = sum(len(_fatos_de(v, k)) for k, v in fatos.items() if k not in CHAVES_RESERVADAS and k not in expandidos)
    return {
        "versao": 1, "tela": tela, "superficie": superficie, "catalogo": str(Path(caminho_catalogo).resolve()),
        "pasta_fatos": str(Path(pasta).resolve()),
        "cenarios_pedidos": list(dict.fromkeys(pedidos)), "cenarios_expandidos": expandidos,
        "cenarios_sem_fatos": sem_fatos, "sem_arquivo_de_ausencias": ausencias is None,
        "fora": {"fatos": fora_fatos,
                 "cenarios": sum(1 for c in da_tela if c["id"] not in expandidos),
                 "sem_cenario": len(_fatos_de(fatos.get("sem_cenario", []), "sem_cenario"))},
        "linhas": unicas,
    }


def resumo_lista(c):
    por_origem = {"fato": 0, "ausencia": 0, "biblioteca": 0}
    for x in c["linhas"]:
        por_origem[x["origem"].split(":")[0]] += 1
    fora = c["fora"]
    saida = [f"# Checklist do ajuste: {c['tela']}", "",
             f"Cenários pedidos: {', '.join(c['cenarios_pedidos'])}. Expandidos pela região: {', '.join(c['cenarios_expandidos'])}.",
             f"{len(c['linhas'])} linhas: {por_origem['fato']} fatos, {por_origem['ausencia']} ausências, {por_origem['biblioteca']} de biblioteca.",
             f"Fora da checklist: {fora['fatos']} fato(s) em {fora['cenarios']} cenário(s) da tela; {fora['sem_cenario']} em sem_cenario."]
    if c["cenarios_sem_fatos"]:
        saida.append(f"Cenário sem fato no arquivo (confira se a passada de fatos cobriu): {', '.join(c['cenarios_sem_fatos'])}.")
    if c["sem_arquivo_de_ausencias"]:
        saida.append("Tela sem ausências guardadas (`ausencias/<TL-id>.json`): nenhuma linha de ausência.")
    saida += ["", "| id | origem | texto | fonte |", "|---|---|---|---|"]
    saida += [f"| {x['id']} | {_celula(x['origem'])} | {_celula(x['texto'])} | {_celula(x['fonte'])} |" for x in c["linhas"]]
    return "\n".join(saida)


def _cmd_lista(args):
    catalogo = _ler_json(args.catalogo, "catálogo")
    if not isinstance(catalogo, dict):
        raise ErroDeUso(f"catálogo: {args.catalogo} deveria ser um objeto")
    c = montar_checklist(catalogo, args.pasta_fatos, args.tela, args.cenarios, args.superficie, args.catalogo)
    saida = Path(args.saida)
    if not c["linhas"]:
        try:
            velha = saida.is_file()
            if velha:
                saida.unlink()
        except OSError as erro:
            raise ErroDeUso(f"saída: não consegui remover {args.saida} ({erro.strerror})")
        print(f"Checklist vazia: não há linha para conferir em {args.tela} (sem fato nos cenários {', '.join(c['cenarios_expandidos'])}, "
              "sem ausência com resposta NAO e sem padrão de biblioteca). Nada foi gravado"
              + (f"; removi o {args.saida} que já existia, para não sobrar checklist velha" if velha else "")
              + ": confira a passada de fatos antes de ajustar.")
        return SAIDA_ITENS
    try:
        saida.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError as erro:
        raise ErroDeUso(f"saída: não consegui gravar {args.saida} ({erro.strerror})")
    print(resumo_lista(c))
    return SAIDA_OK


def _ler_checklist(caminho):
    c = _ler_json(caminho, "checklist")
    linhas = c.get("linhas") if isinstance(c, dict) else None
    if (not isinstance(linhas, list)
            or any(not isinstance(x, dict) or not isinstance(x.get("id"), str) or not isinstance(x.get("texto"), str) for x in linhas)
            or not all(isinstance(c.get(k), str) and c[k] for k in ("tela", "superficie"))
            or not isinstance(c.get("cenarios_pedidos"), list) or not c["cenarios_pedidos"]
            or any(not isinstance(x, str) for x in c["cenarios_pedidos"])):
        raise ErroDeUso(f"checklist: {caminho} não tem o formato que `lista` grava (linhas com id e texto, tela, superficie, cenarios_pedidos)")
    return c


def _ler_marcas(caminho):
    m = _ler_json(caminho, "marcas")
    if not isinstance(m, list) or any(not isinstance(x, dict) for x in m):
        raise ErroDeUso(f"marcas: {caminho} deveria ser uma lista de {{id, marca, evidencia, motivo}}")
    return m


def _evidencias(valor):
    if isinstance(valor, str):
        return [valor]
    return valor if isinstance(valor, list) and all(isinstance(x, str) for x in valor) else None


def _problema_da_evidencia(texto, raiz):
    """Motivo pelo qual `arquivo:linha` não vale como evidência no produto, ou None."""
    achado = EVIDENCIA.match(texto.strip())
    if not achado:
        return f"`{texto}` não é arquivo:linha"
    ini, fim = int(achado["ini"]), int(achado["fim"] or achado["ini"])
    if ini < 1 or fim < ini:
        return f"`{texto}` tem linha inválida"
    try:
        caminho = Path(achado["arquivo"])
        destino = (caminho if caminho.is_absolute() else raiz / caminho).resolve()
        try:
            relativo = destino.relative_to(raiz)
        except ValueError:
            return f"`{texto}` fica fora do produto"
        if any(parte in PASTAS_SEM_PROVA for parte in relativo.parts):
            return f"`{texto}` fica em .git/ ou .squad/: catálogo e fatos não provam o que o produto faz"
        if not destino.is_file():
            return f"`{texto}`: o arquivo não existe no produto"
        dados = destino.read_bytes()
    except (ValueError, OSError) as erro:
        return f"`{texto}` não pôde ser lido ({erro})"
    if b"\0" in dados:
        return f"`{texto}`: arquivo binário não prova comportamento"
    linhas = dados.decode("utf-8", errors="replace").split("\n")
    total = len(linhas) - 1 if linhas[-1] == "" else len(linhas)
    if fim > total:
        return f"`{texto}`: o arquivo tem {total} linha(s)"
    return None


def conferir(checklist, marcas, raiz):
    """(problemas, marcadas): problemas como (id, motivo); marcadas, só as marcas válidas, como id -> marca."""
    conhecidas = {x["id"]: x for x in checklist["linhas"]}
    problemas, marcadas, vistos = [], {}, set()
    for m in marcas:
        ident = m.get("id")
        if not isinstance(ident, str):
            problemas.append((repr(ident), "id inválido: deveria ser o texto do id de uma linha"))
            continue
        if ident not in conhecidas:
            problemas.append((ident, "id desconhecido: não é de nenhuma linha desta checklist"))
            continue
        if ident in vistos:
            problemas.append((ident, "marcada mais de uma vez"))
            continue
        vistos.add(ident)
        marca = m.get("marca")
        if marca not in MARCAS:
            problemas.append((ident, f"marca inválida ({marca!r}); use cumpre, muda, diverge ou nao_verificado"))
            continue
        if marca == "nao_verificado":
            if not isinstance(m.get("motivo"), str) or not m["motivo"].strip():
                problemas.append((ident, "nao_verificado exige motivo"))
                continue
            marcadas[ident] = m
            continue
        evidencias = _evidencias(m.get("evidencia"))
        if not evidencias or not any(e.strip() for e in evidencias):
            problemas.append((ident, f"{marca} exige evidência arquivo:linha"))
            continue
        invalidas = [(ident, f"evidência inválida: {motivo}") for motivo in (_problema_da_evidencia(e, raiz) for e in evidencias) if motivo]
        problemas += invalidas
        if not invalidas:
            marcadas[ident] = m
    for ident in conhecidas:
        if ident not in vistos:
            problemas.append((ident, "sem marca"))
    return problemas, marcadas


def comparar_com_a_gerada(checklist, gerada):
    """Problemas (id, motivo) entre as linhas do arquivo e as que `montar_checklist` gera hoje."""
    esperadas = {x["id"]: x for x in gerada["linhas"]}
    problemas, vistos = [], set()
    for x in checklist["linhas"]:
        if x["id"] in vistos or esperadas.get(x["id"]) != x:
            problemas.append((x["id"], "linha difere da checklist gerada"))
        vistos.add(x["id"])
    problemas += [(ident, "linha ausente da checklist recebida") for ident in esperadas if ident not in vistos]
    return problemas


def _gerar(checklist, caminho_catalogo, pasta_fatos):
    """Remonta a checklist; catálogo ou fatos inacessíveis saem 2 citando `--catalogo` e `--pasta-fatos`."""
    dica = "; informe outro caminho com --catalogo e --pasta-fatos"
    try:
        catalogo = _ler_json(caminho_catalogo, "catálogo")
    except ErroDeUso as erro:
        raise ErroDeUso(f"{erro}{dica}")
    if not isinstance(catalogo, dict):
        raise ErroDeUso(f"catálogo: {caminho_catalogo} deveria ser um objeto{dica}")
    if not Path(pasta_fatos).is_dir():
        raise ErroDeUso(f"fatos: {pasta_fatos} não é uma pasta{dica}")
    try:
        gerada = montar_checklist(catalogo, pasta_fatos, checklist["tela"], checklist["cenarios_pedidos"], checklist["superficie"], caminho_catalogo)
    except ErroDeUso as erro:
        raise ErroDeUso(f"{erro}{dica}")
    return catalogo, gerada


def situacao_dos_testes(catalogo, checklist, raiz):
    """Linhas de tabela: cada cenário da tela, a dimensão e o que `tests[]` diz dele."""
    testes = {}
    em_tests = catalogo.get("tests")
    for t in em_tests if isinstance(em_tests, list) else []:
        if isinstance(t, dict):
            for sid in t.get("scenario_ids") or []:
                testes.setdefault(sid, []).append(t.get("file"))
    linhas = []
    for c in sorted(_cenarios_da_superficie(catalogo, checklist["superficie"]), key=lambda c: _numero(c["id"])):
        visual = _eh_visual(c)
        arquivos = [f for f in testes.get(c["id"], []) if isinstance(f, str)]
        if arquivos:
            situacao = ", ".join(f"`{f}` ({'existe' if (raiz / f).is_file() else 'não existe no produto'})" for f in arquivos)
        elif visual:
            situacao = "sem teste (visual não recebe teste)"
        else:
            situacao = "sem teste em tests[]: não edite o catálogo; vira diferença nova com plano curto"
        na_lista = "sim" if c["id"] in checklist.get("cenarios_expandidos", []) else "não"
        linhas.append(f"| {c['id']} | {'visual' if visual else 'funcional'} | {na_lista} | {situacao} |")
    return linhas


def _cmd_confere(args):
    checklist = _ler_checklist(args.checklist)
    marcas = _ler_marcas(args.marcas)
    raiz = Path(args.raiz)
    if not raiz.is_dir():
        raise ErroDeUso(f"raiz do produto: {args.raiz} não é uma pasta")
    raiz = raiz.resolve()
    catalogo, gerada = _gerar(checklist, args.catalogo or checklist.get("catalogo") or "", args.pasta_fatos or checklist.get("pasta_fatos") or "")

    saida = [f"# Conferência do ajuste: {checklist.get('tela')}", ""]
    problemas, marcadas = conferir(checklist, marcas, raiz)
    if not checklist["linhas"]:
        problemas.append(("-", "checklist vazia: sem linhas, não há o que conferir"))
    problemas += comparar_com_a_gerada(checklist, gerada)
    contagem = {m: [i for i, x in marcadas.items() if x["marca"] == m] for m in MARCAS}
    if checklist["linhas"] and not contagem["muda"]:
        problemas.append(("-", "nenhuma linha marcada muda: a correção pedida não está ligada à checklist"))
    if problemas:
        saida += [f"{len(problemas)} problema(s); a conferência não passa:", ""]
        saida += [f"- {ident}: {motivo}" for ident, motivo in problemas] + [""]
    por_linha = {x["id"]: x for x in checklist["linhas"]}
    saida.append(f"Marcas: {len(contagem['cumpre'])} cumpre, {len(contagem['muda'])} muda, {len(contagem['diverge'])} diverge, "
                 f"{len(contagem['nao_verificado'])} nao_verificado, de {len(checklist['linhas'])} linhas.")
    for marca, titulo in (("muda", "Muda (alterado nesta entrega)"), ("diverge", "Diverge (fora do pedido, não corrigido: vai ao relato)")):
        if contagem[marca]:
            saida += ["", f"## {titulo}"]
            saida += [f"- {i}: {por_linha[i]['texto']} -> {', '.join(_evidencias(marcadas[i].get('evidencia')) or [])}" for i in contagem[marca]]
    if contagem["nao_verificado"]:
        saida += ["", "## Não verificado (não conta como aprovado)"]
        saida += [f"- {i}: {por_linha[i]['texto']} -- motivo: {marcadas[i].get('motivo')}" for i in contagem["nao_verificado"]]
    saida += ["", "## tests[] dos cenários da tela", "", "| cenário | dimensão | na checklist | tests[] |", "|---|---|---|---|"]
    saida += situacao_dos_testes(catalogo, checklist, raiz)
    saida += ["", "Limite: isto prova que nenhuma linha foi pulada e que a evidência existe, não que a marca está certa."]
    print("\n".join(saida))
    return SAIDA_ITENS if problemas else SAIDA_OK


class _Parser(argparse.ArgumentParser):
    def error(self, mensagem):
        raise ErroDeUso(mensagem)


def _parser():
    p = _Parser(description="Checklist e marcas do ajuste numa tela pronta.")
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=_Parser)
    a = sub.add_parser("lista", help="gera a checklist da tela para os cenários das correções")
    a.add_argument("catalogo")
    a.add_argument("pasta_fatos", help=".squad/contracts/parity/fatos")
    a.add_argument("tela", help="id da tela, TL-<tela>")
    a.add_argument("cenarios", nargs="+", help="cenários das correções, SC-<n>")
    a.add_argument("--saida", required=True, help="checklist.json a gravar")
    a.add_argument("--superficie", help="superfície do catálogo, quando não for SF-<tela> (moldura e global)")
    b = sub.add_parser("confere", help="confere as marcas contra a checklist e o produto")
    b.add_argument("checklist")
    b.add_argument("marcas")
    b.add_argument("raiz", help="raiz do produto, onde as evidências existem")
    b.add_argument("--catalogo", help="catálogo para remontar a checklist e ver tests[]; por padrão o que a checklist gravou")
    b.add_argument("--pasta-fatos", help="pasta de fatos para remontar a checklist; por padrão a que a checklist gravou")
    return p


def main(argv=None):
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    try:
        args = _parser().parse_args(argv)
        return _cmd_lista(args) if args.cmd == "lista" else _cmd_confere(args)
    except ErroDeUso as erro:
        print(erro, file=sys.stderr)
        return SAIDA_USO


if __name__ == "__main__":
    sys.exit(main())
