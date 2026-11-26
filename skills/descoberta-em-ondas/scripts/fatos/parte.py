#!/usr/bin/env python3
"""Divide um livro-razão em partes que cabem num agente, sem cortar bloco, repetindo o cabeçalho do arquivo.

uso: parte.py <livro.txt> <pasta> [max_bytes=20000]  -> <pasta>/<nome>.pN.txt
"""
import os,re,sys
ent,pasta=sys.argv[1:3];mx=int(sys.argv[3]) if len(sys.argv)>3 else 20000
os.makedirs(pasta,exist_ok=True)
nome=os.path.basename(ent).rsplit('.',1)[0]
blocos=[];arq='';cur=None
for l in open(ent,encoding='utf-8'):
    if l.startswith('## '): arq=l;continue
    if re.match(r'\[B\d+\]$',l.strip()):
        cur={'arq':arq,'linhas':[l]};blocos.append(cur);continue
    if cur: cur['linhas'].append(l)
partes=[[]];tam=0
for b in blocos:
    n=sum(len(x.encode()) for x in b['linhas'])
    if tam+n>mx and partes[-1]: partes.append([]);tam=0
    partes[-1].append(b);tam+=n
for k,p in enumerate(partes,1):
    o=[];ult=None
    for b in p:
        if b['arq']!=ult: o.append(b['arq']);ult=b['arq']
        o+=b['linhas']
    open(f'{pasta}/{nome}.p{k}.txt','w',encoding='utf-8').write(''.join(o))
print(nome,'blocos',len(blocos),'partes',len(partes),[sum(1 for _ in p) for p in partes])
