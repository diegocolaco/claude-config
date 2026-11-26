#!/usr/bin/env python3
"""Fatos mecânicos de idioma de uma tela: para cada chave i18n usada no fecho, o valor em pt-BR ou AUSENTE (cai no defaultMessage).
Conta também os literais não ASCII fixos no código, que não passam pelo locale.

uso: chaves_locale.py <TL-id> [<TL-id> ...]  (usa <pasta>/fecho.json; a pasta vem de FATOS_PASTA)"""
import json,re,sys
from pathlib import Path
import comum
from ledger import show
import fecho as Fe
F=json.load(open(Path(comum.carrega()['pasta'])/'fecho.json'))
PT=[x for x in Fe.TODOS if x.startswith('src/locales/pt-BR') and x.endswith('.ts')]
VAL={}
for a in PT:
    L=show(a).splitlines()
    for i,l in enumerate(L):
        m=re.match(r"\s*'([\w.\-]+)'\s*:\s*(.*)$",l)
        if m:
            v=m.group(2).strip()
            if not v and i+1<len(L): v=L[i+1].strip()
            VAL[m.group(1)]=v.rstrip(',').strip("'\"`")
CHAVE=re.compile(r"""\bid\s*[:=]\s*\{?\s*['"]([\w.\-]+)['"]""")
for tid in sys.argv[1:]:
    r=F[tid];usadas={};fixos=0
    for k in ['base','rota_pai']:
        for f in r.get(k,[]):
            if not f.startswith('src/') or f.startswith('src/locales'): continue
            s=show(f)
            for c in CHAVE.findall(s):
                if '.' in c: usadas.setdefault(c,f)
            fixos+=len(re.findall(r"""['">][^'"<>\n]*[^\x00-\x7f][^'"<>\n]*['"<]""",s))
    aus=sorted(c for c in usadas if c not in VAL)
    print(json.dumps(dict(tela=tid,chaves=len(usadas),ausentes_em_pt_br=aus,literais_nao_ascii_no_codigo=fixos,idioma=('fixo no código' if fixos and not usadas else ('misto' if fixos else 'locale'))),ensure_ascii=False))
