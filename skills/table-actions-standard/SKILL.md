---
name: table-actions-standard
description: Use quando criar ou alterar dom-table com registros editáveis ou excluíveis,
  para o padrão da coluna de ações.
---
CTX-ID: table-actions-standard@1

# Padrao de Coluna de Acoes ? dom-table (Dom DS)

## Regra

Toda `dom-table` com registros editaveis/excluiveis deve ter a coluna de acoes seguindo este padrao. **Nunca** deixar a coluna sem label adequado ou com tamanho errado. Aplica-se a apps Angular e React/Vite que consomem o Dom DS.

---

## Padrao 2 acoes (Editar + Excluir)

| Campo | Valor |
|-------|-------|
| field | `_acoes` |
| label | `Acoes` |
| width | `100px` |
| action-items | `2` |
| botoes | `edit-outline` (index 0) + `trash-outline` (index 1) |

**Angular:**
```html
<dom-table-column field="_acoes" label="Acoes" cell-type="action"
  [attr.width]="'100px'" [attr.action-items]="'2'">
  <dom-tooltip [attr.label]="'Editar'" [attr.orientation]="'top'">
    <dom-button-icon icon="edit-outline" label="Editar" [attr.size]="'sm'"></dom-button-icon>
  </dom-tooltip>
  <dom-tooltip [attr.label]="'Excluir'" [attr.orientation]="'top'">
    <dom-button-icon icon="trash-outline" label="Excluir" [attr.size]="'sm'"></dom-button-icon>
  </dom-tooltip>
</dom-table-column>
```

**React (atributos diretos; `data` da tabela setado por propriedade via ref):**
```tsx
<dom-table-column field="_acoes" label="Acoes" cell-type="action" width="100px" action-items="2">
  <dom-tooltip label="Editar" orientation="top">
    <dom-button-icon icon="edit-outline" label="Editar" size="sm" />
  </dom-tooltip>
  <dom-tooltip label="Excluir" orientation="top">
    <dom-button-icon icon="trash-outline" label="Excluir" size="sm" />
  </dom-tooltip>
</dom-table-column>
```

**Quando usar:** cadastros e movimentacoes que permitem edicao e exclusao.

---

## Padrao 1 acao (apenas Excluir)

| Campo | Valor |
|-------|-------|
| field | `_acoes` |
| label | `""` (vazio) |
| width | `60px` |
| action-items | `1` |
| botoes | `trash-outline` (index 0) |

**Quando usar:** sub-tabelas ou listas onde a edicao nao se aplica.

---

## Tratamento do evento (`domCellAction`)

O `dom-table` emite `domCellAction` com `{ field, rowIndex, actionIndex, data }`.

**React:**
```ts
function onCellAction(detail: { field: string; actionIndex: number; data: Row }) {
  if (detail.field !== '_acoes') return
  if (detail.actionIndex === 0) abrirEditar(detail.data)        // Editar = index 0
  else if (detail.actionIndex === 1) confirmarExclusao(detail.data) // Excluir = index 1
}
```

**Angular:**
```ts
protected onCell(ev: Event) {
  const e = ev as CustomEvent<{ field?: string; actionIndex?: number; data: Row }>
  if (e.detail?.field !== '_acoes') return
  if (e.detail.actionIndex === 0) this.abrirEditar(e.detail.data)
  else if (e.detail.actionIndex === 1) this.confirmItem.set(e.detail.data)
}
```

**Importante:** quando ha apenas 1 acao (Excluir), o `actionIndex` e `0`, nao `1`.

---

## Confirmacao de exclusao

Confirmacao e **texto puro** -> `dom-dialog` e adequado (ele so renderiza texto via `description`).
Para qualquer dialogo com **formulario/conteudo**, usar `dom-modal` (corpo via slot), nunca `dom-dialog`.

```html
<dom-dialog
  [attr.open]="'true'"
  heading="Confirmar exclusao"
  [attr.description]="'Deseja excluir ' + (item?.descricao ?? 'este item') + '? Esta acao nao pode ser desfeita.'"
  primary-button-label="Excluir"
  secondary-button-label="Cancelar"
  icon-name="trash-outline"
  (domDialogPrimaryAction)="confirmarDelete()"
  (domDialogSecondaryAction)="cancelar()"
  (domDialogClose)="cancelar()">
</dom-dialog>
```

---

## Erros comuns

```
ERRADO: label vazio com 2 acoes
ERRADO: width 60px para 2 acoes (use 100px)
ERRADO: acoes sem dom-tooltip
ERRADO: icone fora do catalogo @onviobr/dom-icons (botao fica invisivel)
ERRADO: domClick em dom-button-icon (usar onClick/(click) ou o evento domCellAction da tabela)
```
