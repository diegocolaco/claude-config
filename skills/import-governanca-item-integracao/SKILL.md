---
name: import-governanca-item-integracao
description: Use quando reimportar propostas do modelo externo sobre integração de ITEM para ficheiros fonte do playground.
disable-model-invocation: true
---
CTX-ID: import-governanca-item-integracao@2

# Import — propostas do export de integração de ITEM

**Projeto:** TR Jarbas Ai Multi-agents squad.

O export anonimizado **não** é fonte canónica: tokens `«…-OMITIDO/A»`, caminhos pseudonimizados e blocos
`[SEGURANÇA: …]` **nunca** são copiados para o repo. Sempre editar o **ficheiro fonte** indicado em cada anexo.

Par export: skill **`export-governanca-item-integracao`**.

## Quando usar

- O Diego (ou um modelo externo) devolveu sugestões de melhoria ao processo ITEM / harness / paridade.
- Há um `.md` de propostas, comentários por anexo ou diff conceptual sobre o pacote v3.

## Entrada esperada

| Tipo | Onde guardar |
|---|---|
| Propostas do modelo externo | AAAA-MM-DD-propostas.md |
| Export usado na ida (referência) | export-governanca-superpowers-jarbas-prototipo-item.md (commit ou data no nome das propostas) |

Criar a pasta `import-governanca-item-integracao/` na primeira importação.

## Procedimento

### 1. Segurança e escopo

1. Se as propostas trouxerem dados sensíveis reconstituídos, **parar** — não gravar no repo; skill `documentar-seguranca-gate`.
2. Classificar cada item: **processo** (skill/rule/doc), **automação** (`jarbas.py` / export), **produto SGD** (`repo/`) — só o primeiro e segundo são escopo habitual desta skill.

### 2. Triage (obrigatório antes de editar)

Montar tabela no chat ou no ficheiro de propostas:

| # | Proposta (resumo) | Anexo / secção | **Fonte** (path real no repo) | Tipo de edição |
|---|-------------------|----------------|-------------------------------|----------------|
| 1 | … | Anexo 7 | lovable-proto.md | profile rule |

**Resolver path real:**

1. Preferir a linha **`**Fonte:** \`path\``** de cada anexo no export **interno** (`--no-anonymize`) ou no repo, não no texto anonimizado partilhado.
2. Se só existir o export anonimizado, usar o índice da secção 0 + `build_item_integration_export.py` (SSOT dos anexos).
3. Mapear anexo → path conforme `references/manifest-anexos.md` nesta skill.

### 3. Aprovação

- Mudança que altera gates, ordem harness ou regra de negócio → **apresentar ao Diego** antes do **developer** implementar.
- Mudança só em redação/clareza do processo → pode seguir com diff pequeno, ainda assim listar ficheiros tocados.

### 4. Implementação (developer, worktree)

| Destino no repo | Editar | Depois |
|-----------------|--------|--------|
| Skill/rule playground | `ecosystem/canonical/...` (content.md + `meta.yaml`) | `python3 ecosystem/automation/jarbas.py materialize --target all` |
| Skill/rule profile `sgd-novo` | `ecosystem/profiles/sgd-novo/skills/` ou `rules/` | Sem materialize (profile sob demanda) |
| Comando Cursor | Fonte canónica se existir; senão só após confirmar com `jarbas-author-skills-rules` | `materialize` se aplicável |
| Flow / automação export | `ecosystem/automation/governance_export/`, governance-export.md | `platform-check`, testes de `tests/test_governance_export*.py` se mexeu no anonimizador |
| Processo documentado | `user-doc/novo-sgd/fluxograma-processos/`, `docs/execucao/regras/` | — |

**Proibido:** colocar governança nova em `repo/**/.cursor/`.

### 5. Pós-import

1. Se mudou o **processo de ITEM** → skill `item-process-changelog` + doc-sgd-novo-processo-item-historico.md quando aplicável.
2. Regenerar export: skill **`export-governanca-item-integracao`** (Procedimento A).
3. Commit worktree + merge agregado (`playground-commit-workflow`).

## Erros comuns

| Erro | Correção |
|---|---|
| Colar texto com `«EMPRESA-OMITIDA»` no fonte | Reescrever em linguagem neutra ou termo interno aprovado |
| Editar só `ecosystem/canonical/skills/` | Fonte é `ecosystem/canonical/` |
| Ignorar `materialize` após canonical | Diff em `.cursor/` desactualizado |
| Aplicar sugestão de produto sem ITEM/worktree SGD | Escalar para entrega governada `governed-numbered-item-delivery` |

## Referências

- `references/manifest-anexos.md` — mapa anexo → path (alinhado ao builder v3).
- governance-export.md.
