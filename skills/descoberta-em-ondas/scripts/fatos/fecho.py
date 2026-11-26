#!/usr/bin/env python3
"""Fecho de arquivos de uma tela: o mapa só segue imports; aqui entram também mock, rota-pai, locale e os globais.

uso: fecho.py <mapa.json>  -> grava <pasta>/fecho.json (a pasta vem de FATOS_PASTA)
Só lê o protótipo por git.
"""
import json, re, sys, collections, posixpath
from pathlib import Path
import comum
CFG = comum.carrega()
TODOS = comum.todos(CFG)
def show(f): return comum.show(CFG, f)
GLOBAIS = CFG['moldura']
LOCALE = [f for f in TODOS if f.startswith('src/locales/pt-BR')]
MOCKS = [f for f in TODOS if f.startswith('mock/') or f.startswith('cloudflare-worker/src/routes/')]
API = re.compile(r"""['"`]((?:/api)?/[\w/:.-]{3,})['"`]""")
KEY = re.compile(r"""['"]((?:pages|menu|component|app|navBar|settings|network|form|layout)\.[\w.-]+)['"]""")
IMP = re.compile(r"""from\s+['"](\.[^'"]+)['"]""")
def rotas_pai(rota):
    """Componentes de rotas-pai: path é prefixo da rota da tela e tem `component`."""
    t = show('config/routes.ts'); pares = re.findall(r"path:\s*'([^']+)'[^{}]*?component:\s*'([^']+)'", t, re.S)
    saida = []
    for p, c in pares:
        if p != rota and rota.startswith(p.rstrip('/') + '/'):
            b = 'src/pages/' + c.lstrip('./')
            for suf in ['/index.tsx', '.tsx', '/index.ts', '.ts']:
                if b + suf in TODOS: saida.append(b + suf); break
    return saida
# conteúdo importado que vira texto na tela: markdown, json, csv. O mapa só segue código.
CONT = re.compile(r"""from\s+['"]([^'"]+\.(?:md|mdx|json|txt|csv)(?:\?raw)?)['"]""")
def conteudo(f):
    out = set()
    for m in CONT.findall(show(f)):
        m = m.split('?')[0]
        if m.startswith('@root/'): c = m[6:]
        elif m.startswith('@/'): c = 'src/' + m[2:]
        elif m.startswith('.'): c = posixpath.normpath(posixpath.join(posixpath.dirname(f), m))
        else: continue
        # package.json só serve para a versão, e o resto é ruído
        if c in TODOS and c != 'package.json': out.add(c)
    return out
def resolve(base, rel):
    alvo = posixpath.normpath(posixpath.join(posixpath.dirname(base), rel))
    for suf in ['', '.ts', '.tsx', '/index.ts', '/index.tsx']:
        if alvo + suf in TODOS: return alvo + suf
def fecha_imports(fs):
    fila = list(fs); vistos = set(fs)
    while fila:
        f = fila.pop()
        for rel in IMP.findall(show(f)):
            r = resolve(f, rel)
            if r and r not in vistos: vistos.add(r); fila.append(r)
    return vistos
def fecho(t):
    base = set(t['dependencias']) | {t['arquivo']}
    novo = collections.defaultdict(set)
    pais = rotas_pai(t['rota'])
    for p in pais: novo['rota_pai'].add(p)
    base2 = base | set(pais)
    for f in sorted(base2): novo['conteudo'] |= conteudo(f)
    for f in sorted(base2):
        d = posixpath.dirname(f)
        for m in (d + '/_mock.ts',):
            if m in TODOS: novo['mock_vizinho'].add(m)
    apis = set()
    for f in base2:
        if f.startswith('src/services/'): continue
        apis |= set(API.findall(show(f)))
    # serviço compartilhado: só os endpoints das funções que a tela usa de fato
    usado = '\n'.join(show(f) for f in base2 if not f.startswith('src/services/'))
    for f in base2:
        if not f.startswith('src/services/'): continue
        tx = show(f)
        for m in re.finditer(r'export\s+(?:async\s+)?function\s+(\w+)[\s\S]*?(?=\nexport\s|\Z)', tx):
            if re.search(r'\b' + m.group(1) + r'\b', usado): apis |= set(API.findall(m.group(0)))
    apis = {a for a in apis if a.startswith('/api/') or a.count("/")>=2}
    for m in MOCKS:
        tx = show(m)
        if any(a.replace('/api', '') in tx for a in apis): novo['mock_api'].add(m)
    mk = fecha_imports(novo['mock_vizinho'] | novo['mock_api'])
    novo['mock_import'] = mk - novo['mock_vizinho'] - novo['mock_api']
    chaves = set()
    for f in base2: chaves |= set(KEY.findall(show(f)))
    chaves.add('menu.' + t['rota'].strip('/').replace('/', '.'))
    for l in LOCALE:
        tx = show(l)
        if any(("'" + k + "'") in tx for k in chaves): novo['locale'].add(l)
    novo['rotas'].add('config/routes.ts')
    return base, {k: sorted(v) for k, v in novo.items()}
def calcula(mapa):
    res = {}
    for t in mapa['telas']:
        b, n = fecho(t); res[t['id']] = dict(base=sorted(b), **n)
    return res
if __name__ == '__main__':
    if len(sys.argv) != 2: sys.exit('uso: fecho.py <mapa.json>')
    m = json.load(open(sys.argv[1]))
    res = calcula(m)
    json.dump(res, open(Path(CFG['pasta']) / 'fecho.json', 'w'), indent=0)
    tok = lambda fs: sum(len(show(f)) // 4 for f in fs)
    if res: print('tokens por tela: base', sum(tok(r['base']) for r in res.values()) // len(res), 'com fecho', sum(tok(set(sum((v for k, v in r.items()), []))) for r in res.values()) // len(res))
