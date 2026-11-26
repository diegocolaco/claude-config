#!/usr/bin/env python3
"""O que está escrito e ninguém usa: quem reconstrói sem saber copia código morto, ou deixa de reconstruir o que parecia vivo.

uso: nao_usado.py <fecho.json> <TL-id> [<TL-id> ...]  -> JSON por linha: {tela, itens:[{tipo, texto, fonte}]}
Procura, nos arquivos da tela: classe de estilo sem uso; função de serviço sem chamador; endpoint de mock sem chamador;
chave de objeto constante nunca lida; tipo exportado sem importador; estado cujo setter nunca é chamado; handler vazio.
Lê só o git. Busca por nome em todo src/, então pode deixar passar uso dinâmico: é candidato, e quem decide é o revisor.
"""
import json,re,sys
import comum
CFG=comum.carrega()
TODOS=comum.todos(CFG)
COD=[f for f in TODOS if f.startswith('src/') and re.search(r'\.(tsx?|jsx?)$',f) and not re.search(r'\.test\.|\.d\.ts$',f)]
def show(f): return comum.show(CFG,f)
def linha(s,i): return s.count('\n',0,i)+1
def inicio_de_chave(s,i):
    """Só é chave de objeto se antes dela vierem apenas espaços desde a quebra de linha, a vírgula ou a chave."""
    j=i-1
    while j>=0 and s[j] in ' \t': j-=1
    return j<0 or s[j] in '\n,{'
def conta_nome(nome,fora=()):
    p=re.compile(r'\b'+re.escape(nome)+r'\b')
    return [f for f in COD if f not in fora and p.search(show(f))]
def estilos(arq,arqs):
    s=show(arq);o=[]
    # só chaves de primeiro nível do objeto devolvido por createStyles
    m=re.search(r'createStyles\(.*?return\s*\{',s,re.S)
    if not m: return o
    i=m.end();d=1;chaves=[]
    while i<len(s) and d:
        if d==1 and inicio_de_chave(s,i):
            k=re.match(r"['\"]?([\w-]+)['\"]?\s*:\s*\{",s[i:])
            if k: chaves.append((k.group(1),i+k.start(1)));i+=k.end();d+=1;continue
        if s[i]=='{': d+=1
        elif s[i]=='}': d-=1
        i+=1
    pasta=arq.rsplit('/',1)[0]
    # consumidor é quem está na pasta do estilo; sem nenhum lá, os arquivos da tela. Um styles[flag] de outra pasta não silencia este estilo.
    vizinhos=[f for f in COD if f.startswith(pasta+'/') and f!=arq] or [f for f in arqs if f!=arq]
    txt='\n'.join(show(f) for f in set(vizinhos))
    # styles[flag]: a chave vem de fora em tempo de execução, então nenhuma ausência pode ser afirmada
    if re.search(r"\w*styles?\w*\s*\[\s*[^'\"\s\]]",txt,re.I): return o
    for k,pos in chaves:
        if not re.search(r"\w*styles?\w*\s*(\.|\?\.|\[['\"])"+re.escape(k)+r"(?![\w-])",txt,re.I):
            o.append(dict(tipo='aparencia',texto=f'Classe de estilo {k} é definida e nenhum arquivo da tela a usa (NÃO USADO): o que ela define não aparece.',fonte=f'{arq}:{linha(s,pos)}'))
    return o
def servicos(arq,arqs):
    s=show(arq);o=[]
    for m in re.finditer(r'export\s+(?:async\s+)?function\s+(\w+)',s):
        n=m.group(1)
        # `query` é palavra comum: só conta quem importa o nome ou chama pelo módulo, não quem contém a palavra
        p=re.compile(r"import\s[^;]*\b"+n+r"\b[^;]*from|export\s*\{[^}]*\b"+n+r"\b[^}]*\}\s*from|\b\w*[sS]ervices?\w*\."+n+r"\b")
        if not [f for f in COD if f!=arq and p.search(show(f))]:
            api=re.search(r"['\"`]((?:/api)?/[\w/:.-]{3,})['\"`]",s[m.end():m.end()+300])
            o.append(dict(tipo='comportamento',texto=f'Serviço {n}{" ("+api.group(1)+")" if api else ""} é exportado e ninguém chama (NÃO USADO): a tela não faz essa chamada.',fonte=f'{arq}:{linha(s,m.start())}'))
    return o
def tipos(arq):
    s=show(arq);o=[]
    for m in re.finditer(r'export\s+(?:type|interface)\s+(\w+)',s):
        n=m.group(1)
        if not conta_nome(n,fora=(arq,)) and len(re.findall(r'\b'+n+r'\b',s))==1:
            o.append(dict(tipo='comportamento',texto=f'Tipo {n} é exportado e ninguém usa (NÃO USADO): não descreve nada que a tela faça.',fonte=f'{arq}:{linha(s,m.start())}'))
    return o
def objetos(arq):
    """const X = { a: ..., b: ... } em que algumas chaves nunca são lidas e não há leitura dinâmica nem repasse do objeto."""
    s=show(arq);o=[]
    for m in re.finditer(r'(?:^|\n)\s*(?:export\s+)?const\s+(\w+)(?:\s*:[^=\n]+)?\s*=\s*\{',s):
        n=m.group(1);i=m.end();d=1;chaves=[]
        while i<len(s) and d:
            if d==1 and inicio_de_chave(s,i):
                k=re.match(r"['\"]?([\w-]+)['\"]?\s*:",s[i:])
                if k: chaves.append((k.group(1),i+k.start(1)));i+=k.end();continue
            if s[i]=='{': d+=1
            elif s[i]=='}': d-=1
            i+=1
        depois=s[i:];usos=re.findall(r'\b'+n+r'\b(\s*\.\s*\w+|\s*\[|\?\.\w+)?',depois)
        if not usos or any(u=='' or '[' in u for u in usos) or len(chaves)<2: continue
        lidas={re.sub(r'[\s.?]','',u) for u in usos}
        for k,pos in chaves:
            if k not in lidas:
                o.append(dict(tipo='comportamento',texto=f'{n}.{k} é definido e nunca lido (NÃO USADO): o valor não chega à tela.',fonte=f'{arq}:{linha(s,pos)}'))
    return o
def estados(arq):
    s=show(arq);o=[]
    for m in re.finditer(r'const\s*\[\s*(\w+)\s*,\s*(\w+)\s*\]\s*=\s*useState',s):
        v,st=m.groups()
        if len(re.findall(r'\b'+st+r'\b',s))==1:
            o.append(dict(tipo='comportamento',texto=f'Estado {v}: o setter {st} nunca é chamado, então o valor fica sempre no inicial.',fonte=f'{arq}:{linha(s,m.start())}'))
        elif len(re.findall(r'\b'+v+r'\b',s))==1:
            o.append(dict(tipo='comportamento',texto=f'Estado {v} é preenchido por {st} e nunca lido, então não muda nada na tela.',fonte=f'{arq}:{linha(s,m.start())}'))
    for m in re.finditer(r'\b(on[A-Z]\w*)\s*=\s*\{\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{\s*\}\s*\}',s):
        o.append(dict(tipo='comportamento',texto=f'{m.group(1)} tem handler vazio: a ação não faz nada.',fonte=f'{arq}:{linha(s,m.start())}'))
    return o
def mocks(arq):
    s=show(arq);o=[]
    src='\n'.join(show(f) for f in COD if not f.endswith('_mock.ts'))
    for m in re.finditer(r"['\"](?:GET|POST|PUT|DELETE|PATCH)\s+(/api/[^'\"]+)['\"]",s):
        p=m.group(1);chave=re.split(r'/:',p)[0]
        if chave not in src:
            o.append(dict(tipo='comportamento',texto=f'Mock de {p} existe e nenhum código em src/ chama esse endereço (NÃO USADO).',fonte=f'{arq}:{linha(s,m.start())}'))
    return o
if __name__=='__main__':
    fe=json.load(open(sys.argv[1]))
    for tid in sys.argv[2:]:
        r=fe[tid];its=[];arqs=r.get('base',[])+r.get('rota_pai',[])
        for f in arqs:
            if 'locales/' in f or 'components/' in f and f.startswith('src/components'): continue
            if re.search(r'style\.style\.ts$|\.style\.ts$',f): its+=estilos(f,arqs)
            if re.search(r'service\.ts$',f) and not f.startswith('src/services/'): its+=servicos(f,arqs)
            if re.search(r'\.tsx?$',f): its+=tipos(f)
            if f.endswith('.tsx'): its+=objetos(f)+estados(f)
        for f in r.get('mock_vizinho',[]): its+=mocks(f)
        vistos=set();uni=[]
        for x in its:
            k=(x['texto'],x['fonte'])
            if k not in vistos: vistos.add(k);uni.append(x)
        print(json.dumps(dict(tela=tid,itens=uni),ensure_ascii=False))
    # mock compartilhado da raiz: uma vez só, para o projeto
    its=[]
    for f in TODOS:
        if f.startswith('mock/') and f.endswith('.ts'): its+=mocks(f)
        if f.startswith('src/services/') and re.search(r'\.tsx?$',f) and not f.endswith('.d.ts'): its+=servicos(f,[])
    print(json.dumps(dict(tela='TL-moldura',itens=its),ensure_ascii=False))
