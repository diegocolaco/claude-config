"""Confere a divisão em grupos da etapa de decisões contra o catálogo e o inventário.

Acusa diferença sem destino ou em dois destinos, previsão com cenários demais por tarefa,
grupo acima do limite de tarefas, par declarado independente que divide arquivo do protótipo
e pacote do inventário fora da lista decidida. Devolve só o resumo, para não encher o contexto.
Formato de --grupos: {"grupos": {"G0": {"diferencas": ["DF-1"], "tarefas_cenario": 9, "tarefas_base": 6,
"cenarios_a_criar": 2}}, "excecoes": ["DF-2"], "pares_independentes": [["G1", "G2"]],
"bibliotecas": ["antd"], "bibliotecas_recusadas": ["@umijs/max"]}. `cenarios_a_criar` é opcional:
sem ele, conta 2 por diferença aberta sem requisito.
Saída: 0 = nada a conferir, 11 = há itens, 2 = uso inválido. Só biblioteca padrão.
"""
import argparse
from collections import defaultdict
import json
import sys

SAIDA_OK = 0
SAIDA_ITENS = 11
SAIDA_USO = 2


def conferir(catalogo, grupos, inventario=None, limite_cenarios=6, limite_tarefas=15):
    """Devolve (linhas por grupo, itens a conferir)."""
    diferencas = {d["id"]: d for d in catalogo["differences"]}
    requisitos = {r["id"]: r for r in catalogo["requirements"]}
    superficies = {s["id"]: s for s in catalogo["surfaces"]}
    itens = []
    destinos = defaultdict(list)
    linhas = []
    arquivos_do_grupo = {}
    for nome, grupo in grupos["grupos"].items():
        cenarios = set()
        arquivos = set()
        sem_requisito = 0
        for df in grupo["diferencas"]:
            destinos[df].append(nome)
            diferenca = diferencas.get(df)
            if diferenca is None:
                itens.append(f"DIFERENCA_INEXISTENTE {nome}: {df}")
                continue
            for req in diferenca["requirement_ids"]:
                cenarios.update(requisitos[req]["scenario_ids"])
            if not diferenca["requirement_ids"]:
                sem_requisito += 1
            for sf in diferenca["surface_ids"]:
                if superficies[sf].get("rota"):
                    arquivos.update(superficies[sf].get("arquivos", []))
        arquivos_do_grupo[nome] = arquivos
        # Diferença aberta sem requisito ganha um cenário funcional e um visual.
        total_cenarios = len(cenarios) + grupo.get("cenarios_a_criar", sem_requisito * 2)
        por_cenario = grupo["tarefas_cenario"]
        total = por_cenario + grupo.get("tarefas_base", 0)
        razao = total_cenarios / por_cenario if por_cenario else float("inf")
        linhas.append(f"{nome}: {len(grupo['diferencas'])} diferenças, {total_cenarios} cenários, "
                      f"{total} tarefas ({por_cenario} pelos cenários, {razao:.1f} por tarefa)")
        if razao > limite_cenarios:
            itens.append(f"CENARIOS_POR_TAREFA {nome}: {razao:.1f}, limite {limite_cenarios}")
        if total > limite_tarefas:
            itens.append(f"ACIMA_DO_LIMITE {nome}: {total} tarefas, limite {limite_tarefas}")
    for df in grupos.get("excecoes", []):
        destinos[df].append("exceção")
    for df in diferencas:
        if not destinos.get(df):
            itens.append(f"SEM_DESTINO {df}")
    for df, onde in destinos.items():
        if len(onde) > 1:
            itens.append(f"DOIS_DESTINOS {df}: {', '.join(onde)}")
    for a, b in grupos.get("pares_independentes", []):
        comuns = sorted(arquivos_do_grupo[a] & arquivos_do_grupo[b])
        if comuns:
            exemplos = ", ".join(comuns[:3])
            itens.append(f"PAR_NAO_INDEPENDENTE {a} e {b}: {len(comuns)} arquivos em comum, como {exemplos}")
    if inventario is not None and "bibliotecas" in grupos:
        for pacote in sorted(set(inventario["global"]) - set(grupos["bibliotecas"]) - set(grupos.get("bibliotecas_recusadas", []))):
            itens.append(f"BIBLIOTECA_SEM_DECISAO {pacote}")
    return linhas, itens


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogo", required=True)
    parser.add_argument("--grupos", required=True)
    parser.add_argument("--inventario")
    parser.add_argument("--limite-cenarios", type=float, default=6)
    parser.add_argument("--limite-tarefas", type=int, default=15)
    args = parser.parse_args(argv)
    try:
        catalogo = json.load(open(args.catalogo, encoding="utf-8"))
        grupos = json.load(open(args.grupos, encoding="utf-8"))
        inventario = json.load(open(args.inventario, encoding="utf-8")) if args.inventario else None
    except (OSError, ValueError) as erro:
        print(f"uso inválido: {erro}", file=sys.stderr)
        return SAIDA_USO
    linhas, itens = conferir(catalogo, grupos, inventario, args.limite_cenarios, args.limite_tarefas)
    print("\n".join(linhas))
    print(f"\nA conferir: {len(itens)}")
    print("\n".join(itens))
    return SAIDA_ITENS if itens else SAIDA_OK


if __name__ == "__main__":
    sys.exit(main())
