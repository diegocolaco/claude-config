"""Cenário `primeira-sincronizacao` do montador de versões: o uso real em que o pedido é vago e não há versão nomeada.

Importado só por `montar_versoes.py --cenario primeira-sincronizacao` (tamanho grande). Reproduz em material sintético:
- protótipo com DOIS commits em `main`: `init` (só README.md, o `commit_sha` do `upstream.json`) e o conteúdo da v11 do tamanho
  grande (as mesmas telas) com o `reference-version.json` do próprio protótipo (não é a vigente do produto);
- `package-lock.json` com centenas de pacotes e a chave `"version"` repetida em ~6000 linhas;
- `mock/mapa-grande.ts` com ~5000 linhas, usado por UMA tela (Margem);
- produto = scaffold com uma tela genérica, sem catálogo de paridade (`.squad/contracts/parity/catalog.json` ausente).
O gabarito (telas, lockfile, mock volumoso, diferenças esperadas por tela) é gravado só em `--gabarito`, fora do destino.
Saída determinística (nada de relógio nem sorteio). Só biblioteca padrão.
"""
import base64
import hashlib
import tempfile
from pathlib import Path

TELA_DO_MOCK = 'Margem'  # a única tela que lê /api/mapa-grande
ENDPOINT_ANTIGO = '/api/relatorios/margem'
ENDPOINT_MOCK = '/api/mapa-grande'
CAMPO_MOCK = 'codigoMapaGrande'
PACOTES = 860
REGISTROS_MOCK = 560
README_INICIAL = '# Protótipo de gestão\n'
REGIOES = ['Sul', 'Sudeste', 'Centro-Oeste', 'Nordeste', 'Norte']


def _versao(i):
    return f'{1 + i % 7}.{i % 13}.{i % 5}'


def lockfile():
    """package-lock.json (v3) com `PACOTES` pacotes; cada um repete a chave `"version"`."""
    pacotes = {'': {'name': 'prototipo-gestao', 'version': '1.0.0',
                    'dependencies': {'antd': '^6.0.0', '@umijs/max': '^4.4.0', 'dayjs': '^1.11.13', 'react': '^19.0.0'}}}
    pacotes['node_modules/antd'] = {'version': '6.0.0', 'resolved': 'https://registry.example.invalid/antd/-/antd-6.0.0.tgz',
                                    'integrity': _integridade('antd@6.0.0'), 'license': 'MIT'}
    for i in range(1, PACOTES):
        nome = f'@fixture/pacote-{i:04d}'
        v = _versao(i)
        entrada = {'version': v, 'resolved': f'https://registry.example.invalid/{nome}/-/pacote-{i:04d}-{v}.tgz',
                   'integrity': _integridade(f'{nome}@{v}'), 'license': 'MIT'}
        if i % 3 == 0:
            entrada['dependencies'] = {f'@fixture/pacote-{i - 1:04d}': f'^{_versao(i - 1)}'}
        pacotes[f'node_modules/{nome}'] = entrada
    return {'name': 'prototipo-gestao', 'version': '1.0.0', 'lockfileVersion': 3, 'requires': True, 'packages': pacotes}


def _integridade(texto):
    return 'sha512-' + base64.b64encode(hashlib.sha512(texto.encode('utf-8')).digest()).decode('ascii')


def mock_grande():
    """mock/mapa-grande.ts: dado gerado de ~5000 linhas, com um campo próprio que só a tela Margem usa."""
    L = ["import type { Request, Response } from 'express';", '', 'const mapaGrande = [']
    for i in range(1, REGISTROS_MOCK + 1):
        L += ['  {', f'    id: {i},', f"    {CAMPO_MOCK}: 'MG-{i:05d}',", f"    regiao: '{REGIOES[i % len(REGIOES)]}',",
              f"    volume: {1000 + i * 37},", f"    margemPrevista: {(i % 17) + 0.5},", f"    competencia: '2026-{1 + i % 12:02d}',",
              f"    observacao: 'Faixa {i % 40} do mapa',", '  },']
    L += ['];', '', 'export default {', f"  'GET {ENDPOINT_MOCK}': (req: Request, res: Response) => {{",
          '    res.json({ data: mapaGrande, total: mapaGrande.length });', '  },', '};', '']
    return '\n'.join(L)


def liga_tela_ao_mock(texto):
    """A tela Margem passa a ler o endpoint e o campo do mock grande."""
    if ENDPOINT_ANTIGO not in texto or '  margem?: number;' not in texto:
        raise SystemExit('Margem.tsx mudou: ajuste primeira_sincronizacao.liga_tela_ao_mock')
    texto = texto.replace(ENDPOINT_ANTIGO, ENDPOINT_MOCK)
    return texto.replace('  margem?: number;', f'  margem?: number;\n  {CAMPO_MOCK}?: string;', 1)


def arquivos_prototipo(mv):
    """Conteúdo da v11 do tamanho grande, com o lockfile grande e o mock grande ligado a uma tela."""
    arquivos = mv.arquivos_proto('grande', '11')
    arquivos['package-lock.json'] = lockfile()
    arquivos['mock/mapa-grande.ts'] = mock_grande()
    tela = next(t for t in mv.TELAS_GRANDE if t[1] == TELA_DO_MOCK)
    caminho = mv.arquivo_proto(tela)
    arquivos[caminho] = liga_tela_ao_mock(arquivos[caminho])
    return arquivos


def _commit_inicial(mv, raiz):
    """Primeiro commit do protótipo, quase vazio (só o README), como o histórico real; é o `commit_sha` do `upstream.json`."""
    mv.git_init(raiz)
    mv.mf.write(raiz, {'README.md': README_INICIAL})
    return mv.mf.commit(raiz, 'init')


def _registro_do_prototipo(mv, workspace, arquivos, inicial):
    """`reference-version.json` e a impressão digital dele, gerados num repositório descartável.

    O registro grava no repositório um log de operações com ids aleatórios; fazê-lo num descartável (com o mesmo commit
    inicial, que tem o mesmo SHA por ter conteúdo e datas fixos) mantém a saída do protótipo determinística.
    """
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp) / 'origem'
        if _commit_inicial(mv, raiz) != inicial:
            raise SystemExit('o commit inicial do descartável difere do commit inicial do protótipo')
        mv.mf.write(raiz, {c: arquivos[c] for c in ('package.json', 'package-lock.json', 'upstream.json')})
        mv.registrar(workspace, raiz)
        return (raiz / 'reference-version.json').read_text(encoding='utf-8'), mv.inspecionar(workspace, raiz)


def construir_prototipo(mv, dest, workspace):
    """Dois commits em `main`: `init` (só README.md) e a v11 grande com o `reference-version.json` do próprio protótipo.

    O `commit_sha` do `upstream.json` é o commit `init`, ancestral do HEAD: `reference inspect` e `register-version` funcionam.
    O registro do protótipo não é a vigente do produto.
    """
    root = dest / 'prototipo'
    inicial = _commit_inicial(mv, root)
    arquivos = arquivos_prototipo(mv)
    arquivos['upstream.json'] = {
        'schema_version': '1.0', 'repository': 'https://example.invalid/upstream', 'commit_sha': inicial,
        'branch': 'master', 'license': 'MIT', 'local_project': 'prototipo-gestao', 'source_type': 'public-repository',
        'lovable_generation': None, 'export_archive': None, 'sdd_supplied': False}
    arquivos['reference-version.json'], digest = _registro_do_prototipo(mv, workspace, arquivos, inicial)
    arquivos['.squad/project.yaml'] = (f'schema_version: "1.0"\nproject_uid: {mv.mf.PROTO_UID}\nproject_slug: prototipo-gestao\n'
                                       'name: Protótipo de gestão\ndefault_branch: main\n')
    mv.mf.write(root, arquivos)
    candidata = mv.mf.commit(root, 'feat: protótipo de gestão')
    return root, inicial, candidata, digest


def construir_produto(mv, dest):
    """Scaffold sem catálogo: uma tela genérica, a rota e o `project.yaml`."""
    root = dest / 'produto'
    mv.git_init(root)
    mv.mf.write(root, {
        '.squad/project.yaml': (f'schema_version: "1.0"\nproject_uid: {mv.mf.PRODUCT_UID}\nproject_slug: produto-gestao\n'
                                'name: Produto de gestão\ndefault_branch: main\n'),
        'README.md': '# Produto de gestão\n\nScaffold inicial: uma tela genérica e nenhuma paridade com o protótipo ainda.\n',
        'apps/web/src/pages/Inicio.tsx': ("export default function Inicio() {\n  return <h1>Bem-vindo</h1>;\n}\n"),
        'apps/web/src/app.tsx': ("import { createBrowserRouter } from 'react-router-dom';\nimport Inicio from './pages/Inicio';\n\n"
                                 "export const router = createBrowserRouter([\n  { path: '/', element: <Inicio /> },\n]);\n"),
    })
    mv.mf.commit(root, 'chore: scaffold do produto')
    return root


def montar_gabarito(mv, mapa, candidata, vigente_vazia, digest_proprio, inicial):
    """Telas (nomes e IDs), lockfile, mock volumoso e as diferenças esperadas por tela (todas novas na primeira sincronização)."""
    por_arquivo = {t['arquivo']: t for t in mapa['telas'] if t['arquivo']}
    telas, difs = [], []
    for t in mv.telas_da_versao(mv.TELAS_GRANDE, '11'):
        arquivo = mv.arquivo_proto(t)
        no_mapa = por_arquivo.get(arquivo)
        telas.append({'nome': t[1], 'id': no_mapa['id'] if no_mapa else None, 'rota': mv.rota_da_tela(t), 'arquivo': arquivo})
        if no_mapa:
            difs.append({'id': f'DF-{no_mapa["id"]}', 'tela': no_mapa['id'], 'tipo': 'nova', 'arquivo': arquivo,
                         'descricao': f'Tela {t[1]} nova no produto: não existia na vigente (árvore vazia)', 'trechos': no_mapa['trechos']})
    trechos_lock = [t['id'] for t in mapa['trechos'] if t['arquivo'] == 'package-lock.json']
    trechos_mock = [t['id'] for t in mapa['trechos'] if t['arquivo'] == 'mock/mapa-grande.ts']
    tela_mock = por_arquivo[mv.arquivo_proto(next(t for t in mv.TELAS_GRANDE if t[1] == TELA_DO_MOCK))]
    return {
        'cenario': 'primeira-sincronizacao', 'tamanho': 'grande', 'commit_inicial': inicial, 'candidata': candidata, 'vigente': vigente_vazia,
        'orcamento': mv.ORCAMENTO, 'peso_total': mapa['peso_total'], 'peso_sem_tela': mapa['peso_sem_tela'],
        'n_trechos': len(mapa['trechos']), 'n_telas_no_mapa': len(mapa['telas']),
        'registro_do_proprio_prototipo': {'fingerprint': digest_proprio, 'e_vigente_do_produto': False},
        'telas': telas, 'diferencas_esperadas': difs,
        'lockfile': {'arquivo': 'package-lock.json', 'pacotes': PACOTES, 'trechos': trechos_lock,
                     'esperado': 'um trecho único do tipo arquivo, com destino SEM_IMPACTO e motivo'},
        'mock_volumoso': {'arquivo': 'mock/mapa-grande.ts', 'registros': REGISTROS_MOCK, 'trechos': trechos_mock,
                          'tela_que_usa': tela_mock['id'], 'esperado': 'só aviso; destino pelo cabeçalho e pelas chaves'},
        'catalogo_do_produto': None,
    }
