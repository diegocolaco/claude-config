#!/usr/bin/env python3
"""Livro-razão dos arquivos globais do projeto: lido uma vez só, e os fatos valem para todas as telas.

uso: livro_global.py <saida.txt>
"""
import sys
from ledger import show,blocos
import fecho as Fe
o=[];n=0
for a in Fe.GLOBAIS:
    if a not in Fe.TODOS: continue
    o.append(f'## {a}')
    for b in blocos(show(a),10):
        n+=1;o.append(f'[B{n}]');o+=[f'{i}: {l}' for i,l in b]
open(sys.argv[1],'w').write('\n'.join(o)+'\n');print('blocos',n,'bytes',len('\n'.join(o).encode()))
