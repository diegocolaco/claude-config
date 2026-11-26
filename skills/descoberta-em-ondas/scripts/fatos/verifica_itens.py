#!/usr/bin/env python3
"""Confere por script se os valores citados num item de inventário existem no código, perto da linha citada.

uso: verifica_itens.py <inventario.json ...>  [--saida suspeitos.json]
Cada item traz `texto` e `fonte` (arquivo:linha ou arquivo:ini-fim). Extrai do texto os literais entre aspas, os hex e os números
com unidade, e procura cada um no arquivo citado, numa janela de 8 linhas em volta. Não prova que o item está certo: aponta o que
vale olhar. Item sem arquivo reconhecível vai como SEM_FONTE.
"""
import json,re,sys,collections
import comum
CFG=comum.carrega()
TODOS=comum.todos(CFG)
def show(f): return comum.show(CFG,f).splitlines()
QUOTE=re.compile(r"""['"`«“]([^'"`»”\n]{1,80})['"`»”]""")
HEX=re.compile(r"#[0-9a-fA-F]{3,8}\b")
# número solto com 2 ou mais dígitos, tirando o que é referência de linha
LINHAREF=re.compile(r"\(?(?:linhas?|l\.|L|:)\s*\d+(?:\s*(?:-|,|e|a|até|ate)\s*\d+)*(?:\s*entre\s*\d+\s*e\s*\d+)?\)?|entre\s+\d+\s+e\s+\d+|[\w./-]+\.(?:tsx?|jsx?|json|less|css)(?:[:\s]+\d+(?:\s*-\s*\d+)?)?",re.I)
# aviso do agente sobre o recorte, sem fato da tela
SO_AVISO=re.compile(r"^\s*(?:TRECHO CORTADO|Linhas?\s+\d[\d\s,e-]*\s*(?:ausentes?|n[aã]o est[aã]o|n[aã]o aparecem|cortad|fora))",re.I)
INTEIRO=re.compile(r"(?<![\w.#:-])(\d{2,}(?:\.\d+)?)(?![\w%])")
NUM=re.compile(r"(?<![\w.#:-])(\d+(?:\.\d+)?)(?:\s?(?:px|ms|%|rem|em|vh|vw))(?![\w])")
def resolve(fonte):
    m=re.search(r'([\w./@-]+\.(?:tsx?|jsx?|json|less|css))(?::(\d+)(?:-(\d+))?)?',fonte or '')
    if not m: return None,None,None
    f=m.group(1)
    if f not in TODOS:
        c=[x for x in TODOS if x.endswith('/'+f)]
        if len(c)!=1: return None,None,None
        f=c[0]
    ini=int(m.group(2)) if m.group(2) else None
    fim=int(m.group(3)) if m.group(3) else ini
    return f,ini,fim
def confere(it,arq=None):
    f,ini,fim=resolve(it.get('fonte'))
    if not f and arq and arq in TODOS:
        # fonte só com a linha ou com nome ambíguo: vale o arquivo do bloco
        m=re.search(r'(\d+)(?:-(\d+))?',it.get('fonte') or '')
        f=arq
        if m: ini=int(m.group(1));fim=int(m.group(2)) if m.group(2) else ini
    if not f: return 'SEM_FONTE',[]
    L=show(f)
    if ini:
        if ini>len(L): return 'LINHA_FORA',[]
        jan='\n'.join(L[max(0,ini-5):(fim or ini)+4])
    else: jan='\n'.join(L)
    tot='\n'.join(L)
    tx=it.get('texto','')
    if SO_AVISO.match(tx): return 'AVISO',[]
    sem_linha=LINHAREF.sub(' ',tx)
    vals=[('s',x.strip()) for x in QUOTE.findall(tx) if len(x.strip())>=2 and '${' not in x]+[('c',x) for x in HEX.findall(tx)]+[('n',x) for x in NUM.findall(tx)]+[('n',x) for x in INTEIRO.findall(sem_linha)]
    faltam=[];longe=[]
    for k,v in vals:
        if not v: continue
        if v.lower() in jan.lower(): continue
        if v.lower() in tot.lower(): longe.append(v);continue
        faltam.append(v)
    if faltam: return 'VALOR_AUSENTE',faltam
    if longe: return 'LONGE_DA_LINHA',longe
    return ('OK' if vals else 'SEM_VALOR'),[]
if __name__=='__main__':
    args=[a for a in sys.argv[1:] if not a.startswith('--')]
    saida=None
    if '--saida' in sys.argv:
        saida=sys.argv[sys.argv.index('--saida')+1];args=[a for a in args if a!=saida]
    def arq_do_livro(a):
        # .../I-Hm/TL-x.p1.json -> L3/TL-x.txt: arquivo de cada bloco
        m=re.search(r'(TL-[\w-]+?)\.p\d+\.json$',a)
        B={}
        if m:
            cur=None
            import os
            # o livro pode estar em qualquer uma das rodadas; vale a primeira que tiver a tela
            livro=next((f'{d}/{m.group(1)}.txt' for d in [*(x for x in os.environ.get('LIVROS','').split(':') if x),CFG['pasta']+'/livro'] if os.path.exists(f'{d}/{m.group(1)}.txt')),None)
            if not livro: return B
            for l in open(livro,encoding='utf-8'):
                if l.startswith('## '): cur=l[3:].split(' (')[0].strip()
                else:
                    k=re.match(r'\[(B\d+)\]$',l.strip())
                    if k: B[k.group(1)]=cur
        return B
    cnt=collections.Counter();sus=[]
    for a in args:
        B=arq_do_livro(a)
        for b in json.load(open(a)):
            for it in b.get('itens',[]):
                st,v=confere(it,B.get(b['bloco']));cnt[st]+=1
                if st in('VALOR_AUSENTE','LONGE_DA_LINHA','LINHA_FORA','SEM_FONTE'): sus.append({'arquivo':a,'bloco':b['bloco'],'status':st,'valores':v,**it})
    print(dict(cnt),'total',sum(cnt.values()))
    if saida: json.dump(sus,open(saida,'w'),ensure_ascii=False,indent=0)
