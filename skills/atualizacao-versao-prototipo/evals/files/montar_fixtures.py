"""Monta repositórios sintéticos (protótipo e produto) para as avaliações da skill.

Uso: python3 montar_fixtures.py <destino> --cenario sem-catalogo|com-catalogo|fechar-onda --workspace <raiz-do-playground>
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

GIT = ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'init.defaultBranch=main',
       '-c', 'commit.gpgsign=false']
PRODUCT_UID = '01FIXTUREPRODUTO0000000001'
PROTO_UID = '01FIXTUREPROTOTIPO00000001'


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def write(root, files):
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text if isinstance(text, str) else json.dumps(text, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def commit(root, message):
    run(GIT + ['add', '-A'], root)
    run(GIT + ['commit', '-q', '-m', message], root)
    return run(['git', 'rev-parse', 'HEAD'], root)


def pedidos_proto(extra_button, filtro):
    botoes = ['<Button>Novo pedido</Button>'] + ([f'<Button>{extra_button}</Button>'] if extra_button else [])
    filtro_txt = '\n      <RangePicker placeholder="Período" />' if filtro else ''
    return f'''import {{ Button, Table, DatePicker }} from 'antd';
const {{ RangePicker }} = DatePicker;
export default function Pedidos() {{
  return (
    <div>{filtro_txt}
      {' '.join(botoes)}
      <Table columns={{[{{ title: 'Número' }}, {{ title: 'Cliente' }}, {{ title: 'Status' }}]}} />
    </div>
  );
}}
'''


def clientes_proto(cpf_obrigatorio):
    regra = "rules={[{ required: true, message: 'Informe o CPF' }]}" if cpf_obrigatorio else ''
    return f'''import {{ Form, Input, Button }} from 'antd';
export default function Clientes() {{
  return (
    <Form>
      <Form.Item label="Nome" name="nome"><Input /></Form.Item>
      <Form.Item label="CPF" name="cpf" {regra}><Input /></Form.Item>
      <Button htmlType="submit">Salvar</Button>
    </Form>
  );
}}
'''


def build_prototype(dest, workspace, scenario):
    root = dest / 'prototipo'
    root.mkdir(parents=True)
    run(GIT + ['init', '-q'], root)
    run(['git', 'config', 'user.name', 'Fixture'], root)
    run(['git', 'config', 'user.email', 'fixture@example.invalid'], root)
    write(root, {
        'package.json': {'name': 'prototipo-fixture', 'version': '1.0.0', 'private': True, 'dependencies': {'antd': '5.0.0'}},
        'package-lock.json': {'name': 'prototipo-fixture', 'lockfileVersion': 3, 'packages': {}},
        'config/routes.ts': "export default [\n  { path: '/pedidos', component: './Pedidos' },\n  { path: '/clientes', component: './Clientes' },\n];\n",
        'src/pages/Pedidos.tsx': pedidos_proto('Exportar CSV', False),
        'src/pages/Clientes.tsx': clientes_proto(False),
        'README.md': '# Protótipo (fixture)\n',
    })
    upstream = commit(root, 'upstream: base app')
    write(root, {
        'upstream.json': {'schema_version': '1.0', 'repository': 'https://example.invalid/upstream', 'commit_sha': upstream,
                          'branch': 'master', 'license': 'MIT', 'local_project': 'prototipo-fixture',
                          'source_type': 'public-repository', 'lovable_generation': None, 'export_archive': None,
                          'sdd_supplied': False},
        '.squad/project.yaml': f'schema_version: "1.0"\nproject_uid: {PROTO_UID}\nproject_slug: prototipo-fixture\nname: Protótipo fixture\ndefault_branch: main\n',
    })
    commit(root, 'chore: registra origem upstream')
    jarbas = workspace / 'ecosystem/automation/jarbas.py'
    subprocess.run([sys.executable, str(jarbas), 'reference', 'register-version', '--project-root', str(root),
                    '--kind', 'public-repository'], check=True, capture_output=True, text=True, cwd=workspace)
    vigente = commit(root, 'chore: registra versão de referência vigente')
    run(GIT + ['checkout', '-q', '-b', 'nova-versao'], root)
    write(root, {'src/pages/Pedidos.tsx': pedidos_proto(None, True), 'src/pages/Clientes.tsx': clientes_proto(True)})
    nova = commit(root, 'feat: filtro por período em pedidos, CPF obrigatório, remove exportação CSV')
    run(GIT + ['checkout', '-q', 'main'], root)
    if scenario == 'fechar-onda':
        # onda já adotada: a versão nova entrou no main e foi registrada
        run(GIT + ['merge', '-q', '--ff-only', 'nova-versao'], root)
        subprocess.run([sys.executable, str(jarbas), 'reference', 'register-version', '--project-root', str(root),
                        '--kind', 'public-repository', '--overwrite'], check=True, capture_output=True, text=True, cwd=workspace)
        nova = commit(root, 'chore: registra versão de referência adotada')
    return root, upstream, vigente, nova


def build_product(dest, scenario, proto_vigente, proto_nova, proto_digest):
    root = dest / 'produto'
    root.mkdir(parents=True)
    run(GIT + ['init', '-q'], root)
    run(['git', 'config', 'user.name', 'Fixture'], root)
    run(['git', 'config', 'user.email', 'fixture@example.invalid'], root)
    write(root, {
        '.squad/project.yaml': f'schema_version: "1.0"\nproject_uid: {PRODUCT_UID}\nproject_slug: produto-fixture\nname: Produto fixture\ndefault_branch: main\n',
        'apps/web/src/app.tsx': "import Pedidos from './pages/Pedidos';\nimport Clientes from './pages/Clientes';\nexport const routes = [\n  { path: '/pedidos', element: <Pedidos /> },\n  { path: '/clientes', element: <Clientes /> },\n];\nexport const nav = ['Pedidos', 'Clientes'];\n",
        'apps/web/src/pages/Pedidos.tsx': '''import { Button, Table, message } from 'antd';
import { reenviarAoErp } from '../integracoes/erp';
export default function Pedidos() {
  const salvar = async () => {
    try { await reenviarAoErp(); } catch (e) { message.error(`Erro ao salvar (código de rastreio: ${e.traceId})`); }
  };
  return (
    <div>
      <Button>Novo pedido</Button> <Button>Exportar CSV</Button> <Button onClick={salvar}>Reenviar ao ERP</Button>
      <Table columns={[{ title: 'Número' }, { title: 'Cliente' }, { title: 'Status' }]} />
    </div>
  );
}
''',
        'apps/web/src/pages/Clientes.tsx': '''import { Form, Input, Button } from 'antd';
export default function Clientes() {
  return (
    <Form>
      <Form.Item label="Nome" name="nome"><Input /></Form.Item>
      <Form.Item label="CPF" name="cpf"><Input /></Form.Item>
      <Button htmlType="submit">Salvar</Button>
    </Form>
  );
}
''',
        'apps/web/src/integracoes/erp.ts': "export async function reenviarAoErp() { /* fila real do ERP */ }\n",
    })
    base = commit(root, 'feat: telas de pedidos e clientes')
    if scenario == 'fechar-onda':
        # onda implementada: filtro e CPF da versão nova; sobras (CSV, ERP, rótulo) ainda pendentes de decisão
        pedidos = (root / 'apps/web/src/pages/Pedidos.tsx').read_text(encoding='utf-8')
        pedidos = pedidos.replace("import { Button, Table, message } from 'antd';", "import { Button, Table, DatePicker, message } from 'antd';\nconst { RangePicker } = DatePicker;")
        pedidos = pedidos.replace('    <div>\n', '    <div>\n      <RangePicker placeholder="Período" />\n')
        clientes = (root / 'apps/web/src/pages/Clientes.tsx').read_text(encoding='utf-8')
        clientes = clientes.replace('label="Nome"', 'label="Nome completo"').replace(
            '<Form.Item label="CPF" name="cpf">', "<Form.Item label=\"CPF\" name=\"cpf\" rules={[{ required: true, message: 'Informe o CPF' }]}>")
        write(root, {'apps/web/src/pages/Pedidos.tsx': pedidos, 'apps/web/src/pages/Clientes.tsx': clientes})
        base = commit(root, 'feat: onda da versão nova (filtro por período, CPF obrigatório)')
    if scenario == 'sem-catalogo':
        return root
    catalog = catalog_for(scenario, base, proto_vigente, proto_nova, proto_digest)
    write(root, {'.squad/contracts/parity/catalog.json': catalog})
    commit(root, 'chore: catálogo de paridade')
    if scenario == 'com-catalogo':
        write(root, {'apps/web/src/pages/Clientes.tsx': (root / 'apps/web/src/pages/Clientes.tsx').read_text(encoding='utf-8').replace('label="Nome"', 'label="Nome completo"')})
        commit(root, 'fix: rótulo do nome do cliente')
    return root


def catalog_for(scenario, product_commit, proto_vigente, proto_nova, proto_digest):
    ev = lambda i, kind, loc: {'id': i, 'kind': kind, 'locator': loc}
    common = {
        'schema_version': '1.0', 'project_uid': PRODUCT_UID, 'mode': 'FULL', 'scope_claim': 'KNOWN_SCENARIOS',
        'surfaces': [{'id': 'SF-PEDIDOS'}, {'id': 'SF-CLIENTES'}],
        'regions': [
            {'id': 'RG-PEDIDOS-ACOES', 'surface_id': 'SF-PEDIDOS', 'discovery_status': 'INVESTIGADO', 'provenance_refs': ['EV-P1']},
            {'id': 'RG-CLIENTES-FORM', 'surface_id': 'SF-CLIENTES', 'discovery_status': 'INVESTIGADO', 'provenance_refs': ['EV-C1']},
        ],
        'states': [
            {'id': 'ST-PEDIDOS-LISTA', 'region_id': 'RG-PEDIDOS-ACOES', 'discovery_status': 'INVESTIGADO', 'provenance_refs': ['EV-P1']},
            {'id': 'ST-CLIENTES-NOVO', 'region_id': 'RG-CLIENTES-FORM', 'discovery_status': 'INVESTIGADO', 'provenance_refs': ['EV-C1']},
        ],
        'scenarios': [
            {'id': 'SC-PEDIDOS-ACOES', 'region_id': 'RG-PEDIDOS-ACOES', 'state_id': 'ST-PEDIDOS-LISTA', 'dimensions': ['functional'],
             'definition': {'botoes': ['Novo pedido', 'Exportar CSV'], 'colunas': ['Número', 'Cliente', 'Status']}},
            {'id': 'SC-CLIENTES-FORM', 'region_id': 'RG-CLIENTES-FORM', 'state_id': 'ST-CLIENTES-NOVO', 'dimensions': ['functional'],
             'definition': {'campos': ['Nome', 'CPF'], 'cpf_obrigatorio': False}},
        ],
        'evidence': [ev('EV-P1', 'src', f'prototipo@{proto_vigente}:src/pages/Pedidos.tsx'),
                     ev('EV-C1', 'src', f'prototipo@{proto_vigente}:src/pages/Clientes.tsx')],
        'differences': [], 'requirements': [], 'journeys': [], 'tasks': [], 'tests': [],
    }
    if scenario == 'com-catalogo':
        common.update({'reference': {'version': proto_vigente, 'digest': proto_digest}, 'target': {'commit': product_commit},
                       'baseline': {'trusted': True, 'reference_digest': proto_digest, 'target_commit': product_commit}})
        return common
    # fechar-onda: catálogo adotado da versão nova, com sobras pendentes de decisão
    common['scenarios'][0]['definition'] = {'botoes': ['Novo pedido'], 'filtros': ['Período'], 'colunas': ['Número', 'Cliente', 'Status']}
    common['scenarios'][1]['definition'] = {'campos': ['Nome', 'CPF'], 'cpf_obrigatorio': True}
    common['evidence'] = [ev('EV-P1', 'src', f'prototipo@{proto_nova}:src/pages/Pedidos.tsx'),
                          ev('EV-C1', 'src', f'prototipo@{proto_nova}:src/pages/Clientes.tsx')]
    common.update({'reference': {'version': proto_nova, 'digest': proto_digest}, 'target': {'commit': product_commit},
                   'baseline': {'trusted': False}})
    common['differences'] = [
        {'id': 'DF-ERP', 'surface_id': 'SF-PEDIDOS', 'classe': 'SGD-PROPRIO', 'resumo': 'Botão «Reenviar ao ERP» só no produto (integração real com a fila do ERP)', 'requirement_ids': [], 'task_ids': []},
        {'id': 'DF-CSV', 'surface_id': 'SF-PEDIDOS', 'classe': 'SOBRA-PROTO-ANTIGO', 'resumo': '«Exportar CSV» existia na versão anterior e saiu da nova', 'prova': f'prototipo@{proto_vigente}:src/pages/Pedidos.tsx', 'requirement_ids': [], 'task_ids': []},
        {'id': 'DF-NOME', 'surface_id': 'SF-CLIENTES', 'classe': 'NAO_COMPROVADA', 'resumo': 'Rótulo «Nome completo» só no produto, sem origem comprovada', 'requirement_ids': [], 'task_ids': []},
    ]
    return common


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('destino', type=Path)
    parser.add_argument('--cenario', required=True, choices=['sem-catalogo', 'com-catalogo', 'fechar-onda'])
    parser.add_argument('--workspace', required=True, type=Path)
    args = parser.parse_args()
    dest = args.destino.resolve()
    if dest.exists() and any(dest.iterdir()):
        sys.exit(f'destino não vazio: {dest}')
    dest.mkdir(parents=True, exist_ok=True)
    proto, upstream, vigente, nova = build_prototype(dest, args.workspace.resolve(), args.cenario)
    inspect = json.loads(subprocess.run([sys.executable, str(args.workspace.resolve() / 'ecosystem/automation/jarbas.py'), 'reference',
                                         'inspect', '--project-root', str(proto)], check=True, capture_output=True, text=True).stdout)
    digest = inspect.get('fingerprint') or inspect.get('version', {}).get('fingerprint')
    build_product(dest, args.cenario, vigente, nova, digest)
    print(json.dumps({'prototipo': str(proto), 'produto': str(dest / 'produto'), 'upstream': upstream,
                      'vigente': vigente, 'nova_versao': nova, 'fingerprint': digest}, indent=2))


if __name__ == '__main__':
    main()
