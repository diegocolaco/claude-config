"""Simula a passagem do protótipo da v10 para a v11 (repositórios sintéticos + gabarito) para as avaliações da skill.

Uso: python3 montar_versoes.py <destino> --tamanho pequena|grande --cenario com-catalogo|sem-catalogo|entregue|primeira-sincronizacao
                                --workspace <raiz-do-playground> --gabarito <arquivo.json> [--variante nenhuma|irmas|com-excecao]

- Protótipo: `main` = v10 registrada (Umi + antd 6); branch `v11` = versão nova (sem registro, como chega do upstream).
- Produto: `main`, implementa a v10 no estilo próprio (telas declarativas sobre componentes padrão).
- O gabarito (diferenças esperadas, iscas, oco, requisito sem teste) é gravado só em --gabarito, fora de <destino>.
- `--variante irmas` (só com `--tamanho grande`) acrescenta telas irmãs escritas à mão (evals/files/variante_irmas.py) para
  avaliar o cruzamento entre telas; sem ela (`nenhuma`, o padrão) a saída é a de sempre.
- `--cenario primeira-sincronizacao` (só com `--tamanho grande`) monta o uso real sem versão nomeada: protótipo com DOIS commits
  (`init` só com README.md e a v11 grande, lockfile e mock enormes) e produto scaffold sem catálogo (evals/files/primeira_sincronizacao.py).
- `--variante com-excecao` (só com `--cenario com-catalogo`) acrescenta ao catálogo commitado no produto uma diferença antiga, `DF-ANTIGA-01`,
  com `disposition` de exceção aprovada (para avaliar o refazer do zero, que não herda `disposition`); o gabarito ganha `excecao_antiga`.
- Saída determinística: o conteúdo não depende de relógio nem de sorteio e as datas do git são fixas.
Só biblioteca padrão; reaproveita os helpers de montar_fixtures.py sem alterá-los.
"""
import argparse
import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.dont_write_bytecode = True
import montar_fixtures as mf  # noqa: E402  (precisa do sys.path acima)

DATA_GIT = '2026-10-15T12:00:00+00:00'
ORCAMENTO = 100_000
VARIANTE = None  # módulo variante_irmas, importado só com --variante irmas
EXCECAO_ANTIGA = False  # `--variante com-excecao`: o catálogo do produto traz uma diferença antiga com exceção aprovada
DIFERENCA_ANTIGA = {
    'id': 'DF-ANTIGA-01',
    'descricao': 'Exportação de pedidos em planilha pela tela de consulta, mantida só na v9 e deixada fora do escopo do SGD',
    'disposition': {'kind': 'approved-exception', 'reason': 'A exportação em planilha é feita pelo relatório gerencial, que o SGD não substitui',
                    'decision_ref': 'DEC-2026-10-02-exportacao-fora-do-escopo', 'approved_by': 'Diego'},
}
ACESSO_ROTA = {}  # tela -> access da rota (só a variante usa)


# --------------------------------------------------------------------------------------------------------------------
# Vocabulário de campos: chave -> rótulo, tipo, opções (separadas por vírgula)
# --------------------------------------------------------------------------------------------------------------------
VOCABULARIO = '''
numero|Número|texto
cliente|Cliente|texto
data|Emissão|data
validade|Validade|data
total|Valor total|moeda
status|Status|status|Aberto,Em andamento,Concluído,Cancelado
representante|Representante|texto
condicaoPagamento|Condição de pagamento|select|À vista,30 dias,30/60 dias,30/60/90 dias
formaPagamento|Forma de pagamento|select|Boleto,Pix,Cartão,Transferência
observacao|Observações|area
desconto|Desconto (%)|numero
canalVenda|Canal de venda|select|Balcão,Televendas,E-commerce,Representante
prazoEntrega|Prazo de entrega|data
periodo|Período|periodo
nome|Nome|texto
documento|Documento|texto
email|E-mail|texto
telefone|Telefone|texto
cep|CEP|texto
endereco|Endereço|texto
cidade|Cidade|texto
uf|UF|select|SP,RJ,MG,PR,SC,RS,BA,GO
limiteCredito|Limite de crédito|moeda
sku|SKU|texto
descricao|Descrição|texto
categoria|Categoria|select|Alimentos,Bebidas,Limpeza,Higiene,Utilidades
marca|Marca|texto
medida|Unidade de medida|select|UN,CX,KG,LT,PC
ncm|NCM|texto
custo|Custo|moeda
preco|Preço de venda|moeda
estoqueAtual|Estoque atual|numero
estoqueMinimo|Estoque mínimo|numero
peso|Peso (kg)|numero
ativo|Ativo|switch
tipo|Tipo|select|Entrada,Saída,Ajuste
produto|Produto|texto
deposito|Depósito|select|Matriz,Filial Norte,Filial Sul,Transitório
origem|Depósito de origem|select|Matriz,Filial Norte,Filial Sul,Transitório
destino|Depósito de destino|select|Matriz,Filial Norte,Filial Sul,Transitório
quantidade|Quantidade|numero
usuario|Usuário|texto
codigo|Código|texto
competencia|Competência|texto
base|Base de cálculo|moeda
percentual|Percentual (%)|numero
valor|Valor|moeda
pedidoOrigem|Pedido de origem|texto
motivo|Motivo|select|Avaria,Divergência de pedido,Arrependimento,Prazo vencido
contagem|Contagem|texto
divergencias|Divergências|numero
responsavel|Responsável|texto
itens|Itens|numero
razaoSocial|Razão social|texto
nomeFantasia|Nome fantasia|texto
prazoPagamento|Prazo de pagamento (dias)|numero
contato|Contato|texto
banco|Banco|texto
agencia|Agência|texto
conta|Conta|texto
fornecedor|Fornecedor|texto
previsao|Previsão de entrega|data
vencimento|Vencimento|data
pagamento|Pagamento|data
historico|Histórico|texto
centroCusto|Centro de custo|select|Administrativo,Comercial,Logística,Produção
entradas|Entradas|moeda
saidas|Saídas|moeda
saldo|Saldo do dia|moeda
saldoAcumulado|Saldo acumulado|moeda
chave|Chave de acesso|texto
serie|Série|numero
natureza|Natureza da operação|select|Venda,Devolução,Transferência,Remessa
icms|ICMS|moeda
pis|PIS|moeda
grupo|Grupo de acesso|select|Administrador,Comercial,Estoque,Financeiro
login|Login|texto
senha|Senha|texto
lembrar|Lembrar de mim|switch
ramal|Ramal|texto
placa|Placa do veículo|texto
prazoMedio|Prazo médio (dias)|numero
freteMinimo|Frete mínimo|moeda
coberturaDias|Cobertura (dias)|numero
diasAtraso|Dias em atraso|numero
margem|Margem (%)|numero
diasTolerancia|Dias de tolerância|numero
multa|Multa por atraso (%)|numero
juros|Juros ao mês (%)|numero
emailNotificacao|E-mail de notificação|texto
moedaPadrao|Moeda padrão|select|BRL,USD
casasDecimais|Casas decimais|numero
bloqueioAutomatico|Bloqueio automático|switch
permiteEstoqueNegativo|Permite estoque negativo|switch
sistema|Sistema|texto
endpointUrl|Endereço (URL)|texto
intervalo|Intervalo (min)|numero
capacidade|Capacidade (volumes)|numero
'''
VOC = {}
for _linha in VOCABULARIO.strip().splitlines():
    _p = _linha.split('|')
    VOC[_p[0]] = (_p[1], _p[2], _p[3].split(',') if len(_p) > 3 else [])


def _item(dsl):
    """`chave`, `chave:Rótulo` ou `chave:Rótulo|regras` -> dicionário do vocabulário (+ regras)."""
    cabeca, _, regras = dsl.partition('|')
    chave, _, rotulo = cabeca.partition(':')
    rot, tipo, opcoes = VOC[chave]
    item = {'chave': chave, 'rotulo': rotulo.replace('_', ' ') or rot, 'tipo': tipo, 'opcoes': list(opcoes)}
    item['regras'] = [_regra(t, item['rotulo']) for t in regras.split(',') if t]
    return item


def _regra(token, rotulo):
    k, _, v = token.partition('=')
    msgs = {'req': f'Campo obrigatório: {rotulo}', 'email': 'E-mail inválido', 'cpf': 'CPF deve ter 11 dígitos',
            'cnpj': 'CNPJ deve ter 14 dígitos', 'cep': 'CEP inválido', 'ncm': 'NCM deve ter 8 dígitos',
            'max': f'Máximo de {v} caracteres', 'min': f'Mínimo de {v} caracteres', 'ate': f'Valor máximo: {v}',
            'de': f'Valor mínimo: {v}'}
    return {'k': k, 'v': int(v) if v else None, 'msg': msgs[k]}


def lista(titulo, endpoint, colunas, filtros, campos, **extra):
    spec = {'tipo': 'lista', 'titulo': titulo, 'endpoint': endpoint, 'colunas': [_item(c) for c in colunas.split()],
            'filtros': [_item(f) for f in filtros.split()], 'campos': [_item(c) for c in campos.split()]}
    spec.update(extra)
    return spec


def formulario(titulo, endpoint, secoes, **extra):
    spec = {'tipo': 'form', 'titulo': titulo, 'endpoint': endpoint,
            'secoes': [(nome, [_item(c) for c in campos.split()]) for nome, campos in secoes]}
    spec.update(extra)
    return spec


COMUM = ['novo', 'buscar', 'limpar', 'acoes', 'status', 'editar', 'excluir', 'salvar', 'cancelar', 'confirmar']
COMUM_LITERAL = {'novo': 'Novo', 'buscar': 'Buscar', 'limpar': 'Limpar', 'acoes': 'Ações', 'status': 'Status',
                 'editar': 'Editar', 'excluir': 'Excluir', 'salvar': 'Salvar', 'cancelar': 'Cancelar',
                 'confirmar': 'Confirma a exclusão deste registro?'}


def i18n_tela(ns, *slots):
    """Mapa slot -> chave do locale: comum.* para os botões padrão e `ns.*` para o resto."""
    mapa = {s: f'comum.{s}' for s in COMUM}
    mapa.update({s: f'{ns}.{s}' for s in slots})
    return mapa


# --------------------------------------------------------------------------------------------------------------------
# Especificação das telas (a mesma v10 serve ao protótipo e ao produto)
# --------------------------------------------------------------------------------------------------------------------
def _specs():
    s = {}
    s['Login'] = formulario('Entrar no sistema', '/api/login', [('Acesso', 'login|req senha|req,min=6 lembrar')], simples=True)
    s['Painel'] = {'tipo': 'painel', 'titulo': 'Painel gerencial', 'endpoint': '/api/painel',
                   'cartoes': [('Pedidos do mês', '312', ''), ('Faturamento', '184.920,00', 'R$'),
                               ('Ticket médio', '592,69', 'R$'), ('Inadimplência', '3,8', '%')],
                   'colunas': [_item(c) for c in 'numero cliente total status'.split()],
                   'tabela': 'Últimos pedidos'}
    s['Pedidos'] = lista('Pedidos de venda', '/api/pedidos',
                         'numero cliente data representante condicaoPagamento total status',
                         'numero cliente status periodo',
                         'cliente|req representante|req condicaoPagamento|req formaPagamento desconto|ate=30 observacao|max=500',
                         perm_excluir=True)
    s['Orcamentos'] = lista('Orçamentos', '/api/orcamentos', 'numero cliente data validade total status',
                            'numero cliente status periodo', 'cliente|req validade|req desconto|ate=30 observacao|max=500',
                            filtro_comp=True)
    s['Clientes'] = lista('Clientes', '/api/clientes', 'nome documento cidade uf telefone limiteCredito status',
                          'nome documento uf status',
                          'nome|req,max=120 documento|cpf email|email telefone cep|cep endereco cidade uf|req '
                          'limiteCredito observacao|max=500')
    s['Comissoes'] = lista('Comissões', '/api/comissoes', 'representante competencia base percentual valor status',
                           'representante competencia status',
                           'representante|req competencia|req base|req percentual|ate=20',
                           i18n=i18n_tela('comissoes', 'titulo', 'col.representante', 'col.competencia', 'col.base',
                                          'col.percentual', 'col.valor', 'campo.representante', 'campo.competencia',
                                          'campo.base', 'campo.percentual'))
    s['Devolucoes'] = lista('Devoluções', '/api/devolucoes', 'numero pedidoOrigem cliente data motivo total status',
                            'numero cliente status periodo',
                            'pedidoOrigem|req cliente|req motivo|req total|req observacao|max=500')
    s['Produtos'] = lista('Produtos', '/api/produtos',
                          'sku descricao categoria marca medida custo preco estoqueAtual estoqueMinimo status',
                          'sku descricao categoria status',
                          'sku|req,max=20 descricao|req,max=120 categoria|req marca medida|req ncm|ncm custo|req,de=0 '
                          'preco|req,de=0 estoqueMinimo estoqueAtual peso ativo observacao|max=500',
                          perm_excluir=True)
    s['Movimentacoes'] = lista('Movimentações de estoque', '/api/movimentacoes',
                               'data tipo produto deposito quantidade usuario',
                               'periodo tipo produto deposito', 'tipo|req produto|req deposito|req quantidade|req observacao')
    s['Inventario'] = lista('Inventário', '/api/inventarios', 'contagem deposito data divergencias responsavel status',
                            'contagem deposito status',
                            'contagem|req deposito|req responsavel|req divergencias',
                            i18n=i18n_tela('inventario', 'titulo', 'col.contagem', 'col.deposito', 'col.data',
                                           'col.divergencias', 'col.responsavel', 'campo.contagem', 'campo.deposito',
                                           'campo.responsavel', 'campo.divergencias'))
    s['Depositos'] = lista('Depósitos', '/api/depositos', 'codigo nome cidade uf responsavel status',
                           'codigo nome status', 'codigo|req,max=10 nome|req,max=80 cidade uf responsavel')
    s['Transferencias'] = lista('Transferências entre depósitos', '/api/transferencias',
                                'numero origem destino data itens status', 'numero origem destino status',
                                'origem|req destino|req itens|req observacao|max=500')
    s['Fornecedores'] = lista('Fornecedores', '/api/fornecedores',
                              'razaoSocial documento cidade uf prazoPagamento contato email status',
                              'razaoSocial documento uf status',
                              'razaoSocial|req,max=120 nomeFantasia documento|req,cnpj email|email telefone contato cep|cep '
                              'endereco cidade uf prazoPagamento|ate=120 condicaoPagamento banco agencia conta '
                              'observacao|max=500', perm_excluir=True)
    s['PedidosCompra'] = lista('Pedidos de compra', '/api/pedidos-compra', 'numero fornecedor data previsao total status',
                               'numero fornecedor status periodo', 'fornecedor|req previsao|req condicaoPagamento observacao',
                               filtro_comp=True)
    s['Cotacoes'] = lista('Cotações', '/api/cotacoes', 'numero fornecedor data validade total status',
                          'numero fornecedor status periodo', 'fornecedor|req validade|req total|req', filtro_comp=True)
    s['Recebimentos'] = lista('Recebimentos', '/api/recebimentos', 'numero fornecedor pedidoOrigem data itens status',
                              'numero fornecedor status',
                              'fornecedor|req pedidoOrigem|req data:Data_de_recebimento|req itens|req',
                              i18n=i18n_tela('recebimentos', 'titulo', 'col.numero', 'col.fornecedor', 'col.pedidoOrigem',
                                             'col.data', 'col.itens', 'campo.fornecedor', 'campo.pedidoOrigem', 'campo.data',
                                             'campo.itens'))
    s['ContasReceber'] = lista('Contas a receber', '/api/contas-receber', 'numero cliente vencimento valor pagamento status',
                               'numero cliente status periodo', 'cliente|req vencimento|req valor|req,de=0 historico',
                               filtro_comp=True)
    s['ContasPagar'] = lista('Contas a pagar', '/api/contas-pagar', 'numero fornecedor vencimento valor centroCusto status',
                             'numero fornecedor status periodo',
                             'fornecedor|req vencimento|req valor|req,de=0 centroCusto|req historico',
                             filtro_comp=True, perm_excluir=True)
    s['FluxoCaixa'] = lista('Fluxo de caixa', '/api/fluxo-caixa', 'data entradas saidas saldo', 'periodo centroCusto', '',
                            leitura=True)
    # Tela de estrutura própria (painel): o git não deve confundi-la, como renomeação, com as telas novas da v11.
    s['Conciliacao'] = {'tipo': 'painel', 'titulo': 'Conciliação bancária', 'endpoint': '/api/conciliacao',
                        'cartoes': [('Lançamentos do extrato', '248', ''), ('Conciliados', '231', ''), ('Pendentes', '17', ''),
                                    ('Diferença', '1.204,50', 'R$')],
                        'colunas': [_item(c) for c in 'data historico valor banco status'.split()],
                        'tabela': 'Lançamentos pendentes de conciliação'}
    s['CentrosCusto'] = lista('Centros de custo', '/api/centros-custo', 'codigo nome responsavel status',
                              'codigo nome status', 'codigo|req,max=10 nome|req,max=80 responsavel')
    s['Notas'] = lista('Notas fiscais', '/api/notas', 'numero serie cliente data total natureza status',
                       'numero cliente natureza periodo', 'numero|req serie|req cliente|req natureza|req total|req',
                       filtro_comp=True, perm_excluir=True)
    s['Naturezas'] = lista('Naturezas de operação', '/api/naturezas', 'codigo descricao natureza icms pis status',
                           'codigo descricao status', 'codigo|req,max=10 descricao|req,max=120 natureza|req icms pis')
    s['Apuracao'] = lista('Apuração de impostos', '/api/apuracao', 'competencia icms pis total status',
                          'competencia status', '', leitura=True)
    s['Usuarios'] = lista('Usuários', '/api/usuarios', 'nome login email grupo ramal status', 'nome login grupo status',
                          'nome|req,max=120 login|req,min=3 email|email,req grupo|req ramal',
                          perm_excluir=True)
    s['GruposAcesso'] = lista('Grupos de acesso', '/api/grupos', 'codigo nome descricao status', 'codigo nome status',
                              'codigo|req nome|req descricao|max=200')
    s['Transportadoras'] = lista('Transportadoras', '/api/transportadoras', 'razaoSocial documento cidade uf prazoMedio status',
                                 'razaoSocial documento uf status',
                                 'razaoSocial|req,max=120 documento|req,cnpj cidade uf placa telefone')
    s['RelVendas'] = lista('Relatório de vendas', '/api/pedidos', 'data cliente representante total canalVenda',
                           'periodo cliente representante canalVenda', '', leitura=True)
    s['EstoqueCritico'] = lista('Estoque crítico', '/api/relatorios/estoque-critico',
                                'sku descricao estoqueAtual estoqueMinimo deposito', 'sku deposito categoria', '', leitura=True)
    s['Inadimplencia'] = lista('Inadimplência', '/api/relatorios/inadimplencia', 'cliente vencimento valor diasAtraso',
                               'cliente periodo', '', leitura=True)
    s['Margem'] = lista('Margem por produto', '/api/relatorios/margem', 'sku descricao custo preco margem',
                        'sku categoria', '', leitura=True)
    s['Parametros'] = formulario('Parâmetros do sistema', '/api/parametros', [
        ('Cobrança', 'diasTolerancia|req,de=0 multa|ate=10 juros|ate=10'),
        ('Notificações', 'emailNotificacao|email moedaPadrao casasDecimais|ate=6'),
        ('Estoque', 'bloqueioAutomatico permiteEstoqueNegativo')])
    s['Integracoes'] = lista('Integrações', '/api/integracoes', 'sistema endpointUrl intervalo status',
                             'sistema status', 'sistema|req endpointUrl|req intervalo|de=1 ativo')
    s['404'] = {'tipo': 'excecao', 'titulo': 'Página não encontrada', 'endpoint': ''}
    return s


SPECS = _specs()
# Rótulos do filtro de status usam as opções do vocabulário; telas de cadastro simples usam Ativo/Inativo.
for _nome in ('Clientes', 'Depositos', 'Fornecedores', 'GruposAcesso', 'Transportadoras', 'Usuarios', 'Produtos',
              'CentrosCusto', 'Integracoes', 'Naturezas'):
    for _chave in ('colunas', 'filtros', 'campos'):
        for _it in SPECS[_nome][_chave]:
            if _it['chave'] == 'status':
                _it['opcoes'] = ['Ativo', 'Inativo']

# --------------------------------------------------------------------------------------------------------------------
# Locale: 40 chaves mudam na v11 (10 comuns às três telas + 10 de cada uma)
# --------------------------------------------------------------------------------------------------------------------
LOCALE_V11 = {
    'comum.novo': 'Adicionar', 'comum.buscar': 'Pesquisar', 'comum.limpar': 'Limpar filtros', 'comum.acoes': 'Opções',
    'comum.status': 'Situação', 'comum.editar': 'Alterar', 'comum.excluir': 'Remover', 'comum.salvar': 'Salvar alterações',
    'comum.cancelar': 'Descartar', 'comum.confirmar': 'Confirma a remoção deste registro?',
    'comissoes.titulo': 'Comissões de representantes', 'comissoes.col.representante': 'Representante comercial',
    'comissoes.col.competencia': 'Mês de competência', 'comissoes.col.base': 'Base de comissão',
    'comissoes.col.percentual': 'Alíquota (%)', 'comissoes.col.valor': 'Comissão devida',
    'comissoes.campo.representante': 'Representante comercial', 'comissoes.campo.competencia': 'Mês de competência',
    'comissoes.campo.base': 'Base de cálculo (R$)', 'comissoes.campo.percentual': 'Alíquota (%)',
    'inventario.titulo': 'Inventário de estoque', 'inventario.col.contagem': 'Código da contagem',
    'inventario.col.deposito': 'Depósito inventariado', 'inventario.col.data': 'Data da contagem',
    'inventario.col.divergencias': 'Itens divergentes', 'inventario.col.responsavel': 'Conferente',
    'inventario.campo.contagem': 'Código da contagem', 'inventario.campo.deposito': 'Depósito inventariado',
    'inventario.campo.responsavel': 'Conferente', 'inventario.campo.divergencias': 'Itens divergentes',
    'recebimentos.titulo': 'Recebimento de mercadorias', 'recebimentos.col.numero': 'Nº do recebimento',
    'recebimentos.col.fornecedor': 'Fornecedor/Remetente', 'recebimentos.col.pedidoOrigem': 'Pedido de compra',
    'recebimentos.col.data': 'Recebido em', 'recebimentos.col.itens': 'Qtd. de itens',
    'recebimentos.campo.fornecedor': 'Fornecedor da mercadoria', 'recebimentos.campo.pedidoOrigem': 'Pedido de compra',
    'recebimentos.campo.data': 'Recebido em', 'recebimentos.campo.itens': 'Qtd. de itens',
}


def literais(spec):
    """Texto literal (v10) de cada slot de rótulo: é o valor do locale v10 e o texto do produto."""
    lit = dict(COMUM_LITERAL)
    lit['titulo'] = spec['titulo']
    for grupo, prefixo in (('colunas', 'col.'), ('filtros', 'filtro.'), ('campos', 'campo.')):
        for it in spec.get(grupo, []):
            lit[prefixo + it['chave']] = it['rotulo']
    return lit


def locale_v10():
    """Locale v10: menu, chaves comuns, as 40 que mudam e títulos das demais telas (não consumidos pelas telas do diff)."""
    linhas = {}
    for dir_, nome, slug, menu, _ in TELAS_GRANDE:
        linhas[f'menu.{dir_ or "raiz"}.{slug}'.replace('*', 'curinga')] = menu
    for chave, texto in (('comum.sim', 'Sim'), ('comum.nao', 'Não'), ('comum.carregando', 'Carregando...'),
                         ('comum.voltar', 'Voltar'), ('comum.fechar', 'Fechar'), ('comum.erro', 'Ocorreu um erro')):
        linhas[chave] = texto
    for nome, spec in SPECS.items():
        if spec.get('irma'):
            continue
        if spec.get('i18n'):
            lit = literais(spec)
            for slot, chave in spec['i18n'].items():
                linhas[chave] = lit[slot]
        elif spec['tipo'] in ('lista', 'form', 'painel'):
            linhas[f'{nome.lower()}.cabecalho'] = spec['titulo']
    return linhas


def texto_locale(v11):
    valores = locale_v10()
    if v11:
        # as 40 chaves precisam existir na v10 e mudar de verdade (valor igual não gera trecho no diff)
        assert len(LOCALE_V11) == 40 and all(valores.get(k) not in (None, v) for k, v in LOCALE_V11.items())
        valores.update(LOCALE_V11)
    corpo = ''.join(f"  {ts(k)}: {ts(v)},\n" for k, v in valores.items())
    if VARIANTE:  # o locale das telas irmãs mora num subarquivo, espalhado como no ant-design-pro
        return f"import analises from './pt-BR/analises';\n\nexport default {{\n  ...analises,\n{corpo}}};\n"
    return f'export default {{\n{corpo}}};\n'


# --------------------------------------------------------------------------------------------------------------------
# Geração das telas do protótipo (Umi + antd 6)
# --------------------------------------------------------------------------------------------------------------------
def ts(texto):
    return "'" + texto.replace('\\', '\\\\').replace("'", "\\'") + "'"


def regra_ts(r):
    k, v, m = r['k'], r['v'], ts(r['msg'])
    if k == 'req':
        return f'{{ required: true, message: {m} }}'
    if k == 'email':
        return f'{{ type: \'email\', message: {m} }}'
    if k in ('cpf', 'cnpj', 'cep', 'ncm'):
        digitos = {'cpf': 11, 'cnpj': 14, 'cep': 8, 'ncm': 8}[k]
        return '{ pattern: /^\\d{' + str(digitos) + '}$/, message: ' + m + ' }'
    if k in ('max', 'min'):
        return f'{{ {k}: {v}, message: {m} }}'
    return f'{{ type: \'number\', {"max" if k == "ate" else "min"}: {v}, message: {m} }}'


def _slot(prefixo, chave, i18n):
    return 'status' if chave == 'status' and 'status' in i18n else prefixo + chave


def _tipo_ts(tipo):
    return {'moeda': 'number', 'numero': 'number', 'switch': 'boolean'}.get(tipo, 'string')


def _const_opcoes(itens):
    vistos, linhas = set(), []
    for it in itens:
        if it['tipo'] in ('select', 'status') and it['chave'] not in vistos:
            vistos.add(it['chave'])
            linhas.append(f"const OPCOES_{it['chave'].upper()} = [")
            linhas += [f"  {{ value: {ts(o)}, label: {ts(o)} }}," for o in it['opcoes']]
            linhas += ['];', '']
    return linhas


def _controle(it, largura=None, cheio=False):
    est = 'style={{ width: \'100%\' }}' if cheio else f'style={{{{ width: {largura or 180} }}}}'
    t = it['tipo']
    if t in ('select', 'status'):
        return f'<Select allowClear placeholder="Selecione" {est} options={{OPCOES_{it["chave"].upper()}}} />'
    if t == 'periodo':
        return '<RangePicker format="DD/MM/YYYY" />'
    if t == 'data':
        return f'<DatePicker format="DD/MM/YYYY" {est} />'
    if t in ('numero', 'moeda'):
        extra = ' precision={2} decimalSeparator=","' if t == 'moeda' else ''
        return f'<InputNumber {est}{extra} />'
    if t == 'area':
        return '<Input.TextArea rows={3} showCount maxLength={500} />'
    if t == 'switch':
        return '<Switch />'
    senha = ' type="password"' if it['chave'] == 'senha' else ''
    return f'<Input allowClear{senha} placeholder="{it["rotulo"]}" />'


def _item_form(it, rotulo_attr, indent):
    regras = [regra_ts(r) for r in it.get('regras', [])]
    pre = ' ' * indent
    saida = [f'{pre}<Form.Item', f'{pre}  {rotulo_attr}', f'{pre}  name="{it["chave"]}"']
    if it['tipo'] == 'switch':
        saida.append(f'{pre}  valuePropName="checked"')
    if regras:
        saida.append(f'{pre}  rules={{[')
        saida += [f'{pre}    {r},' for r in regras]
        saida.append(f'{pre}  ]}}')
    saida.append(f'{pre}>')
    saida.append(f'{pre}  {_controle(it, cheio=True)}')
    saida.append(f'{pre}</Form.Item>')
    return saida


def _coluna(it, i18n):
    chave = it['chave']
    titulo = f"t({ts(i18n[_slot('col.', chave, i18n)])})" if _slot('col.', chave, i18n) in i18n else ts(it['rotulo'])
    linhas = ['{', f'  title: {titulo},', f"  dataIndex: '{chave}',", f"  key: '{chave}',"]
    t = it['tipo']
    if t in ('numero', 'moeda'):
        linhas += ["  align: 'right',", f"  sorter: (a, b) => (a.{chave} ?? 0) - (b.{chave} ?? 0),"]
    elif t in ('texto', 'data'):
        linhas.append(f"  sorter: (a, b) => String(a.{chave} ?? '').localeCompare(String(b.{chave} ?? '')),")
    if t == 'data':
        linhas.append("  render: (valor?: string) => (valor ? dayjs(valor).format('DD/MM/YYYY') : '-'),")
    elif t == 'moeda':
        linhas.append('  render: (valor?: number) => formatarMoeda(valor),')
    elif t == 'status':
        linhas.append('  render: (valor: string) => <StatusTag valor={valor} />,')
    elif t == 'switch':
        linhas.append("  render: (valor?: boolean) => (valor ? <Tag color=\"green\">Sim</Tag> : <Tag>Não</Tag>),")
    linhas.append('},')
    if it.get('perm'):
        # coluna visível só com a permissão: o objeto vai dentro de um spread condicional
        linhas = [f'...(access.{it["perm"]}', '  ? [', *['      ' + l for l in linhas], '    ]', '  : []),']
    return linhas


def gerar_tela(nome, spec):
    return {'lista': gerar_lista, 'form': gerar_form, 'painel': gerar_painel, 'excecao': gerar_excecao}[spec['tipo']](nome, spec)


def _imports(spec, extras=()):
    usa_t, usa_access = bool(spec.get('i18n')), _usa_access(spec)
    umi = ['request'] + (['useAccess'] if usa_access else []) + (['useIntl'] if usa_t else [])
    return ["import React, { useEffect, useState } from 'react';",
            "import { Button, Card, Col, DatePicker, Form, Input, InputNumber, Modal, Popconfirm, Row, Select, Space, "
            "Switch, Table, Tag, Tooltip, message } from 'antd';",
            "import type { ColumnsType } from 'antd/es/table';",
            "import { DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons';",
            "import dayjs from 'dayjs';",
            f"import {{ {', '.join(sorted(umi))} }} from '@umijs/max';",
            "import PageHeader from '@/components/PageHeader';",
            "import StatusTag from '@/components/StatusTag';", *extras]


def _usa_access(spec):
    return bool(spec.get('perm_excluir') or any(c.get('perm') for c in spec.get('colunas', [])))


def gerar_lista(nome, spec):
    i18n, lit = spec.get('i18n', {}), literais(spec)
    leitura, usa_filtro = spec.get('leitura'), spec.get('filtro_comp')
    access = _usa_access(spec)

    def T(slot):
        return f"t({ts(i18n[slot])})" if slot in i18n else ts(lit[slot])

    def A(atributo, slot):
        return f"{atributo}={{{T(slot)}}}" if slot in i18n else f'{atributo}="{lit[slot]}"'

    colunas, filtros, campos = spec['colunas'], spec['filtros'], spec['campos']
    extras = ["import Filtro from '@/components/Filtro';"] if usa_filtro else []
    L = _imports(spec, extras) + ['', 'const { RangePicker } = DatePicker;', '']
    L += [f'interface Registro {{', '  id: number;']
    vistos = set()
    for it in colunas + campos:
        if it['chave'] not in vistos and it['tipo'] != 'periodo':
            vistos.add(it['chave'])
            L.append(f"  {it['chave']}?: {_tipo_ts(it['tipo'])};")
    L += ['}', '']
    L += _const_opcoes(filtros + campos)
    if any(c['tipo'] == 'moeda' for c in colunas):
        L += ['const formatarMoeda = (valor?: number) =>', '  valor === undefined || valor === null', "    ? '-'",
              "    : valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });", '']
    if usa_filtro:
        L.append('const CAMPOS_FILTRO = [')
        for f in filtros:
            tipo = 'select' if f['tipo'] == 'status' else f['tipo']
            opc = f", opcoes: OPCOES_{f['chave'].upper()}" if f['tipo'] in ('select', 'status') else ''
            L.append(f"  {{ chave: '{f['chave']}', rotulo: {ts(f['rotulo'])}, tipo: '{tipo}'{opc} }},")
        L += ['];', '']
    L += [f'export default function {_ident(nome)}() {{']
    if i18n:
        L += ['  const intl = useIntl();', '  const t = (id: string) => intl.formatMessage({ id });']
    if access:
        L.append('  const access = useAccess();')
    L += ['  const [filtrosForm] = Form.useForm();', '  const [formulario] = Form.useForm();',
          '  const [dados, setDados] = useState<Registro[]>([]);', '  const [carregando, setCarregando] = useState(false);',
          '  const [editando, setEditando] = useState<Registro | null>(null);',
          '  const [modalAberto, setModalAberto] = useState(false);',
          '  const [paginacao, setPaginacao] = useState({ current: 1, pageSize: 10, total: 0 });', '',
          '  const carregar = async (pagina = 1, valores: Record<string, unknown> = filtrosForm.getFieldsValue()) => {',
          '    setCarregando(true);', '    try {',
          f"      const resposta = await request('{spec['endpoint']}', {{",
          '        params: { ...valores, pagina, tamanho: paginacao.pageSize },', '      });',
          '      setDados(resposta.data ?? []);',
          '      setPaginacao((atual) => ({ ...atual, current: pagina, total: resposta.total ?? 0 }));',
          '    } catch (erro) {', "      message.error('Não foi possível carregar os registros');", '    } finally {',
          '      setCarregando(false);', '    }', '  };', '', '  useEffect(() => {', '    carregar(1, {});', '  }, []);', '']
    if not leitura:
        L += ['  const abrirModal = (registro?: Registro) => {', '    setEditando(registro ?? null);',
              '    formulario.resetFields();', '    if (registro) {', '      formulario.setFieldsValue(registro);', '    }',
              '    setModalAberto(true);', '  };', '',
              '  const salvar = async () => {', '    const valores = await formulario.validateFields();',
              '    try {', f"      await request(`{spec['endpoint']}${{editando ? `/${{editando.id}}` : ''}}`, {{",
              "        method: editando ? 'PUT' : 'POST',", '        data: valores,', '      });',
              "      message.success('Registro salvo com sucesso');", '      setModalAberto(false);',
              '      carregar(paginacao.current);', '    } catch (erro) {', "      message.error('Não foi possível salvar o registro');",
              '    }', '  };', '',
              '  const excluir = async (registro: Registro) => {', '    try {',
              f"      await request(`{spec['endpoint']}/${{registro.id}}`, {{ method: 'DELETE' }});",
              "      message.success('Registro excluído');", '      carregar(1);', '    } catch (erro) {',
              "      message.error('Não foi possível excluir o registro');", '    }', '  };', '']
    L.append('  const colunas: ColumnsType<Registro> = [')
    for c in colunas:
        c = dict(c)
        for linha in _coluna(c, i18n):
            L.append('    ' + linha)
    if not leitura:
        excluir = ['<Popconfirm', f'  title={{{T("confirmar")}}}', '  onConfirm={() => excluir(registro)}', '>',
                   f'  <Tooltip title={{{T("excluir")}}}>', '    <Button danger size="small" icon={<DeleteOutlined />} />',
                   '  </Tooltip>', '</Popconfirm>']
        if spec.get('perm_excluir'):
            excluir = ['{access.canExcluir ? (', *['  ' + l for l in excluir], ') : null}']
        L += ['    {', f'      title: {T("acoes")},', "      key: 'acoes',", '      width: 110,',
              '      render: (_, registro) => (', '        <Space>', f'          <Tooltip title={{{T("editar")}}}>',
              '            <Button size="small" icon={<EditOutlined />} onClick={() => abrirModal(registro)} />',
              '          </Tooltip>', *['          ' + l for l in excluir], '        </Space>', '      ),', '    },']
    L += ['  ];', '', '  return (', '    <div>']
    novo = ['      extra={', '        <Button type="primary" icon={<PlusOutlined />} onClick={() => abrirModal()}>',
            f'          {{{T("novo")}}}', '        </Button>', '      }'] if not leitura else []
    L += ['      <PageHeader', f'        titulo={{{T("titulo")}}}', *novo, '      />']
    if usa_filtro:
        L += ['      <Filtro', '        campos={CAMPOS_FILTRO}', '        carregando={carregando}',
              '        onBuscar={(valores) => carregar(1, valores)}', '      />']
    else:
        L += ['      <Card style={{ marginBottom: 16 }}>',
              '        <Form form={filtrosForm} layout="inline" onFinish={(valores) => carregar(1, valores)}>']
        for f in filtros:
            slot = _slot('filtro.', f['chave'], i18n)
            L += ['          <Form.Item ' + A('label', slot) + f' name="{f["chave"]}">',
                  '            ' + _controle(f), '          </Form.Item>']
        L += ['          <Form.Item>', '            <Space>',
              '              <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>',
              f'                {{{T("buscar")}}}', '              </Button>',
              '              <Button icon={<ReloadOutlined />} onClick={() => { filtrosForm.resetFields(); carregar(1, {}); }}>',
              f'                {{{T("limpar")}}}', '              </Button>', '            </Space>', '          </Form.Item>',
              '        </Form>', '      </Card>']
    L += ['      <Table', '        rowKey="id"', '        loading={carregando}', '        columns={colunas}',
          '        dataSource={dados}', '        pagination={{',
          '          ...paginacao,', '          showSizeChanger: false,',
          '          showTotal: (total) => `${total} registros`,', '          onChange: (pagina) => carregar(pagina),',
          '        }}', '      />']
    if not leitura:
        L += ['      <Modal', f"        title={{editando ? {T('editar')} : {T('novo')}}}", '        open={modalAberto}',
              '        onOk={salvar}', '        onCancel={() => setModalAberto(false)}', f'        okText={{{T("salvar")}}}',
              f'        cancelText={{{T("cancelar")}}}', '        width={640}', '        destroyOnClose', '      >',
              '        <Form form={formulario} layout="vertical">', '          <Row gutter={16}>']
        for c in campos:
            slot = _slot('campo.', c['chave'], i18n)
            L.append(f"            <Col span={{{24 if c['tipo'] == 'area' else 12}}}>")
            L += _item_form(c, A('label', slot), 14)
            L.append('            </Col>')
        L += ['          </Row>', '        </Form>', '      </Modal>']
    L += ['    </div>', '  );', '}', '']
    return '\n'.join(L)


def _ident(nome):
    return 'Tela' + nome if nome[0].isdigit() else nome


def gerar_form(nome, spec):
    L = ["import React, { useState } from 'react';",
                              "import { Button, Card, Col, Form, Input, InputNumber, Row, Select, Space, Switch, message } from 'antd';",
                              "import { request } from '@umijs/max';", "import PageHeader from '@/components/PageHeader';", '']
    L += _const_opcoes([c for _, cs in spec['secoes'] for c in cs])
    L += [f'export default function {_ident(nome)}() {{', '  const [form] = Form.useForm();',
          '  const [salvando, setSalvando] = useState(false);', '',
          '  const enviar = async () => {', '    const valores = await form.validateFields();', '    setSalvando(true);', '    try {',
          f"      await request('{spec['endpoint']}', {{ method: 'POST', data: valores }});",
          "      message.success('Dados enviados com sucesso');", '    } catch (erro) {',
          "      message.error('Não foi possível enviar os dados');", '    } finally {', '      setSalvando(false);', '    }', '  };', '',
          '  return (', '    <div>', f'      <PageHeader titulo="{spec["titulo"]}" />',
          '      <Form form={form} layout="vertical" onFinish={enviar}>']
    for secao, campos in spec['secoes']:
        if not spec.get('simples'):
            L.append(f'        <Card title="{secao}" style={{{{ marginBottom: 16 }}}}>')
        L.append('          <Row gutter={16}>')
        for c in campos:
            L.append('            <Col span={12}>')
            L += _item_form(c, f'label="{c["rotulo"]}"', 14)
            L.append('            </Col>')
        L.append('          </Row>')
        if not spec.get('simples'):
            L.append('        </Card>')
    L += ['        <Space>', '          <Button type="primary" htmlType="submit" loading={salvando}>',
          '            Salvar', '          </Button>', '          <Button onClick={() => form.resetFields()}>Cancelar</Button>',
          '        </Space>', '      </Form>', '    </div>', '  );', '}', '']
    return '\n'.join(L)


def gerar_painel(nome, spec):
    L = ["import React, { useEffect, useState } from 'react';", "import { Card, Col, Row, Statistic, Table } from 'antd';",
         "import type { ColumnsType } from 'antd/es/table';", "import { request } from '@umijs/max';",
         "import PageHeader from '@/components/PageHeader';", "import StatusTag from '@/components/StatusTag';", '',
         'interface Linha {', '  id: number;']
    L += [f"  {c['chave']}?: {_tipo_ts(c['tipo'])};" for c in spec['colunas']]
    L += ['}', '', f'export default function {_ident(nome)}() {{', '  const [linhas, setLinhas] = useState<Linha[]>([]);', '',
          '  useEffect(() => {', f"    request('{spec['endpoint']}').then((resposta) => setLinhas(resposta.recentes ?? []));",
          '  }, []);', '', '  const colunas: ColumnsType<Linha> = [']
    for c in spec['colunas']:
        L += ['    {', f"      title: {ts(c['rotulo'])},", f"      dataIndex: '{c['chave']}',"]
        if c['tipo'] == 'status':
            L.append('      render: (valor: string) => <StatusTag valor={valor} />,')
        elif c['tipo'] == 'moeda':
            L.append("      render: (valor?: number) => (valor ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }),")
        L.append('    },')
    L += ['  ];', '', '  return (', '    <div>', f'      <PageHeader titulo="{spec["titulo"]}" />', '      <Row gutter={16}>']
    for titulo, valor, sufixo in spec['cartoes']:
        L += ['        <Col span={6}>', '          <Card>',
              f'            <Statistic title="{titulo}" value="{valor}" suffix="{sufixo}" />', '          </Card>', '        </Col>']
    L += ['      </Row>', f'      <Card title="{spec["tabela"]}" style={{{{ marginTop: 16 }}}}>',
          '        <Table rowKey="id" columns={colunas} dataSource={linhas} pagination={false} />', '      </Card>',
          '    </div>', '  );', '}', '']
    return '\n'.join(L)


def gerar_excecao(nome, spec):
    return "\n".join(["import React from 'react';", "import { Button, Result } from 'antd';", "import { history } from '@umijs/max';", '',
                      'export default function NaoEncontrada() {', '  return (', '    <Result', '      status="404"',
                      f'      title="404"', f'      subTitle="{spec["titulo"]}"',
                      "      extra={<Button type=\"primary\" onClick={() => history.push('/painel')}>Voltar ao painel</Button>}",
                      '    />', '  );', '}', ''])


PAGE_HEADER = '''import React from 'react';
import { Space, Typography } from 'antd';

interface PageHeaderProps {
  titulo: string;
  extra?: React.ReactNode;
}

export default function PageHeader({ titulo, extra }: PageHeaderProps) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
      <Typography.Title level={4} style={{ margin: 0 }}>
        {titulo}
      </Typography.Title>
      <Space>{extra}</Space>
    </div>
  );
}
'''
STATUS_TAG = '''import React from 'react';
import { Tag } from 'antd';

const CORES: Record<string, string> = {
  Aberto: 'blue',
  'Em andamento': 'gold',
  Concluído: 'green',
  Cancelado: 'red',
  Ativo: 'green',
  Inativo: 'default',
};

export default function StatusTag({ valor }: { valor?: string }) {
  if (!valor) {
    return <span>-</span>;
  }
  return <Tag color={CORES[valor] ?? 'default'}>{valor}</Tag>;
}
'''


def filtro_tsx(v11):
    """Filtro compartilhado; a v11 acrescenta o período padrão de 30 dias e os filtros avançados recolhíveis."""
    L = ["import React, { useState } from 'react';",
         "import { Button, DatePicker, Form, Input, InputNumber, Select, Space } from 'antd';",
         "import { DownOutlined, ReloadOutlined, SearchOutlined, UpOutlined } from '@ant-design/icons';"
         if v11 else "import { ReloadOutlined, SearchOutlined } from '@ant-design/icons';"]
    if v11:
        L.insert(2, "import dayjs from 'dayjs';")
    L += ['', 'const { RangePicker } = DatePicker;', '', 'export interface CampoFiltro {', '  chave: string;', '  rotulo: string;',
          "  tipo?: 'texto' | 'select' | 'periodo' | 'numero';", '  opcoes?: { value: string; label: string }[];',
          '  largura?: number;']
    if v11:
        L.append('  avancado?: boolean;')
    L += ['}', '', 'interface FiltroProps {', '  campos: CampoFiltro[];', '  carregando?: boolean;',
          '  onBuscar: (valores: Record<string, unknown>) => void;', '  onLimpar?: () => void;', '}', '']
    if v11:
        L += ['const PERIODO_PADRAO_DIAS = 30;', '']
    L += ['export default function Filtro({ campos, carregando, onBuscar, onLimpar }: FiltroProps) {', '  const [form] = Form.useForm();']
    if v11:
        L += ['  const [expandido, setExpandido] = useState(false);',
              '  const temAvancado = campos.some((campo) => campo.avancado);']
    L += ['', '  const limpar = () => {', '    form.resetFields();', '    onLimpar?.();']
    L += ['    onBuscar(valoresIniciais());' if v11 else '    onBuscar({});', '  };', '']
    if v11:
        L += ['  const valoresIniciais = () => {', "    const periodo = campos.find((campo) => campo.tipo === 'periodo');",
              '    return periodo', '      ? { [periodo.chave]: [dayjs().subtract(PERIODO_PADRAO_DIAS, \'day\'), dayjs()] }',
              '      : {};', '  };', '']
    L += ['  const controle = (campo: CampoFiltro) => {', '    switch (campo.tipo) {', "      case 'select':",
          '        return (', '          <Select', '            allowClear', '            placeholder="Todos"',
          '            style={{ width: campo.largura ?? 170 }}', '            options={campo.opcoes}', '          />',
          '        );', "      case 'periodo':", '        return <RangePicker format="DD/MM/YYYY" />;', "      case 'numero':",
          '        return <InputNumber style={{ width: campo.largura ?? 120 }} />;', '      default:',
          '        return <Input allowClear placeholder={campo.rotulo} style={{ width: campo.largura ?? 180 }} />;',
          '    }', '  };', '']
    visiveis = '(expandido ? campos : campos.filter((campo) => !campo.avancado))' if v11 else 'campos'
    L += ['  return (', '    <Form', '      form={form}', '      layout="inline"',
          '      style={{ marginBottom: 16, rowGap: 12 }}']
    if v11:
        L.append('      initialValues={valoresIniciais()}')
    L += ['      onFinish={(valores) => onBuscar(valores)}', '    >', f'      {{{visiveis}.map((campo) => (',
          '        <Form.Item key={campo.chave} label={campo.rotulo} name={campo.chave}>', '          {controle(campo)}',
          '        </Form.Item>', '      ))}', '      <Form.Item>', '        <Space>',
          '          <Button type="primary" htmlType="submit" loading={carregando} icon={<SearchOutlined />}>',
          '            Filtrar', '          </Button>', '          <Button onClick={limpar} icon={<ReloadOutlined />}>',
          '            Limpar', '          </Button>']
    if v11:
        L += ['          {temAvancado ? (', '            <Button type="link" onClick={() => setExpandido(!expandido)}>',
              "              {expandido ? <UpOutlined /> : <DownOutlined />} Filtros avançados", '            </Button>',
              '          ) : null}']
    L += ['        </Space>', '      </Form.Item>', '    </Form>', '  );', '}', '']
    return '\n'.join(L)


# --------------------------------------------------------------------------------------------------------------------
# Telas (rotas), mocks e evoluções por tamanho
# --------------------------------------------------------------------------------------------------------------------
# (dir, tela, slug, menu, versões): '10' só na v10, '11' só na v11, 'ambas'
TELAS_GRANDE = [
    ('user', 'Login', 'login', 'Entrar', 'ambas'),
    ('', 'Painel', 'painel', 'Painel', 'ambas'),
    ('vendas', 'Pedidos', 'pedidos', 'Pedidos', 'ambas'),
    ('vendas', 'Orcamentos', 'orcamentos', 'Orçamentos', 'ambas'),
    ('vendas', 'Clientes', 'clientes', 'Clientes', 'ambas'),
    ('vendas', 'Comissoes', 'comissoes', 'Comissões', 'ambas'),
    ('vendas', 'Devolucoes', 'devolucoes', 'Devoluções', '11'),
    ('estoque', 'Produtos', 'produtos', 'Produtos', 'ambas'),
    ('estoque', 'Movimentacoes', 'movimentacoes', 'Movimentações', 'ambas'),
    ('estoque', 'Inventario', 'inventario', 'Inventário', 'ambas'),
    ('estoque', 'Depositos', 'depositos', 'Depósitos', 'ambas'),
    ('estoque', 'Transferencias', 'transferencias', 'Transferências', '11'),
    ('compras', 'Fornecedores', 'fornecedores', 'Fornecedores', 'ambas'),
    ('compras', 'PedidosCompra', 'pedidos', 'Pedidos de compra', 'ambas'),
    ('compras', 'Cotacoes', 'cotacoes', 'Cotações', 'ambas'),
    ('compras', 'Recebimentos', 'recebimentos', 'Recebimentos', 'ambas'),
    ('financeiro', 'ContasReceber', 'receber', 'Contas a receber', 'ambas'),
    ('financeiro', 'ContasPagar', 'pagar', 'Contas a pagar', 'ambas'),
    ('financeiro', 'FluxoCaixa', 'fluxo-caixa', 'Fluxo de caixa', 'ambas'),
    ('financeiro', 'Conciliacao', 'conciliacao', 'Conciliação bancária', '10'),
    ('financeiro', 'CentrosCusto', 'centros-custo', 'Centros de custo', 'ambas'),
    ('fiscal', 'Notas', 'notas', 'Notas fiscais', 'ambas'),
    ('fiscal', 'Naturezas', 'naturezas', 'Naturezas de operação', 'ambas'),
    ('fiscal', 'Apuracao', 'apuracao', 'Apuração de impostos', 'ambas'),
    ('cadastros', 'Usuarios', 'usuarios', 'Usuários', 'ambas'),
    ('cadastros', 'GruposAcesso', 'grupos', 'Grupos de acesso', 'ambas'),
    ('cadastros', 'Transportadoras', 'transportadoras', 'Transportadoras', 'ambas'),
    ('relatorios', 'RelVendas', 'vendas', 'Vendas', 'ambas'),
    ('relatorios', 'EstoqueCritico', 'estoque-critico', 'Estoque crítico', 'ambas'),
    ('relatorios', 'Inadimplencia', 'inadimplencia', 'Inadimplência', 'ambas'),
    ('relatorios', 'Margem', 'margem', 'Margem por produto', '11'),
    ('configuracoes', 'Parametros', 'parametros', 'Parâmetros', 'ambas'),
    ('configuracoes', 'Integracoes', 'integracoes', 'Integrações', 'ambas'),
    ('', '404', '*', 'Não encontrada', 'ambas'),
]
TELAS_PEQUENA = [
    ('', 'Painel', 'painel', 'Painel', 'ambas'),
    ('', 'Pedidos', 'pedidos', 'Pedidos', 'ambas'),
    ('', 'Clientes', 'clientes', 'Clientes', 'ambas'),
    ('', 'Produtos', 'produtos', 'Produtos', 'ambas'),
]
GRUPOS = {'vendas': ('Vendas', 'shopping', False), 'estoque': ('Estoque', 'database', True),
          'compras': ('Compras', 'shoppingCart', False), 'financeiro': ('Financeiro', 'dollar', True),
          'fiscal': ('Fiscal', 'fileText', False), 'cadastros': ('Cadastros', 'team', True),
          'relatorios': ('Relatórios', 'barChart', False), 'configuracoes': ('Configurações', 'setting', True)}


def rota_da_tela(tela):
    dir_, _, slug, _, _ = tela
    if slug == '*':
        return '*'
    return '/' + '/'.join(p for p in (dir_, slug) if p)


def componente(tela):
    dir_, nome = tela[0], tela[1]
    return './' + '/'.join(p for p in (dir_, nome) if p)


def arquivo_proto(tela):
    return 'src/pages/' + componente(tela)[2:] + '.tsx'


def arquivo_produto(tela):
    return 'apps/web/src/pages/' + componente(tela)[2:] + '.tsx'


def telas_da_versao(telas, versao):
    return [t for t in telas if t[4] in ('ambas', versao)]


def routes_ts(telas, versao):
    ativas = telas_da_versao(telas, versao)
    L = ['/**', ' * Rotas da aplicação (Umi). Caminhos relativos se juntam ao do grupo.', ' */', 'export default [']
    login = [t for t in ativas if t[0] == 'user']
    if login:
        L += ['  {', "    path: '/user',", '    layout: false,', '    routes: [']
        for t in login:
            L += ['      {', f"        path: '{rota_da_tela(t)}',", f"        name: '{t[3].lower()}',", f"        component: '{componente(t)}',", '      },']
        L += ['    ],', '  },']
    for t in [t for t in ativas if t[0] == '' and t[2] != '*']:
        L += ['  {', f"    path: '{rota_da_tela(t)}',", f"    name: '{t[3]}',", "    icon: 'dashboard',", f"    component: '{componente(t)}',", '  },']
    for grupo, (menu, icone, relativo) in GRUPOS.items():
        filhas = [t for t in ativas if t[0] == grupo]
        if not filhas:
            continue
        L += ['  {', f"    path: '/{grupo}',", f"    name: '{menu}',", f"    icon: '{icone}',"]
        if grupo == 'configuracoes':
            L.append("    access: 'canAdmin',")
        L += ['    routes: [', f"      {{ path: '/{grupo}', redirect: '{rota_da_tela(filhas[0])}' }},"]
        for t in filhas:
            caminho = t[2] if relativo else rota_da_tela(t)
            L += ['      {', f"        path: '{caminho}',", f"        name: '{t[3]}',"]
            if t[1] in ACESSO_ROTA:
                L.append(f"        access: '{ACESSO_ROTA[t[1]]}',")
            L += [f"        component: '{componente(t)}',", '      },']
        L += ['    ],', '  },']
    for t in [t for t in ativas if t[2] == '*']:
        L += ['  {', "    path: '*',", f"    component: '{componente(t)}',", '  },']
    L += ['];', '']
    return '\n'.join(L)


MOCK_PEDIDOS_LINHAS = [
    ('PV-0001', 'Mercantil Aurora Ltda', 'Balcão', '2026-10-02'), ('PV-0002', 'Distribuidora Vale Verde', 'Televendas', '2026-10-03'),
    ('PV-0003', 'Casa do Construtor ME', 'E-commerce', '2026-10-05'), ('PV-0004', 'Supermercado Bom Preço', 'Representante', '2026-10-07'),
    ('PV-0005', 'Padaria Estrela do Sul', 'Balcão', '2026-10-09'),
]


REPRESENTANTES = ['Marcos Teles', 'Renata Pires', 'Otávio Braga']


def mock_pedidos(v11):
    L = ["import type { Request, Response } from 'express';", '', 'const pedidos = [']
    for i, (num, cliente, canal, entrega) in enumerate(MOCK_PEDIDOS_LINHAS, start=1):
        L += ['  {', f'    id: {i},', f"    numero: '{num}',", f"    cliente: '{cliente}',", f"    data: '2026-09-{10 + i}',",
              f"    representante: '{REPRESENTANTES[i % 3]}',", f"    total: {1200 + i * 317}.5,", "    status: 'Aberto',"]
        if v11:
            L += [f"    prazoEntrega: '{entrega}',", f"    canalVenda: '{canal}',"]
        L.append('  },')
    L += ['];', '', 'export default {', "  'GET /api/pedidos': (req: Request, res: Response) => {",
          '    res.json({ data: pedidos, total: pedidos.length });', '  },', "  'DELETE /api/pedidos/:id': (req: Request, res: Response) => {",
          '    res.json({ ok: true });', '  },', '};', '']
    return '\n'.join(L)


def mock_clientes():
    L = ["import type { Request, Response } from 'express';", '', 'const clientes = [']
    for i, nome in enumerate(['Mercantil Aurora Ltda', 'Distribuidora Vale Verde', 'Casa do Construtor ME'], start=1):
        L += ['  {', f'    id: {i},', f"    nome: '{nome}',", f"    documento: '0000000000{i}',", "    status: 'Ativo',", '  },']
    L += ['];', '', 'export default {', "  'GET /api/clientes': (req: Request, res: Response) => {",
          '    res.json({ data: clientes, total: clientes.length });', '  },', '};', '']
    return '\n'.join(L)


# ----- evoluções (v10 -> v11) -----
def _ev_add_coluna(chave, depois=None, rotulo=None):
    def f(s):
        it = _item(chave + (':' + rotulo if rotulo else ''))
        pos = next((i for i, c in enumerate(s['colunas']) if c['chave'] == depois), len(s['colunas']) - 1) + 1
        s['colunas'].insert(pos, it)
    return f


def _ev_add_filtro(chave, depois=None):
    def f(s):
        pos = next((i for i, c in enumerate(s['filtros']) if c['chave'] == depois), len(s['filtros']) - 1) + 1
        s['filtros'].insert(pos, _item(chave))
    return f


def _ev_add_campo(dsl, depois=None):
    def f(s):
        pos = next((i for i, c in enumerate(s['campos']) if c['chave'] == depois), len(s['campos']) - 1) + 1
        s['campos'].insert(pos, _item(dsl))
    return f


def _ev_regra(chave, k, v=None, msg=None):
    """Troca (ou acrescenta) a regra `k` do campo `chave`; `msg` troca só a mensagem."""
    def f(s):
        campo = next(c for c in s['campos'] if c['chave'] == chave)
        existente = next((r for r in campo['regras'] if r['k'] == k), None)
        if existente is None:
            campo['regras'].insert(0, {'k': k, 'v': v, 'msg': msg})
        else:
            if v is not None:
                existente['v'] = v
            if msg is not None:
                existente['msg'] = msg
    return f


def _ev_secao_campo(secao, dsl):
    def f(s):
        for nome, campos in s['secoes']:
            if nome == secao:
                campos.append(_item(dsl))
    return f


def _ev_perm_coluna(chave, perm):
    def f(s):
        next(c for c in s['colunas'] if c['chave'] == chave)['perm'] = perm
    return f


def ev(id_, tela, descricao, aplicar, marcadores, entrega='nao', teste=True, **extra):
    d = {'id': id_, 'tela': tela, 'tipo': 'tela', 'descricao': descricao, 'aplicar': aplicar, 'marcadores': marcadores,
         'entrega': entrega, 'teste': teste}
    d.update(extra)
    return d


EVOLUCOES_PEQUENA = [
    ev('DF-01', 'Pedidos', 'Pedidos ganha o filtro «Canal de venda»', _ev_add_filtro('canalVenda'), ['canalVenda'],
       entrega='stub', teste=True),
    ev('DF-02', 'Pedidos', 'Pedidos ganha a coluna «Prazo de entrega»', _ev_add_coluna('prazoEntrega', 'data'),
       ['prazoEntrega'], entrega='nao'),
    ev('DF-03', 'Clientes', 'CPF do cliente passa a ser obrigatório (mensagem «Informe o CPF»)',
       _ev_regra('documento', 'req', msg='Informe o CPF'), ['Informe o CPF'], entrega='sim', teste=False),
]

AFETADAS_FILTRO = ['Orcamentos', 'PedidosCompra', 'Cotacoes', 'ContasReceber', 'ContasPagar', 'Notas']
AFETADAS_LOCALE = ['Comissoes', 'Inventario', 'Recebimentos']

EVOLUCOES_GRANDE = [
    ev('DF-01', 'Devolucoes', 'Tela nova: devoluções de venda (lista, filtros e cadastro)', None, [], entrega='stub', teste=True, tipo='nova'),
    ev('DF-02', 'Transferencias', 'Tela nova: transferências entre depósitos', None, [], entrega='sim', teste=True, tipo='nova'),
    ev('DF-03', 'Margem', 'Tela nova: relatório de margem por produto', None, [], entrega='nao', tipo='nova'),
    ev('DF-04', 'Conciliacao', 'Tela removida: conciliação bancária saiu do menu Financeiro', None, [], entrega='nao', tipo='removida'),
    ev('DF-05', 'Pedidos', 'Pedidos ganha as colunas «Prazo de entrega» e «Canal de venda» (campos novos do mock)',
       lambda s: (_ev_add_coluna('prazoEntrega', 'data')(s), _ev_add_coluna('canalVenda', 'prazoEntrega')(s)),
       ['prazoEntrega', 'canalVenda'], entrega='sim', teste=True),
    ev('DF-06', 'Clientes', 'Limite de crédito passa a ser obrigatório no cadastro',
       _ev_regra('limiteCredito', 'req', msg='Informe o limite de crédito'), ['Informe o limite de crédito'], entrega='sim', teste=True),
    ev('DF-07', 'Depositos', 'Depósitos ganha o campo «Capacidade (volumes)» no cadastro',
       _ev_add_campo('capacidade|req,de=1', 'nome'), ['capacidade'], entrega='sim', teste=False),
    ev('DF-08', 'FluxoCaixa', 'Fluxo de caixa ganha a coluna «Saldo acumulado»', _ev_add_coluna('saldoAcumulado', 'saldo'),
       ['saldoAcumulado'], entrega='sim', teste=True),
    ev('DF-09', 'Movimentacoes', 'Movimentações ganha o filtro «Usuário»', _ev_add_filtro('usuario', 'deposito'), ['usuario'], entrega='nao'),
    ev('DF-10', 'CentrosCusto', 'Responsável do centro de custo passa a ser obrigatório',
       _ev_regra('responsavel', 'req', msg='Informe o responsável'), ['Informe o responsável'], entrega='nao'),
    ev('DF-11', 'Usuarios', 'Usuários ganha o filtro «Ramal»', _ev_add_filtro('ramal'), ['ramal'], entrega='nao'),
    ev('DF-12', 'Transportadoras', 'Transportadoras ganha o campo «Frete mínimo» no cadastro',
       _ev_add_campo('freteMinimo|de=0', 'placa'), ['freteMinimo'], entrega='nao'),
    ev('DF-13', 'EstoqueCritico', 'Estoque crítico ganha a coluna «Cobertura (dias)»', _ev_add_coluna('coberturaDias', 'estoqueMinimo'),
       ['coberturaDias'], entrega='nao'),
    ev('DF-14', 'Parametros', 'Parâmetros ganha «Dias de tolerância» na seção Estoque',
       _ev_secao_campo('Estoque', 'diasTolerancia'), ['diasTolerancia'], entrega='nao'),
    ev('DF-15', 'Fornecedores', 'Mensagem de validação do CNPJ do fornecedor mudou (isca: mudança discreta num formulário grande)',
       _ev_regra('documento', 'cnpj', msg='Informe um CNPJ válido, somente números'), ['somente números'], entrega='nao', isca=True),
    ev('DF-16', 'Produtos', 'Coluna «Custo» de Produtos só aparece para quem tem a permissão canVerCusto (isca: coluna oculta por permissão)',
       _ev_perm_coluna('custo', 'canVerCusto'), ['canVerCusto'], entrega='nao', isca=True),
]
# Entradas transversais (não editam spec): Filtro, locale, mock e rotas.
TRANSVERSAIS_GRANDE = [
    {'id': 'DF-17', 'tipo': 'compartilhado', 'tela': 'Filtro', 'arquivo': 'src/components/Filtro.tsx',
     'descricao': 'Filtro compartilhado: período padrão de 30 dias e filtros avançados recolhíveis (afeta 6 telas sem diff próprio)',
     'marcadores': [], 'afetadas': AFETADAS_FILTRO, 'entrega': 'nao', 'teste': True},
    {'id': 'DF-18', 'tipo': 'locale', 'tela': 'Locale', 'arquivo': 'src/locales/pt-BR.ts',
     'descricao': '40 textos do locale pt-BR reescritos (10 comuns + 10 de cada uma de Comissões, Inventário e Recebimentos)',
     'marcadores': [], 'afetadas': AFETADAS_LOCALE, 'entrega': 'nao', 'teste': True},
    {'id': 'DF-19', 'tipo': 'mock', 'tela': 'Mock', 'arquivo': 'mock/pedidos.ts',
     'descricao': ('Mock de pedidos (GET /api/pedidos) passa a devolver prazoEntrega e canalVenda: Pedidos exibe as novas colunas e o '
                   'Relatório de vendas, sem diff próprio, passa a mostrar valores na coluna e no filtro «Canal de venda», que antes vinham vazios'),
     'marcadores': [], 'afetadas': ['Pedidos', 'RelVendas'], 'entrega': 'nao', 'teste': True},
    {'id': 'DF-20', 'tipo': 'rotas', 'tela': 'Rotas', 'arquivo': 'config/routes.ts',
     'descricao': 'Rotas: entram devoluções, transferências e margem; sai a conciliação bancária',
     'marcadores': [], 'afetadas': ['Devolucoes', 'Transferencias', 'Margem', 'Conciliacao'], 'entrega': 'nao', 'teste': True},
]


# --------------------------------------------------------------------------------------------------------------------
# Arquivos do protótipo por versão
# --------------------------------------------------------------------------------------------------------------------
def spec_v11(nome, evolucoes):
    spec = copy.deepcopy(SPECS[nome])
    for e in evolucoes:
        if e['tela'] == nome and e.get('aplicar'):
            e['aplicar'](spec)
    return spec


def arquivos_proto(tamanho, versao):
    grande = tamanho == 'grande'
    telas = TELAS_GRANDE if grande else TELAS_PEQUENA
    evolucoes = EVOLUCOES_GRANDE if grande else EVOLUCOES_PEQUENA
    v11 = versao == '11'
    arquivos = {
        'package.json': {'name': 'prototipo-gestao', 'version': '1.0.0', 'private': True,
                         'dependencies': {'antd': '^6.0.0', '@umijs/max': '^4.4.0', 'dayjs': '^1.11.13', 'react': '^19.0.0'}},
        'package-lock.json': {'name': 'prototipo-gestao', 'lockfileVersion': 3, 'packages': {}},
        'config/routes.ts': routes_ts(telas, versao),
        'src/components/PageHeader.tsx': PAGE_HEADER, 'src/components/StatusTag.tsx': STATUS_TAG,
        'README.md': '# Protótipo de gestão comercial\n\nAplicação Umi + antd (vendas, estoque, compras, financeiro e fiscal).\n',
    }
    if grande:
        arquivos['src/components/Filtro.tsx'] = filtro_tsx(v11)
        arquivos['src/locales/pt-BR.ts'] = texto_locale(v11)
        if VARIANTE:
            arquivos[VARIANTE.LOCALE_ARQUIVO] = VARIANTE.locale(v11)
        arquivos['mock/pedidos.ts'] = mock_pedidos(v11)
        arquivos['mock/clientes.ts'] = mock_clientes()
    for t in telas_da_versao(telas, versao):
        if VARIANTE and t[1] in VARIANTE.NOMES:
            arquivos[arquivo_proto(t)] = VARIANTE.tela(t[1], v11)
            continue
        spec = spec_v11(t[1], evolucoes) if v11 else SPECS[t[1]]
        arquivos[arquivo_proto(t)] = gerar_tela(t[1], spec)
    return arquivos


# --------------------------------------------------------------------------------------------------------------------
# Git, registro de versão e protótipo
# --------------------------------------------------------------------------------------------------------------------
def git_init(root):
    root.mkdir(parents=True)
    mf.run(mf.GIT + ['init', '-q'], root)
    mf.run(['git', 'config', 'user.name', 'Fixture'], root)
    mf.run(['git', 'config', 'user.email', 'fixture@example.invalid'], root)


def registrar(workspace, root, sobrescrever=False):
    cmd = [sys.executable, str(workspace / 'ecosystem/automation/jarbas.py'), 'reference', 'register-version',
           '--project-root', str(root), '--kind', 'public-repository'] + (['--overwrite'] if sobrescrever else [])
    subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=workspace)


def inspecionar(workspace, root):
    saida = subprocess.run([sys.executable, str(workspace / 'ecosystem/automation/jarbas.py'), 'reference', 'inspect',
                            '--project-root', str(root)], check=True, capture_output=True, text=True).stdout
    dados = json.loads(saida)
    return dados.get('fingerprint') or dados.get('version', {}).get('fingerprint')


def construir_prototipo(dest, workspace, tamanho, registrar_candidata):
    root = dest / 'prototipo'
    git_init(root)
    mf.write(root, arquivos_proto(tamanho, '10'))
    upstream = mf.commit(root, 'upstream: v10 do protótipo')
    mf.write(root, {
        'upstream.json': {'schema_version': '1.0', 'repository': 'https://example.invalid/upstream', 'commit_sha': upstream,
                          'branch': 'master', 'license': 'MIT', 'local_project': 'prototipo-gestao',
                          'source_type': 'public-repository', 'lovable_generation': None, 'export_archive': None,
                          'sdd_supplied': False},
        '.squad/project.yaml': f'schema_version: "1.0"\nproject_uid: {mf.PROTO_UID}\nproject_slug: prototipo-gestao\nname: Protótipo de gestão\ndefault_branch: main\n',
    })
    mf.commit(root, 'chore: registra origem upstream')
    registrar(workspace, root)
    vigente = mf.commit(root, 'chore: registra versão de referência vigente (v10)')
    digest = inspecionar(workspace, root)
    # v11: o que chega do upstream, sem registro (a skill registra a candidata no próprio fluxo)
    mf.run(mf.GIT + ['checkout', '-q', '-b', 'v11'], root)
    novos = arquivos_proto(tamanho, '11')
    antigos = arquivos_proto(tamanho, '10')
    for caminho in antigos:
        if caminho not in novos:
            (root / caminho).unlink()
    mf.write(root, {c: v for c, v in novos.items() if antigos.get(c) != v})
    candidata = mf.commit(root, 'feat: v11 do protótipo')
    registrada, digest_v11 = None, None
    if registrar_candidata:
        mf.run(mf.GIT + ['checkout', '-q', '-b', 'v11-registro'], root)
        registrar(workspace, root, sobrescrever=True)
        registrada = mf.commit(root, 'chore: registra versão de referência candidata (v11)')
        digest_v11 = inspecionar(workspace, root)
    mf.run(mf.GIT + ['checkout', '-q', 'main'], root)
    return root, vigente, digest, candidata, registrada, digest_v11


# --------------------------------------------------------------------------------------------------------------------
# Produto: estilo próprio (telas declarativas sobre componentes padrão)
# --------------------------------------------------------------------------------------------------------------------
LISTA_PADRAO = '''import { useEffect, useState } from 'react';
import { Button, DatePicker, Form, Input, InputNumber, Modal, Popconfirm, Select, Switch, Table, Tag, message } from 'antd';
import dayjs from 'dayjs';
import { api } from './api';

export interface ColunaCfg {
  chave: string;
  titulo: string;
  formato?: 'data' | 'moeda' | 'numero' | 'status' | 'booleano';
}
export interface CampoCfg {
  chave: string;
  rotulo: string;
  tipo?: 'texto' | 'numero' | 'moeda' | 'select' | 'data' | 'area' | 'switch' | 'periodo';
  opcoes?: string[];
  regras?: object[];
}
interface Props {
  titulo: string;
  endpoint: string;
  colunas: ColunaCfg[];
  filtros: CampoCfg[];
  campos: CampoCfg[];
  somenteLeitura?: boolean;
}

const moeda = (v?: number) => (v === undefined ? '-' : v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }));

function entrada(c: CampoCfg) {
  const opcoes = (c.opcoes ?? []).map((o) => ({ value: o, label: o }));
  switch (c.tipo) {
    case 'select':
      return <Select allowClear options={opcoes} style={{ minWidth: 160 }} />;
    case 'periodo':
      return <DatePicker.RangePicker format="DD/MM/YYYY" />;
    case 'data':
      return <DatePicker format="DD/MM/YYYY" />;
    case 'numero':
    case 'moeda':
      return <InputNumber style={{ minWidth: 140 }} />;
    case 'area':
      return <Input.TextArea rows={3} />;
    case 'switch':
      return <Switch />;
    default:
      return <Input allowClear />;
  }
}

export default function ListaPadrao({ titulo, endpoint, colunas, filtros, campos, somenteLeitura }: Props) {
  const [filtroForm] = Form.useForm();
  const [cadastroForm] = Form.useForm();
  const [linhas, setLinhas] = useState<any[]>([]);
  const [editando, setEditando] = useState<any | undefined>();
  const [aberto, setAberto] = useState(false);

  const buscar = async () => {
    try {
      setLinhas(await api.listar(endpoint, filtroForm.getFieldsValue()));
    } catch (e) {
      message.error('Não foi possível carregar os registros');
    }
  };
  useEffect(() => {
    buscar();
  }, []);

  const salvar = async () => {
    const valores = await cadastroForm.validateFields();
    await api.gravar(endpoint, editando?.id, valores);
    message.success('Registro salvo com sucesso');
    setAberto(false);
    buscar();
  };

  const celula = (c: ColunaCfg, v: any) => {
    if (c.formato === 'data') return v ? dayjs(v).format('DD/MM/YYYY') : '-';
    if (c.formato === 'moeda') return moeda(v);
    if (c.formato === 'status') return <Tag>{v}</Tag>;
    if (c.formato === 'booleano') return v ? 'Sim' : 'Não';
    return v;
  };

  const tabela = colunas.map((c) => ({ title: c.titulo, dataIndex: c.chave, render: (v: any) => celula(c, v) }));
  if (!somenteLeitura) {
    tabela.push({
      title: 'Ações',
      dataIndex: 'id',
      render: (_: any, linha: any) => (
        <>
          <Button size="small" onClick={() => { setEditando(linha); cadastroForm.setFieldsValue(linha); setAberto(true); }}>
            Editar
          </Button>
          <Popconfirm title="Confirma a exclusão deste registro?" onConfirm={() => api.remover(endpoint, linha.id).then(buscar)}>
            <Button size="small" danger>
              Excluir
            </Button>
          </Popconfirm>
        </>
      ),
    });
  }

  return (
    <section>
      <h2>{titulo}</h2>
      <Form form={filtroForm} layout="inline" onFinish={buscar}>
        {filtros.map((f) => (
          <Form.Item key={f.chave} name={f.chave} label={f.rotulo}>
            {entrada(f)}
          </Form.Item>
        ))}
        <Button type="primary" htmlType="submit">
          Buscar
        </Button>
        <Button onClick={() => { filtroForm.resetFields(); buscar(); }}>Limpar</Button>
      </Form>
      {!somenteLeitura && (
        <Button type="primary" onClick={() => { setEditando(undefined); cadastroForm.resetFields(); setAberto(true); }}>
          Novo
        </Button>
      )}
      <Table rowKey="id" columns={tabela} dataSource={linhas} />
      <Modal open={aberto} title={titulo} onOk={salvar} onCancel={() => setAberto(false)} okText="Salvar" cancelText="Cancelar">
        <Form form={cadastroForm} layout="vertical">
          {campos.map((c) => (
            <Form.Item key={c.chave} name={c.chave} label={c.rotulo} rules={c.regras} valuePropName={c.tipo === 'switch' ? 'checked' : 'value'}>
              {entrada(c)}
            </Form.Item>
          ))}
        </Form>
      </Modal>
    </section>
  );
}
'''
API_TS = '''export const api = {
  async listar(endpoint: string, filtros: Record<string, unknown>) {
    const resposta = await fetch(endpoint + '?' + new URLSearchParams(JSON.stringify(filtros)));
    return (await resposta.json()).data;
  },
  async gravar(endpoint: string, id: number | undefined, valores: object) {
    await fetch(id ? `${endpoint}/${id}` : endpoint, { method: id ? 'PUT' : 'POST', body: JSON.stringify(valores) });
  },
  async remover(endpoint: string, id: number) {
    await fetch(`${endpoint}/${id}`, { method: 'DELETE' });
  },
};
'''
FORM_PADRAO = '''import { Button, Form, Input, InputNumber, Select, Switch, message } from 'antd';

export interface SecaoCfg {
  titulo: string;
  campos: { chave: string; rotulo: string; tipo?: string; opcoes?: string[]; regras?: object[] }[];
}

export default function FormPadrao({ titulo, endpoint, secoes }: { titulo: string; endpoint: string; secoes: SecaoCfg[] }) {
  const [form] = Form.useForm();
  const enviar = async (valores: object) => {
    await fetch(endpoint, { method: 'POST', body: JSON.stringify(valores) });
    message.success('Dados enviados com sucesso');
  };
  return (
    <section>
      <h2>{titulo}</h2>
      <Form form={form} layout="vertical" onFinish={enviar}>
        {secoes.map((s) => (
          <fieldset key={s.titulo}>
            <legend>{s.titulo}</legend>
            {s.campos.map((c) => (
              <Form.Item key={c.chave} name={c.chave} label={c.rotulo} rules={c.regras} valuePropName={c.tipo === 'switch' ? 'checked' : 'value'}>
                {c.tipo === 'select' ? (
                  <Select options={(c.opcoes ?? []).map((o) => ({ value: o, label: o }))} />
                ) : c.tipo === 'numero' ? (
                  <InputNumber />
                ) : c.tipo === 'switch' ? (
                  <Switch />
                ) : (
                  <Input />
                )}
              </Form.Item>
            ))}
          </fieldset>
        ))}
        <Button type="primary" htmlType="submit">
          Salvar
        </Button>
      </Form>
    </section>
  );
}
'''


def aj(valor):
    """Valor de atributo JSX: aspas duplas quando possível, expressão com aspas simples nos demais casos."""
    return f'"{valor}"' if '"' not in valor and '\\' not in valor else '{' + ts(valor) + '}'


def _cfg_colunas(spec):
    mapa = {'data': 'data', 'moeda': 'moeda', 'numero': 'numero', 'status': 'status', 'switch': 'booleano'}
    saida = []
    for c in spec['colunas']:
        formato = f", formato: '{mapa[c['tipo']]}'" if c['tipo'] in mapa else ''
        saida.append(f"        {{ chave: '{c['chave']}', titulo: {ts(c['rotulo'])}{formato} }},")
    return saida


def _cfg_campos(itens, com_regras):
    saida = []
    for c in itens:
        tipo = {'status': 'select'}.get(c['tipo'], c['tipo'])
        partes = [f"chave: '{c['chave']}'", f"rotulo: {ts(c['rotulo'])}", f"tipo: '{tipo}'"]
        if c['tipo'] in ('select', 'status'):
            partes.append('opcoes: [' + ', '.join(ts(o) for o in c['opcoes']) + ']')
        if com_regras and c.get('regras'):
            partes.append('regras: [' + ', '.join(regra_ts(r) for r in c['regras']) + ']')
        saida.append('        { ' + ', '.join(partes) + ' },')
    return saida


def produto_tela(tela, spec, oco=False):
    nome = _ident(tela[1])
    fundo = '../' * (arquivo_produto(tela).count('/') - 3)
    if spec['tipo'] == 'lista' and not oco:
        L = [f"import ListaPadrao from '{fundo}shared/ListaPadrao';", '', f'export default function {nome}() {{', '  return (', '    <ListaPadrao',
             f"      titulo={aj(spec['titulo'])}", f"      endpoint={aj(spec['endpoint'])}"]
        if spec.get('leitura'):
            L.append('      somenteLeitura')
        L += ['      colunas={[', *_cfg_colunas(spec), '      ]}', '      filtros={[', *_cfg_campos(spec['filtros'], False), '      ]}',
              '      campos={[', *_cfg_campos(spec['campos'], True), '      ]}', '    />', '  );', '}', '']
        return '\n'.join(L)
    if spec['tipo'] == 'lista':
        # tela entregue pela metade: filtros e colunas prontos, mas a tabela ainda não recebe dados
        L = ["import { Button, Form, Input, Table } from 'antd';", '', f'export default function {nome}() {{', '  return (', '    <section>',
             f"      <h2>{spec['titulo']}</h2>", '      <Form layout="inline">']
        for f in spec['filtros']:
            L += [f'        <Form.Item name="{f["chave"]}" label={aj(f["rotulo"])}>', '          <Input allowClear />', '        </Form.Item>']
        L += ['        <Button type="primary" htmlType="submit">', '          Buscar', '        </Button>', '      </Form>', '      <Table',
              "        rowKey=\"id\"", '        columns={[']
        L += [f"          {{ title: {ts(c['rotulo'])}, dataIndex: '{c['chave']}' }}," for c in spec['colunas']]
        L += ['        ]}', '        dataSource={[]}', '      />', '    </section>', '  );', '}', '']
        return '\n'.join(L)
    if spec['tipo'] == 'form':
        L = [f"import FormPadrao from '{fundo}shared/FormPadrao';", '', f'export default function {nome}() {{', '  return (', '    <FormPadrao',
             f"      titulo={aj(spec['titulo'])}", f"      endpoint={aj(spec['endpoint'])}", '      secoes={[']
        for secao, campos in spec['secoes']:
            L += ['        {', f"          titulo: {ts(secao)},", '          campos: [', *['  ' + l for l in _cfg_campos(campos, True)], '          ],', '        },']
        L += ['      ]}', '    />', '  );', '}', '']
        return '\n'.join(L)
    if spec['tipo'] == 'painel':
        L = [f'export default function {nome}() {{', '  return (', '    <section>', f"      <h2>{spec['titulo']}</h2>", '      <ul>']
        L += [f"        <li>{t}: {v}{' ' + suf if suf else ''}</li>" for t, v, suf in spec['cartoes']]
        L += ['      </ul>', f"      <h3>{spec['tabela']}</h3>", '      <table>', '        <thead>', '          <tr>']
        L += [f"            <th>{c['rotulo']}</th>" for c in spec['colunas']]
        L += ['          </tr>', '        </thead>', '      </table>', '    </section>', '  );', '}', '']
        return '\n'.join(L)
    return "export default function NaoEncontrada() {\n  return <section><h2>%s</h2></section>;\n}\n" % spec['titulo']


def app_tsx(telas):
    L = ["import { createBrowserRouter } from 'react-router-dom';"]
    for t in telas:
        L.append(f"import {_ident(t[1])} from './pages/{componente(t)[2:]}';")
    L += ['', 'export const router = createBrowserRouter([']
    for t in telas:
        L.append(f"  {{ path: '{rota_da_tela(t)}', element: <{_ident(t[1])} /> }},")
    L += [']);', '']
    return '\n'.join(L)


def teste_tsx(tela, descricao):
    nome = _ident(tela[1])
    caminho = f'../{tela[0]}/{tela[1]}' if tela[0] else f'../{tela[1]}'
    return (f"import {{ render, screen }} from '@testing-library/react';\nimport {{ describe, expect, it }} from 'vitest';\n"
            f"import {nome} from '{caminho}';\n\ndescribe('{nome}', () => {{\n  it({ts(descricao)}, () => {{\n"
            f"    render(<{nome} />);\n    expect(screen.getAllByRole('heading').length).toBeGreaterThan(0);\n  }});\n}});\n")


def construir_produto(dest, tamanho, cenario, ctx):
    """Produto em `main`: v10 fiel; `entregue` acrescenta a v11 parcial e o catálogo da v11 com tarefas."""
    grande = tamanho == 'grande'
    telas = TELAS_GRANDE if grande else TELAS_PEQUENA
    evolucoes = EVOLUCOES_GRANDE if grande else EVOLUCOES_PEQUENA
    root = dest / 'produto'
    git_init(root)
    arquivos = {
        '.squad/project.yaml': f'schema_version: "1.0"\nproject_uid: {mf.PRODUCT_UID}\nproject_slug: produto-gestao\nname: Produto de gestão\ndefault_branch: main\n',
        'apps/web/src/shared/ListaPadrao.tsx': LISTA_PADRAO, 'apps/web/src/shared/api.ts': API_TS,
        'apps/web/src/shared/FormPadrao.tsx': FORM_PADRAO,
    }
    v10 = telas_da_versao(telas, '10')
    for t in v10:
        arquivos[arquivo_produto(t)] = produto_tela(t, SPECS[t[1]])
    arquivos['apps/web/src/app.tsx'] = app_tsx(v10)
    mf.write(root, arquivos)
    base = mf.commit(root, 'feat: telas do produto na versão 10 do protótipo')
    ctx['v10_commit'] = base
    if cenario == 'sem-catalogo':
        return root
    if cenario == 'com-catalogo':
        cat = catalogo_v10(telas, ctx, base)
        if EXCECAO_ANTIGA:
            cat['differences'].append(copy.deepcopy(DIFERENCA_ANTIGA))
        mf.write(root, {'.squad/contracts/parity/catalog.json': cat,
                        '.squad/milestones/v10.json': {'marco': 'versao-liberada', 'versao': 'v10', 'target_commit': base,
                                                       'reference_version': ctx['vigente'], 'confirmado_por': 'Diego',
                                                       'decision_ref': 'DEC-2026-10-15-v10-liberada'}})
        mf.commit(root, 'chore: catálogo de paridade da v10 e marco registrado')
        return root
    # entregue: v11 em parte (telas entregues, uma delas oca), catálogo da v11 com tarefas
    entregues = {e['tela']: e for e in evolucoes if e['entrega'] in ('sim', 'stub')}
    novos = {}
    ativas = list(v10)
    for t in telas:
        if t[4] == '11' and t[1] in entregues:
            ativas.append(t)
    for t in ativas:
        e_tela = [e for e in evolucoes if e['tela'] == t[1] and e['entrega'] in ('sim', 'stub') and e.get('aplicar')]
        spec = copy.deepcopy(SPECS[t[1]])
        for e in e_tela:
            e['aplicar'](spec)
        oco = any(e['entrega'] == 'stub' for e in evolucoes if e['tela'] == t[1])
        if e_tela or oco or t[4] == '11':
            novos[arquivo_produto(t)] = produto_tela(t, spec, oco=oco)
            if oco:
                ctx['stub'] = {'arquivo': arquivo_produto(t), 'tela': t[1], 'padrao': 'lista_vazia_em_prop'}
    novos['apps/web/src/app.tsx'] = app_tsx(ativas)
    for e in evolucoes:
        if e['entrega'] in ('sim', 'stub') and e['teste'] and e['tipo'] != 'removida':
            tela = next(t for t in telas if t[1] == e['tela'])
            novos[f"apps/web/src/pages/__tests__/{tela[1]}.test.tsx"] = teste_tsx(tela, e['descricao'])
    mf.write(root, novos)
    parcial = mf.commit(root, 'feat: v11 em andamento (telas entregues parcialmente)')
    cat = catalogo_v11(telas, evolucoes, ctx, parcial)
    mf.write(root, {'.squad/contracts/parity/catalog.json': cat})
    mf.commit(root, 'chore: catálogo de paridade da v11 com tarefas')
    return root


# --------------------------------------------------------------------------------------------------------------------
# Catálogos
# --------------------------------------------------------------------------------------------------------------------
def _sufixo(tela):
    return re.sub(r'[^A-Z0-9]+', '-', rota_da_tela(tela).upper()).strip('-') or 'RAIZ'


def _definicao(spec, rota):
    if spec['tipo'] == 'lista':
        return {'rota': rota, 'titulo': spec['titulo'], 'colunas': [c['rotulo'] for c in spec['colunas']],
                'filtros': [f['rotulo'] for f in spec['filtros']], 'campos': [c['rotulo'] for c in spec['campos']]}
    if spec['tipo'] == 'form':
        return {'rota': rota, 'titulo': spec['titulo'], 'campos': [c['rotulo'] for _, cs in spec['secoes'] for c in cs]}
    return {'rota': rota, 'titulo': spec['titulo']}


def _dependencias_proto(tela, spec):
    deps = ['src/components/PageHeader.tsx'] if spec['tipo'] != 'excecao' else []
    if spec['tipo'] in ('lista', 'painel'):
        deps.append('src/components/StatusTag.tsx')
    if spec.get('filtro_comp'):
        deps.append('src/components/Filtro.tsx')
    return deps


def base_catalogo(telas, versao_evidencia, ctx, referencia_por_tela=None):
    """Esqueleto do catálogo: uma superfície, região, estado, cenário e evidência por tela."""
    cat = {'schema_version': '1.0', 'project_uid': mf.PRODUCT_UID, 'surfaces': [], 'regions': [], 'states': [], 'scenarios': [],
           'evidence': [], 'differences': [], 'requirements': [], 'journeys': [], 'tasks': [], 'tests': [],
           'scope_claim': 'KNOWN_SCENARIOS'}
    for t in telas:
        suf, spec = _sufixo(t), SPECS[t[1]]
        commit = (referencia_por_tela or {}).get(t[1], versao_evidencia)
        cat['surfaces'].append({'id': f'SF-{suf}', 'name': spec['titulo']})
        cat['regions'].append({'id': f'RG-{suf}', 'surface_id': f'SF-{suf}', 'discovery_status': 'INVESTIGADO', 'provenance_refs': [f'EV-{suf}']})
        cat['states'].append({'id': f'ST-{suf}', 'region_id': f'RG-{suf}', 'discovery_status': 'INVESTIGADO', 'provenance_refs': [f'EV-{suf}']})
        cenario = {'id': f'SC-{suf}', 'region_id': f'RG-{suf}', 'state_id': f'ST-{suf}', 'dimensions': ['functional'],
                   'definition': _definicao(spec, rota_da_tela(t)),
                   'files': {'prototipo': [arquivo_proto(t)] + _dependencias_proto(t, spec), 'produto': [arquivo_produto(t)]}}
        if referencia_por_tela is not None and t[1] not in referencia_por_tela:
            cenario['carried_from'] = ctx['vigente']
        cat['scenarios'].append(cenario)
        cat['evidence'].append({'id': f'EV-{suf}', 'kind': 'src', 'locator': f'prototipo@{commit}:{arquivo_proto(t)}'})
    return cat


def catalogo_v10(telas, ctx, base):
    cat = base_catalogo(telas_da_versao(telas, '10'), ctx['vigente'], ctx)
    cat.update({'mode': 'FULL', 'reference': {'version': ctx['vigente'], 'digest': ctx['digest']}, 'target': {'commit': base},
                'baseline': {'trusted': True, 'reference_version': ctx['vigente'], 'reference_digest': ctx['digest'],
                             'target_commit': base,
                             'milestone': {'tipo': 'versao-liberada', 'descricao': 'v10 liberada em produção', 'registro': '.squad/milestones/v10.json'},
                             'evidence_refs': [e['id'] for e in cat['evidence'][:1]], 'confirmed_by': 'Diego',
                             'decision_ref': 'DEC-2026-10-15-v10-liberada'}})
    return cat


def _tela_da_superficie(e, por_nome, ativas):
    """Tela cuja superfície recebe a diferença: a própria, a primeira afetada ou, se removida, uma irmã de pasta."""
    if e['tipo'] == 'removida':
        tela = por_nome[e['tela']]
        return next(t for t in ativas if t[0] == tela[0])
    return por_nome[e['tela']] if e['tela'] in por_nome else por_nome[e['afetadas'][0]]


def catalogo_v11(telas, evolucoes, ctx, parcial):
    ativas = telas_da_versao(telas, '11')
    tocadas = {e['tela'] for e in evolucoes}
    cat = base_catalogo(ativas, ctx['vigente'], ctx, referencia_por_tela={n: ctx['registrada'] for n in tocadas})
    cat.update({'mode': 'INCREMENTAL', 'reference': {'version': ctx['registrada'], 'digest': ctx['digest_v11']},
                'target': {'commit': parcial}, 'baseline': {'trusted': False}})
    por_nome = {t[1]: t for t in telas}
    tk = ts_ = 0
    for n, e in enumerate(evolucoes + ctx['transversais'], start=1):
        tela = _tela_da_superficie(e, por_nome, ativas)
        suf = _sufixo(tela)
        sc = f"SC-{suf}-{e['id']}"
        req = f"REQ-{e['id'][3:]}"
        cat['scenarios'].append({'id': sc, 'region_id': f'RG-{suf}', 'state_id': f'ST-{suf}', 'dimensions': ['functional'],
                                 'definition': {'mudanca': e['descricao']}})
        dif = {'id': e['id'], 'surface_id': f'SF-{suf}', 'classe': 'MUDANCA-V11', 'resumo': e['descricao'],
               'requirement_ids': [req], 'task_ids': []}
        requisito = {'id': req, 'scenario_ids': [sc], 'difference_ids': [e['id']], 'task_ids': []}
        if e['entrega'] in ('sim', 'stub'):
            tk += 1
            tarefa = f'TK-{tk:02d}'
            dif['task_ids'] = [tarefa]
            requisito['task_ids'] = [tarefa]
            cat['tasks'].append({'id': tarefa, 'requirement_ids': [req], 'scenario_ids': [sc], 'depends_on': [],
                                 'resumo': e['descricao'], 'status': 'entregue'})
            if e['teste']:
                ts_ += 1
                cat['tests'].append({'id': f'TS-{ts_:02d}', 'task_id': tarefa, 'scenario_ids': [sc], 'kind': 'unit',
                                     'file': f"apps/web/src/pages/__tests__/{por_nome[e['tela']][1]}.test.tsx"})
            else:
                ctx['sem_teste'] = req
        cat['differences'].append(dif)
        cat['requirements'].append(requisito)
    return cat


# --------------------------------------------------------------------------------------------------------------------
# Gabarito
# --------------------------------------------------------------------------------------------------------------------
def _linhas_do_marcador(texto, marcadores):
    baixos = [m.lower() for m in marcadores]
    return [i for i, linha in enumerate(texto.splitlines(), start=1) if any(m in linha.lower() for m in baixos)]


def trechos_do_arquivo(mapa, arquivo, texto_novo, marcadores):
    """Ids dos trechos do `arquivo`; com `marcadores`, só os que cobrem alguma linha que os contém no texto novo."""
    todos = [t for t in mapa['trechos'] if t['arquivo'] == arquivo]
    if not marcadores:
        return [t['id'] for t in todos]
    linhas = _linhas_do_marcador(texto_novo, marcadores)
    achados = [t['id'] for t in todos if t['linhas'] and any(t['linhas'][0] <= n <= t['linhas'][1] for n in linhas)]
    if not achados:
        raise SystemExit(f'marcadores {marcadores} sem trecho em {arquivo}')
    return achados


def montar_gabarito(tamanho, telas, evolucoes, transversais, mapa, proto, candidata, ctx):
    ids_tela = {t['arquivo']: t['id'] for t in mapa['telas'] if t['arquivo']}
    por_nome = {t[1]: t for t in telas}
    leitor = mapa_leitor(proto, candidata)
    difs, iscas = [], []
    for e in evolucoes + transversais:
        if e['tipo'] in ('tela', 'nova', 'removida'):
            tela = por_nome[e['tela']]
            arquivo = arquivo_proto(tela)
            texto = '' if e['tipo'] == 'removida' else leitor(arquivo)
            trechos = trechos_do_arquivo(mapa, arquivo, texto, e['marcadores'])
            item = {'id': e['id'], 'tela': ids_tela[arquivo], 'tipo': e['tipo'], 'arquivo': arquivo, 'descricao': e['descricao'],
                    'trechos': trechos}
        else:
            afetadas = [ids_tela[arquivo_proto(por_nome[n])] for n in e['afetadas'] if arquivo_proto(por_nome[n]) in ids_tela]
            item = {'id': e['id'], 'tela': e['arquivo'], 'tipo': e['tipo'], 'arquivo': e['arquivo'], 'descricao': e['descricao'],
                    'trechos': trechos_do_arquivo(mapa, e['arquivo'], leitor(e['arquivo']), e['marcadores']), 'telas_afetadas': afetadas}
        difs.append(item)
        if e.get('isca'):
            iscas.append({'id': e['id'], 'tela': item['tela'], 'arquivo': item['arquivo'], 'descricao': e['descricao'], 'trechos': item['trechos']})
    removida = next((ids_tela_removida(mapa, arquivo_proto(por_nome[e['tela']])) for e in evolucoes if e['tipo'] == 'removida'), None)
    return {'tamanho': tamanho, 'vigente': ctx['vigente'], 'candidata': candidata, 'orcamento': ORCAMENTO,
            'peso_total': mapa['peso_total'], 'n_trechos': len(mapa['trechos']), 'n_telas_no_mapa': len(mapa['telas']),
            'diferencas_esperadas': difs, 'iscas': iscas, 'removida': removida}


def ids_tela_removida(mapa, arquivo):
    return next(t['id'] for t in mapa['telas'] if t['arquivo'] == arquivo)


def mapa_leitor(proto, rev):
    def ler(caminho):
        return mf.run(['git', 'show', f'{rev}:{caminho}'], proto) + '\n'
    return ler


# --------------------------------------------------------------------------------------------------------------------
# Variantes
# --------------------------------------------------------------------------------------------------------------------
def ativar_variante(nome):
    """`irmas`: acrescenta as telas, as specs do produto, o grupo de rotas e o access de rota da variante (só em `main`)."""
    global VARIANTE, EXCECAO_ANTIGA
    EXCECAO_ANTIGA = nome == 'com-excecao'
    if nome != 'irmas':
        return
    spec = importlib.util.spec_from_file_location('variante_irmas', AQUI / 'variante_irmas.py')
    VARIANTE = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(VARIANTE)
    TELAS_GRANDE.extend(VARIANTE.TELAS)
    SPECS.update(VARIANTE.SPECS)
    GRUPOS['analises'] = VARIANTE.GRUPO
    ACESSO_ROTA.update(VARIANTE.ACESSO_ROTA)


# --------------------------------------------------------------------------------------------------------------------
# Principal
# --------------------------------------------------------------------------------------------------------------------
def carregar_mapa(workspace):
    caminho = workspace / 'ecosystem/canonical/skills/atualizacao-versao-prototipo/scripts/cobertura_mapa.py'
    spec = importlib.util.spec_from_file_location('cobertura_mapa', caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def dentro_de(caminho, pai):
    try:
        caminho.relative_to(pai)
        return True
    except ValueError:
        return False


def montar_primeira_sincronizacao(dest, gabarito, workspace):
    spec = importlib.util.spec_from_file_location('primeira_sincronizacao', AQUI / 'primeira_sincronizacao.py')
    ps = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ps)
    mv = sys.modules[__name__]
    proto, inicial, candidata, digest = ps.construir_prototipo(mv, dest, workspace)
    produto = ps.construir_produto(mv, dest)
    modulo_mapa = carregar_mapa(workspace)
    vazia = modulo_mapa.arvore_vazia(proto)
    mapa = modulo_mapa.mapear(proto, vazia, candidata, ORCAMENTO)
    dados = ps.montar_gabarito(mv, mapa, candidata, vazia, digest, inicial)
    gabarito.parent.mkdir(parents=True, exist_ok=True)
    gabarito.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'prototipo': str(proto), 'produto': str(produto), 'vigente': vazia, 'commit_inicial': inicial,
                      'candidata': candidata, 'produto_commit': mf.run(['git', 'rev-parse', 'HEAD'], produto)}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('destino', type=Path)
    parser.add_argument('--tamanho', required=True, choices=['pequena', 'grande'])
    parser.add_argument('--cenario', required=True, choices=['com-catalogo', 'sem-catalogo', 'entregue', 'primeira-sincronizacao'])
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--gabarito', required=True, type=Path)
    parser.add_argument('--variante', choices=['nenhuma', 'irmas', 'com-excecao'], default='nenhuma')
    args = parser.parse_args()
    if args.variante == 'irmas' and args.tamanho != 'grande':
        parser.error('--variante irmas só vale com --tamanho grande')
    if args.variante == 'com-excecao' and args.cenario != 'com-catalogo':
        parser.error('--variante com-excecao só vale com --cenario com-catalogo')
    if args.cenario == 'primeira-sincronizacao' and (args.tamanho != 'grande' or args.variante != 'nenhuma'):
        parser.error('--cenario primeira-sincronizacao só vale com --tamanho grande e sem --variante')
    dest, gabarito, workspace = args.destino.resolve(), args.gabarito.resolve(), args.workspace.resolve()
    if dentro_de(gabarito, dest):
        parser.error(f'o gabarito não pode ficar dentro do destino: {gabarito}')
    if dest.exists() and any(dest.iterdir()):
        parser.error(f'destino não vazio: {dest}')
    os.environ.update({'GIT_AUTHOR_DATE': DATA_GIT, 'GIT_COMMITTER_DATE': DATA_GIT})
    dest.mkdir(parents=True, exist_ok=True)
    ativar_variante(args.variante)
    if args.cenario == 'primeira-sincronizacao':
        montar_primeira_sincronizacao(dest, gabarito, workspace)
        return
    grande = args.tamanho == 'grande'
    telas = TELAS_GRANDE if grande else TELAS_PEQUENA
    evolucoes = EVOLUCOES_GRANDE if grande else EVOLUCOES_PEQUENA
    transversais = TRANSVERSAIS_GRANDE if grande else []

    proto, vigente, digest, candidata, registrada, digest_v11 = construir_prototipo(dest, workspace, args.tamanho, args.cenario == 'entregue')
    ctx = {'vigente': vigente, 'digest': digest, 'registrada': registrada, 'digest_v11': digest_v11, 'transversais': transversais}
    produto = construir_produto(dest, args.tamanho, args.cenario, ctx)

    modulo_mapa = carregar_mapa(workspace)
    mapa = modulo_mapa.mapear(proto, vigente, candidata, ORCAMENTO)
    dados = montar_gabarito(args.tamanho, telas, evolucoes, transversais, mapa, proto, candidata, ctx)
    if VARIANTE:
        ids_mapa = {t['arquivo']: t['id'] for t in mapa['telas'] if t['arquivo']}
        ids = {t[1]: ids_mapa.get(arquivo_proto(t)) or modulo_mapa._slug_da_rota(rota_da_tela(t)) for t in VARIANTE.TELAS}
        dados.update(VARIANTE.gabarito(ids, [i for i in ids.values() if i not in {t['id'] for t in mapa['telas']}]))
    if EXCECAO_ANTIGA:
        dados['excecao_antiga'] = DIFERENCA_ANTIGA['id']
    dados['stub'] = ctx.get('stub')
    dados['sem_teste'] = ctx.get('sem_teste')
    gabarito.parent.mkdir(parents=True, exist_ok=True)
    gabarito.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'prototipo': str(proto), 'produto': str(produto), 'vigente': vigente, 'candidata': candidata,
                      'produto_commit': mf.run(['git', 'rev-parse', 'HEAD'], produto)}, indent=2))


if __name__ == '__main__':
    main()
