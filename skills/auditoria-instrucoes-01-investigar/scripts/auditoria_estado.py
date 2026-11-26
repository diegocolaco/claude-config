#!/usr/bin/env python3
"""Estado e gates da auditoria de instruções de agente (etapas 01, 02 e 03).

Cria a pasta da auditoria, grava o cabeçalho de cada etapa e verifica se a
próxima etapa pode começar. Usa apenas a biblioteca padrão.
"""
import argparse
from datetime import date
import hashlib
from pathlib import Path
import re
import subprocess
import sys

BASE = Path("user-doc") / "auditoria-instrucoes"
ARQUIVOS = {"01": "01-investigacao.md", "02": "02-reescrita.md", "03": "03-ataque.md"}
STATUS = ("em_andamento", "concluida", "parcial", "bloqueada")
COM_MOTIVO = ("parcial", "bloqueada")


class Recusa(Exception):
    """Condição que impede o comando; vira mensagem e código 2."""


def slug_de(caminho):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]", "-", caminho.lower())).strip("-")


def sha256_de(arquivo):
    return hashlib.sha256(arquivo.read_bytes()).hexdigest()


def commit_de(raiz):
    try:
        saida = subprocess.run(["git", "rev-parse", "HEAD"], cwd=raiz,
                               capture_output=True, text=True, check=False)
    except OSError:
        return "desconhecido"
    valor = saida.stdout.strip()
    return valor if saida.returncode == 0 and valor else "desconhecido"


def _aspas(texto):
    return '"' + texto.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _sem_aspas(valor):
    if len(valor) >= 2 and valor[0] == valor[-1] == '"':
        return re.sub(r"\\(.)", r"\1", valor[1:-1])
    return valor


def escrever_cabecalho(dados, corpo):
    linhas = ["---", f"etapa: {_aspas(dados['etapa'])}", f"status: {dados['status']}", "alvo:"]
    for item in dados["alvo"]:
        linhas += [f"  - caminho: {item['caminho']}", f"    sha256: {item['sha256']}"]
    linhas += [
        f"commit_base: {dados['commit_base']}",
        f"data: {dados['data']}",
        f"motivo_status: {_aspas(dados.get('motivo_status', ''))}",
        "---",
    ]
    return "\n".join(linhas) + "\n" + corpo


def ler_cabecalho(texto):
    """Lê o primeiro bloco de frontmatter no formato emitido por escrever_cabecalho."""
    if not texto.startswith("---\n"):
        raise Recusa("cabeçalho de estado ausente")
    fim = texto.find("\n---\n", 3)
    if fim < 0:
        raise Recusa("cabeçalho de estado sem fechamento")
    dados = {"alvo": []}
    for linha in texto[4:fim].splitlines():
        if linha.startswith("  - caminho: "):
            dados["alvo"].append({"caminho": linha[len("  - caminho: "):]})
        elif linha.startswith("    sha256: ") and dados["alvo"]:
            dados["alvo"][-1]["sha256"] = linha[len("    sha256: "):]
        elif ": " in linha and not linha.startswith(" "):
            chave, valor = linha.split(": ", 1)
            dados[chave] = _sem_aspas(valor)
    return dados, texto[fim + len("\n---\n"):]


def _ler_etapa(pasta, etapa):
    arquivo = pasta / ARQUIVOS[etapa]
    if not arquivo.is_file():
        return None, ""
    return ler_cabecalho(arquivo.read_text(encoding="utf-8"))


def _raiz_da_pasta(pasta):
    return pasta.resolve().parents[2]


def iniciar(args):
    raiz = Path(args.raiz).resolve()
    alvos = []
    for caminho in args.alvo:
        arquivo = raiz / caminho
        if not arquivo.is_file():
            raise Recusa(f"alvo não encontrado: {caminho}")
        alvos.append({"caminho": Path(caminho).as_posix(), "sha256": sha256_de(arquivo)})
    data = args.data or date.today().isoformat()
    relativa = BASE / f"{data}-{args.slug or slug_de(args.alvo[0])}"
    pasta = raiz / relativa
    if pasta.exists():
        raise Recusa(f"a pasta já existe; retome-a ou use outro --slug: {relativa.as_posix()}")
    pasta.mkdir(parents=True)
    dados = {"etapa": "01", "status": "em_andamento", "alvo": alvos,
             "commit_base": commit_de(raiz), "data": data, "motivo_status": ""}
    (pasta / ARQUIVOS["01"]).write_text(escrever_cabecalho(dados, ""), encoding="utf-8")
    print(relativa.as_posix())


def marcar(args):
    pasta = Path(args.pasta)
    if args.status in COM_MOTIVO and not args.motivo:
        raise Recusa(f"o status {args.status} exige --motivo")
    dados, corpo = _ler_etapa(pasta, args.etapa)
    if dados is None:
        if args.etapa == "01":
            raise Recusa(f"{ARQUIVOS['01']} não existe; use iniciar")
        base, _ = _ler_etapa(pasta, "01")
        if base is None:
            raise Recusa(f"{ARQUIVOS['01']} não existe em {pasta.as_posix()}")
        dados = {"alvo": base["alvo"], "commit_base": base["commit_base"]}
    dados.update(etapa=args.etapa, status=args.status, data=date.today().isoformat(),
                 motivo_status=args.motivo or "")
    (pasta / ARQUIVOS[args.etapa]).write_text(escrever_cabecalho(dados, corpo), encoding="utf-8")
    print(f"{ARQUIVOS[args.etapa]}: {args.status}")


def _exigir_concluida(pasta, etapa, aceitar_parcial):
    dados, _ = _ler_etapa(pasta, etapa)
    nome = ARQUIVOS[etapa]
    if dados is None:
        raise Recusa(f"etapa {etapa} ausente: {nome} não existe em {pasta.as_posix()}")
    status = dados.get("status")
    if status == "concluida" or (status == "parcial" and aceitar_parcial):
        return dados
    motivo = dados.get("motivo_status") or "sem motivo registrado"
    if status == "parcial":
        raise Recusa(f"{nome} está parcial ({motivo}); avance só com aceite do usuário via --aceitar-parcial")
    raise Recusa(f"{nome} está com status {status} ({motivo})")


def verificar(args):
    pasta = Path(args.pasta)
    base = _exigir_concluida(pasta, "01", args.aceitar_parcial)
    if args.etapa == "03":
        _exigir_concluida(pasta, "02", args.aceitar_parcial)
        proposta = pasta / "02-versao-proposta"
        if not proposta.is_dir() or not any(proposta.iterdir()):
            raise Recusa("02-versao-proposta ausente ou vazia")
    raiz = _raiz_da_pasta(pasta)
    for item in base["alvo"]:
        arquivo = raiz / item["caminho"]
        if not arquivo.is_file():
            raise Recusa(f"alvo não encontrado: {item['caminho']}; a investigação está desatualizada")
        if sha256_de(arquivo) != item.get("sha256"):
            raise Recusa(f"o alvo mudou desde a etapa 01: {item['caminho']}; a investigação está desatualizada")
    print(f"etapa {args.etapa} liberada: {pasta.as_posix()}")


def listar(args):
    raiz = Path(args.raiz).resolve()
    base = raiz / BASE
    if not base.is_dir():
        return
    for pasta in sorted(p for p in base.iterdir() if p.is_dir()):
        status = {}
        for etapa in ARQUIVOS:
            try:
                dados, _ = _ler_etapa(pasta, etapa)
            except Recusa:
                dados = {"status": "invalido"}
            status[etapa] = dados["status"] if dados else "-"
        if status["03"] == "concluida":
            proxima = "aplicar"
        elif status["02"] == "concluida":
            proxima = "03"
        elif status["01"] == "concluida":
            proxima = "02"
        else:
            proxima = "01"
        relativa = pasta.relative_to(raiz).as_posix()
        print(f"{relativa} 01={status['01']} 02={status['02']} 03={status['03']} proxima={proxima}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("iniciar", help="cria a pasta da auditoria e o cabeçalho da etapa 01")
    p.add_argument("--alvo", nargs="+", required=True, help="caminhos relativos à raiz")
    p.add_argument("--slug")
    p.add_argument("--raiz", default=".")
    p.add_argument("--data", help="AAAA-MM-DD; padrão: hoje")
    p.set_defaults(func=iniciar)

    p = sub.add_parser("marcar", help="grava o status de uma etapa preservando o corpo")
    p.add_argument("pasta")
    p.add_argument("--etapa", choices=sorted(ARQUIVOS), required=True)
    p.add_argument("--status", choices=STATUS, required=True)
    p.add_argument("--motivo")
    p.set_defaults(func=marcar)

    p = sub.add_parser("verificar", help="confere se a etapa pode começar")
    p.add_argument("pasta")
    p.add_argument("--etapa", choices=("02", "03"), required=True)
    p.add_argument("--aceitar-parcial", action="store_true")
    p.set_defaults(func=verificar)

    p = sub.add_parser("listar", help="lista auditorias e a próxima etapa")
    p.add_argument("--raiz", default=".")
    p.set_defaults(func=listar)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except Recusa as erro:
        print(f"auditoria_estado: {erro}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
