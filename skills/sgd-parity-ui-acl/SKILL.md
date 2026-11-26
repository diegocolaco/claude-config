---
name: sgd-parity-ui-acl
description: Use quando criar ou mover tela do SGD, para registrar a rota no catálogo
  de paridade e ACL.
---
CTX-ID: sgd-parity-ui-acl@1

# SGD — ACL de menu e padrao de UI (obrigatorio para o developer)

Aplica-se a **toda** tela nova ou movida no SGD.

> **Condição de uso do Dom DS (§2 e §3):** as orientações de Dom DS (chrome do Dom DS, `dom-table`, componentes `dom-*`, «sem clonar Ant Design») valem quando `@onviobr/dom-components` estiver no `package.json` do alvo. Sem o pacote, elas não se aplicam, e a biblioteca é a de [atualizacao-versao-prototipo/references/sgd.md](../atualizacao-versao-prototipo/references/sgd.md) (Ant Design agora, Dom DS depois, se vier). O resto continua valendo: a ACL de menu (§1) e a disposição, a ordem e o tamanho do protótipo. Sem o pacote, prevalece a paridade com o protótipo, «O máximo possivel igual dentro do possível», inclusive onde esta skill manda divergir dele: «Pixel-perfect Recharts **nao** e obrigatorio» (§2), a paginação que o SGD acrescenta onde o protótipo não pagina (§3) e o placeholder inventado quando o protótipo não tem (checklist de formulário). Motivo: sem o pacote, mandar usar `dom-*` ou divergir do protótipo atropelaria a decisão do Diego.

Fonte: pedido humano 2026-09-22 + SDD geral de paridade v6, secao 5.1.

## 1. Diretivas de acesso a menu (sempre)

Toda rota nova/movida **obrigatoriamente** entra no catalogo de menus com `menuKey` estavel.

| Perfil | Comportamento |
|---|---|
| **master** | Ve **todos** os itens (mesmo com grupo restrito). Nunca filtrar master por `allowedMenuKeys`. Itens so-master usam `roles: ['master']` (ex.: Empresas). |
| **admin** | Ve os menus de processo/config como hoje (`admin || master` no BE `getMenuAccess`). Nao esconder item novo do admin sem SDD explicito. |
| **user** (normal) | So ve o item se o **grupo** tiver a `menuKey` em `menu_ids` / `permission_group_menus` (`view` / `canCreate` / `canEdit` / `canApprove` quando couber). Sem grupo = sem menu. |

Checklist do developer (nao entregar sem isto):

1. `AppLayout.tsx` — item com `to`, `label`, `icon`, **`menuKey`** no grupo certo (Cadastros vs Configuracoes vs Comercial…).
2. Catalogo de permissoes (tela Permissoes de Usuario) — a nova key aparece para o admin marcar no grupo.
3. BE `PermissionsService.getMenuAccess` — a key entra no catalogo devolvido; master/admin `view=true`; user conforme grupo.
4. **MOVE** de rota (ex. Produtos Config → Cadastros): remap `permission_group_menus` das keys antigas para as novas **sem perder acesso**; redirect da URL antiga.
5. Teste: master ve; admin ve (se for menu de processo); user **sem** a key **nao** ve; user **com** a key ve.
6. Nao promover no menu o que o proto v6 tambem nao mostra no shell (ex.: Representantes).

## 2. Front — disposicao, tamanho e ordem do prototipo

A tela vem do prototipo indicado na sessao. O developer **copia**:

- ordem dos campos, abas, botoes e colunas
- agrupamento visual (o que esta na mesma linha / no mesmo bloco)
- hierarquia (principal vs secundario), densidade aproximada

Pixel-perfect Recharts **nao** e obrigatorio nas telas em geral; **excecao Visao Geral VG2** (humano 2026-09-22): ordem, agrupamento, tamanho relativo, atalho **Detalhar** e alturas dos graficos **iguais ao proto**. Charts em SVG/Dom DS, sem clonar Ant Design pixel a pixel fora desta tela.

## 3. Front — padrao de telas do SGD novo

Por cima do proto, usar o **chrome ja existente** do SGD (Dom DS):

- Listagens: `SortableSearchableTable` / `dom-table` com **paginacao** (server-side se o dataset nao cabe numa pagina).
- **Filtros** quando a lista for grande ou o proto filtrar (nunca load-all de municipios/IBGE).
- Busca/ordenacao sobre o conjunto filtrado (CT-16: nao so a pagina visivel; "selecionar todos" = todos os filtrados).
- Formularios: grids do app (`.form-grid-1/2/3`, `.form-row-24`, `.cadastro-bloco`) + componentes `dom-*`.
- Erro: mensagem + **traceId**.

### Checklist de formulario (toda tela nova ou alterada)

Nao entregar cadastro/formulario sem isto:

1. **Placeholder** em todo `dom-input-text` / select pesquisavel (copiar o proto; se o proto nao tiver, usar `Ex.: …` ou `Selecione`).
2. **Espaco label→campo** = padrao SGD: `dom-input-text` **sem** `show-support-info="false"` (esse attr so em `dom-input-select`, como em Cargos). Nao usar `ds-field-label` paralelo no mesmo campo.
3. **Ativo** = `dom-switch` `{Ativo|Inativo}` (ouro: cadastro **Novo Produto**), **filho direto** do `FormDrawer` — nunca `dom-checkbox` numa celula da grade ao lado de inputs com label (alinha errado). Status na **tabela** continua badge Ativo/Inativo.
4. **Empresa** se o proto tem CompanyField: `dom-input-select` **Empresa** visivel for **master** na criacao; enviar `companyId` na query (mesmo padrao Cargos). Nao campo de UUID.
5. **Nunca** input de texto "IDs separados por virgula". Usar `MultiSelectSearchable` / `dom-input-select` com nome dos itens.

Se o proto for Ant Design tabela unica sem pagina e o SGD ja pagina cadastros semelhantes: **paginar no SGD** (padrao do produto), mantendo colunas e ordem do proto.
