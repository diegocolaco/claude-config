"""Variante `irmas` do montador de versões: telas irmãs escritas à mão, no idioma real do ant-design-pro.

Importado só por `montar_versoes.py --variante irmas` (tamanho grande). As telas usam `ProTable` com `hideInTable`, `ModalForm` e
`ProFormSelect` com `rules`, `useIntl().formatMessage`, `<FormattedMessage>` e `useAccess()`; o locale vive num subarquivo
(`src/locales/pt-BR/analises.ts`) com os valores longos na linha seguinte. Servem para avaliar o cruzamento entre telas
(`cobertura.py cruzar`): duas inconsistências esperadas, duas iscas que passam no detector e sete iscas que ele filtra.
Só biblioteca padrão.
"""

# (dir, tela, slug, menu, versões): as mesmas colunas de TELAS_GRANDE em montar_versoes.py
TELAS = [
    ('analises', 'MargemCliente', 'margem-cliente', 'Margem por cliente', 'ambas'),
    ('analises', 'ComissoesEquipe', 'comissoes-equipe', 'Comissões da equipe', 'ambas'),
    ('financeiro', 'OrcamentoAnual', 'orcamento-anual', 'Orçamento anual', 'ambas'),
    ('analises', 'Rentabilidade', 'rentabilidade', 'Rentabilidade por cliente', '11'),
    ('analises', 'MinhasMetas', 'minhas-metas', 'Minhas metas', '11'),
    ('analises', 'CustosInternos', 'custos-internos', 'Custos internos', '11'),
]
NOMES = {t[1] for t in TELAS}
GRUPO = ('Análises', 'lineChart', False)
ACESSO_ROTA = {'CustosInternos': 'canVerMargem'}  # a rota da tela inteira tem guarda: F4
LOCALE_ARQUIVO = 'src/locales/pt-BR/analises.ts'
REQUISITO_ERRADO = ['Informe a unidade de negócio', 'Selecione a unidade de negócio']


def _item(chave, rotulo, tipo='texto'):
    return {'chave': chave, 'rotulo': rotulo, 'tipo': tipo, 'opcoes': [], 'regras': []}


def _spec(titulo, endpoint, colunas, campos=()):
    return {'tipo': 'lista', 'titulo': titulo, 'endpoint': endpoint, 'colunas': [_item(*c) for c in colunas],
            'filtros': [], 'campos': [_item(*c) for c in campos], 'irma': True}


# O produto implementa a v10 destas telas como as outras (ListaPadrao), sem nenhum dos textos novos.
SPECS = {
    'MargemCliente': _spec('Margem por cliente', '/api/analises/margem-cliente',
                           [('cliente', 'Cliente'), ('margemContribuicao', 'Margem de contribuição', 'moeda'),
                            ('descontoMedio', 'Desconto médio', 'numero'), ('freteMedio', 'Frete médio', 'moeda'),
                            ('observacao', 'Observações')]),
    'ComissoesEquipe': _spec('Comissões da equipe', '/api/analises/comissoes-equipe',
                             [('vendedor', 'Vendedor'), ('valor', 'Valor', 'moeda'),
                              ('comissaoPrevista', 'Comissão prevista', 'moeda')],
                             [('centro', 'Centro de resultado'), ('limite', 'Limite', 'moeda')]),
    'OrcamentoAnual': _spec('Orçamento anual', '/api/financeiro/orcamento-anual',
                            [('centro', 'Centro de resultado'), ('orcado', 'Orçado', 'moeda')],
                            [('centro', 'Centro de resultado')]),
    'Rentabilidade': _spec('Rentabilidade por cliente', '/api/analises/rentabilidade',
                           [('cliente', 'Cliente'), ('margemContribuicao', 'Margem de contribuição', 'moeda'),
                            ('freteMedio', 'Frete médio', 'moeda'), ('status', 'Status', 'status'),
                            ('observacao', 'Observações')]),
    'MinhasMetas': _spec('Minhas metas', '/api/analises/minhas-metas',
                         [('meta', 'Meta', 'moeda'), ('comissaoPrevista', 'Comissão prevista', 'moeda')]),
    'CustosInternos': _spec('Custos internos', '/api/analises/custos-internos',
                            [('departamento', 'Departamento'), ('margemContribuicao', 'Margem de contribuição', 'moeda')]),
}

# --------------------------------------------------------------------------------------------------------------------
# Locale: os valores longos ficam na linha seguinte, como em src/locales/pt-BR/pages.ts do ant-design-pro
# --------------------------------------------------------------------------------------------------------------------
LOCALE = {
    'analises.campo.centro': ('Centro de resultado', 'Unidade de negócio'),
    'analises.col.valor': ('Valor', 'Valor realizado'),
}


def locale(v11):
    corpo = ''.join(f"  '{k}':\n    '{novo if v11 else velho}',\n" for k, (velho, novo) in LOCALE.items())
    return f'export default {{\n{corpo}}};\n'


# --------------------------------------------------------------------------------------------------------------------
# Telas
# --------------------------------------------------------------------------------------------------------------------
MARGEM_CLIENTE = '''import React from 'react';
import { ProTable } from '@ant-design/pro-components';
import { useAccess } from '@umijs/max';

const MargemCliente: React.FC = () => {
  const access = useAccess();
  const columns = [
    { title: 'Cliente', dataIndex: 'cliente' },
    {
      title: 'Margem de contribuição',
      dataIndex: 'margemContribuicao',
      hideInTable: !access.canVerMargem,
    },
    { title: 'Desconto médio', dataIndex: 'descontoMedio', render: (_, r) => (access.canVerMargem ? r.descontoMedio : '—') },
    { title: 'Frete médio', dataIndex: 'freteMedio' },
    { title: 'Observações', dataIndex: 'observacao' },
  ];
  return <ProTable columns={columns} rowKey="cliente" search={false} />;
};

export default MargemCliente;
'''

COMISSOES_EQUIPE = '''import React from 'react';
import { ModalForm, ProFormDigit, ProFormSelect, ProTable } from '@ant-design/pro-components';
import { useAccess, useIntl } from '@umijs/max';

const ComissoesEquipe: React.FC = () => {
  const intl = useIntl();
  const access = useAccess();
  const columns = [
    { title: 'Vendedor', dataIndex: 'vendedor' },
    { title: intl.formatMessage({ id: 'analises.col.valor' }), dataIndex: 'valor' },
    { title: 'Comissão prevista', dataIndex: 'comissaoPrevista'__GUARDA__ },
  ];
  return (
    <>
      <ProTable columns={columns} rowKey="vendedor" search={false} />
      <ModalForm title="Ajustar comissão" open={false}>
        <ProFormSelect
          name="centro"
          label={intl.formatMessage({ id: 'analises.campo.centro' })}
          rules={[{ required: true, message: 'Informe o centro de resultado' }]}
          tooltip="Antes chamado de centro de resultado"
        />
        <ProFormDigit name="limite" label="Limite" rules={[{ message: 'Valor máximo: 999.999' }]} />
      </ModalForm>
    </>
  );
};

export default ComissoesEquipe;
'''

ORCAMENTO_ANUAL = '''import React from 'react';
import { ProForm, ProFormSelect, ProTable } from '@ant-design/pro-components';
import { FormattedMessage, useIntl } from '@umijs/max';

const OrcamentoAnual: React.FC = () => {
  const intl = useIntl();
  const columns = [
    { title: <FormattedMessage id="analises.campo.centro" defaultMessage="Centro de resultado" />, dataIndex: 'centro' },
    { title: 'Orçado', dataIndex: 'orcado' },
  ];
  return (
    <>
      <ProForm submitter={false}>
        <ProFormSelect
          name="centro"
          label={intl.formatMessage({ id: 'analises.campo.centro' })}
          rules={[{ required: true, message: 'Informe o centro de resultado' }]}
          placeholder="Selecione o centro de resultado"
        />
      </ProForm>
      <ProTable columns={columns} rowKey="centro" search={false} />
    </>
  );
};

export default OrcamentoAnual;
'''

RENTABILIDADE = '''import React from 'react';
import { ProTable } from '@ant-design/pro-components';
import { useAccess } from '@umijs/max';

const Rentabilidade: React.FC = () => {
  const access = useAccess();
  const dados: any[] = [];
  const canExportar = dados.length > 0;
  const columns = [
    { title: 'Cliente', dataIndex: 'cliente' },
    { title: 'Margem de contribuição', dataIndex: 'margemContribuicao' },
    { title: 'Frete médio', dataIndex: 'freteMedio' },
    { title: 'Status', dataIndex: 'status', hideInTable: !access.canVerMargem },
    ...(canExportar ? [{ title: 'Observações', dataIndex: 'observacao' }] : []),
  ];
  return <ProTable columns={columns} dataSource={dados} rowKey="cliente" search={false} />;
};

export default Rentabilidade;
'''

MINHAS_METAS = '''import React from 'react';
import { ProTable } from '@ant-design/pro-components';

const MinhasMetas: React.FC = () => {
  const columns = [
    { title: 'Meta', dataIndex: 'meta' },
    { title: 'Comissão prevista', dataIndex: 'comissaoPrevista' },
  ];
  return <ProTable columns={columns} rowKey="meta" search={false} />;
};

export default MinhasMetas;
'''

CUSTOS_INTERNOS = '''import React from 'react';
import { ProTable } from '@ant-design/pro-components';

const CustosInternos: React.FC = () => {
  const columns = [
    { title: 'Departamento', dataIndex: 'departamento' },
    { title: 'Margem de contribuição', dataIndex: 'margemContribuicao' },
  ];
  return <ProTable columns={columns} rowKey="departamento" search={false} />;
};

export default CustosInternos;
'''


def tela(nome, v11):
    """Texto da tela na versão (`v11` verdadeiro ou falso)."""
    if nome == 'ComissoesEquipe':
        return COMISSOES_EQUIPE.replace('__GUARDA__', ', hideInTable: !access.canVerEquipe' if v11 else '')
    return {'MargemCliente': MARGEM_CLIENTE, 'OrcamentoAnual': ORCAMENTO_ANUAL, 'Rentabilidade': RENTABILIDADE,
            'MinhasMetas': MINHAS_METAS, 'CustosInternos': CUSTOS_INTERNOS}[nome]


def gabarito(ids, fora_do_mapa):
    """Parte do gabarito da variante; `ids` mapeia o nome da tela ao ID dela (`TL-…`) e `fora_do_mapa` são os IDs fora do mapa.

    O locale tem o valor na linha seguinte à chave, como no ant-design-pro, e o mapa liga a tela à chave trocada assim mesmo:
    Orçamento anual (sem diff) entra no mapa pelo acoplamento. Só Margem por cliente, que não usa chave nem componente
    alterado, fica de fora.
    """
    i = ids
    return {
        'inconsistencias': [
            {'id': 'E1', 'detector': 'D1', 'chave': 'margemContribuicao',
             'descricao': 'Margem de contribuição com guarda em Margem por cliente (irmã fora do mapa) e sem guarda em Rentabilidade',
             'telas_com_guarda': [i['MargemCliente']], 'telas_sem_guarda': [i['Rentabilidade']],
             'fora_do_mapa': [x for x in (i['MargemCliente'],) if x in fora_do_mapa], 'fora_de_sem_guarda': [i['CustosInternos']]},
            {'id': 'E3', 'detector': 'D2', 'moldes': ['Informe o {antigo}', 'Selecione o {antigo}'],
             'descricao': 'Literais com «centro de resultado» ao lado da chave trocada para «Unidade de negócio», em dois grupos de rota',
             'telas': [i['ComissoesEquipe'], i['OrcamentoAnual']],
             'fora_do_mapa': [x for x in (i['ComissoesEquipe'], i['OrcamentoAnual']) if x in fora_do_mapa]},
        ],
        'iscas_passam': [
            {'id': 'P1', 'detector': 'D1', 'chave': 'comissaoPrevista', 'telas': [i['ComissoesEquipe'], i['MinhasMetas']],
             'descricao': 'Guarda nova em Comissões da equipe e sem guarda em Minhas metas (o vendedor vê a própria comissão): decisão, não requisito'},
            {'id': 'P2', 'detector': 'D2', 'molde': 'Antes chamado de {antigo}', 'telas': [i['ComissoesEquipe']],
             'descricao': 'Tooltip que é nota de migração: decisão, não requisito'},
        ],
        'iscas_filtradas': [
            {'id': 'F1', 'filtro': 'defaultMessage', 'onde': 'OrcamentoAnual', 'descricao': 'defaultMessage="Centro de resultado" ao lado da chave'},
            {'id': 'F2', 'filtro': 'guarda da coluna anterior', 'onde': 'MargemCliente', 'descricao': 'freteMedio logo abaixo do render com access.canVerMargem'},
            {'id': 'F3', 'filtro': 'can* solto', 'onde': 'Rentabilidade', 'descricao': 'canExportar condicionando observacao'},
            {'id': 'F4', 'filtro': 'guarda de rota', 'onde': 'CustosInternos', 'descricao': 'margemContribuicao em tela com access na rota'},
            {'id': 'F5', 'filtro': 'chave genérica', 'onde': 'Rentabilidade', 'descricao': 'status com guarda nova'},
            {'id': 'F6', 'filtro': 'outro elemento', 'onde': 'ComissoesEquipe', 'descricao': '«Valor máximo: 999.999» com «Valor» → «Valor realizado»'},
            {'id': 'F7', 'filtro': 'botão não é elemento', 'onde': 'telas geradas', 'descricao': 'o canExcluir atual dos botões'},
        ],
        'requisito_errado': list(REQUISITO_ERRADO),
    }
