# Decisões da reconstrução do SGD a partir do protótipo (v11)

Documento de decisões já aprovado pelo Diego. O catálogo de paridade (`.squad/contracts/parity/catalog.json`) diz o que o SGD tem de ter; este documento diz como.

## Biblioteca de componentes

- Ant Design 6 (`antd`) é a biblioteca de componentes do SGD, a mesma do protótipo. Componentes fora de `antd` não entram.
- Lista inicial de componentes: `Table`, `Form`, `Input`, `Select`, `DatePicker`, `Button`, `Modal`, `Card`, `Space`, `Typography`.
- Biblioteca nova ou componente fora da lista: parar e perguntar ao Diego.

## Divisão em grupos

Um grupo por chat de implementação, em sequência:

1. `Base`: layout, tema, cabeçalho e rotas.
2. `Painel`: o painel gerencial.
3. `Pedidos`: a consulta de pedidos de venda e o que nasce dela (filtros, colunas e o formulário do pedido).
4. `Cadastros`: Clientes e Produtos.

`Pedidos` é um grupo: o plano dele cobre toda diferença e todo requisito do catálogo que pertença à superfície de Pedidos.

## Testes

- Teste de componente com Vitest e Testing Library, em `apps/web/src/pages/__tests__/<Tela>.test.tsx`.
- A aparência é conferida lendo o código do protótipo; não se sobe o protótipo nem se tiram prints.
