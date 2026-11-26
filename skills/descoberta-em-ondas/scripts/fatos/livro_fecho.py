#!/usr/bin/env python3
"""Gera o livro-razão de uma tela com o fecho completo: base do mapa, mock, rota-pai e recortes de locale e rotas.

uso: livro_fecho.py <tela> <saida.txt> <mapa.json>  (usa <pasta>/fecho-podado.json; a pasta vem de FATOS_PASTA)
Recorte de locale: só as chaves que a tela usa. Recorte de rotas: só as entradas cujo path é prefixo da rota.
"""
import json,re,sys
import comum
from ledger import show,blocos
import fecho as Fe
CFG=comum.carrega()
KEY=Fe.KEY
GRANDE=40000
def corte_locale(arq,chaves):
    L=show(arq).splitlines();saida=[]
    for i,l in enumerate(L,1):
        if any(("'"+k+"'") in l for k in chaves):
            saida.append((i,l[:400]))
            # valor longo vai na linha de baixo: a chave sozinha não diz o texto
            if l.rstrip().endswith(':') and i<len(L): saida.append((i+1,L[i][:400]))
    return saida
def corte_rotas(rota):
    L=show('config/routes.ts').splitlines();saida=[]
    segs=rota.strip('/').split('/');prefixos={'/'+'/'.join(segs[:i+1]) for i in range(len(segs))}
    for i,l in enumerate(L):
        m=re.search(r"path:\s*'([^']+)'",l)
        if m and m.group(1).rstrip('/') in prefixos:
            ini=max(0,i-2);fim=min(len(L),i+6)
            # para na próxima rota: a linha do vizinho viraria fato desta tela
            for k in range(i+1,fim):
                if re.search(r"path:\s*'",L[k]) or L[k].strip()=='{': fim=k;break
            saida+=[(k+1,L[k][:400]) for k in range(ini,fim) if 'routes:' not in L[k]]
    return sorted(set(saida))
def gera(tid,saida,tam=10):
    r=json.load(open(CFG['fecho']))[tid]
    arqs=[]
    for k in ['base','rota_pai','conteudo','mock_vizinho','mock_api','mock_import']:
        for f in r.get(k,[]):
            if f not in arqs and f in Fe.TODOS: arqs.append(f)
    chaves=set()
    for f in arqs: chaves|=set(KEY.findall(show(f)))
    # nome da tela e dos grupos no menu: a chave vem da rota, não do código
    t=[x for x in json.load(open(sys.argv[3]))['telas'] if x['id']==tid][0]
    segs=t['rota'].strip('/').split('/')
    chaves|={'menu.'+'.'.join(segs[:i+1]) for i in range(len(segs))}
    o=[];n=0
    for a in arqs:
        txt=show(a)
        if len(txt)>GRANDE:
            # dado massivo (mapa, geojson): vale a forma, não cada ponto. O agente recebe início, fim e a contagem.
            L=txt.splitlines()
            o.append(f'## {a} (dado grande: {len(L)} linhas, {len(txt)} bytes; só início e fim)')
            n+=1;o.append(f'[B{n}]');o+=[f'{i}: {l[:200]}' for i,l in enumerate(L[:30],1)]
            n+=1;o.append(f'[B{n}]');o+=[f'{i}: {l[:200]}' for i,l in list(enumerate(L,1))[-10:]]
            continue
        o.append(f'## {a}')
        for b in blocos(txt,tam):
            n+=1;o.append(f'[B{n}]');o+=[f'{i}: {l}' for i,l in b]
    for a in r.get('locale',[]):
        c=corte_locale(a,chaves)
        if c:
            o.append(f'## {a} (só as chaves que a tela usa)')
            for k in range(0,len(c),tam):
                n+=1;o.append(f'[B{n}]');o+=[f'{i}: {l}' for i,l in c[k:k+tam]]
    return n,o
if __name__=='__main__':
    tid,saida=sys.argv[1:3]
    t=[x for x in json.load(open(sys.argv[3]))['telas'] if x['id']==tid][0]
    n,o=gera(tid,saida)
    c=corte_rotas(t['rota'])
    if c:
        o.append('## config/routes.ts (só as rotas desta tela)');n+=1;o.append(f'[B{n}]');o+=[f'{i}: {l}' for i,l in c]
    open(saida,'w').write('\n'.join(o)+'\n');print(tid,'blocos',n,'bytes',len('\n'.join(o).encode()))
