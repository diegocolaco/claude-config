#!/usr/bin/env python3
"""Livro-razão de uma tela: todo trecho com efeito do código ganha um ID que precisa de resposta.

gera:    ledger.py gera <entrada TL.json> <saida.txt> [--tam 10]
confere: ledger.py confere <saida.txt> <respostas.json>   (sai 1 se faltar bloco, 2 se a resposta não for JSON)
Só lê o protótipo por `git show`. Respostas: [{"bloco":"B1","status":"...", ...}]
"""
import json, re, sys, collections
import comum
RUIDO = re.compile(r"^\s*(import\b.*|//.*|/\*.*|\*.*|\*/|\}\s*from\b.*|export\s+\*.*)?$")
FECHA = re.compile(r"^\s*(?:[\}\)\]]|/>)[\s;,\)\]\}]*$|^\s*</[\w.]*>[\s;,\)\]\}]*$")
def show(a):
    return comum.show(comum.carrega(), a)
def blocos(texto, tam):
    atual = []; n = 0
    for i, l in enumerate(texto.splitlines(), 1):
        if RUIDO.match(l) or FECHA.match(l):
            if atual and len(atual) >= tam: yield atual; atual = []
            continue
        atual.append((i, l[:400]))
        if len(atual) >= tam * 2: yield atual; atual = []
    if atual: yield atual
def gera(ent, saida, tam=10):
    d = json.load(open(ent)); k = 0; o = []
    for a in d['arquivos']:
        t = show(a)
        if not t: o.append(f'## {a} (vazio ou ausente)'); continue
        o.append(f'## {a}')
        for b in blocos(t, tam):
            k += 1; o.append(f'[B{k}]')
            o += [f'{i}: {l}' for i, l in b]
    open(saida, 'w').write('\n'.join(o) + '\n')
    return k
def confere(lg, resp):
    ids = set(re.findall(r'^\[(B\d+)\]$', open(lg).read(), re.M))
    try:
        r = json.load(open(resp))
        vistos = collections.Counter(x['bloco'] for x in r)
    except (json.JSONDecodeError, TypeError, KeyError):
        print(f'{resp} não é uma lista de respostas com `bloco`'); return 2
    faltam = sorted(ids - set(vistos), key=lambda s: int(s[1:]))
    print('blocos', len(ids), 'respondidos', len(ids & set(vistos)), 'faltam', faltam[:40], 'status', collections.Counter(x.get('status') for x in r))
    return 1 if faltam else 0
if __name__ == '__main__':
    if len(sys.argv) < 4 or sys.argv[1] not in ('gera', 'confere'): sys.exit(__doc__)
    if sys.argv[1] == 'gera': print(gera(sys.argv[2], sys.argv[3]))
    else: sys.exit(confere(sys.argv[2], sys.argv[3]))
