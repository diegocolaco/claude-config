#!/usr/bin/env python3
"""Raio de alcance: dado um arquivo que vai mudar, lista quem o usa, direta ou indiretamente, e em quais telas ele aparece.

uso: raio_alcance.py <repo> <ref> <arquivo> [<arquivo> ...] [--src apps/web/src] [--alias @=src] [--rotas config/routes.ts]
Lê só o git, nada de build. Resolve import relativo e alias e segue o nome através de barril (arquivo que só reexporta):
quem importa `{ Footer }` de `@/components` é consumidor de Footer, e quem importa `{ TagSelect }` do mesmo barril não é.
Não vê import dinâmico por variável nem CSS global: avisa quando há, porque o resultado é piso, não teto.
"""
import re,subprocess,sys,json,posixpath,collections
args=sys.argv[1:]
def sai(msg):
    print(msg,file=sys.stderr);sys.exit(2)
def opt(n,d=None):
    if n in args:
        i=args.index(n)
        if i+1>=len(args): sai(f'{n} sem valor')
        v=args[i+1];del args[i:i+2];return v
    return d
SRC=opt('--src','src').rstrip('/');ALIAS=opt('--alias','@='+SRC);ROTAS=opt('--rotas','config/routes.ts')
if ALIAS.count('=')!=1: sai(f'--alias espera <prefixo>=<pasta>, e veio {ALIAS}')
if len(args)<3: sai(__doc__)
repo,ref,*alvos=args
g=lambda *a:subprocess.run(['git','-C',repo,*a],capture_output=True,text=True,errors='replace').stdout
_ls=subprocess.run(['git','-C',repo,'ls-tree','-r','--name-only',ref],capture_output=True,text=True,errors='replace')
if _ls.returncode: sai(f'não consegui ler {ref} em {repo}: {_ls.stderr.strip()[-200:]}')
TODOS=_ls.stdout.splitlines()
for _a in alvos:
    if _a not in TODOS: sai(f'{_a} não existe em {ref}')
EXT=('.ts','.tsx','.js','.jsx','.mjs','.less','.css')
COD=[f for f in TODOS if f.startswith(SRC+'/') and f.endswith(EXT)]
if not COD: sai(f'nenhum código em {SRC}/ de {ref}: confira --src')
SET=set(TODOS);al,alp=[x.rstrip('/') for x in ALIAS.split('=')];alias_visto=[];alias_achou=[]
def res(de,mod):
    alias=mod.startswith(al+'/')
    if alias: b=alp+mod[len(al):];alias_visto.append(de)
    elif mod.startswith('.'): b=posixpath.normpath(posixpath.join(posixpath.dirname(de),mod))
    else: return None
    for c in [b]+[b+e for e in EXT]+[b+'/index'+e for e in EXT]:
        if c in SET:
            if alias: alias_achou.append(de)
            return c
    return None
COMENT=re.compile(r"/\*.*?\*/|^\s*//.*?$",re.S|re.M)
IMPORT=re.compile(r"""import\s+(type\s+)?([^'";]*?)\s+from\s+['"]([^'"]+)['"][;]?""")
REEXP=re.compile(r"""export\s+(type\s+)?\{([^}]*)\}\s+from\s+['"]([^'"]+)['"][;]?""")
REEXP_T=re.compile(r"""export\s+\*(?:\s+as\s+(\w+))?\s+from\s+['"]([^'"]+)['"][;]?""")
EXP_LOCAL=re.compile(r"""export\s+\{([^}]*)\}[;]?""")
OUTROS=re.compile(r"""import\s*\(\s*['"]([^'"]+)['"]|require\(\s*['"]([^'"]+)['"]|^\s*import\s+['"]([^'"]+)['"]""",re.M)
def nomes(txt):
    """{ a, b as c } -> [(a,a),(b,c)]; o primeiro é o nome de lá, o segundo o de cá."""
    out=[]
    for p in txt.split(','):
        p=re.sub(r'^type\s+','',p.strip())
        if not p: continue
        m=re.match(r'(\S+)\s+as\s+(\S+)',p)
        out.append((m.group(1),m.group(2)) if m else (p,p))
    return out
# usos[arquivo] = (quem usa, nome usado, ou '*' quando pega tudo)
usos=collections.defaultdict(list)
# reexporta[barril] = (arquivo de origem, nome lá, nome aqui); '*' repassa tudo
reexporta=collections.defaultdict(list)
barril=set();din=[]
for f in COD:
    bruto=g('show',f'{ref}:{f}')
    s=COMENT.sub('',bruto)
    locais={}
    # reexportação primeiro, para o IMPORT não pegar o `from` dela por engano
    for tipo,cl,mod in REEXP.findall(s):
        t=res(f,mod)
        if t:
            for la,ca in nomes(cl):
                usos[t].append((f,la));reexporta[f].append((t,la,ca))
    for ns,mod in REEXP_T.findall(s):
        t=res(f,mod)
        if t:
            usos[t].append((f,'*'));reexporta[f].append((t,'*',ns or '*'))
    sem_re=REEXP_T.sub('',REEXP.sub('',s))
    for tipo,cl,mod in IMPORT.findall(sem_re):
        t=res(f,mod)
        if not t: continue
        cl=cl.strip();pegou=[]
        m=re.search(r'\{([^}]*)\}',cl)
        if m: pegou+=nomes(m.group(1))
        fora=re.sub(r'\{[^}]*\}','',cl).strip(' ,')
        if fora:
            if fora.startswith('*'): pegou.append(('*',fora.split()[-1]))
            else: pegou.append(('default',fora))
        for la,ca in pegou:
            locais[ca]=(t,la);usos[t].append((f,la))
    for cl in EXP_LOCAL.findall(sem_re):
        for la,ca in nomes(cl):
            if la in locais:
                t,orig=locais[la];reexporta[f].append((t,orig,ca))
    for a,b,c in OUTROS.findall(sem_re):
        t=res(f,a or b or c)
        if t: usos[t].append((f,'*'))
    if re.search(r'import\(\s*[^\'"\s]',bruto): din.append(f)
    # barril: tirando import e export, não sobra código
    resto=EXP_LOCAL.sub('',IMPORT.sub('',sem_re))
    if reexporta[f] and not re.sub(r'[\s;]','',resto): barril.add(f)
# percurso por (arquivo, nome); nome None quer dizer que o arquivo inteiro mudou
visto={};fila=[(a,None,0) for a in alvos];marcados=set()
while fila:
    a,nome,d=fila.pop(0)
    if (a,nome) in marcados: continue
    marcados.add((a,nome))
    if a not in visto or d<visto[a]: visto[a]=d
    for quem,la in usos.get(a,[]):
        if nome not in (None,'*') and la not in (nome,'*'): continue
        if quem in barril:
            # o barril só repassa: segue pelos nomes que ele reexporta vindos daqui
            for t,orig,ca in reexporta[quem]:
                if t!=a or orig!=la: continue
                fila.append((quem,(nome or '*') if orig=='*' and ca=='*' else ca,d+1))
        else:
            fila.append((quem,None,d+1))
rotas=[]
if ROTAS in SET:
    L=g('show',f'{ref}:{ROTAS}').splitlines();path=None
    for l in L:
        m=re.search(r"path:\s*'([^']+)'",l)
        if m: path=m.group(1)
        c=re.search(r"component:\s*'([^']+)'",l)
        if c: rotas.append((path,c.group(1)))
def tela_de(f):
    for p,c in rotas:
        base=posixpath.normpath(posixpath.join(SRC,'pages',c.lstrip('./')))
        if f==base or f.startswith(base+'/') or f.startswith(base+'.'): return p
GLOBAL=tuple(f'{SRC}/{a}' for a in ('app.tsx','app.ts','global.tsx','global.ts'))
telas=sorted({tela_de(f) for f in visto if tela_de(f)})
print(json.dumps(dict(alvos=alvos,consumidores_diretos=sorted(f for f,d in visto.items() if d==1 and f not in barril),todos_afetados=sorted(f for f in visto if f not in alvos and f not in barril),total_afetados=len([f for f in visto if f not in alvos and f not in barril]),telas=telas,moldura_global=sorted(f for f in visto if f in GLOBAL),barris_atravessados=sorted(f for f in visto if f in barril),aviso='o resultado é piso, não teto: import dinâmico por variável e CSS global não aparecem',avisos=dict(import_dinamico=din[:10],leitura='moldura_global quer dizer que aparece em toda tela; o resultado é piso, não teto',**({} if alias_visto else dict(alias_sem_uso=f'nenhum import começa com {al}/: se o projeto usa alias, confira --alias, porque o resultado sai vazio sem erro')),**({} if alias_achou or not alias_visto else dict(alias_sem_alvo=f'há imports com {al}/, mas nenhum resolve em {alp}/: confira --alias, porque o resultado sai vazio sem erro')),**({} if rotas else dict(rotas_ausentes=f'nenhuma rota lida em {ROTAS}: `telas` sai vazio; liste as telas a partir de todos_afetados')))),ensure_ascii=False,indent=1))
