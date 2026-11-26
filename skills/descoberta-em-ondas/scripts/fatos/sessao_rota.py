#!/usr/bin/env python3
"""Regra de sessão e perfil por rota: a tela sozinha não mostra isso, e o agente que só lê a tela afirma «pública» por engano.

uso: sessao_rota.py <mapa.json>  (pasta em FATOS_PASTA) -> JSON por linha: {tela, rota, itens:[{tipo, texto, fonte}]}
Lê a lista de exceções em src/app.tsx e o `access` em config/routes.ts. Se não achar o padrão, avisa em vez de adivinhar.
"""
import json,re,sys
import comum
CFG=comum.carrega()
show=lambda f:comum.show(CFG,f)
app=show('src/app.tsx');rotas=show('config/routes.ts')
# projeto que não é Umi não tem esses arquivos: o fato sai NÃO VERIFICADO e o aviso vai para a saída de erro
for _a,_t in (('src/app.tsx',app),('config/routes.ts',rotas)):
    if not _t: print(f'aviso: {_a} não existe neste commit; fatos de sessão e perfil saem NÃO VERIFICADO.',file=sys.stderr)
excecoes=[];lin=None
for k,l in enumerate(app.splitlines(),1):
    if re.search(r'PATHS?|paths?\s*=|whiteList|includes\(',l) and re.findall(r"['\"](/user/[\w-]+)['\"]",l):
        excecoes+=re.findall(r"['\"](/user/[\w-]+)['\"]",l);lin=lin or k
if not excecoes:
    m=re.search(r"\[([^\]]*/user/[^\]]*)\]",app,re.S)
    if m: excecoes=re.findall(r"['\"](/[\w/-]+)['\"]",m.group(1));lin=app.count('\n',0,m.start())+1
destino=re.search(r"loginPath\s*=\s*['\"]([^'\"]+)['\"]",app)
destino=destino.group(1) if destino else '/user/login'
m=re.search(r"!\s*\[([^\]]*)\]\s*\.includes",app,re.S)
if m:
    # a lista real: valores literais e identificadores resolvidos no próprio arquivo
    excecoes=[]
    lin=app.count('\n',0,m.start())+1
    for tok in m.group(1).split(','):
        tok=tok.strip()
        if not tok: continue
        q=re.match(r"['\"]([^'\"]+)['\"]",tok)
        if q: excecoes.append(q.group(1));continue
        v=re.search(r"\b"+re.escape(tok)+r"\s*=\s*['\"]([^'\"]+)['\"]",app)
        excecoes.append(v.group(1) if v else f'{tok} (valor não resolvido)')
excecoes=sorted(set(excecoes))
# access por path: bloco do `path` até a linha seguinte de path, sem descer para filhos
acesso={};atual=None
for k,l in enumerate(rotas.splitlines(),1):
    m=re.search(r"path:\s*'([^']+)'",l)
    if m: atual=m.group(1)
    a=re.search(r"access:\s*'([^']+)'",l)
    if a and atual: acesso[atual]=(a.group(1),k)
def perfil(rota):
    for p,(a,k) in acesso.items():
        if rota==p or (p!='/' and rota.startswith(p.rstrip('/')+'/')): return a,k
    return None,None
for t in json.load(open(sys.argv[1]))['telas']:
    r=t['rota'];its=[]
    if not app:
        its.append(dict(tipo='comportamento',texto='src/app.tsx não existe neste commit: regra de sessão NÃO VERIFICADO.',fonte='src/app.tsx'))
    elif not excecoes:
        its.append(dict(tipo='comportamento',texto='Lista de rotas sem sessão não encontrada em src/app.tsx: regra de sessão NÃO VERIFICADA.',fonte='src/app.tsx'))
    elif r in excecoes:
        its.append(dict(tipo='comportamento',texto=f'{r} está na lista de rotas que não buscam usuário na abertura ({", ".join(excecoes)}): abre sem sessão.',fonte=f'src/app.tsx:{lin}'))
    else:
        its.append(dict(tipo='comportamento',texto=f'{r} não está na lista de exceções ({", ".join(excecoes)}): a abertura busca o usuário e, sem sessão, redireciona para {destino}; a tela só aparece com sessão válida.',fonte=f'src/app.tsx:{lin}'))
    a,k=perfil(r)
    if not rotas: its.append(dict(tipo='comportamento',texto=f'config/routes.ts não existe neste commit: perfil de acesso de {r} NÃO VERIFICADO.',fonte='config/routes.ts'))
    elif a: its.append(dict(tipo='comportamento',texto=f'{r} exige o perfil de acesso {a} (ver src/access.ts); sem ele o layout mostra a página de não autorizado.',fonte=f'config/routes.ts:{k}'))
    else: its.append(dict(tipo='comportamento',texto=f'{r} não declara `access`: sem restrição de perfil.',fonte='config/routes.ts'))
    print(json.dumps(dict(tela=t['id'],rota=r,itens=its),ensure_ascii=False))
