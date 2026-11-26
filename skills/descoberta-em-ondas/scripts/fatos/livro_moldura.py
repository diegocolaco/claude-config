#!/usr/bin/env python3
"""Livro da moldura: o que aparece em toda tela (app.tsx e o que ele usa de fato, barril seguido por nome). Lido uma vez só.

uso: livro_moldura.py <saida.txt> [--sem-globais]  (--sem-globais tira os arquivos que o inventário global antigo já leu)
"""
import sys
sys.argv,args=[sys.argv[0]],sys.argv[1:]
from ledger import show,blocos
import fecho as Fe,poda_barril as P
# ponto de partida: o app.tsx quando está na moldura; senão, os próprios arquivos dela
ini=[a for a in Fe.GLOBAIS if a=='src/app.tsx'] or list(Fe.GLOBAIS)
alc=P.fecho_nomes([a for a in ini if a in Fe.TODOS])
arqs=sorted(set(a for a in Fe.GLOBAIS if a in Fe.TODOS)|alc)
if '--sem-globais' in args: arqs=[a for a in arqs if a not in Fe.GLOBAIS]
o=[];n=0
for a in arqs:
    o.append(f'## {a}')
    for b in blocos(show(a),10):
        n+=1;o.append(f'[B{n}]');o+=[f'{i}: {l}' for i,l in b]
open(args[0],'w').write('\n'.join(o)+'\n');print('blocos',n,'bytes',len('\n'.join(o).encode()),arqs)
