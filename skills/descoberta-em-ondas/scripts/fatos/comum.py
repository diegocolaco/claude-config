#!/usr/bin/env python3
"""Configuração e leitura do protótipo, comuns a todos os scripts da passada de fatos.

`<pasta>/config.json` guarda repo, commit, mapa, moldura, superficie_moldura e, se informada, lib. Os scripts acham a pasta
pela variável FATOS_PASTA (o `processo.py` a define). O protótipo só é lido por `git show` e `git ls-tree`.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

MOLDURA_PADRAO = ['src/app.tsx', 'src/requestErrorConfig.ts', 'config/defaultSettings.ts', 'config/config.ts', 'src/access.ts',
                  'src/global.tsx', 'src/global.less', 'src/global.style.ts']
SUPERFICIE_PADRAO = 'SF-LAYOUT'
# mock e worker são apoio do protótipo: o fato existe, mas não é tela que se construa nem omissão a corrigir
BASTIDOR = re.compile(r'(^|/)(mock|cloudflare-worker)/|_mock\.')
PADRAO = 'Padrão de biblioteca: '
_cfgs = {}
_todos = {}
_conj = {}
_shows = {}


def sem_cenario(texto, fonte):
    """Fato que, sem cenário existente, fica só no arquivo ao lado: código de apoio, código que nada alcança ou padrão
    de biblioteca, que aparece na tela mas é de quem usa o componente: cada tela o recebe na chave `biblioteca`."""
    texto = texto or ''
    return bool(BASTIDOR.search(fonte or '')) or 'NÃO USADO' in texto or texto.startswith(PADRAO)


def erro(msg, codigo=2):
    print(msg, file=sys.stderr)
    raise SystemExit(codigo)


def carrega(pasta=None):
    pasta = pasta or os.environ.get('FATOS_PASTA')
    if not pasta:
        erro('pasta da passada de fatos não informada (FATOS_PASTA)')
    pasta = str(Path(pasta).resolve())
    if pasta not in _cfgs:
        arq = Path(pasta) / 'config.json'
        if not arq.exists():
            erro(f'{arq} não existe: rode `processo.py iniciar` antes')
        try:
            cfg = json.loads(arq.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            erro(f'{arq} não é JSON válido: {e}')
        cfg['pasta'] = pasta
        cfg['lib'] = cfg.get('lib') or str(Path(pasta) / 'LIB')
        cfg['moldura'] = cfg.get('moldura') or list(MOLDURA_PADRAO)
        cfg['superficie_moldura'] = cfg.get('superficie_moldura') or SUPERFICIE_PADRAO
        cfg['fecho'] = str(Path(pasta) / 'fecho-podado.json')
        _cfgs[pasta] = cfg
    return _cfgs[pasta]


def git(cfg, *args):
    try:
        return subprocess.run(['git', '-C', cfg['repo'], *args], capture_output=True, text=True, errors='replace')
    except FileNotFoundError:
        erro('git não encontrado')


def todos(cfg):
    """Arquivos do commit. Falha aqui (repositório ou commit errado) sai 2, em vez de virar livro vazio."""
    chave = (cfg['repo'], cfg['commit'])
    if chave not in _todos:
        r = git(cfg, 'ls-tree', '-r', '--name-only', cfg['commit'])
        if r.returncode:
            erro(f"não consegui ler o commit {cfg['commit']} em {cfg['repo']}: {r.stderr.strip()[-200:]}")
        _todos[chave] = r.stdout.splitlines()
        _conj[chave] = set(_todos[chave])
    return _todos[chave]


def show(cfg, arq):
    """Conteúdo do arquivo no commit. Arquivo que não existe nele dá vazio; qualquer outra falha sai 2."""
    chave = (cfg['repo'], cfg['commit'], arq)
    if chave not in _shows:
        todos(cfg)
        if arq not in _conj[(cfg['repo'], cfg['commit'])]:
            _shows[chave] = ''
        else:
            r = git(cfg, 'show', f"{cfg['commit']}:{arq}")
            if r.returncode:
                erro(f"git show falhou para {cfg['commit']}:{arq} em {cfg['repo']}: {r.stderr.strip()[-200:]}")
            _shows[chave] = r.stdout
    return _shows[chave]


def fid(tela, texto, fonte):
    import hashlib
    return 'F-' + hashlib.sha1((tela + texto + fonte).encode()).hexdigest()[:10]


def superficie(cfg, tela):
    """Superfície do catálogo: a moldura e o global ficam numa só, as telas em SF-<id sem TL->."""
    return cfg['superficie_moldura'] if tela in ('TL-moldura', 'TL-global') else 'SF-' + tela[3:]
