#!/usr/bin/env python3
"""Valores que a tela mostra e nascem no build: `define` em config/config.ts resolvido contra package.json.

uso: constantes_build.py  -> JSON em uma linha: {tela:'TL-moldura', itens:[...]}
O que depende do ambiente do build fica NÃO VERIFICADO.
"""
import json,re,sys
import comum
CFG=comum.carrega()
show=lambda f:comum.show(CFG,f)
cfg=show('config/config.ts');its=[]
try: pk=json.loads(show('package.json') or '{}')
except json.JSONDecodeError: pk={}
# sem config/config.ts (projeto que não é Umi) ou sem package.json: fato NÃO VERIFICADO e aviso, sem derrubar
if not cfg:
    print('aviso: config/config.ts não existe neste commit; constantes de build NÃO VERIFICADO.',file=sys.stderr)
    its.append(dict(tipo='dado',texto='config/config.ts não existe neste commit: constantes definidas no build NÃO VERIFICADO.',fonte='config/config.ts'))
if not pk:
    print('aviso: package.json ausente ou ilegível; versões NÃO VERIFICADO.',file=sys.stderr)
    its.append(dict(tipo='dado',texto='package.json ausente ou ilegível neste commit: versões e campos NÃO VERIFICADO.',fonte='package.json'))
m=re.search(r'define:\s*\{(.*?)\n\s*\}',cfg,re.S)
if m:
    base=cfg.count('\n',0,m.start(1))+1
    for k,l in enumerate(m.group(1).splitlines()):
        d=re.match(r"\s*['\"]?([\w.]+)['\"]?\s*:\s*(.+?),?\s*$",l)
        if not d: continue
        nome,val=d.groups();fonte=f'config/config.ts:{base+k}'
        r=re.search(r"require\(['\"]\./\.\./package\.json['\"]\)\.(\w+)",val)
        if r: its.append(dict(tipo='dado',texto=f'{nome} = {pk.get(r.group(1))} (package.json, campo {r.group(1)}).',fonte=fonte+'; package.json'))
        else: its.append(dict(tipo='dado',texto=f'{nome} vem de {val} no build: valor NÃO VERIFICADO no código.',fonte=fonte))
if pk: its.append(dict(tipo='dado',texto=f'package.json repository = {pk.get("repository")}; quem lê esse campo precisa aceitar esse formato.',fonte='package.json'))
# versão muda o padrão de cada componente: quem reconstrói precisa saber qual olhar
deps=pk.get('dependencies',{})
if pk: its.append(dict(tipo='dado',texto='Versões declaradas em package.json: '+', '.join(f'{k} {v}' for k,v in deps.items())+'.',fonte='package.json'))
print(json.dumps(dict(tela='TL-moldura',itens=its),ensure_ascii=False))
