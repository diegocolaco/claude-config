# Formato de skill e rule canonical

Leia ao criar ou editar `meta.yaml`/content.md de uma skill ou rule em `ecosystem/canonical/`.

## Formato — Skill no playground (canonical)

### Layout

```
ecosystem/canonical/skills/<skill-id>/
├── meta.yaml      # metadados + targets.cursor.directory
└── content.md     # corpo INTEIRO do SKILL.md (inclui frontmatter YAML)
```

O materializer grava content.md → `.agents/skills/<directory>/SKILL.md`, fundindo `name`/`description` de `meta.yaml` quando o frontmatter YAML falta no content.md (corpo preservado). Ficheiros e pastas extra da pasta da skill (ex.: `references/`, `ecosystem/canonical/skills/governed-items-portfolio-analysis/reference.md`) são copiados tal como estão para `ecosystem/canonical/skills/<directory>/`; só `meta.yaml` e content.md ficam de fora (um SKILL.md na fonte é ignorado, symlinks são recusados, e ficheiros apagados na fonte desaparecem da saída). Usar `references/` para procedimentos longos lidos sob demanda; **não** encurtar o corpo só para meta de palavras.

### `meta.yaml` (skill)

```yaml
id: <skill-id>                    # kebab-case, estável
type: skill
enabled: true                     # false = materializa com overlay desativado (corpo preservado; não invoca)
scope: agent-requestable          # ou conforme política do ecossistema
description: >-
  Terceira pessoa; só gatilhos (SDO Superpowers). O WHAT fica no corpo (Overview / Quando usar).
targets:
  cursor:
    directory: <skill-id>         # pasta em ecosystem/canonical/skills/
```

### content.md (skill) — frontmatter Cursor

```markdown
---
name: <skill-id>                  # max 64 chars; lowercase e hífens
description: >-
  Mesma intenção do meta.yaml; incluir gatilhos ("Use quando…").
---

# Título

## Quando usar
…

## Procedimento
…

```

### Boas práticas (skills)

- `description` em **terceira pessoa**, alinhada ao SDO do Superpowers `writing-skills`: **só WHEN** (sintomas, contexto, termos de busca; começar por `Use when` / `Use quando` / `Use para`); **sem** resumo de workflow na description. O **WHAT** vive no corpo (`## Quando usar`, Overview).
- Orientação de token (~500 **palavras** na description ou corpo curto) **não** autoriza apagar conteúdo procedural; corpo longo pode usar `references/` numa entrega dedicada.
- Corpo focado; ideal **&lt; 500 linhas** em content.md (linhas, não palavras).
- Um workflow por skill; templates e checklists são bem-vindos.
- Nome do diretório = id estável; evitar `helper`, `utils`.
- Encoding **UTF-8** (acentos). Após gravar, verificar ausência de U+FFFD (ver automation-governance.mdc, referência Jarbas não importada).
- Se a skill **sobrepõe** desenho, plano, execução, bug, verificação ou worktree do Superpowers: incluir secção **«Composição Superpowers»** com `REQUIRED BACKGROUND` / `REQUIRED SUB-SKILL` (`superpowers:<nome>`, sem `@`). Tabela de referência: jarbas-superpowers-fronteira.md § Cross-references.

### Exemplos no repositório

| Skill | Caminho canonical |
|-------|-------------------|
| SDD gate | `ecosystem/canonical/skills/sdd-gate/` |
| Nova página Dom DS | `ecosystem/canonical/skills/new-page-scaffold/` |
| Governança fora de `repo/` | `ecosystem/canonical/skills/repo-governance-artifacts/` |

---

## Formato — Rule no playground (canonical)

### Layout

```
ecosystem/canonical/rule/<rule-id>/
├── meta.yaml
└── content.md     # corpo da rule SEM frontmatter MDC (o materializer gera)
```

### `meta.yaml` (rule)

```yaml
id: <rule-id>
type: rule
description: "Texto curto de uma linha"
activation: always | files         # opcional: sem ele, globs presentes => files; ausentes => always
globs: ["apps/**/*.tsx"]           # lista; obrigatória com files, proibida com always
globs_allow_empty: false           # true só com globs_allow_empty_reason (texto não vazio)
targets:
  cursor:
    include: false                 # única opção aceita por destino (booleana)
```

O materializador gera o frontmatter de `.claude/rules/<id>.md` e de `.cursor/rules/<id>.mdc` a partir desses campos. `alwaysApply` no `meta.yaml` de uma rule ativa é recusado (`INVALID_METADATA`), e `targets.<destino>` aceita só `include`; `filename` e `globs` por destino não existem. Cada glob precisa casar algum ficheiro, senão `GLOB_NO_MATCH`; use `globs_allow_empty: true` com `globs_allow_empty_reason` só quando um glob sem ficheiros é intencional. Um recurso de rule que termine em `.md` é recusado para Claude Code (`RULE_RESOURCE_MARKDOWN`): o Claude o carregaria como rule. A `description` não aceita U+0085, U+2028 nem U+2029. Links relativos do corpo são reescritos, exceto em código, em alvos `scheme:` e em alvos `<...>`.

Skills usam `invocation: auto | manual` no `meta.yaml` (default `auto`). Agentes (`type: agent`) usam o bloco `agent:` com `models` (`claude-code`, `cursor`, `codex`), `effort` (`low|medium|high|xhigh|max`), `readonly` (booleano) e `tools` (lista não vazia); chaves desconhecidas são recusadas.

### content.md (rule)

Markdown puro (títulos, listas, exemplos de código). **Não** incluir `---` de frontmatter no content.md — o script `materialize.py` monta o `.mdc`.

### Rule com globs (ficheiros específicos)

No `meta.yaml`, preferir lista:

```yaml
activation: files
globs:
  - "apps/**/*.tsx"
  - "apps/**/*.ts"
```
