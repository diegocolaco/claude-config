#!/usr/bin/env python3
"""Segue o barril por nome para podar o fecho: quem importa { TagSelect } de @/components não recebe Footer.

uso: poda_barril.py <mapa.json>  -> lê <pasta>/fecho.json e grava <pasta>/fecho-podado.json; imprime bytes antes e depois.
"""
import json,re,sys,posixpath,collections
from pathlib import Path
import comum
import fecho as Fe
CFG=comum.carrega()
show=Fe.show;TODOS=set(Fe.TODOS)
EXT=('.ts','.tsx','.js','.jsx')
ALIAS=dict(visto=0,achou=0)
def res(de,mod):
    alias=mod.startswith('@/')
    if alias: b='src/'+mod[2:];ALIAS['visto']+=1
    elif mod.startswith('.'): b=posixpath.normpath(posixpath.join(posixpath.dirname(de),mod))
    else: return None
    for c in [b]+[b+e for e in EXT]+[b+'/index'+e for e in EXT]:
        if c in TODOS:
            if alias: ALIAS['achou']+=1
            return c
COM=re.compile(r"/\*.*?\*/|^\s*//.*?$",re.S|re.M)
IMPORT=re.compile(r"""import\s+(?:type\s+)?([^'";]*?)\s+from\s+['"]([^'"]+)['"];?""")
REEXP=re.compile(r"""export\s+(?:type\s+)?\{([^}]*)\}\s+from\s+['"]([^'"]+)['"];?""")
REEXPT=re.compile(r"""export\s+\*(?:\s+as\s+\w+)?\s+from\s+['"]([^'"]+)['"];?""")
EXPL=re.compile(r"""export\s+\{([^}]*)\};?""")
def nomes(t):
    o=[]
    for p in t.split(','):
        p=re.sub(r'^type\s+','',p.strip())
        if not p: continue
        m=re.match(r'(\S+)\s+as\s+(\S+)',p);o.append((m.group(1),m.group(2)) if m else (p,p))
    return o
def analisa(f,c={}):
    if f in c: return c[f]
    s=COM.sub('',show(f));rx={};est=[]
    for cl,mod in REEXP.findall(s):
        t=res(f,mod)
        if t:
            for la,ca in nomes(cl): rx[ca]=(t,la)
    for mod in REEXPT.findall(s):
        t=res(f,mod)
        if t: est.append(t)
    sem=REEXPT.sub('',REEXP.sub('',s))
    imp=[];loc={}
    for cl,mod in IMPORT.findall(sem):
        t=res(f,mod)
        if not t: continue
        m=re.search(r'\{([^}]*)\}',cl);pg=nomes(m.group(1)) if m else []
        fora=re.sub(r'\{[^}]*\}','',cl).strip(' ,')
        if fora: pg.append(('*' if fora.startswith('*') else 'default',fora.split()[-1]))
        for la,ca in pg: imp.append((t,la));loc[ca]=(t,la)
    for cl in EXPL.findall(sem):
        for la,ca in nomes(cl):
            if la in loc: rx[ca]=loc[la]
    resto=EXPL.sub('',IMPORT.sub('',sem))
    bar=bool(rx or est) and not re.sub(r'[\s;]','',resto)
    for a in re.findall(r"""import\(\s*['"]([^'"]+)['"]|^\s*import\s+['"]([^'"]+)['"]""",sem,re.M):
        t=res(f,a[0] or a[1])
        if t: imp.append((t,'*'))
    c[f]=dict(bar=bar,rx=rx,est=est,imp=imp);return c[f]
def fecho_nomes(ini):
    v=set();fila=[(f,None) for f in ini];vb=set()
    while fila:
        f,n=fila.pop()
        a=analisa(f)
        if a['bar'] and n is not None:
            if (f,n) in vb: continue
            vb.add((f,n));v.add(f)
            if n=='*':
                for ca,(t,la) in a['rx'].items(): fila.append((t,la))
                fila+=[(t,'*') for t in a['est']]
            elif n in a['rx']:
                t,la=a['rx'][n];fila.append((t,la))
            else: fila+=[(t,n) for t in a['est']]
        else:
            if f in v: continue
            v.add(f)
            fila+=[(t,la) for t,la in a['imp']]
    return v
if __name__=='__main__':
    if len(sys.argv)!=2: sys.exit('uso: poda_barril.py <mapa.json>')
    pasta=Path(CFG['pasta']);m=json.load(open(sys.argv[1]));fec=json.load(open(pasta/'fecho.json'))
    tb=ta=0;saida={}
    alcances={t['id']:fecho_nomes([t['arquivo']]+fec[t['id']].get('rota_pai',[])) for t in m['telas']}
    # alias que não resolve deixa só a própria tela no grafo, e o resto do código sairia do livro sem ninguém ver
    sem_alias=ALIAS['visto'] and not ALIAS['achou']
    if sem_alias: print("aviso: nenhum import com @/ resolve em src/ neste commit: poda desligada, o livro leva todo o fecho do mapa",file=sys.stderr)
    for t in m['telas']:
        r=fec[t['id']]
        base=set(r['base'])
        # css/imagem/estilo não aparecem no grafo de nomes: fica o que o grafo não descreve
        fora=[] if sem_alias else sorted(f for f in base if f not in alcances[t['id']] and f.endswith(EXT))
        ant=sum(len(show(f)) for f in base);dep=ant-sum(len(show(f)) for f in fora)
        tb+=ant;ta+=dep
        saida[t['id']]=dict(r,base=sorted(base-set(fora)),base_removida=fora)
        print(t['id'],'removidos',len(fora),'bytes',ant,'->',dep)
    json.dump(saida,open(pasta/'fecho-podado.json','w'),indent=0)
    if tb: print('TOTAL base',tb,'->',ta,'(%.0f%%)'%(100*ta/tb))
