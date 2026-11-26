#!/usr/bin/env python3
"""Uma entrada só para a passada de fatos: o que é mecânico roda aqui, e o que é de agente sai pronto para despacho.

uso: processo.py <subcomando> <pasta> [argumentos]. Toda a configuração fica em <pasta>/config.json.

iniciar <pasta> --repo R --commit C --mapa M [--lib L] [--moldura ARQ]... [--superficie-moldura SF-X]
                                              grava config.json, o fecho e o fecho podado do protótipo
prepara <pasta> TL...                         livro e partes de cada tela; fatos de script; despachos.json
projeto <pasta>                               uma vez só: moldura e global, build, não usado, perguntas de biblioteca
confere <pasta> TL...                         toda tela tem livro e todo bloco tem resposta? sai 1 e diz o que refazer
junta <pasta> TL...                           I + A + S em fatos/<tela>.json, com id estável, fonte e alarme; recusa saída ausente
duvidas <pasta> TL...                         NÃO VERIFICADO das ausências em lotes de 8 (despachos-duvidas.json)
duvidas-grava <pasta> <lote.json resp.json>...  resposta com citação batendo vira fato; o resto segue aberto
biblioteca-baixa <pasta>                      baixa a versão travada dos pacotes das perguntas para config["lib"]
biblioteca-confere <pasta> <resp.json>...     toda citação existe na versão travada? o que passa vira fato
biblioteca-amostra <pasta> [n=15]             sorteia n respostas conferidas para revisão (despachos-biblioteca-revisao.json)
amostra <pasta> [--tudo] TL...                revisão: todo VALOR_AUSENTE + 6 por tela + dúvidas resolvidas, em lotes de 30
revisao-aplica <pasta>                        FALSO sai dos fatos, IMPRECISO fica anotado; sai 1 se faltar saída ou reenvio, 11 se a taxa de FALSO passar de 2%
dif <pasta> <catalogo.json> TL...             entrada do passo de diferença (despachos-dif.json)
dest <pasta> <catalogo.json> TL...            entrada do passo de destino, só com os fatos NOVO (despachos-dest.json)
grava <pasta> <catalogo.json> <saida.json> [--ao-lado PASTA] TL...
                                              destino do agente + destino fixo, tela a tela; sai 11 se cenário novo ficar sem dono.
                                              Com --ao-lado, guarda também as ausências e o padrão de biblioteca de cada tela
relidas <pasta> <saida.json> TL...            {"telas": {...}} para `cobertura.py resumo --cega`; recusa tela sem fato de leitura
omitidos <pasta> <saida.json> TL...           itens NOVO da diferença, no formato de `--itens-omitidos`
"""
import glob, hashlib, json, os, random, re, shutil, subprocess, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
BRIEFS = AQUI.parents[1] / 'references' / 'briefs'
sys.path.insert(0, str(AQUI))
import comum
CITA = re.compile(r'[\w./@-]+\.\w+:\d+')
DUVIDA = 'Dúvida resolvida'
MOLDURAS = ('TL-moldura', 'TL-global')
COMPONENTE = re.compile(r'([\w.]+) \(([^)]+)\): (.*)', re.S)
CFG = {}
PASTA = ''


def erro(msg, codigo=1):
    comum.erro(msg, codigo)


def ler(f, padrao=None):
    """JSON de um arquivo; ausente ou quebrado sai 1 nomeando o arquivo, em vez de pular em silêncio."""
    if padrao is not None and not os.path.exists(f): return padrao
    if not os.path.exists(f): erro(f'{f} não existe: refaça a etapa que o grava')
    try:
        return json.load(open(f, encoding='utf-8'))
    except json.JSONDecodeError as e:
        erro(f'{f} não é JSON válido ({e}): refaça a etapa que o grava')


def grava(f, o):
    os.makedirs(os.path.dirname(f), exist_ok=True)
    json.dump(o, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)


def rode(script, *a, env=None):
    return subprocess.run([sys.executable, '-B', str(AQUI / script), *map(str, a)], capture_output=True, text=True,
                          env={**os.environ, 'FATOS_PASTA': PASTA, **(env or {})})


def checa(r, nome):
    if r.returncode:
        erro(f'{nome} falhou: {(r.stderr or r.stdout)[-300:].strip()}', 2 if r.returncode == 2 else 1)
    return r


def forma_ok(o):
    """Saída de agente: lista de blocos, e cada bloco com lista de itens. JSON válido não basta: já veio lista de listas."""
    return isinstance(o, list) and all(isinstance(b, dict) and isinstance(b.get('itens', []), list)
                                       and all(isinstance(i, dict) for i in b.get('itens', [])) for b in o)


def saida_ruim(f):
    try:
        return None if forma_ok(json.load(open(f, encoding='utf-8'))) else 'não é uma lista de blocos com `itens`'
    except json.JSONDecodeError:
        return 'saída ilegível'


def telas_do_mapa(telas, moldura=True):
    """Toda etapa por tela: sem tela nenhuma, ou com id errado, não há o que fazer, e isso não pode virar saída 0."""
    if not telas: erro('informe ao menos uma tela', 2)
    ids = {t['id'] for t in ler(CFG['mapa']).get('telas', [])} | (set(MOLDURAS) if moldura else set())
    fora = [t for t in telas if t not in ids]
    if fora: erro(f'{fora}: id fora do mapa {CFG["mapa"]}', 2)
    return telas


def itens(f):
    o = []
    blocos = ler(f)
    if not forma_ok(blocos): erro(f'{f} não é uma lista de blocos com `itens`: refaça a etapa que o grava')
    for b in blocos:
        for i in b.get('itens', []): o.append({**i, 'bloco': b.get('bloco')})
    return o


def tem_blocos(t):
    f = Path(PASTA) / 'livro' / f'{t}.txt'
    return f.exists() and re.search(r'^\[B\d+\]$', f.read_text(encoding='utf-8'), re.M) is not None


def exige_ausencias(t):
    return t != 'TL-global' and tem_blocos(t)


def pacotes_da_lib():
    lib = Path(CFG['lib'])
    return sorted(p.name for p in lib.iterdir() if p.is_dir()) if lib.is_dir() else []


def despacho(etapa, brief, modelo, esforco, entrada, saida, **extra):
    """Entrada pronta para o controlador copiar: o prompt manda ler o brief pelo caminho absoluto e traz o que ele pede."""
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    texto = (f'Leia o brief em {BRIEFS / (brief + ".md")} e siga-o. Entrada: {entrada}. Saída: {saida}. '
             f'Repositório do protótipo: {CFG["repo"]}. Commit: {CFG["commit"]}. Biblioteca na versão travada: {CFG["lib"]}.')
    if etapa in ('biblioteca', 'biblioteca-revisao', 'duvidas'):
        pk = pacotes_da_lib()
        texto += ' Pacotes em ' + CFG['lib'] + ': ' + (', '.join(pk) if pk else 'nenhum baixado ainda') + '.'
    return dict(etapa=etapa, brief=str(BRIEFS / (brief + '.md')), modelo=modelo, esforco=esforco, entrada=str(entrada),
                saida=str(saida), prompt=texto, **extra)


def parte_do_livro(nome, lv, desp):
    r = rode('parte.py', lv, f'{PASTA}/parte', 20000)
    checa(r, f'parte.py {nome}')
    partes = sorted(glob.glob(f'{PASTA}/parte/{nome}.p*.txt'))
    vazias = [p for p in partes if not re.search(r'^\[B\d+\]$', Path(p).read_text(encoding='utf-8'), re.M)]
    for p in vazias: Path(p).unlink()
    partes = [p for p in partes if p not in vazias]
    for p in partes:
        desp.append(despacho('inventario', 'inventario', 'haiku', 'medium', p, f'{PASTA}/I/{os.path.basename(p)[:-4]}.json'))
    return partes


def grava_script(t, scr):
    """`S/<tela>` também recebe o que as etapas seguintes integram: repetir `prepara` ou `projeto` não pode apagar."""
    f = f'{PASTA}/S/{t}.json'
    grava(f, scr + [x for x in ler(f, []) if (x.get('texto') or '').startswith((DUVIDA, comum.PADRAO)) and x not in scr])


def prepara(telas):
    telas_do_mapa(telas, moldura=False)
    # o livro ainda traria rotas e locale, e a tela passaria como lida sem o código dela
    arq = {t['id']: t.get('arquivo') for t in ler(CFG['mapa'])['telas']}; existem = set(comum.todos(CFG))
    sem_codigo = [t for t in telas if arq[t] not in existem]
    if sem_codigo: erro(f'{sem_codigo}: o arquivo da tela não existe no commit {CFG["commit"]}: confira se o mapa é desta versão', 2)
    os.makedirs(f'{PASTA}/livro', exist_ok=True); desp = []
    r = checa(rode('sessao_rota.py', CFG['mapa']), 'sessao_rota.py')
    if r.stderr: print(r.stderr.strip(), file=sys.stderr)
    sessao = {x['tela']: x['itens'] for x in map(json.loads, r.stdout.splitlines())}
    for t in telas:
        lv = f'{PASTA}/livro/{t}.txt'
        checa(rode('livro_fecho.py', t, lv, CFG['mapa']), f'livro de {t}')
        partes = parte_do_livro(t, lv, desp)
        if not tem_blocos(t): erro(f'{t}: nenhum código desta tela no commit {CFG["commit"]}: confira se o mapa é desta versão', 2)
        desp.append(despacho('ausencias', 'ausencias', 'haiku', 'medium', lv, f'{PASTA}/A/{t}.json'))
        scr = []
        for sc in ('props_biblioteca.py', 'nao_usado.py'):
            for l in checa(rode(sc, CFG['fecho'], t), sc).stdout.splitlines():
                x = json.loads(l)
                if x['tela'] == t: scr += x['itens']
        c = json.loads(checa(rode('chaves_locale.py', t), 'chaves_locale.py').stdout.splitlines()[0])
        scr.append(dict(tipo='comportamento', texto=f"Idioma da tela, por script: {c['idioma']}; {c['chaves']} chaves de locale usadas; ausentes em pt-BR: {c['ausentes_em_pt_br']}; {c['literais_nao_ascii_no_codigo']} literais não ASCII fixos no código.", fonte='chaves_locale.py'))
        scr += sessao.get(t, [])
        grava_script(t, scr)
        print(t, 'partes', len(partes), 'fatos de script', len(scr))
    # preparar outra tela não pode perder o despacho das anteriores
    novos = {d['saida'] for d in desp}
    desp = [d for d in ler(f'{PASTA}/despachos.json', []) if d['saida'] not in novos] + desp
    grava(f'{PASTA}/despachos.json', desp); print('despachos', len(desp))


def confere(telas):
    ruim = []
    for t in telas:
        partes = sorted(glob.glob(f'{PASTA}/parte/{t}.p*.txt'))
        etapa = 'projeto' if t in MOLDURAS else 'prepara'
        # moldura sem arquivo nenhum é legítima fora do Umi; tela do mapa sem código, ou etapa não rodada, é trecho que ninguém leu
        if not (Path(PASTA) / 'livro' / f'{t}.txt').exists(): ruim.append((f'{PASTA}/livro/{t}.txt', f'sem livro: rode {etapa}'))
        elif not tem_blocos(t) and t not in MOLDURAS: ruim.append((f'{PASTA}/livro/{t}.txt', 'livro sem blocos: rode prepara'))
        elif not partes and tem_blocos(t): ruim.append((f'{PASTA}/parte/{t}', f'sem partes: rode {etapa}'))
        for p in partes:
            sai = f'{PASTA}/I/{os.path.basename(p)[:-4]}.json'
            if not os.path.exists(sai): ruim.append((p, f'sem saída em {sai}')); continue
            mot = saida_ruim(sai)
            if mot: ruim.append((p, f'{mot}: {sai}')); continue
            r = subprocess.run([sys.executable, '-B', str(AQUI / 'ledger.py'), 'confere', p, sai], capture_output=True, text=True)
            print(os.path.basename(p), r.stdout.strip()[:120])
            if r.returncode == 2: ruim.append((p, f'saída ilegível: {sai}'))
            elif r.returncode: ruim.append((p, 'faltam blocos'))
        if exige_ausencias(t):
            a = f'{PASTA}/A/{t}.json'
            if not os.path.exists(a): ruim.append((a, 'sem saída'))
            elif saida_ruim(a): ruim.append((a, saida_ruim(a)))
    for p, m in ruim: print('REFAZER', p, m)
    sys.exit(1 if ruim else 0)


def revisao_marcas():
    """O que a revisão já decidiu e a junta tem de respeitar: removidos (FALSO) e anotações de imprecisão."""
    return ({x['id'] for x in ler(f'{PASTA}/revisao/removidos.json', [])}, ler(f'{PASTA}/revisao/imprecisos.json', {}))


def junta(telas):
    removidos, imprecisos = revisao_marcas()
    for t in telas:
        partes = sorted(glob.glob(f'{PASTA}/parte/{t}.p*.txt'))
        fontes = [(f'{PASTA}/I/{os.path.basename(p)[:-4]}.json', 'I') for p in partes]
        if exige_ausencias(t): fontes.append((f'{PASTA}/A/{t}.json', 'A'))
        for f, _ in fontes: ler(f)
        sf = f'{PASTA}/S/{t}.json'
        script = ler(sf, [] if t == 'TL-global' else None)
        pares = [(x, orig) for f, orig in fontes for x in itens(f)] + [(x, 'S') for x in script]
        vistos = set(); o = []
        for x, orig in pares:
            tx = x.get('texto') or ''; fo = x.get('fonte') or ''
            h = comum.fid(t, tx, fo)
            if h in vistos or h in removidos: continue
            vistos.add(h)
            fato = dict(id=h, origem=orig, tipo=x.get('tipo'), texto=tx, fonte=fo, pergunta=x.get('pergunta'))
            if h in imprecisos: fato['imprecisao'] = imprecisos[h]
            o.append(fato)
        grava(f'{PASTA}/fatos/{t}.json', o)
        os.makedirs(f'{PASTA}/alarmes', exist_ok=True)
        arq = [f for f, orig in fontes if orig == 'I']
        r = checa(rode('verifica_itens.py', *arq, '--saida', f'{PASTA}/alarmes/{t}.json', env={'LIVROS': f'{PASTA}/livro'}), 'verifica_itens.py') if arq else None
        if r is None: grava(f'{PASTA}/alarmes/{t}.json', [])
        print(t, 'fatos', len(o), {k: sum(1 for x in o if x['origem'] == k) for k in 'IAS'}, '|', r.stdout.strip()[-120:] if r else '')


def cat_tela(c, t):
    sf = comum.superficie(CFG, t); regs = {r['id']: r for r in c['regions'] if r['surface_id'] == sf}
    return [s for s in c['scenarios'] if s['region_id'] in regs], regs


def dif(cat, telas):
    c = ler(cat); desp = []
    for t in telas:
        cen, _ = cat_tela(c, t); o = ler(f'{PASTA}/fatos/{t}.json')
        leitura = [(s.get('definition') or {}).get('agora') or '' for s in cen]
        grava(f'{PASTA}/dif/{t}.json', dict(leitura=json.dumps(leitura, ensure_ascii=False), itens=[dict(i=k + 1, id=x['id'], x=x['texto']) for k, x in enumerate(o)]))
        desp.append(despacho('diferenca', 'diferenca', 'haiku', 'medium', f'{PASTA}/dif/{t}.json', f'{PASTA}/dif-saida/{t}.json'))
        print(t, 'cenários', len(cen), 'itens', len(o))
    grava(f'{PASTA}/despachos-dif.json', desp)


FIXO = [(re.compile(r'lista de (rotas|exceções)|não declara `access`|exige o perfil'), 'NOVO:Acesso e sessão'), (re.compile(r'^Idioma da tela, por script'), 'NOVO:Idioma da tela')]
def fixo(x):
    if x.get('origem') != 'S': return None
    return next((d for r, d in FIXO if r.search(x['texto'])), None)


def padroes_da_tela(t, padroes, imprecisos):
    """Padrão de biblioteca vale para quem usa o componente; `Select.Option.x` é de outro componente, não de `Select`."""
    usa = {m.groups()[:2] for x in ler(f'{PASTA}/S/{t}.json', []) if (m := COMPONENTE.match(x.get('texto') or ''))}
    o = []
    for x in padroes:
        pac = re.match(r'(@?[^@]+)@', x['fonte']); resto = x['texto'][len(comum.PADRAO):]
        if not pac or not any(p == pac.group(1) and resto.startswith(c + '.') and not re.match(r'[A-Z]\w*\.', resto[len(c) + 1:]) for c, p in usa): continue
        mot = imprecisos.get(comum.fid('TL-moldura', x['texto'], x['fonte']))
        o.append(dict(tipo=x.get('tipo'), texto=x['texto'], fonte=x['fonte'], **({'imprecisao': mot} if mot else {})))
    return o


def completa_ao_lado(t, lado, padroes, imprecisos):
    """O que quem planeja lê e não tem cenário: as ausências, porque `<tmp>` não sobrevive até o plano, e o padrão de biblioteca da tela."""
    aus = Path(PASTA) / 'A' / f'{t}.json'
    if aus.exists():
        (Path(lado) / 'ausencias').mkdir(exist_ok=True); shutil.copyfile(aus, Path(lado) / 'ausencias' / f'{t}.json')
    dela = [] if t in MOLDURAS else padroes_da_tela(t, padroes, imprecisos)
    if dela:
        arq = Path(lado) / f'{t}.json'; o = ler(str(arq))
        json.dump({**o, 'biblioteca': dela}, open(arq, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def grava_catalogo(cat, saida, lado, telas):
    """Junta o destino do agente com o destino fixo e chama o integrador tela a tela; a saída de uma é a entrada da próxima."""
    atual = cat; sem_dono = []
    if lado: os.makedirs(lado, exist_ok=True)
    padroes = [x for x in ler(f'{PASTA}/S/TL-moldura.json', []) if (x.get('texto') or '').startswith(comum.PADRAO)]
    imprecisos = ler(f'{PASTA}/revisao/imprecisos.json', {})
    for t in telas:
        d = ler(f'{PASTA}/dest/{t}.json'); ds = ler(f'{PASTA}/dest-saida/{t}.json')
        fx = ler(f'{PASTA}/dest/{t}.fixos.json')
        n = max([x['i'] for x in d['itens']] + [0])
        its = list(d['itens']); dest_ = {str(k): v for k, v in ds.items()}
        for x in fx:
            n += 1; its.append({**x, 'i': n}); dest_[str(n)] = x['destino']
        anotados = {x['id']: x['imprecisao'] for x in ler(f'{PASTA}/fatos/{t}.json', []) if x.get('imprecisao')}
        its = [{**x, 'imprecisao': anotados[x['id']]} if x.get('id') in anotados else x for x in its]
        lista = f'{PASTA}/dest/{t}.final.json'; saida_d = f'{PASTA}/dest/{t}.final.destino.json'
        grava(lista, dict(tela=d['tela'], itens=its)); grava(saida_d, dest_)
        extra = ['--ao-lado', str(Path(lado) / f'{t}.json')] if lado else []
        r = rode('integra_catalogo.py', atual, lista, saida_d, saida, *extra)
        print(r.stdout.strip(), r.stderr.strip()[-200:])
        if r.returncode == 11: sem_dono += [l for l in r.stdout.splitlines() if l.startswith('CENARIO_SEM_DONO')]
        elif r.returncode: sys.exit(1)
        if lado: completa_ao_lado(t, lado, padroes, imprecisos)
        atual = saida
    if sem_dono:
        print('Cenário novo sem requisito na superfície: crie a diferença e o requisito à mão.', file=sys.stderr)
        sys.exit(11)


def dest(cat, telas):
    c = ler(cat); desp = []
    for t in telas:
        cen, regs = cat_tela(c, t); o = {x['id']: x for x in ler(f'{PASTA}/fatos/{t}.json')}
        ent = ler(f'{PASTA}/dif/{t}.json'); res = ler(f'{PASTA}/dif-saida/{t}.json')
        por = {x['i']: x for x in ent['itens']}
        faltou = sorted(set(por) - set(res['novos']) - set(res['ja']))
        if faltou: erro(f'{t}: itens sem decisão na diferença: {faltou[:10]}', 2)
        novos = [o[por[n]['id']] for n in res['novos']]
        fx = [dict(id=x['id'], tipo=x['tipo'], texto=x['texto'], fonte=x['fonte'], destino=fixo(x)) for x in novos if fixo(x)]
        grava(f'{PASTA}/dest/{t}.fixos.json', fx)
        L = [dict(i=k + 1, id=x['id'], tipo=x['tipo'], texto=x['texto'], fonte=x['fonte']) for k, x in enumerate(x for x in novos if not fixo(x))]
        grava(f'{PASTA}/dest/{t}.json', dict(tela=comum.superficie(CFG, t)[3:], cenarios=[dict(id=s['id'], regiao=regs[s['region_id']].get('label'), dim=s.get('dimensions'), inicio=((s.get('definition') or {}).get('agora') or '')[:220]) for s in cen], itens=L))
        if L: desp.append(despacho('destino', 'destino', 'haiku', 'medium', f'{PASTA}/dest/{t}.json', f'{PASTA}/dest-saida/{t}.json'))
        else: grava(f'{PASTA}/dest-saida/{t}.json', {})
        print(t, 'novos', len(L), 'já no catálogo', len(res['ja']))
    grava(f'{PASTA}/despachos-dest.json', desp)


def duvida(x):
    return (x.get('texto') or '').startswith(DUVIDA)


def amostra(telas, tudo=False, por_tela=6, semente=7):
    import verifica_itens as V
    random.seed(semente); itens_ = []
    def entrada(t, x, grupo):
        return dict(tela=t, id=x['id'], tipo=x.get('tipo'), texto=x['texto'], fonte=x['fonte'], arquivo=V.resolve(x['fonte'])[0],
                    origem=x['origem'], grupo=grupo, alarme=grupo == 'alarme')
    for t in telas:
        fatos = ler(f'{PASTA}/fatos/{t}.json')
        o = {(x['texto'], x['fonte']): x for x in fatos}
        if tudo:
            itens_ += [entrada(t, x, 'tudo') for x in fatos if x['origem'] != 'S' or duvida(x)]
            continue
        al = ler(f'{PASTA}/alarmes/{t}.json', [])
        va = {(a.get('texto'), a.get('fonte')) for a in al if a.get('status') == 'VALOR_AUSENTE'}
        vai = [x for k, x in o.items() if k in va and x['origem'] != 'S']
        resto = [x for k, x in o.items() if k not in va and x['origem'] != 'S']
        sorteio = random.sample(resto, min(len(resto), por_tela))
        itens_ += [entrada(t, x, 'alarme') for x in vai] + [entrada(t, x, 'sorteado') for x in sorteio]
        itens_ += [entrada(t, x, 'duvida') for x in fatos if duvida(x)]
        print(t, 'alarme', len(va), 'revisão', len(vai) + len(sorteio))
    rev = Path(PASTA) / 'revisao'; rev.mkdir(parents=True, exist_ok=True)
    # amostra nova é revisão nova: a saída velha casaria pela posição com outro item. O já decidido segue em removidos e imprecisos
    for velho in [*rev.glob('lote-*.json'), *(Path(PASTA) / 'revisao-saida').glob('*.json'), rev / 'reenvio.json', rev / 'reenviar.json', Path(PASTA) / 'despachos-reenvio.json']:
        velho.unlink(missing_ok=True)
    desp = []
    for k in range(0, len(itens_), 30):
        n = f'{k // 30:02d}'
        grava(str(rev / f'lote-{n}.json'), [{**x, 'i': j} for j, x in enumerate(itens_[k:k + 30], 1)])
        desp.append(despacho('revisao', 'revisao', 'sonnet', 'medium', rev / f'lote-{n}.json', f'{PASTA}/revisao-saida/lote-{n}.json'))
    grava(f'{PASTA}/despachos-revisao.json', desp); print('lotes', len(desp), 'itens', len(itens_))


def remove_fato(tela, texto, fonte, h):
    for f in (f'{PASTA}/fatos/{tela}.json', f'{PASTA}/S/{tela}.json'):
        if not os.path.exists(f): continue
        a = ler(f); b = [x for x in a if comum.fid(tela, x.get('texto') or '', x.get('fonte') or '') != h]
        if len(b) != len(a): grava(f, b)


def anota_imprecisao(tela, h, motivo):
    f = f'{PASTA}/fatos/{tela}.json'
    if not os.path.exists(f): return
    a = ler(f)
    for x in a:
        if x['id'] == h: x['imprecisao'] = motivo
    grava(f, a)


def revisao_aplica():
    pasta = Path(PASTA); lotes = sorted((pasta / 'revisao').glob('lote-*.json'))
    if not lotes: erro(f'nenhum lote em {PASTA}/revisao: rode `amostra` e despache a revisão antes')
    amo, bsaida = pasta / 'biblioteca/amostra-revisao.json', pasta / 'biblioteca/revisao-saida.json'
    faltam = [f'revisao-saida/{l.name}' for l in lotes if not (pasta / 'revisao-saida' / l.name).exists()]
    if ler(f'{PASTA}/revisao/reenvio.json', []) and not (pasta / 'revisao-saida/reenvio.json').exists(): faltam.append('revisao-saida/reenvio.json')
    if amo.exists() and ler(str(amo)) and not bsaida.exists(): faltam.append('biblioteca/revisao-saida.json')
    if faltam: erro(f'sem saída: {", ".join(faltam)}. Despache o que falta; nada foi aplicado')
    removidos = ler(f'{PASTA}/revisao/removidos.json', []); imprecisos = ler(f'{PASTA}/revisao/imprecisos.json', {})
    ja = {x['id'] for x in removidos}; reenviar = []; voltam = []; n = falsos = 0
    # quem voltou sem citação vai a um agente novo, uma vez só; a resposta dele vale no lugar da primeira
    re_itens = ler(f'{PASTA}/revisao/reenvio.json', []); re_saida = {}
    if re_itens:
        por_i = {x['i']: x['id'] for x in re_itens}
        re_saida = {por_i[r['i']]: r for r in ler(f'{PASTA}/revisao-saida/reenvio.json') if r.get('i') in por_i}
    def tira(tela, texto, fonte, h, motivo, origem):
        remove_fato(tela, texto, fonte, h)
        if h not in ja: ja.add(h); removidos.append(dict(id=h, tela=tela, texto=texto, fonte=fonte, decisao='FALSO', motivo=motivo, origem=origem))
    for lote in lotes:
        its = ler(lote); saida = pasta / 'revisao-saida' / lote.name
        por = {r.get('i'): r for r in ler(str(saida))}
        for x in its:
            r = re_saida.get(x['id']) or por.get(x['i']); dec = (r or {}).get('decisao'); mot = (r or {}).get('motivo') or ''
            if dec not in ('CORRETO', 'IMPRECISO', 'FALSO') or not CITA.search(mot):
                reenviar.append(dict(lote=lote.name, i=x['i'], id=x['id'], tela=x['tela'], motivo=mot or 'sem decisão')); voltam.append(x); continue
            if x.get('grupo') == 'sorteado':
                n += 1; falsos += dec == 'FALSO'
            if dec == 'FALSO': tira(x['tela'], x['texto'], x['fonte'], x['id'], mot, x['origem'])
            elif dec == 'IMPRECISO': imprecisos[x['id']] = mot; anota_imprecisao(x['tela'], x['id'], mot)
    if amo.exists() and bsaida.exists():
        am = ler(str(amo)); cont = {}
        for r in ler(str(bsaida)):
            a = am[r['n']] if isinstance(r.get('n'), int) and 0 <= r['n'] < len(am) else None
            if not a: continue
            f = a['fato']; h = comum.fid('TL-moldura', f['texto'], f['fonte']); nota = r.get('nota'); mot = r.get('motivo') or ''
            cont[nota] = cont.get(nota, 0) + 1
            if nota == 'FALSO':
                if CITA.search(mot): tira('TL-moldura', f['texto'], f['fonte'], h, mot, 'S')
                else: reenviar.append(dict(lote='biblioteca', i=r['n'], id=h, tela='TL-moldura', motivo=mot or 'sem motivo'))
            elif nota == 'IMPRECISO': imprecisos[h] = mot; anota_imprecisao('TL-moldura', h, mot)
        print('revisão de biblioteca', cont)
    grava(f'{PASTA}/revisao/removidos.json', removidos); grava(f'{PASTA}/revisao/imprecisos.json', imprecisos)
    grava(f'{PASTA}/revisao/reenviar.json', reenviar)
    taxa = 100 * falsos / n if n else 0.0
    print(f'taxa de FALSO entre os sorteados (sem os alarmes): {taxa:.1f}% ({falsos}/{n}); removidos {len(removidos)}; para reenviar {len(reenviar)}')
    if voltam and not re_itens:
        grava(f'{PASTA}/revisao/reenvio.json', [dict(x, i=k) for k, x in enumerate(voltam, 1)])
        grava(f'{PASTA}/despachos-reenvio.json', [despacho('revisao', 'revisao', 'sonnet', 'medium', f'{PASTA}/revisao/reenvio.json', f'{PASTA}/revisao-saida/reenvio.json')])
        erro(f'{len(voltam)} itens sem decisão com citação: despache despachos-reenvio.json, uma vez, e rode revisao-aplica de novo')
    if voltam:
        print(f'{len(voltam)} itens sem revisão depois do reenvio: o fato fica, e isso vai ao resumo')
    if n and falsos / n > 0.02:
        print(f'taxa acima de 2%: rode `processo.py amostra {PASTA} --tudo TL...` para conferir todos os fatos.', file=sys.stderr)
        sys.exit(11)


def projeto():
    """O que vale para toda tela: lê uma vez, e nenhum agente de tela repete."""
    os.makedirs(f'{PASTA}/livro', exist_ok=True); desp = []
    for nome, sc in (('TL-moldura', 'livro_moldura.py'), ('TL-global', 'livro_global.py')):
        lv = f'{PASTA}/livro/{nome}.txt'
        checa(rode(sc, lv), f'livro {nome}')
        parte_do_livro(nome, lv, desp)
    if tem_blocos('TL-moldura'):
        desp.append(despacho('ausencias', 'ausencias', 'haiku', 'medium', f'{PASTA}/livro/TL-moldura.txt', f'{PASTA}/A/TL-moldura.json'))
    scr = []
    r = checa(rode('constantes_build.py'), 'constantes_build.py')
    if r.stderr: print(r.stderr.strip(), file=sys.stderr)
    for l in r.stdout.splitlines(): scr += json.loads(l)['itens']
    # só a última linha do script é do projeto; as de tela já foram para S/<tela>.json
    l = checa(rode('nao_usado.py', CFG['fecho']), 'nao_usado.py').stdout.splitlines()
    if l: scr += json.loads(l[-1])['itens']
    grava_script('TL-moldura', scr)
    # perguntas de biblioteca: um componente só uma vez, juntando o que as telas deixaram para o padrão dele
    q = {}
    for f in sorted(glob.glob(f'{PASTA}/S/TL-*.json')):
        for x in ler(f):
            m = COMPONENTE.match(x.get('texto', ''))
            if not m or 'NÃO VERIFICADO' not in m.group(3): continue
            c = q.setdefault((m.group(1), m.group(2)), dict(componente=m.group(1), pacote=m.group(2), props=set(), internos=set()))
            nd = re.search(r'não define ([^;]+?), então vale', m.group(3))
            if nd: c['props'] |= {p.strip() for p in nd.group(1).split(',')}
            elif 'vêm do componente' in m.group(3): c['internos'].add(m.group(3).split(' vêm do componente')[0])
    pacotes = sorted({c['pacote'] for c in q.values()}); nq = 0
    # uma passada por pacote: o agente busca só numa pasta, e o contexto não cresce a ponto de encarecer
    for pac in pacotes:
        pg = [dict(q=i, componente=c['componente'], props=sorted(c['props']), internos=sorted(c['internos'])) for i, c in enumerate(sorted((c for c in q.values() if c['pacote'] == pac), key=lambda c: c['componente']), 1)]
        nq += len(pg); n = pac.replace('/', '__')
        grava(f'{PASTA}/biblioteca/perguntas-{n}.json', dict(pacote=pac, perguntas=pg))
        desp.append(despacho('biblioteca', 'biblioteca', 'haiku', 'medium', f'{PASTA}/biblioteca/perguntas-{n}.json', f'{PASTA}/biblioteca/respostas-{n}.json', pacote=pac))
    grava(f'{PASTA}/despachos-projeto.json', desp)
    print('despachos de projeto', len(desp), 'fatos de script', len(scr), 'perguntas de biblioteca', nq, 'pacotes', pacotes)


def biblioteca_baixa():
    pacotes = sorted({ler(f)['pacote'] for f in glob.glob(f'{PASTA}/biblioteca/perguntas-*.json')})
    if not pacotes:
        if not os.path.exists(f'{PASTA}/despachos-projeto.json'): erro(f'{PASTA} ainda não tem perguntas de biblioteca: rode `projeto` antes', 2)
        print('nada a baixar: nenhuma pergunta de biblioteca'); return
    r = checa(rode('fonte_biblioteca.py', CFG['lib'], *pacotes), 'fonte_biblioteca.py')
    print(r.stdout.strip())
    # `projeto` monta o despacho antes do download: só agora o prompt pode dizer quais pacotes existem
    arq = f'{PASTA}/despachos-projeto.json'
    if os.path.exists(arq):
        grava(arq, [despacho('biblioteca', 'biblioteca', d['modelo'], d['esforco'], d['entrada'], d['saida'], pacote=d['pacote'])
                    if d['etapa'] == 'biblioteca' else d for d in ler(arq)])


def valida_citacao(lib, r):
    """A citação é a prova: só vale o que está naquela linha da versão travada. Devolve (fato, None), (None, motivo) ou (None, None) para NAO_ACHEI."""
    nome = f"{r.get('componente')}.{r.get('item')}"
    if str(r.get('valor')).startswith('NAO_ACHEI'): return None, None
    m = re.match(r'(@?[^@]+)@([^/]+)/(.+):(\d+)', str(r.get('fonte') or ''))
    if not m: return None, (nome, f"citação sem arquivo e linha: {r.get('fonte')}")
    pac, ver, cam, lin = m.groups(); raiz = f"{lib}/{pac.replace('/', '__')}@{ver}"
    arq = next((c for c in (f'{raiz}/{cam}', f'{raiz}/package/{cam}') if os.path.exists(c)), None)
    if not arq: return None, (nome, f'arquivo não existe: {cam}')
    L = open(arq, errors='replace').read().splitlines(); k = int(lin)
    perto = ' '.join(L[max(0, k - 3):k + 2]); tr = (r.get('trecho') or '').strip()
    if not tr or tr[:30] not in perto: return None, (nome, f'trecho não está em {cam}:{lin}')
    return dict(tipo='comportamento', texto=f"{comum.PADRAO}{nome} = {r.get('valor')} ({pac}@{ver}).", fonte=f'{pac}@{ver}/{cam}:{lin}'), None


def biblioteca_confere(resps):
    # glob sem arquivo chega aqui com o asterisco: sem pergunta é legítimo, com pergunta é etapa que não rodou
    resps = [a for r in resps for a in (sorted(glob.glob(r)) if '*' in r else [r])]
    if not resps:
        perguntas = glob.glob(f'{PASTA}/biblioteca/perguntas-*.json')
        if perguntas: erro(f'{len(perguntas)} arquivos de perguntas e nenhuma resposta: despache a biblioteca antes')
        print('nada a conferir: nenhuma pergunta de biblioteca'); return
    ok = []; ruim = []; achei = 0; lib = CFG['lib']
    removidos, _ = revisao_marcas()
    for resp in resps:
        for r in ler(resp):
            fato, mot = valida_citacao(lib, r)
            if fato: ok.append(fato)
            elif mot: ruim.append(mot)
            else: achei += 1
    ok = [x for x in ok if comum.fid('TL-moldura', x['texto'], x['fonte']) not in removidos]
    atual = ler(f'{PASTA}/S/TL-moldura.json', [])
    chave = {(x['texto'], x['fonte']) for x in atual}
    grava(f'{PASTA}/S/TL-moldura.json', atual + [x for x in ok if (x['texto'], x['fonte']) not in chave])
    print('citações conferidas', len(ok), 'recusadas', len(ruim), 'NAO_ACHEI', achei)
    for q, m in ruim: print(' RECUSADA', q, m)


def biblioteca_amostra(n=15):
    passou = []
    for f in sorted(glob.glob(f'{PASTA}/biblioteca/respostas-*.json')):
        for r in ler(f):
            fato, _ = valida_citacao(CFG['lib'], r)
            if fato: passou.append({**r, 'fato': dict(texto=fato['texto'], fonte=fato['fonte'])})
    amo = random.Random(7).sample(passou, min(n, len(passou)))
    grava(f'{PASTA}/biblioteca/amostra-revisao.json', amo)
    grava(f'{PASTA}/despachos-biblioteca-revisao.json', [despacho('biblioteca-revisao', 'biblioteca-revisao', 'sonnet', 'medium', f'{PASTA}/biblioteca/amostra-revisao.json', f'{PASTA}/biblioteca/revisao-saida.json')] if amo else [])
    print('respostas conferidas', len(passou), 'na amostra', len(amo))


def duvidas(telas, lote=8):
    """Os NÃO VERIFICADO das ausências viram lotes pequenos: 21 num agente só estouraram 60 turnos sem gravar nada."""
    fila = []; fatos = {t: ler(f'{PASTA}/fatos/{t}.json') for t in telas}
    resolvidas = {m for fs in fatos.values() for x in fs for m in re.findall(r'^Dúvida resolvida \((F-\w+)\)', x.get('texto') or '')}
    for t in telas:
        for x in fatos[t]:
            tx = x.get('texto') or ''
            # o de script é respondido pela biblioteca; o de corte de trecho é ruído; o já resolvido não volta
            if x.get('origem') == 'S' or x['id'] in resolvidas or not re.search(r'N[ÃA]O[ _]VERIFICAD', tx) or re.search(r'salto|fora do trecho|n[ãa]o est[ãa]o? no trecho', tx, re.I): continue
            fila.append(dict(id=x['id'], tela=t, texto=tx, fonte=x.get('fonte')))
    d = Path(PASTA) / 'duvidas'; d.mkdir(parents=True, exist_ok=True)
    for velho in d.glob('lote-*.json'): velho.unlink()
    desp = []
    for i in range(0, len(fila), lote):
        f = f'{PASTA}/duvidas/lote-{i // lote:02d}.json'; grava(f, fila[i:i + lote])
        desp.append(despacho('duvidas', 'duvidas', 'haiku', 'medium', f, f'{PASTA}/duvidas/resp-{i // lote:02d}.json'))
    grava(f'{PASTA}/despachos-duvidas.json', desp); print('dúvidas', len(fila), 'lotes', len(desp))


def duvidas_grava(pares):
    """Só vira fato o que tem citação batendo. O resto segue visível como NÃO VERIFICADO, sem adivinhar."""
    if len(pares) % 2 or not pares: erro('duvidas-grava espera pares <lote.json> <resp.json>', 2)
    feitos = 0; recusa = []; segue = 0; por = {}
    for ent, resp in zip(pares[::2], pares[1::2]):
        E = ler(ent)
        for r in ler(resp):
            if not isinstance(r.get('n'), int) or not 0 <= r['n'] < len(E): recusa.append((str(r.get('n')), f'n fora do lote {ent}')); continue
            e = E[r['n']]
            if r.get('estado') != 'RESOLVIDO': segue += 1; continue
            m = re.search(r'([^\s;,]+):(\d+)', str(r.get('fonte') or '')); tr = (r.get('trecho') or '').strip()
            if not m or not tr: recusa.append((e['id'], 'sem citação')); continue
            cam, lin = m.group(1), int(m.group(2))
            txt = comum.show(CFG, cam)
            if not txt:
                c = [f for f in glob.glob(f"{CFG['lib']}/**/{os.path.basename(cam)}", recursive=True) if f.endswith(cam.split('package/')[-1])]
                if not c: recusa.append((e['id'], f'arquivo não existe: {cam}')); continue
                txt = open(c[0], errors='replace').read()
            L = txt.splitlines()
            if tr[:25] not in ' '.join(L[max(0, lin - 3):lin + 2]): recusa.append((e['id'], f'trecho não está em {cam}:{lin}')); continue
            por.setdefault(e['tela'], []).append(dict(tipo='comportamento', texto=f"{DUVIDA} ({e['id']}): {r.get('resposta')}", fonte=f'{cam}:{lin}')); feitos += 1
    for t, its in por.items():
        f = f'{PASTA}/S/{t}.json'; a = ler(f, [])
        ch = {(x['texto'], x['fonte']) for x in a}; grava(f, a + [x for x in its if (x['texto'], x['fonte']) not in ch])
    print('resolvidas', feitos, 'seguem abertas', segue, 'recusadas', len(recusa))
    for i, m in recusa: print(' RECUSADA', i, m)


def relidas(saida, telas):
    telas = [t for t in telas if t not in MOLDURAS]  # não são telas do mapa: o resumo as contaria como relidas
    # só fato de script não é leitura: a tela contaria como relida sem ninguém ter lido
    nao_lidas = [t for t in telas if not any(x.get('origem') == 'I' for x in ler(f'{PASTA}/fatos/{t}.json'))]
    if nao_lidas: erro(f'{nao_lidas}: sem fato de leitura, não contam como relidas')
    grava(saida, {'telas': {t: [dict(tipo=x.get('tipo'), texto=x['texto'], fonte=x['fonte']) for x in ler(f'{PASTA}/fatos/{t}.json')] for t in telas}})
    print('telas relidas', len(telas))


def omitidos(saida, telas):
    o = {}
    for t in telas:
        fatos = {x['id']: x for x in ler(f'{PASTA}/fatos/{t}.json')}
        por = {x['i']: x for x in ler(f'{PASTA}/dif/{t}.json')['itens']}
        res = ler(f'{PASTA}/dif-saida/{t}.json')
        o[t] = [dict(tipo=fatos[por[n]['id']].get('tipo'), texto=fatos[por[n]['id']]['texto'], fonte=fatos[por[n]['id']]['fonte'], origem='cega') for n in res['novos'] if not comum.sem_cenario(fatos[por[n]['id']]['texto'], fatos[por[n]['id']]['fonte'])]
    grava(saida, o); print('itens omitidos', sum(len(v) for v in o.values()), 'em', sum(1 for v in o.values() if v), 'telas')


def iniciar(pasta, args):
    def opcao(nome, multiplo=False):
        vals = []
        while nome in args:
            i = args.index(nome)
            if i + 1 >= len(args): erro(f'{nome} sem valor', 2)
            vals.append(args[i + 1]); del args[i:i + 2]
        return vals if multiplo else (vals[-1] if vals else None)
    repo, commit, mapa, lib = opcao('--repo'), opcao('--commit'), opcao('--mapa'), opcao('--lib')
    moldura, sup = opcao('--moldura', True), opcao('--superficie-moldura')
    if args or not (repo and commit and mapa): erro('uso: processo.py iniciar <pasta> --repo R --commit C --mapa M [--lib L] [--moldura ARQ]... [--superficie-moldura SF-X]', 2)
    if not Path(mapa).is_file(): erro(f'mapa não existe: {mapa}', 2)
    try: dados = json.load(open(mapa, encoding='utf-8'))
    except json.JSONDecodeError as e: erro(f'mapa não é JSON válido: {mapa} ({e})', 2)
    alvo = dict(repo=str(Path(repo).resolve()), commit=commit)
    arquivos = comum.todos(alvo)  # sai 2 em commit ou repositório errado
    # mapa de outra versão leria telas que este commit não tem, e o livro sairia vazio sem erro
    real = comum.git(alvo, 'rev-parse', f'{commit}^{{commit}}').stdout.strip()
    if dados.get('candidata_sha') and dados['candidata_sha'] != real:
        erro(f"o mapa é da versão {dados['candidata_sha']}, e --commit é {real}: gere o mapa deste commit", 2)
    fora = [a for a in moldura if a not in arquivos]
    if fora: erro(f'--moldura fora do commit {commit}: {fora}', 2)
    if not moldura and not set(comum.MOLDURA_PADRAO) & set(arquivos):
        print('aviso: nenhum arquivo da moldura padrão neste commit. Passe --moldura, ou os fatos de moldura ficam vazios.', file=sys.stderr)
    cfg = dict(repo=str(Path(repo).resolve()), commit=commit, mapa=str(Path(mapa).resolve()),
               moldura=moldura or list(comum.MOLDURA_PADRAO), superficie_moldura=sup or comum.SUPERFICIE_PADRAO)
    if lib: cfg['lib'] = str(Path(lib).resolve())
    os.makedirs(pasta, exist_ok=True)
    grava(f'{pasta}/config.json', cfg)
    global PASTA, CFG
    PASTA = str(Path(pasta).resolve()); os.environ['FATOS_PASTA'] = PASTA; CFG = comum.carrega(PASTA)
    checa(rode('fecho.py', cfg['mapa']), 'fecho.py')
    r = checa(rode('poda_barril.py', cfg['mapa']), 'poda_barril.py')
    if r.stderr: print(r.stderr.strip(), file=sys.stderr)
    print(r.stdout.strip().splitlines()[-1:] or '')
    print('iniciado em', PASTA)


def main(argv):
    global PASTA, CFG
    if len(argv) < 2: print(__doc__, file=sys.stderr); sys.exit(2)
    cmd, pasta, *r = argv
    if cmd == 'iniciar': return iniciar(pasta, r)
    if cmd not in COMANDOS: print(f'subcomando desconhecido: {cmd}\n{__doc__}', file=sys.stderr); sys.exit(2)
    PASTA = str(Path(pasta).resolve()); os.environ['FATOS_PASTA'] = PASTA
    CFG = comum.carrega(PASTA)
    COMANDOS[cmd](r)


def _ao_lado(r):
    if '--ao-lado' not in r: return None, r
    i = r.index('--ao-lado'); lado = r[i + 1] if i + 1 < len(r) else erro('--ao-lado sem pasta', 2)
    return lado, r[:i] + r[i + 2:]


def _grava(r):
    lado, r = _ao_lado(r)
    if len(r) < 3: erro('uso: grava <pasta> <catalogo.json> <saida.json> [--ao-lado PASTA] TL...', 2)
    grava_catalogo(r[0], r[1], lado, telas_do_mapa(r[2:]))


def _duas(f, n, uso):
    def g(r):
        if len(r) < n: erro('uso: ' + uso, 2)
        return f(r)
    return g


COMANDOS = {
    'prepara': lambda r: prepara(r), 'confere': lambda r: confere(telas_do_mapa(r)), 'junta': lambda r: junta(telas_do_mapa(r)),
    'dif': _duas(lambda r: dif(r[0], telas_do_mapa(r[1:])), 2, 'dif <pasta> <catalogo.json> TL...'),
    'dest': _duas(lambda r: dest(r[0], telas_do_mapa(r[1:])), 2, 'dest <pasta> <catalogo.json> TL...'),
    'amostra': lambda r: amostra(telas_do_mapa([a for a in r if a != '--tudo']), '--tudo' in r),
    'grava': _grava, 'projeto': lambda r: projeto(), 'duvidas': lambda r: duvidas(telas_do_mapa(r)),
    'duvidas-grava': lambda r: duvidas_grava(r), 'biblioteca-baixa': lambda r: biblioteca_baixa(),
    'biblioteca-confere': lambda r: biblioteca_confere(r), 'biblioteca-amostra': lambda r: biblioteca_amostra(int(r[0]) if r else 15),
    'revisao-aplica': lambda r: revisao_aplica(),
    'relidas': _duas(lambda r: relidas(r[0], telas_do_mapa(r[1:])), 2, 'relidas <pasta> <saida.json> TL...'),
    'omitidos': _duas(lambda r: omitidos(r[0], telas_do_mapa(r[1:])), 2, 'omitidos <pasta> <saida.json> TL...'),
}

if __name__ == '__main__':
    main(sys.argv[1:])
