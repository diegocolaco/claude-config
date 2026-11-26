---
name: jarbas-author-skills-rules
description: Use quando criar, editar ou mover o arquivo de uma skill, rule ou agent em ecosystem/canonical ou profiles.
---
CTX-ID: jarbas-author-skills-rules@3

# Autoria de skills e rules — TR Jarbas Ai Multi-agents squad

Guia jarbas de **onde** e **em que formato** gravar; **como** escrever e testar a skill é o método do Superpowers. **REQUIRED SUB-SKILL:** `superpowers:writing-skills` ao criar ou editar skill (cross-references, descrição de descoberta); para autoria e avaliação o processo principal é o Creator (`ecosystem/docs/creator-led-skill-authoring.md`).

## Regras que valem sempre

- A fonte vive só em `ecosystem/canonical/` (playground) ou `ecosystem/profiles/<profile_id>/` (um produto).
- **Nunca** editar `.claude/rules/`, `.cursor/rules/`, `.agents/skills/` ou `.claude/skills/` como fonte: são saída de `python3 ecosystem/automation/materialize/materialize.py` (ou `jarbas.py materialize`) e serão sobrescritas.
- **Proibido** usar `repo/**/.cursor/{rules,skills,agents,commands}/` como fonte de governança; skill `repo-governance-artifacts` (migrar para canonical ou profile).
- Uma fonte por skill: consulte o catálogo e as skills canônicas antes de criar.
- Texto **verbatim** do usuário na skill/rule: copiar sem parafrasear.
- UTF-8; após gravar, conferir ausência de U+FFFD.

## Passo 0 — Classificar o pedido

Path sob `repo/` com rules/skills/agents/commands? Pare e use `repo-governance-artifacts`.

| Escolher **canonical** (playground) | Escolher **profile** |
|---|---|
| Gates jarbas (TEST, DBA, traceId, SDD), agentes funcionais, automação, RAG, materialize | Stack, domínio ou repo de **um** produto; `activation_triggers` do `profile.yaml` |
| Skill usada em qualquer repo em `repo/` | Regras que não devem poluir outros perfis (entregas.md, mapa de tabelas) |

Destinos: skill canonical em `ecosystem/canonical/skills/<id>/`; rule canonical em `ecosystem/canonical/rule/<id>/`; skill de profile em `ecosystem/profiles/<id>/skills/<dir>/SKILL.md`; rule de profile em `ecosystem/profiles/<id>/rules/*.md`. SGD novo: rule `playground-profiles` (roteamento) + conteúdo em `ecosystem/profiles/sgd-novo/rules/*.md`. Skills pessoais em `~/.cursor/skills/` só se o usuário pedir, sem materializar.

## Passo 1 — Clarify mínimo

Se o pedido não fixar, pergunte **uma rodada** (ou infira do chat): (1) tipo, skill ou rule; (2) escopo, playground ou qual `profile_id`; (3) gatilho (`description` ou `activation_triggers`); (4) `activation` da rule, `always` ou `files` com `globs`; (5) quais globs; (6) é agente funcional novo?

## Formato essencial

- **Skill canonical:** `meta.yaml` (`id`, `type: skill`, `description` em terceira pessoa só com gatilhos «Use quando…», sem resumo de workflow) + content.md (frontmatter `name`/`description` + corpo) + `references/`, `evals/` quando necessários. Corpo focado, abaixo de 500 linhas; detalhes longos em `references/`.
- **Rule canonical:** `meta.yaml` (`id`, `type: rule`, `description`, `activation: always|files`, `globs` obrigatório com `files` e proibido com `always`) + content.md **sem** frontmatter (o materializador gera `.claude/rules/<id>.md` e `.cursor/rules/<id>.mdc`). Cada glob precisa casar algum arquivo (`GLOB_NO_MATCH`).
- **Profile:** SKILL.md com frontmatter e rules em `.md` (não `.mdc`); **não** rodar materialize para publicá-los.
- **Agente funcional novo:** rule canonical + `registry.yaml` + `routing-rules.yaml` + tabela do orchestrator.

Leia `references/formato-skill-rule.md` ao escrever `meta.yaml`/content.md (campos, erros do materializador, boas práticas, exemplos); `references/profiles.md` para artefato de profile; `references/agentes.md` para agente ou subagente.

## Fluxo ao criar ou editar

1. Localizar a fonte (`rg` em `ecosystem/canonical` e `ecosystem/profiles`); se só existir em `.cursor/`, migrar antes de editar.
2. Criar/editar a fonte e rodar `python3 ecosystem/automation/materialize/materialize.py` (canonical; `--target all` pelo `jarbas.py materialize`).
3. Revisar o diff de `.cursor/` e `.claude/`: só a saída esperada; validar só no `.cursor/`.
4. Renomeou, moveu ou apagou: atualizar as referências no mesmo commit (`rg` pelo nome antigo).
5. Commit com fontes, saídas geradas e `.squad/skill-materialization.json` juntos; avaliações em `evals/`, resultados em `tests/skill-authoring/<nome>-workspace/`, temporários em `.cache/skill-authoring/<nome>/`.
6. Tipo ou local novo de objeto: cobrir em `ecosystem/shared/governance-export.yaml`.

Leia `references/workflow-e-governanca.md` para os checklists completos e o governance-export; `references/localizacao-e-fonte-unica.md` para a política de localização e conferência final.

## Erros comuns

Editar SKILL.md/saída direto; skill de produto em canonical; rule `always` para contexto de um repo (use profile ou `files` com globs); frontmatter `---` no content.md de rule; criar `.md` com `echo`/`sed`. Leia `references/anti-padroes-promocao-templates.md` para a tabela completa, os flows de promoção (`promote-skill`, `promote-knowledge`, `promote-behavior`) e os templates de nova skill/rule.

Pedido de «skill no Cursor» sem contexto jarbas: aplicar este guia; no playground o destino continua canonical, nunca `.cursor/` nem `~/.cursor/skills-cursor/`.
