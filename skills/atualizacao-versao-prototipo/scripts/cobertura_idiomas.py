"""Idiomas fora da referência: compara cada um com o idioma de referência, por script, sem agente.

Só diz o que falta, sobra ou continua igual à referência; não julga a qualidade da tradução. Lê só do git, na candidata.
Grava os achados da `U-IDIOMAS` no formato das demais unidades, para seguirem pela mesma conferência e integração.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

import cobertura_conferir as conferir  # noqa: E402
import cobertura_cruzar as cruzar  # noqa: E402
import cobertura_mapa as cm  # noqa: E402

EXEMPLOS = 10


def _valores(leitor, arquivos):
    valores = {}
    for caminho in arquivos:
        valores.update(cruzar._ler_locale(caminho, leitor.texto(caminho) or ""))
    return valores


def _arquivos_por_idioma(leitor):
    por_idioma = {}
    for caminho in sorted(leitor.caminhos):
        idioma = conferir.idioma_do_caminho(caminho)
        if idioma and caminho.endswith((".ts", ".js", ".json")):
            por_idioma.setdefault(idioma, []).append(caminho)
    return por_idioma


def _nome_do_idioma(arquivo):
    """Grafia do idioma como está no caminho (`en-US`), para os textos e o `ref`."""
    return conferir.IDIOMA_NO_CAMINHO.search(arquivo).group(1).replace("_", "-")


def _agora(nome, referencia, chaves, faltando, a_mais, iguais):
    partes = [f"Idioma {nome} com {chaves} chaves; comparado com {referencia}: {len(faltando)} faltando, "
              f"{len(a_mais)} a mais, {len(iguais)} com o mesmo texto da referência (provável sem tradução)."]
    for rotulo, lista in (("Faltando", faltando), ("A mais", a_mais), ("Iguais", iguais)):
        if lista:
            partes.append(f"{rotulo}, até {EXEMPLOS}: {', '.join(lista[:EXEMPLOS])}.")
    return " ".join(partes)


def comparar(repo, mapa, unidades):
    """Achados da `U-IDIOMAS`. Referência sem chave legível vira `status: FALHA`, porque nada foi comparado."""
    unidade = conferir._unidade_por_id(unidades, conferir.UNIDADE_IDIOMAS)
    referencia = unidade.get("referencia")
    revisao = mapa.get("candidata_sha") or mapa.get("candidata")
    if not referencia or not revisao:
        raise ValueError("A unidade precisa de `referencia` e o mapa, de `candidata`.")
    leitor = cm._Leitor(repo, revisao)
    arquivos = _arquivos_por_idioma(leitor)
    base = _valores(leitor, arquivos.get(referencia.lower().replace("_", "-"), []))
    do_mapa = {t["id"]: t["arquivo"] for t in mapa.get("trechos", [])}

    por_idioma = {}
    for trecho in conferir._textos(unidade.get("trechos")):
        if trecho in do_mapa:
            por_idioma.setdefault(_nome_do_idioma(do_mapa[trecho]), []).append(trecho)

    trechos, propostas = {}, []
    for nome, ids in sorted(por_idioma.items()):
        valores = _valores(leitor, arquivos.get(nome.lower(), []))
        faltando = sorted(set(base) - set(valores))
        a_mais = sorted(set(valores) - set(base))
        iguais = sorted(k for k in set(base) & set(valores) if base[k] == valores[k])
        ref = f"P-{nome}"
        propostas.append({
            "ref": ref, "tela": "TODAS", "regiao": f"idioma {nome}", "idioma": nome,
            "antes": "Não conferido pelo script: o integrador lê os idiomas do produto.",
            "agora": _agora(nome, referencia, len(valores), faltando, a_mais, iguais),
            "fonte_prototipo": ", ".join(arquivos.get(nome.lower(), [])) or f"{nome}: sem arquivo na candidata",
            "fonte_produto": "A conferir pelo integrador.",
            "trechos": sorted(ids), "chaves": len(valores),
            "faltando": faltando, "a_mais": a_mais, "iguais_a_referencia": iguais,
        })
        trechos.update({t: {"destino": conferir.DIFERENCA, "proposta": ref} for t in ids})
    return {"unidade": conferir.UNIDADE_IDIOMAS, "status": "OK" if base else "FALHA", "referencia": referencia,
            "trechos": trechos, "propostas": propostas}
