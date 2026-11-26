"""Acende sinal quando um ajuste mexe em permissão, em dados do servidor ou em arquivo compartilhado.

Revisor sozinho não é trava de permissão: o sinal vem de um programa, que não se convence por argumento.

uso: paradas.py <repo> <base> [<head>] [--compartilhados <pasta/> ...] [--json]

Sem <head>, lê a pasta de trabalho contra a base comum com <base>, inclusive arquivo novo ainda sem `git add`.
Com <head>, lê o que <head> tem a mais que a base comum. Lê linhas acrescentadas e removidas: tirar uma trava
é tão sério quanto pôr. Arquivos de teste não acendem e saem listados em `testes_ignorados`.

É busca por padrão, não entendimento: sinal é motivo para olhar, e sinal apagado não prova que está tudo certo.
Saída: 0 = sem sinal, 1 = há sinal, 2 = uso inválido, git falhou ou nenhuma alteração, que é «não conferido». Só biblioteca padrão.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

SAIDA_OK = 0
SAIDA_SINAL = 1
SAIDA_USO = 2

ARQUIVO_TESTE = re.compile(r"(\.(spec|test|e2e)\.[a-z]+$|(^|/)(__tests__|__mocks__|tests?|e2e)/)", re.I)
PERMISSAO = re.compile(
    r"permiss|autoriz|authoriz|\bhasRole\b|\buserRole\b|\broles\b|\brole\s*[!=]==?|\.role\b|\bisAdmin\b|\bcan(Access|Edit|View|Delete|Create)\b"
    r"|\bacl\b|\bRequireAuth\b|\b(Private|Protected)Route\b|\bkeycloak\b|\bguard\b",
    re.I,
)
PERMISSAO_CAMINHO = re.compile(r"(^|/)[^/]*(permiss|acl|guard|autoriz|authoriz)[^/]*(/|$)", re.I)
DADOS = re.compile(
    r"\bfetch\(|\baxios\b|\bsupabase\b|\buse(Query|Mutation|InfiniteQuery)\b|\bhttp(Client)?\.(get|post|put|patch|delete)\b"
    r"|['\"`]/api/|\bcreateServerFn\b|\bdrizzle\b",
)
DADOS_CAMINHO = re.compile(r"(^|/)(apps/api|api|server|backend|migrations|supabase|drizzle|controllers?)/|\.(sql|cs|java)$", re.I)
COMPARTILHADO_CAMINHO = ("components/", "hooks/", "lib/", "shared/", "common/", "utils/", "services/", "packages/", "contexts/", "stores/")


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout


def ler_alteracoes(repo, base, head):
    """Devolve {arquivo: [(numero, sinal, texto)]}; arquivo sem linha alterada (renome, binário) fica com lista vazia."""
    comum = _git(repo, "merge-base", base, head or "HEAD").strip()
    alvo = [comum, head] if head else [comum]
    bruto = _git(repo, "diff", "--unified=0", "--no-color", "--no-ext-diff", *alvo, "--")
    alteracoes = {}
    atual = None
    no_cabecalho = False
    numero = {"+": 0, "-": 0}
    for linha in bruto.splitlines():
        if linha.startswith("diff --git "):
            atual = None
            no_cabecalho = True
        elif no_cabecalho and linha.startswith(("--- ", "+++ ")):
            caminho = linha[4:].split("\t")[0].strip().strip('"')
            if caminho != "/dev/null":
                atual = caminho[2:] if caminho[:2] in ("a/", "b/") else caminho
                alteracoes.setdefault(atual, [])
        elif no_cabecalho and linha.startswith("rename to "):
            atual = linha[len("rename to "):].strip()
            alteracoes.setdefault(atual, [])
        elif linha.startswith("@@"):
            no_cabecalho = False
            achado = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)", linha)
            numero = {"-": int(achado[1]), "+": int(achado[2])}
        elif atual and linha[:1] in numero:
            alteracoes[atual].append((numero[linha[0]], linha[0], linha[1:]))
            numero[linha[0]] += 1
    if not head:
        for novo in _git(repo, "ls-files", "--others", "--exclude-standard").splitlines():
            try:
                texto = (Path(repo) / novo).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                alteracoes[novo] = []
                continue
            alteracoes[novo] = [(i, "+", t) for i, t in enumerate(texto.splitlines(), 1)]
    return alteracoes


def _eh_compartilhado(arquivo, pastas):
    return any(arquivo.startswith(p) or f"/{p}" in arquivo for p in pastas)


def _sinal(tipo, onde, trecho):
    return {"tipo": tipo, "onde": onde, "trecho": trecho.strip()[:160]}


def achar_sinais(alteracoes, pastas):
    sinais = []
    ignorados = []
    for arquivo, linhas in sorted(alteracoes.items()):
        if ARQUIVO_TESTE.search(arquivo):
            ignorados.append(arquivo)
            continue
        if PERMISSAO_CAMINHO.search(arquivo):
            sinais.append(_sinal("permissao", arquivo, "caminho do arquivo"))
        if DADOS_CAMINHO.search(arquivo):
            sinais.append(_sinal("dados", arquivo, "caminho do arquivo"))
        if _eh_compartilhado(arquivo, pastas):
            sinais.append(_sinal("compartilhado", arquivo, "caminho do arquivo"))
        for numero, marca, texto in linhas:
            onde = f"{arquivo}:{numero} ({'acrescentada' if marca == '+' else 'removida'})"
            if PERMISSAO.search(texto):
                sinais.append(_sinal("permissao", onde, texto))
            if DADOS.search(texto):
                sinais.append(_sinal("dados", onde, texto))
    return sinais, ignorados


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo")
    parser.add_argument("base")
    parser.add_argument("head", nargs="?")
    parser.add_argument("--compartilhados", nargs="*", default=[], help="pastas a mais, além das de sempre")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        alteracoes = ler_alteracoes(args.repo, args.base, args.head)
    except (subprocess.CalledProcessError, OSError) as erro:
        print(f"não deu para ler as alterações: {getattr(erro, 'stderr', erro)}", file=sys.stderr)
        return SAIDA_USO
    sinais, ignorados = achar_sinais(alteracoes, (*COMPARTILHADO_CAMINHO, *args.compartilhados))
    if args.json:
        print(json.dumps({"arquivos": len(alteracoes), "sinais": sinais, "testes_ignorados": ignorados}, ensure_ascii=False, indent=1))
    elif not alteracoes:
        print("Nenhuma alteração em relação à base: não conferido.")
    elif not sinais:
        print(f"Nenhum sinal em {len(alteracoes)} arquivo(s).")
    else:
        for sinal in sinais:
            print(f"{sinal['tipo']}: {sinal['onde']}: {sinal['trecho']}")
    if ignorados and not args.json:
        print(f"Arquivos de teste não olhados: {', '.join(ignorados)}")
    if not alteracoes:
        return SAIDA_USO
    return SAIDA_SINAL if sinais else SAIDA_OK


if __name__ == "__main__":
    sys.exit(main())
