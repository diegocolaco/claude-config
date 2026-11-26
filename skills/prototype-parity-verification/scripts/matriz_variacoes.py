#!/usr/bin/env python3
"""Matriz de variações para o plano, derivada da passada de ausências. Cada alvo da tela vira linhas por estado, com o que o protótipo faz.
O teste do plano precisa cobrir cada linha; quando a resposta é NAO, o esperado é a ausência (não inventar mensagem que o protótipo não tem).

uso: matriz_variacoes.py <A-Hm/TL-x.json> [<A-Hm/TL-y.json> ...]"""
import json,sys,os,re
NOME={'A':'sessão e permissão','1':'carregamento','2':'falha','3':'vazio','4':'sucesso','5':'efeito real','6':'entrada','7':'caminho do dado','8':'navegação'}
def sai(msg):
    print(msg,file=sys.stderr);sys.exit(2)
if len(sys.argv)<2: sai(__doc__)
lidos=[]
for a in sys.argv[1:]:
    try: d=json.load(open(a,encoding='utf-8'))
    except OSError as e: sai(f'{a}: não consegui abrir ({e.strerror})')
    except json.JSONDecodeError as e: sai(f'{a}: não é JSON válido ({e})')
    if not isinstance(d,list) or any(not isinstance(b,dict) for b in d): sai(f'{a}: esperava a lista de alvos da passada de ausências')
    lidos.append((a,d))
for a,d in lidos:
    t=re.sub(r'\.json$','',os.path.basename(a));tot=0;nao=0
    print(f'## {t}\n')
    print('| Alvo | Variação | O protótipo faz | Fonte |');print('|---|---|---|---|')
    for b in d:
        for it in b.get('itens',[]):
            n=NOME.get(str(it.get('pergunta')),'?');tx=(it.get('texto') or '').replace('|','\\|').replace('\n',' ')
            tot+=1;nao+=it.get('resposta')=='NAO'
            print(f"| {b.get('alvo')} | {n} | {'não tem: ' if it.get('resposta')=='NAO' else ''}{tx} | {it.get('fonte')} |")
    print(f'\n{tot} variações, {nao} são ausências.\n')
