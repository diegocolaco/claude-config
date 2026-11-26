"""Compara, por nome, o que falhava antes e depois de um ajuste, em vez de só contar as falhas.

Contar esconde a troca: 30 falhas antes e 30 depois podem ser falhas diferentes.

uso: falhas_por_nome.py extrai --saida <x.json> [--testes <relatorio>] [--tipos <saida-do-tsc> --tipos-codigo <n>] [--raiz <worktree>]
     falhas_por_nome.py compara <antes.json> <depois.json>

--testes aceita o relatório de `vitest run --reporter=json`, de `jest --json` ou JUnit XML.
--tipos aceita a saída de `tsc --noEmit`; o nome do erro não leva linha e coluna, que mudam com a edição.
--tipos-codigo é o código de saída do `tsc`: saída sem erro só vale como zero erros com o código 0, porque um comando que nem rodou também sai vazio.
--raiz tira o caminho do worktree dos nomes, para comparar execuções em pastas diferentes.

Relatório vazio ou ilegível é erro, nunca «sem falhas». Grave os dois JSON fora do produto.
Saída de `compara`: 0 = nenhuma falha nova, 1 = há falha nova ou teste que sumiu, 2 = uso inválido ou
verificação que não rodou dos dois lados. Só biblioteca padrão.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

SAIDA_OK = 0
SAIDA_ACUSA = 1
SAIDA_USO = 2

ERRO_TIPO = re.compile(r"^(?P<arquivo>[^\s(][^(]*)\(\d+,\d+\): error (?P<codigo>TS\d+): (?P<mensagem>.*)$")
STATUS_FALHA = {"failed", "fail"}


class RelatorioInvalido(Exception):
    pass


def _relativo(caminho, raiz):
    if raiz and caminho.startswith(raiz.rstrip("/") + "/"):
        return caminho[len(raiz.rstrip("/")) + 1:]
    return caminho


def _ler_json(dados, raiz):
    if not isinstance(dados, dict) or not isinstance(dados.get("testResults"), list):
        raise RelatorioInvalido("o relatório não tem testResults")
    testes = {}
    for arquivo in dados["testResults"]:
        nome = _relativo(str(arquivo.get("name", "?")), raiz)
        resultados = arquivo.get("assertionResults") or []
        if not resultados and arquivo.get("status") in STATUS_FALHA:
            # O arquivo nem carregou: é falha, ainda que nenhum teste tenha rodado.
            testes[f"{nome} > (arquivo não carregou)"] = "failed"
        for teste in resultados:
            testes[f"{nome} > {teste.get('fullName') or teste.get('title')}"] = teste.get("status", "?")
    return testes


def _ler_junit(texto):
    raiz = ET.fromstring(texto)
    testes = {}
    for caso in raiz.iter("testcase"):
        falhou = caso.find("failure") is not None or caso.find("error") is not None
        pulou = caso.find("skipped") is not None
        status = "failed" if falhou else "skipped" if pulou else "passed"
        testes[f"{caso.get('classname', '?')} > {caso.get('name', '?')}"] = status
    return testes


def ler_testes(texto, raiz):
    try:
        if texto.lstrip().startswith("<"):
            testes = _ler_junit(texto)
        else:
            testes = _ler_json(json.loads(texto), raiz)
    except (ValueError, ET.ParseError) as erro:
        raise RelatorioInvalido(f"o relatório de testes não pôde ser lido: {erro}") from erro
    if not testes:
        raise RelatorioInvalido("o relatório de testes não traz nenhum teste")
    return testes


def ler_tipos(texto, raiz):
    erros = Counter()
    for linha in texto.splitlines():
        achado = ERRO_TIPO.match(linha)
        if achado:
            erros[f"{_relativo(achado['arquivo'], raiz)}: {achado['codigo']}: {achado['mensagem']}"] += 1
    return erros


def extrair(args):
    if not args.testes and not args.tipos:
        print("informe --testes, --tipos ou os dois", file=sys.stderr)
        return SAIDA_USO
    registro = {"testes": None, "tipos": None}
    try:
        if args.testes:
            registro["testes"] = ler_testes(Path(args.testes).read_text(encoding="utf-8"), args.raiz)
        if args.tipos:
            erros = ler_tipos(Path(args.tipos).read_text(encoding="utf-8"), args.raiz)
            if not erros and args.tipos_codigo != 0:
                raise RelatorioInvalido("verificação de tipos sem erro e sem --tipos-codigo 0: não dá para saber se ela rodou")
            registro["tipos"] = dict(erros)
    except (OSError, RelatorioInvalido) as erro:
        print(f"não deu para extrair: {erro}", file=sys.stderr)
        return SAIDA_USO
    Path(args.saida).write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")
    falhas = sum(s in STATUS_FALHA for s in (registro["testes"] or {}).values())
    print(f"Testes: {len(registro['testes'] or {})}, com falha: {falhas}. Erros de tipo: {sum((registro['tipos'] or {}).values())}.")
    return SAIDA_OK


def _secao(titulo, itens):
    if itens:
        print(f"{titulo} ({len(itens)}):")
        for item in sorted(itens):
            print(f"  {item}")


def comparar(args):
    try:
        antes = json.loads(Path(args.antes).read_text(encoding="utf-8"))
        depois = json.loads(Path(args.depois).read_text(encoding="utf-8"))
    except (OSError, ValueError) as erro:
        print(f"não deu para ler: {erro}", file=sys.stderr)
        return SAIDA_USO
    for chave in ("testes", "tipos"):
        if (antes.get(chave) is None) != (depois.get(chave) is None):
            print(f"A verificação de {chave} rodou só de um lado: rode dos dois para comparar.")
            return SAIDA_USO
    testes_a, testes_d = antes.get("testes") or {}, depois.get("testes") or {}
    tipos_a, tipos_d = Counter(antes.get("tipos") or {}), Counter(depois.get("tipos") or {})
    falhas_a = {n for n, s in testes_a.items() if s in STATUS_FALHA}
    falhas_d = {n for n, s in testes_d.items() if s in STATUS_FALHA}
    novas = falhas_d - falhas_a
    sumiram = set(testes_a) - set(testes_d)
    tipos_novos = {e for e in tipos_d if tipos_d[e] > tipos_a[e]}
    _secao("Teste com falha nova", novas)
    _secao("Teste que sumiu", sumiram)
    _secao("Erro de tipo novo", tipos_novos)
    _secao("Teste que deixou de falhar", falhas_a - falhas_d - sumiram)
    print(f"Falhas que já existiam e continuam: {len(falhas_a & falhas_d)}.")
    if novas or sumiram or tipos_novos:
        return SAIDA_ACUSA
    print("Nenhuma falha nova.")
    return SAIDA_OK


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    comandos = parser.add_subparsers(dest="comando", required=True)
    extrai = comandos.add_parser("extrai")
    extrai.add_argument("--saida", required=True)
    extrai.add_argument("--testes")
    extrai.add_argument("--tipos")
    extrai.add_argument("--tipos-codigo", type=int)
    extrai.add_argument("--raiz")
    extrai.set_defaults(funcao=extrair)
    compara = comandos.add_parser("compara")
    compara.add_argument("antes")
    compara.add_argument("depois")
    compara.set_defaults(funcao=comparar)
    args = parser.parse_args()
    return args.funcao(args)


if __name__ == "__main__":
    sys.exit(main())
