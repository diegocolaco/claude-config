#!/usr/bin/env python3
"""Fatos que quem lê o código não vê: o que cada componente de biblioteca NÃO recebe e o que fica por conta dele.

uso: props_biblioteca.py <fecho.json> <TL-id> [<TL-id> ...]  -> JSON por linha: {tela, itens:[{tipo, texto, fonte}]}
Lê só o git. Percorre a abertura de cada tag com contagem de chaves e aspas, sem executar nada.
O script não sabe o padrão da biblioteca; ele registra que o padrão vale e deixa NÃO VERIFICADO.
"""
import json,re,sys,collections
import comum
CFG=comum.carrega()
def show(f): return comum.show(CFG,f)
LIB=re.compile(r"^(antd|@ant-design/[\w-]+|@umijs/max|rc-[\w-]+)$")
# Props cuja falta muda o que se constrói. Quem não está aqui só entra pelo texto interno.
ATENCAO={
 'Select':['allowClear','showSearch','mode','onChange','loading','notFoundContent'],
 'Tag':['closable','onClose'],
 'Table':['rowKey','pagination','loading','locale'],'ProTable':['rowKey','pagination','search','toolBarRender'],
 'Modal':['destroyOnHidden','destroyOnClose','maskClosable','keyboard','footer','confirmLoading'],
 'ModalForm':['modalProps','submitter','onOpenChange'],'DrawerForm':['drawerProps','submitter','onOpenChange'],
 'Drawer':['destroyOnHidden','destroyOnClose','maskClosable','closable'],
 'Form':['onFinish','onFinishFailed','requiredMark','validateTrigger'],'ProForm':['onFinish','submitter','requiredMark'],
 'Input':['allowClear','maxLength'],'Input.Search':['allowClear','enterButton','loading','onSearch'],'Input.Password':['allowClear','maxLength'],
 'List':['loading','pagination','locale','rowKey'],
 'Upload':['accept','maxCount','beforeUpload','showUploadList','customRequest'],
 'Tabs':['activeKey','onChange'],'Dropdown':['trigger','disabled'],
 'Popconfirm':['okText','cancelText','onCancel'],'Radio.Group':['onChange','value'],'DatePicker':['allowClear','disabledDate'],
 'DatePicker.RangePicker':['allowClear','disabledDate'],'InputNumber':['min','max','precision'],'Pagination':['showSizeChanger','showQuickJumper','onChange'],
}
# Textos ou comportamento que nascem dentro do componente, quando o código não diz nada.
INTERNO={
 'LoginForm':'rótulo e carregamento do botão de envio',
 'StepsForm':'textos e posição dos botões anterior, próximo e enviar',
 'ProForm':'rótulos dos botões enviar e redefinir','ModalForm':'rótulos e carregamento dos botões do rodapé','DrawerForm':'rótulos e carregamento dos botões do rodapé',
 'ProTable':'textos de busca, redefinir, recolher, paginação, configuração da tabela e vazio',
 'Table':'texto de vazio, ordem da ordenação e textos de paginação','List':'texto de vazio e textos de paginação',
 'Modal':'textos OK e Cancelar quando não definidos','Popconfirm':'textos OK e Cancelar quando não definidos',
 'Select':'texto de vazio da lista','Upload':'lista de arquivos e textos internos','Pagination':'textos de total e tamanho de página',
 'Conversations':'onde o menu abre e os textos internos','Sender':'envio por Enter, campo vazio e textos internos','Bubble':'estados de carregando e textos internos','Bubble.List':'rolagem e textos internos',
 'Prompts':'layout e textos internos','Welcome':'layout interno',
 'Line':'desenho, eixos, legenda e tooltip','Column':'desenho, eixos, legenda e tooltip','Pie':'desenho, legenda e tooltip','Area':'desenho, eixos e tooltip','Gauge':'desenho do arco e do texto','Liquid':'desenho da onda e do texto','WordCloud':'desenho e posição das palavras','Radar':'desenho, legenda e tooltip','Tiny.Line':'desenho','Tiny.Area':'desenho','Tiny.Column':'desenho','Tiny.Progress':'desenho',
 'PageContainer':'título vindo da rota e breadcrumb','ProLayout':'menu, cabeçalho e recolhimento','Result':'ícone por status','Empty':'imagem e texto padrão',
}
# Slot: a prop diz onde a peça fica, e o inventário costuma listar a peça sem dizer o lugar.
SLOT={('Card','actions'):'rodapé do card',('Card','extra'):'canto direito do cabeçalho do card',('Card','tabList'):'abas no cabeçalho do card',('Card','cover'):'capa acima do conteúdo',
 ('PageContainer','extra'):'canto direito do cabeçalho da página',('PageContainer','tabList'):'abas no cabeçalho da página',('PageContainer','content'):'bloco abaixo do título',('PageContainer','footer'):'barra fixa no rodapé',
 ('Modal','footer'):'rodapé do modal',('Table','summary'):'linha de totais no fim da tabela',('List.Item','actions'):'à direita do item',('List.Item','extra'):'bloco lateral do item',('List','footer'):'rodapé da lista',('List','header'):'cabeçalho da lista',
 ('ProTable','toolBarRender'):'barra acima da tabela',('ProTable','headerTitle'):'título acima da tabela',('Result','extra'):'botões abaixo do resultado'}
ABRE=re.compile(r'<([A-Z][\w]*(?:\.[A-Z][\w]*)*)(?=[\s/>])')
def imports(s):
    m={}
    for cl,mod in re.findall(r"import\s+(?!type\b)([^;]*?)\s+from\s+['\"]([^'\"]+)['\"]",s):
        if not LIB.match(mod): continue
        for nome,loc in [(a,b or a) for a,b in re.findall(r"(\w+)(?:\s+as\s+(\w+))?",(re.search(r'\{([^}]*)\}',cl) or [None,''])[1])]:
            m[loc]=(nome,mod)
        fora=re.sub(r'\{[^}]*\}','',cl).strip(' ,')
        if fora and not fora.startswith('*'): m[fora]=(fora,mod)
    return m
def pula(s,i,fecho):
    """Avança até o `}` que casa, tratando aspas, template e comentário."""
    d=1
    while i<len(s) and d:
        c=s[i]
        if c in '"\'`':
            q=c;i+=1
            while i<len(s) and s[i]!=q:
                if s[i]=='\\': i+=1
                i+=1
        elif s[i:i+2]=='//':
            i=s.find('\n',i);i=len(s) if i<0 else i
        elif s[i:i+2]=='/*':
            i=s.find('*/',i);i=len(s) if i<0 else i+1
        elif c=='{': d+=1
        elif c=='}': d-=1
        i+=1
    return i
def atributos(s,i):
    props=[];espalha=False
    while i<len(s):
        while i<len(s) and s[i].isspace(): i+=1
        if i>=len(s): break
        if s[i]=='>' or s[i:i+2]=='/>': return props,espalha,i
        if s[i]=='{':
            if s[i+1:].lstrip().startswith('...'): espalha=True
            i=pula(s,i+1,'}');continue
        m=re.match(r'[\w:-]+',s[i:])
        if not m: i+=1;continue
        n=m.group(0);i+=len(n);props.append(n)
        while i<len(s) and s[i].isspace(): i+=1
        if i<len(s) and s[i]=='=':
            i+=1
            while i<len(s) and s[i].isspace(): i+=1
            if i<len(s) and s[i] in '"\'':
                q=s[i];i=s.find(q,i+1)+1
            elif i<len(s) and s[i]=='{':
                i=pula(s,i+1,'}')
    return props,espalha,i
def fatos(arq):
    s=show(arq);imp=imports(s);saida=[]
    for m in ABRE.finditer(s):
        nome=m.group(1);raiz=nome.split('.')[0]
        if raiz not in imp: continue
        real=imp[raiz][0]+nome[len(raiz):];lib=imp[raiz][1]
        props,esp,_=atributos(s,m.end())
        linha=s.count('\n',0,m.start())+1;fonte=f'{arq}:{linha}'
        falta=[p for p in ATENCAO.get(real,[]) if p not in props]
        # `destroyOnClose` e `destroyOnHidden` são o mesmo fato em versões diferentes do antd
        if 'destroyOnClose' in falta and 'destroyOnHidden' in falta: falta.remove('destroyOnHidden')
        if falta and real in ('Modal','Drawer') and ('destroyOnClose' in props or 'destroyOnHidden' in props):
            falta=[p for p in falta if not p.startswith('destroyOn')]
        ress=' Recebe props por espalhamento, então a falta aqui é só do que está escrito.' if esp else ''
        for p in props:
            if (real,p) in SLOT: saida.append(dict(tipo='aparencia',texto=f'{real} ({lib}): o que vem em {p} fica em: {SLOT[(real,p)]}.',fonte=fonte))
        if falta:
            saida.append(dict(tipo='comportamento',texto=f'{real} ({lib}): o código passa {", ".join(props) or "nenhuma prop"}; não define {", ".join(falta)}, então vale o padrão do componente (NÃO VERIFICADO).{ress}',fonte=fonte))
        if real in INTERNO:
            saida.append(dict(tipo='comportamento',texto=f'{real} ({lib}): {INTERNO[real]} vêm do componente, não do código (NÃO VERIFICADO); conferir na versão instalada.',fonte=fonte))
    return saida
if __name__=='__main__':
    fe=json.load(open(sys.argv[1]))
    for tid in sys.argv[2:]:
        r=fe[tid];vistos=set();its=[]
        for f in r.get('base',[])+r.get('rota_pai',[]):
            if not f.endswith('.tsx') or f in vistos: continue
            vistos.add(f);its+=fatos(f)
        print(json.dumps(dict(tela=tid,itens=its),ensure_ascii=False))
