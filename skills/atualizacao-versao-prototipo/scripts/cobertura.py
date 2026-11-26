"""CLI de cobertura da atualização de versão do protótipo.

Subcomandos: `mapear`, `rastreio`, `omissoes`, `unidades`, `fatiar`, `achados`, `idiomas`, `cruzar`, `inventario`, `resumo`. JSON no stdout.
Saída: 0 = ok, 11 = achados, 2 = uso inválido (argumento errado ou JSON ilegível; mensagem no stderr).
Só biblioteca padrão.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).parent))

import cobertura_conferir  # noqa: E402
import cobertura_cruzar  # noqa: E402
import cobertura_idiomas  # noqa: E402
import cobertura_inventario  # noqa: E402
import cobertura_mapa  # noqa: E402

SAIDA_OK = 0
SAIDA_ACHADOS = 11
SAIDA_USO = 2


class ErroDeUso(Exception):
    """Entrada inválida (arquivo ausente, JSON ilegível, ref inexistente): vira saída 2."""


def _ler_json(caminho):
    try:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError) as erro:  # ValueError cobre JSON inválido e UnicodeDecodeError
        raise ErroDeUso(f"Não foi possível ler JSON de {caminho}: {erro}") from erro
    if not isinstance(dados, dict):
        raise ErroDeUso(f"{caminho}: o JSON deve ser um objeto na raiz, não {type(dados).__name__}.")
    return dados


def _imprimir(dados):
    print(json.dumps(dados, ensure_ascii=False, indent=2))


def _cmd_mapear(args):
    vigente = args.vigente
    try:
        if args.sem_vigente:  # primeira sincronização: a vigente é a árvore vazia
            vigente = cobertura_mapa.arvore_vazia(args.repo)
        mapa = cobertura_mapa.mapear(args.repo, vigente, args.candidata, args.orcamento, args.rotas)
    except cobertura_mapa.PresetInvalido as erro:
        raise ErroDeUso(str(erro)) from erro
    except subprocess.CalledProcessError as erro:
        detalhe = (erro.stderr or b"").decode("utf-8", errors="replace").strip()
        origem = vigente or "árvore vazia"
        raise ErroDeUso(f"git falhou em {args.repo} ({origem}..{args.candidata}): {detalhe or erro}") from erro
    except OSError as erro:
        raise ErroDeUso(f"Não foi possível mapear {args.repo}: {erro}") from erro
    if args.saida:
        _gravar_json(args.saida, mapa)
        _imprimir({
            "peso_total": mapa["peso_total"],
            "cabe_em_um_agente": mapa["cabe_em_um_agente"],
            "trechos": len(mapa["trechos"]),
            "telas": len(mapa["telas"]),
            "peso_sem_tela": mapa["peso_sem_tela"],
        })
    else:
        _imprimir(mapa)
    return SAIDA_OK


def _cmd_rastreio(args):
    mapa, rastreio, catalogo = _ler_json(args.mapa), _ler_json(args.rastreio), _ler_json(args.catalogo)
    cruzamentos = _ler_json(args.cruzamentos) if args.cruzamentos else None
    atuais = None
    if args.repo:  # SHA atual das refs com que o mapa foi gerado: pega a branch que andou depois dele
        try:
            atuais = {ref: cobertura_mapa.resolver_sha(args.repo, mapa[ref])
                      for ref in ("vigente", "candidata") if isinstance(mapa.get(ref), str)}
        except (subprocess.CalledProcessError, OSError) as erro:
            raise ErroDeUso(f"Não foi possível resolver as versões do mapa em {args.repo}: {erro}") from erro
    try:
        resultado = cobertura_conferir.conferir_rastreio(mapa, rastreio, catalogo, atuais, cruzamentos)
    except ValueError as erro:
        raise ErroDeUso(f"{args.mapa}: {erro}") from erro
    _imprimir(resultado)
    return SAIDA_OK if resultado["ok"] else SAIDA_ACHADOS


def _cmd_omissoes(args):
    _imprimir(cobertura_conferir.listar_omissoes(_ler_json(args.antes), _ler_json(args.depois)))
    return SAIDA_OK


def _gravar_json(caminho, dados):
    try:
        Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as erro:
        raise ErroDeUso(f"Não foi possível gravar {caminho}: {erro}") from erro


def _cmd_unidades(args):
    mapa = _ler_json(args.mapa)
    if not args.propor:
        if args.saida:
            raise ErroDeUso("--saida só vale com --propor.")
        if args.orcamento is not None and args.orcamento <= 0:
            raise ErroDeUso(f"Orçamento inválido: {args.orcamento} (esperado inteiro positivo).")
        try:  # o orçamento da conferência é --orcamento ou o do mapa, nunca o do arquivo de unidades
            resultado = cobertura_conferir.conferir_unidades(mapa, _ler_json(args.unidades), args.orcamento)
        except ValueError as erro:
            raise ErroDeUso(f"{args.mapa}: {erro}") from erro
        _imprimir(resultado)
        return SAIDA_OK if resultado["ok"] else SAIDA_ACHADOS
    orcamento = args.orcamento
    if orcamento is None:  # sem --orcamento vale o do mapa
        orcamento = mapa.get("orcamento")
        if isinstance(orcamento, bool) or not isinstance(orcamento, int) or orcamento <= 0:
            orcamento = cobertura_mapa.ORCAMENTO_PADRAO
    try:
        proposta = cobertura_conferir.propor_unidades(mapa, orcamento, args.idioma_referencia)
        ok = cobertura_conferir.conferir_unidades(mapa, proposta, orcamento)["ok"]
    except ValueError as erro:
        raise ErroDeUso(f"{args.mapa}: {erro}") from erro
    if args.saida:
        _gravar_json(args.saida, proposta)
        _imprimir({"unidades": len(proposta["unidades"]), "ok": ok})
    else:
        _imprimir(proposta)
    return SAIDA_OK


def _cmd_fatiar(args):
    fatias = cobertura_conferir.fatiar_unidades(_ler_json(args.mapa), _ler_json(args.unidades))
    Path(args.pasta).mkdir(parents=True, exist_ok=True)
    for unidade_id, fatia in fatias.items():
        _gravar_json(str(Path(args.pasta) / f"{unidade_id}.json"), fatia)
    _imprimir({"arquivos": len(fatias), "pasta": args.pasta})
    return SAIDA_OK


def _cmd_idiomas(args):
    mapa, unidades = _ler_json(args.mapa), _ler_json(args.unidades)
    try:
        achados = cobertura_idiomas.comparar(args.repo, mapa, unidades)
    except ValueError as erro:
        raise ErroDeUso(str(erro)) from erro
    except subprocess.CalledProcessError as erro:
        detalhe = (erro.stderr or b"").decode("utf-8", errors="replace").strip()
        raise ErroDeUso(f"git falhou em {args.repo}: {detalhe or erro}") from erro
    except OSError as erro:
        raise ErroDeUso(f"Não foi possível ler os idiomas de {args.repo}: {erro}") from erro
    _gravar_json(args.saida, achados)
    _imprimir({"status": achados["status"], "trechos": len(achados["trechos"]), "idiomas": [
        {campo: (len(p[campo]) if isinstance(p[campo], list) else p[campo])
         for campo in ("idioma", "chaves", "faltando", "a_mais", "iguais_a_referencia")} for p in achados["propostas"]]})
    return SAIDA_OK if achados["status"] == "OK" else SAIDA_ACHADOS


def _cmd_resumo(args):
    mapa, rastreio, catalogo = _ler_json(args.mapa), _ler_json(args.rastreio), _ler_json(args.catalogo)
    relidas = None
    if args.cega:
        relidas = [tela for arquivo in args.cega for tela in (_ler_json(arquivo).get("telas") or {})]
    try:
        resultado = cobertura_conferir.resumir_cobertura(
            mapa, rastreio, catalogo,
            antes=_ler_json(args.antes) if args.antes else None,
            itens_omitidos=_ler_json(args.itens_omitidos) if args.itens_omitidos else None,
            telas_relidas=relidas,
            cruzamentos=_ler_json(args.cruzamentos) if args.cruzamentos else None,
            caminho=args.caminho)
    except ValueError as erro:
        raise ErroDeUso(f"{args.mapa}: {erro}") from erro
    _imprimir(resultado)
    return SAIDA_OK if resultado["ok"] else SAIDA_ACHADOS


def _cmd_cruzar(args):
    mapa = _ler_json(args.mapa)
    catalogo = _ler_json(args.catalogo) if args.catalogo else None
    unidades = _ler_json(args.unidades) if args.unidades else None
    try:
        resultado = cobertura_cruzar.cruzar(args.repo, mapa, catalogo, unidades, args.idioma)
    except ValueError as erro:  # entrada inválida e preset de rotas do mapa ilegível
        raise ErroDeUso(f"{args.mapa}: {erro}") from erro
    except subprocess.CalledProcessError as erro:
        detalhe = (erro.stderr or b"").decode("utf-8", errors="replace").strip()
        raise ErroDeUso(f"git falhou em {args.repo}: {detalhe or erro}") from erro
    except OSError as erro:
        raise ErroDeUso(f"Não foi possível cruzar as telas de {args.repo}: {erro}") from erro
    if args.saida:
        _gravar_json(args.saida, resultado)
        resumo = resultado["resumo"]
        _imprimir({"fortes": resumo["fortes"], "fracas": resumo["fracas"], "preexistentes": resumo["preexistentes"],
                   "identidade": resultado["identidade"], "avisos": resultado["avisos"]})
    else:
        _imprimir(resultado)
    return SAIDA_ACHADOS if resultado["resumo"]["fortes"] or resultado["identidade"] else SAIDA_OK


def _cmd_inventario(args):
    mapa = _ler_json(args.mapa)
    try:
        resultado = cobertura_inventario.inventariar(args.repo, mapa, args.moldura or [])
    except cobertura_inventario.MolduraAusente as erro:
        raise ErroDeUso(str(erro)) from erro
    except ValueError as erro:  # mapa sem candidata ou telas
        raise ErroDeUso(f"{args.mapa}: {erro}") from erro
    except subprocess.CalledProcessError as erro:
        detalhe = (erro.stderr or b"").decode("utf-8", errors="replace").strip()
        raise ErroDeUso(f"git falhou em {args.repo}: {detalhe or erro}") from erro
    except OSError as erro:
        raise ErroDeUso(f"Não foi possível inventariar {args.repo}: {erro}") from erro
    if args.saida:
        _gravar_json(args.saida, resultado)
        _imprimir({
            "versao": resultado["versao"], "telas": len(resultado["telas"]), "molduras": len(resultado["molduras"]),
            "global": resultado["global"], "avisos": resultado["avisos"],
        })
    else:
        _imprimir(resultado)
    return SAIDA_OK


def _cmd_achados(args):
    regioes = args.regiao or []
    if regioes and len(regioes) != len(args.arquivo):
        raise ErroDeUso(f"--regiao e --arquivo vão em pares: {len(regioes)} regiões para {len(args.arquivo)} arquivos.")
    if len(set(regioes)) != len(regioes):
        raise ErroDeUso("--regiao repetida: um arquivo por região.")
    if not regioes and len(args.arquivo) != 1:
        raise ErroDeUso("Sem --regiao vale um só --arquivo (o da unidade inteira); para vários, informe --regiao antes de cada --arquivo.")
    try:
        unidades = _ler_json(args.unidades)
        if regioes:
            resultado = cobertura_conferir.conferir_achados_por_regiao(
                unidades, args.unidade, {r: Path(a) for r, a in zip(regioes, args.arquivo)})
        else:
            resultado = cobertura_conferir.conferir_achados(unidades, args.unidade, Path(args.arquivo[0]))
    except ValueError as erro:
        raise ErroDeUso(f"{args.unidades}: {erro}") from erro
    _imprimir(resultado)
    return SAIDA_OK if resultado["ok"] else SAIDA_ACHADOS


def _parser():
    parser = argparse.ArgumentParser(prog="cobertura.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("mapear", help="corta o diff entre duas versões em trechos e estima o peso")
    p.add_argument("--repo", required=True)
    versao = p.add_mutually_exclusive_group(required=True)
    versao.add_argument("--vigente")
    versao.add_argument("--sem-vigente", action="store_true",
                        help="primeira sincronização, sem versão anterior: a vigente é a árvore vazia e toda tela entra como nova")
    p.add_argument("--candidata", required=True)
    p.add_argument("--orcamento", type=int, default=cobertura_mapa.ORCAMENTO_PADRAO)
    p.add_argument("--rotas", help="preset JSON de rotas: usa só ele e pula a detecção dos presets da skill")
    p.add_argument("--saida", help="grava o mapa neste arquivo e imprime só um resumo")
    p.set_defaults(func=_cmd_mapear)

    p = sub.add_parser("rastreio", help="confere que todo trecho do mapa tem destino")
    p.add_argument("--mapa", required=True)
    p.add_argument("--rastreio", required=True)
    p.add_argument("--catalogo", required=True)
    p.add_argument("--repo", help="repositório do protótipo: confere que as versões do mapa ainda apontam para os mesmos commits")
    p.add_argument("--cruzamentos", help="saída do `cruzar`: toda suspeita forte precisa de uma diferença INCONSISTENCIA-PROTO no catálogo")
    p.set_defaults(func=_cmd_rastreio)

    p = sub.add_parser("omissoes", help="lista diferenças do catálogo novo ausentes no anterior")
    p.add_argument("--antes", required=True)
    p.add_argument("--depois", required=True)
    p.set_defaults(func=_cmd_omissoes)

    p = sub.add_parser("unidades", help="propõe unidades de descoberta (--propor) ou confere as existentes (--unidades)")
    p.add_argument("--mapa", required=True)
    modo = p.add_mutually_exclusive_group(required=True)
    modo.add_argument("--propor", action="store_true")
    modo.add_argument("--unidades", help="arquivo de unidades a conferir")
    p.add_argument("--orcamento", type=int, help="orçamento da proposta ou da conferência; padrão: o orçamento do mapa")
    p.add_argument("--saida", help="só com --propor: grava a proposta neste arquivo e imprime só um resumo")
    p.add_argument("--idioma-referencia", default="pt-BR",
                   help="só com --propor: idioma lido pelos agentes; os demais vão à U-IDIOMAS, comparados por script (padrão pt-BR)")
    p.set_defaults(func=_cmd_unidades)

    p = sub.add_parser("fatiar", help="grava um arquivo por unidade com agente, com só o que o brief dela precisa do mapa")
    p.add_argument("--mapa", required=True)
    p.add_argument("--unidades", required=True)
    p.add_argument("--pasta", required=True)
    p.set_defaults(func=_cmd_fatiar)

    p = sub.add_parser("idiomas", help="compara os idiomas da U-IDIOMAS com a referência e grava os achados da unidade")
    p.add_argument("--mapa", required=True)
    p.add_argument("--unidades", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--saida", required=True, help="arquivo de achados, em geral <tmp>/achados/U-IDIOMAS.json")
    p.set_defaults(func=_cmd_idiomas)

    p = sub.add_parser("resumo", help="conta os números do resumo nos arquivos e monta a linha de cobertura")
    p.add_argument("--mapa", required=True)
    p.add_argument("--rastreio", required=True)
    p.add_argument("--catalogo", required=True)
    p.add_argument("--antes", help="catálogo copiado antes de integrar a leitura cega")
    p.add_argument("--cega", action="append", help="arquivo da leitura cega; repita para vários")
    p.add_argument("--itens-omitidos", help="JSON tela -> itens que a leitura cega viu e o catálogo não tinha")
    p.add_argument("--cruzamentos", help="saída do `cruzar`")
    p.add_argument("--caminho", default="", help="um agente ou ondas, com o motivo")
    p.set_defaults(func=_cmd_resumo)

    p = sub.add_parser("cruzar", help="procura inconsistências entre telas da candidata (guarda assimétrica e texto antigo intacto)")
    p.add_argument("--mapa", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--catalogo", help="catálogo: liga cada suspeita às diferenças afetadas (`afeta_df`)")
    p.add_argument("--unidades", help="unidades: liga cada suspeita às unidades e acusa as telas fora do mapa")
    p.add_argument("--idioma", default="pt-BR", help="idioma dos arquivos de locale lidos pelo texto antigo (padrão pt-BR)")
    p.add_argument("--saida", help="grava o cruzamento neste arquivo e imprime só um resumo")
    p.set_defaults(func=_cmd_cruzar)

    p = sub.add_parser("inventario", help="lista, por tela, os arquivos e os componentes que ela usa (lido do git, na candidata do mapa)")
    p.add_argument("--mapa", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--moldura", action="append",
                   help="arquivo de entrada que não é tela (layout comum, src/app.tsx, tema); repita para vários")
    p.add_argument("--saida", help="grava o inventário neste arquivo e imprime só um resumo")
    p.set_defaults(func=_cmd_inventario)

    p = sub.add_parser("achados", help="confere o arquivo de achados de uma unidade (ou os arquivos de suas regiões)")
    p.add_argument("--unidades", required=True)
    p.add_argument("--unidade", required=True)
    p.add_argument("--arquivo", required=True, action="append",
                   help="achados da unidade; em unidade dividida por região, um por --regiao (repita o par)")
    p.add_argument("--regiao", action="append", help="região do --arquivo correspondente; a cobertura é a união dos arquivos")
    p.set_defaults(func=_cmd_achados)
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
