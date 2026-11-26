#!/usr/bin/env python3
"""Escreve, numa cópia do catálogo, os fatos com destino decidido; prova que a última etapa funciona e que o validador aceita.

uso: integra_catalogo.py <catalogo.json> <list-tela.json> <saida-destino.json> <saida.json> [--ao-lado <arquivo>]
Sem --ao-lado: fato entra em scenario.definition.fatos[]. Com --ao-lado: o catálogo não muda e o fato vai para um arquivo com o id do cenário.
Cenário novo: criado na região nova com estado próprio, e a evidência aponta para a fonte do fato; o integrador é o único que escreve.
Idempotente: fato já presente (mesmo texto e fonte) não entra de novo.
Cenário em região nova entra no `scenario_ids` do primeiro requisito (menor número) de uma diferença da superfície, sem `disposition`.
Sem esse requisito o cenário é gravado mesmo assim e listado: imprime `CENARIO_SEM_DONO: <id> (<superficie>)` e sai 11.
Com --ao-lado, fato de mock, worker, padrão de biblioteca ou NÃO USADO que iria para `NOVO:` não cria região: fica na chave `sem_cenario` do arquivo.
Toda ligação automática sai numa linha `CENARIO_LIGADO <cenário> -> <requisito>`, porque o requisito foi escolhido só pela superfície.
"""
import json,os,sys,re,hashlib
import comum
args=[a for a in sys.argv[1:] if a!='--aceita-sem-fonte'];lado=None
if '--ao-lado' in args:
    i=args.index('--ao-lado');lado=args[i+1];del args[i:i+2]
cat_f,lista_f,dest_f,saida=args
c=json.load(open(cat_f));L=json.load(open(lista_f));D=json.load(open(dest_f))
tela=L['tela'];surf='SF-'+tela
cen={s['id']:s for s in c['scenarios']}
itens={str(x['i']):x for x in L['itens']}
ids=lambda col,pref:max([int(m.group(1)) for r in c[col] if (m:=re.match(pref+r'-(\d+)$',r['id']))]+[0])
faltam=[k for k in itens if k not in D];inval=[k for k,v in D.items() if not (v in cen or v.startswith('NOVO:'))]
if faltam or inval:
    print('ERRO: destino incompleto',dict(sem_destino=faltam[:5],invalido=inval[:5]));sys.exit(1)
# fato sem fonte vira evidência vazia, que o validador aceita e ninguém consegue conferir: recusa aqui
sem=[k for k,x in itens.items() if not (x.get('f') or x.get('fonte'))]
if sem and '--aceita-sem-fonte' not in sys.argv:
    print('ERRO: fato sem fonte',sem[:5],'de',len(sem));sys.exit(1)
# rodar de novo não pode duplicar: região nova já criada é reencontrada pelo rótulo dentro da superfície
novos={r['label']:next((x['id'] for x in c['scenarios'] if x['region_id']==r['id']),None) for r in c['regions'] if r['surface_id']==surf and r.get('label')}
cont=dict(existente=0,novo=0,repetido=0);externo={};criadas=0;usados=[];guardados=0
def dono():
    """Primeiro requisito (menor número) ligado por difference_ids a uma diferença da superfície e sem disposition."""
    difs={d['id']:d for d in c.get('differences',[])}
    achados=[]
    for r in c.get('requirements',[]):
        for di in r.get('difference_ids',[]):
            d=difs.get(di)
            if d and not d.get('disposition') and (d.get('surface_id')==surf or surf in d.get('surface_ids',[])): achados.append(r);break
    num=lambda r:int(m.group(0)) if (m:=re.search(r'\d+',r['id'])) else 0
    return min(achados,key=num) if achados else None
VER=c['reference']['version']
def fato(x): return dict(tipo=x.get('tipo'),texto=x['x'] if 'x' in x else x['texto'],fonte=x.get('f') or x.get('fonte'),**({'imprecisao':x['imprecisao']} if x.get('imprecisao') else {}))
for k,x in itens.items():
    d=D[k];alvo=d
    if lado is not None and d.startswith('NOVO:') and comum.sem_cenario(fato(x)['texto'],fato(x)['fonte']):
        externo.setdefault('sem_cenario',[]).append(fato(x));guardados+=1;continue
    if d.startswith('NOVO:'):
        rot=d[5:].strip()
        if not novos.get(rot):
            criadas+=1
            n=ids('regions','RG')+1;ev=ids('evidence','EV')+1;st=ids('states','ST')+1;sc=ids('scenarios','SC')+1
            ev_id=f'EV-{ev}';rg=f'RG-{n}';es=f'ST-{st}';sid=f'SC-{sc}'
            fonte=fato(x)['fonte'] or ''
            c['evidence'].append(dict(id=ev_id,kind='src',locator=f'prototipo@{VER}:{fonte}'))
            c['regions'].append(dict(id=rg,surface_id=surf,label=rot,discovery_status='INVESTIGADO',provenance_refs=[ev_id]))
            c['states'].append(dict(id=es,region_id=rg,discovery_status='INVESTIGADO',provenance_refs=[ev_id]))
            c['scenarios'].append(dict(id=sid,region_id=rg,state_id=es,dimensions=['visual' if x.get('tipo')=='aparencia' else 'functional'],definition=dict(agora=(f"Fatos em `fatos/{os.path.basename(lado)}`, ao lado do catálogo." if lado else ''),fatos=[])))
            cen[sid]=c['scenarios'][-1];novos[rot]=sid
        alvo=novos[rot];cont['novo']+=1
        if alvo not in usados: usados.append(alvo)
    else: cont['existente']+=1
    f=fato(x)
    if lado is not None:
        externo.setdefault(alvo,[]).append(f);continue
    dfn=cen[alvo].setdefault('definition',{});lista=dfn.setdefault('fatos',[])
    if any(y['texto']==f['texto'] and y.get('fonte')==f['fonte'] for y in lista): cont['repetido']+=1;continue
    lista.append(f)
sem_dono=[]
for sid in usados:
    r=next((q for q in c.get('requirements',[]) if sid in q.get('scenario_ids',[])),None) or dono()
    if r is None: sem_dono.append(sid);continue
    if sid not in r.setdefault('scenario_ids',[]): r['scenario_ids'].append(sid)
    print(f"CENARIO_LIGADO {sid} -> {r['id']}")
if lado: json.dump(externo,open(lado,'w'),ensure_ascii=False,indent=1)
json.dump(c,open(saida,'w'),ensure_ascii=False,indent=2)
print(tela,cont,'regiões novas',criadas,'sem cenário',guardados,'bytes',len(json.dumps(c,ensure_ascii=False)))
for sid in sem_dono: print(f'CENARIO_SEM_DONO: {sid} ({surf})')
sys.exit(11 if sem_dono else 0)
