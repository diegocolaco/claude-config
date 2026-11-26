---
name: new-page-scaffold
description: Use ao criar nova página, listagem ou formulário Dom DS no SGD novo (Angular ou React/Vite), e só quando `@onviobr/dom-components` estiver no `package.json` do alvo.
---
CTX-ID: new-page-scaffold@2

# new-page-scaffold ? Estruturar o Design System antes de implementar

> **Condição de uso:** vale quando `@onviobr/dom-components` estiver no `package.json` do alvo. Sem o pacote, este scaffold não se aplica, e a biblioteca de componentes é a da decisão do Diego ([atualizacao-versao-prototipo/references/sgd.md](../atualizacao-versao-prototipo/references/sgd.md): Ant Design agora, Dom DS depois, se vier). Motivo: sem o pacote, este scaffold mandaria usar uma biblioteca indisponível e atropelaria essa decisão.

## Composição Superpowers

Pré-scaffold do Dom DS antes de codar a UI; o ciclo de implementação que segue é o do Superpowers.

**REQUIRED BACKGROUND:** You MUST understand `superpowers:test-driven-development` — o scaffold prepara o contrato do DS; o código da página nasce por RED→GREEN.

## Por que esta skill existe

Toda vez que o agente implementa uma nova pagina **sem conhecer o contrato real dos componentes do Dom DS**, surgem bugs silenciosos: componente que renderiza vazio, formulario que nao aparece, opcoes que nao carregam, botao invisivel, labels desalinhados.

**Causa:** confiar na memoria / nas definicoes de tipo (`.d.ts`) em vez do contrato real (o `render()` e o ciclo de vida do componente) e/ou tentar seguir uma "app de referencia" que **nao existe** neste workspace.

**Solucao:** estruturar bem o DS a partir da fonte de verdade ? o **pacote instalado** e o **Storybook** ? e definir as convencoes de layout no proprio app.

> Nao ha app de referencia (`apps/...`) neste workspace. Nao tente le-la. A fonte de verdade e `node_modules/@onviobr/dom-components` + Storybook.

---

## OBRIGATORIO ? Executar ANTES de criar qualquer arquivo novo

### Passo 1 ? Ler o contrato real de cada componente do DS que vai usar

Para cada `dom-*` que a pagina vai usar, ler:

```
node_modules/@onviobr/dom-components/dist/collection/components/<componente>/<componente>.js
node_modules/@onviobr/dom-components/dist/collection/components/<componente>/<componente>.stories.js
```

O que extrair:
- `render()`: existe alguma guarda que retorna `null` (o componente nao renderiza sem certas props)?
- `componentDidLoad()` / `@Watch`: o que e sincronizado **uma unica vez** vs. o que e observado? (impacta opcoes/dados assincronos)
- Eventos emitidos (`dom*`) e como as props sao recebidas (atributo vs. propriedade).
- Storybook (catalogo visual + props minimas): `https://lab01.onvio.com.br/br-storybook/`

### Passo 2 ? Estruturar as convencoes de layout no proprio app

Definir, **no stylesheet global do app** (nao em CSS escopado de componente), as classes de layout do padrao:
`.cadastro-bloco`, `.pad`, `.flow-table-wrap`, `.flow-stack`, `.form-grid-1`, `.form-grid-2`, `.form-grid-3`, `.paginacao-wrap`.

Estrutura de pagina de cadastro (lista + form):
```
cadastro-bloco -> toolbar -> div.pad -> div.flow-table-wrap -> dom-table + paginacao
```

Importar os tokens do DS globalmente: `@onviobr/dom-tokens`.

### Passo 3 ? Integracao do DS por framework

- **React/Vite:** `defineCustomElements(window)` de `@onviobr/dom-components/loader` no `main.tsx`; props complexas (arrays/objetos) setadas por **propriedade** via `ref`; eventos `dom*` via `addEventListener`.
- **Angular:** `CUSTOM_ELEMENTS_SCHEMA` nas views; tokens no `angular.json`; `[data]`, `(domFilterChange)` etc. nos templates.

---

## Contratos de componentes que mais quebram (conferir no Passo 1)

| Componente | Armadilha | Como usar certo |
|---|---|---|
| `dom-dialog` | corpo so via prop `description` (texto); sem slot | formulario/conteudo -> `dom-modal` (corpo via slot) |
| `dom-input-select` | renderiza `null` sem `show-support-info="false"` (ou support-text); opcoes sincronizadas so uma vez | setar `show-support-info="false"`; re-montar/re-sincronizar quando as `<option>` mudam |
| `dom-button` / `dom-button-icon` | evento nativo `click`; icone invalido = botao invisivel | React `onClick` / Angular `(click)`; `variant` atributo; icones so de `@onviobr/dom-icons` |
| `dom-table` | dados por propriedade `data`, nao por slot | setar `data` por propriedade; colunas com `cell-type`/`header-type` |
| `dom-modal` (focus trap) | trap decide "dentro" via `shadowRoot.contains(activeElement)`; com formulario slotted (light DOM) o Tab salta para o "X" em vez do proximo campo | `addEventListener('keydown', e => { if (e.key === 'Tab') e.stopPropagation() })` no `dom-modal` -> Tab nativo percorre os campos |
| `dom-modal` (eventos em React) | listeners `domModalClose/PrimaryAction/SecondaryAction` atados quando o elemento ainda nao existia (wrapper montado renderizando null) -> X/Cancelar/Salvar "sem efeito" | montar o `dom-modal` SO quando aberto (componente interno) para os listeners ligarem ao elemento presente |
| `dom-input-select` / `dom-pagination` (page-size) | valor/opcoes sincronizados so no load -> mostra valor errado / nao muda | valor como atributo no mount + remontar via `key` quando muda; tratar `domChange`/`domPageSizeChange` |
| `dom-pagination` (Ir para a pagina) | input `fit-to-label` renderiza com largura 0 (nao habilita) | construir paginador de primitivos do DS (dom-button + dom-input-text + dom-input-select) - excecao aprovada (ver playbook) |
| `dom-checkbox` (teste/clique) | `<input>` nativo oculto | clicar no rotulo visivel (ou `force`) |

---

## Paridade visual com a tela de origem (ANTES do primeiro JSX)

Quando a tela nasce de um prototipo (v6 ou outro), o contrato do Dom DS nao substitui a tela. Sem este inventario, o primeiro desenho erra campo, fonte e alinhamento.

1. **Inventario, uma linha por controle, antes de escrever JSX:** rotulo, componente `dom-*`, obrigatorio, valor inicial. A quantidade e a ordem tem de ser as da tela de origem. Campo a mais ou a menos: parar.
2. **Mesma familia na mesma linha.** Dois campos lado a lado usam o mesmo `dom-*`. Nunca `dom-input-text` ao lado de `<input>` nativo.
3. **Um rotulo so.** O texto fica na prop `label` do `dom-*`. Sem `<label>` extra por fora (isso duplica a descricao).
4. **Grid so pelas classes globais** `.form-grid-1/2/3`. Sem `style={{ display:'grid' }}` e sem `align-items`.
5. **Sem componente no DS** (hora, data/hora): parar e perguntar A/B/C. Nao publicar input nativo na mesma linha de um campo do DS.
6. **Pronto so com as duas telas juntas:** mesmos campos, mesma ordem, mesmo pareamento de linha, rotulos alinhados. Teste verde de payload nao fecha este item.
7. **Botao de novo item no canto superior direito.** Fica em `PageHeader` `actions`, na mesma linha do titulo. Nao fica numa faixa abaixo do titulo e nao se mistura com filtro nem com troca de visao (kanban/lista). Essas ficam na faixa de filtros.

## Regras de layout de formulario (verificar em TODO template/JSX escrito)

### Regra A ? Nunca `align-items` em form-grids
`align-items: end/start` desalinha labels verticalmente. O padrao `stretch` (sem `align-items`) e o correto.

### Regra B ? Contar itens vs colunas ANTES de escrever o grid
`form-grid-2` com 3 itens -> errado (3 nao e multiplo de 2). Separar em linhas.

### Regra C ? Elemento unico em flex-column ja ocupa largura total (sem wrapper de grid).

### Regra D ? Comentarios em templates Angular: `<!-- -->` (nunca `{{-- --}}`).

---

## Checklist de verificacao pre-entrega

```
CONTRATO
[ ] Li o .js + .stories.js de cada dom-* novo usado (render()/lifecycle/eventos)

TABELA
[ ] dom-table recebe data por propriedade ? sem slot cells manuais
[ ] Filtros via filterable + header-type + (domFilterChange)
[ ] Estrutura: cadastro-bloco -> toolbar -> div.pad -> flow-table-wrap + paginacao

PARIDADE COM A TELA DE ORIGEM
[ ] Inventario de campos escrito antes do JSX (rotulo, dom-*, obrigatorio, default) e a contagem bate com o prototipo
[ ] Campos da mesma linha sao o mesmo dom-*; nenhum input nativo ao lado de dom-input-text
[ ] Um rotulo so (prop label). Nenhum <label> duplicado por fora
[ ] Layout com .form-grid-*, sem grid inline e sem align-items
[ ] Gap de DS (hora/data) parado em A/B/C, nao preenchido com nativo em silencio
[ ] Botao de criar/incluir em PageHeader actions (direita superior). Troca de visao e filtros ficam abaixo

CAMPOS
[ ] dom-input-select com show-support-info="false" (quando sem support-text)
[ ] Opcoes assincronas re-sincronizadas/remontadas
[ ] Formulario em dom-modal (nao dom-dialog)

BOTOES
[ ] Clique via onClick (React) / (click) (Angular) ? nenhum domClick
[ ] variant="primary/secondary/tertiary" ? nenhum [attr.type]
[ ] Icones validos do catalogo @onviobr/dom-icons

CSS
[ ] Classes globais de layout no stylesheet global, nao no CSS do componente
[ ] Nenhum form-grid com align-items

SMOKE TEST (runtime) ? antes de declarar pronto
[ ] App rodando, pagina renderizada, fluxo percorrido
[ ] INTERACAO por controle (renderizar != funcionar): cada botao clicado dispara efeito; cada input digitado persiste; cada select muda; modal fecha por X, Cancelar E acao primaria; acao de linha da tabela; paginacao Anterior/Proximo/Ir/Itens-por-pagina
[ ] Console sem erros/warns do DS (ex.: "[dom-input-select] Invalid usage...")
[ ] Nenhum campo/secao do DS renderizando vazio
[ ] Teclado no modal: Tab/Shift+Tab percorre os campos e NAO salta para o "X" (focus trap slotted)
[ ] ATENCAO: E2E com .fill() NAO exercita o Tab -> usar keyboard.press('Tab') para cobrir o focus trap
```

---

## Regra de ouro

> **Nenhuma pagina e declarada "pronta" sem (1) inventario de campos igual ao da tela de origem, (2) ter lido o contrato real dos componentes do DS, (3) um smoke test em runtime com console limpo e (4) INTERACAO verificada em cada controle (botao/input/select/modal/tabela/paginacao) - renderizar != funcionar. Teste de payload verde nao substitui o item (1).**
>
> Armadilhas de integracao React <-> Dom DS (modal sem handler, sync-once, jump width 0, checkbox oculto): ver react-dom-ds-playbook.md.
>
> Se a sessao ja leu o contrato dos componentes em uso, anotar: `> new-page-scaffold: contratos lidos em [mensagem anterior]` e seguir.
