#!/usr/bin/env python3
"""Baixa o código publicado de uma biblioteca na versão travada do protótipo, para responder o que o código da tela não mostra.

uso: fonte_biblioteca.py <pasta-da-biblioteca> <pacote> [<pacote> ...]  -> uma linha por pacote: pacote versão caminho
A versão vem do package-lock.json do commit do protótipo (config da passada, em FATOS_PASTA). Só baixa e extrai: nada é instalado
nem executado. Pacote sem entrada no lock sai como NAO_TRAVADO, em vez de cair na versão mais nova.
"""
import json,os,sys,tarfile,urllib.request
import comum
CFG=comum.carrega()
texto=comum.show(CFG,'package-lock.json')
if not texto: comum.erro('package-lock.json não existe neste commit: sem ele não há versão travada para baixar')
try: lock=json.loads(texto)
except json.JSONDecodeError as e: comum.erro(f'package-lock.json ilegível: {e}')
pk=lock.get('packages',{})
if len(sys.argv)<3: sys.exit(__doc__)
pasta,*pacotes=sys.argv[1:]
os.makedirs(pasta,exist_ok=True)
for p in pacotes:
    e=pk.get(f'node_modules/{p}')
    if not e or not e.get('version'):
        print(p,'NAO_TRAVADO','-');continue
    v=e['version'];d=os.path.join(pasta,f"{p.replace('/','__')}@{v}")
    if not os.path.isdir(d):
        nome=p.split('/')[-1];url=e.get('resolved') or f'https://registry.npmjs.org/{p}/-/{nome}-{v}.tgz'
        tgz=d+'.tgz';urllib.request.urlretrieve(url,tgz);os.makedirs(d)
        with tarfile.open(tgz) as t: t.extractall(d,filter='data')
        os.remove(tgz)
    print(p,v,d)
