"""Lista, por git, os pontos do protótipo que podem expor dados ou acesso.

Não decide nada: é o ponto de partida da varredura de riscos da etapa de decisões.
Lê só o commit indicado, sem executar nada do protótipo. Saída curta, por categoria.
Saída: 0 = executou, 2 = uso inválido. Só biblioteca padrão.
"""
import argparse
from collections import Counter, defaultdict
import re
import subprocess
import sys

SAIDA_OK = 0
SAIDA_USO = 2
FORA = [":!*.lock", ":!pnpm-lock.yaml", ":!package-lock.json", ":!*.svg", ":!src/locales/*", ":!*.md",
        ":!.github/*", ":!.agents/*", ":!.claude/*", ":!docs/*", ":!e2e/*", ":!tests/*", ":!**/*.test.*",
        ":!config/oneapi.json"]
HOST = re.compile(r"https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")
HOST_INOFENSIVO = ("w3.org", "schema.org", "localhost", "example.com")
CATEGORIAS = {
    "credencial e entrada": r"password|senha|currentAuthority|type === .mobile",
    "sessão e saída": r"outLogin|currentUser|localStorage|sessionStorage|document\.cookie|authorization",
    "outra origem": r"Access-Control|cors|credentials:|withCredentials",
    "conteúdo sem filtro": r"dangerouslySetInnerHTML|innerHTML|eval\(|new Function",
    "cadastro e escrita pública": r"/api/register|POST +/api",
}


def git_grep(repo, commit, padrao):
    comando = ["git", "-C", repo, "grep", "-nIE", padrao, commit, "--", "."] + FORA
    saida = subprocess.run(comando, capture_output=True, text=True)
    if saida.returncode not in (0, 1):
        raise ValueError(saida.stderr.strip())
    prefixo = commit + ":"
    return [linha[len(prefixo):] if linha.startswith(prefixo) else linha for linha in saida.stdout.splitlines()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--max-linhas", type=int, default=40)
    args = parser.parse_args(argv)
    try:
        hosts = Counter()
        arquivos = defaultdict(set)
        for linha in git_grep(args.repo, args.commit, r"https?://"):
            caminho = linha.split(":", 1)[0]
            for host in HOST.findall(linha):
                if not host.endswith(HOST_INOFENSIVO):
                    hosts[host] += 1
                    arquivos[host].add(caminho)
        print("## Hosts externos")
        for host, total in hosts.most_common():
            exemplos = ", ".join(sorted(arquivos[host])[:3])
            print(f"{host}: {total} ocorrências em {len(arquivos[host])} arquivos, como {exemplos}")
        for categoria, padrao in CATEGORIAS.items():
            achados = git_grep(args.repo, args.commit, padrao)
            print(f"\n## {categoria}: {len(achados)} linhas")
            for linha in achados[:args.max_linhas]:
                print(linha[:150])
    except (OSError, ValueError) as erro:
        print(f"uso inválido: {erro}", file=sys.stderr)
        return SAIDA_USO
    return SAIDA_OK


if __name__ == "__main__":
    sys.exit(main())
