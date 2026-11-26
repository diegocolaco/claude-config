# Novo agente funcional e subagentes

Leia ao criar um agente (rule + registry) ou um subagente em `ecosystem/canonical/agents/subagents/`.

## Novo agente funcional (rule + registry)

Só para **agentes** do ecossistema (não para cada skill):

1. `ecosystem/canonical/rule/<agent-slug>/` — content.md com papel, limites, readonly se aplicável.
2. `meta.yaml` — `type: rule`, `activation: files` com `globs`, ou `always` (sem `globs`) para a sessão principal.
3. `ecosystem/canonical/agents/registry.yaml` — entrada `id`, `name`, `rule`, `layer`, `subagent_type`.
4. `ecosystem/canonical/agents/routing-rules.yaml` — roteamento jarbas.
5. Atualizar classificação em content.md (tabela de routing).
6. `jarbas.py materialize` + documentação em jarbas.md / `AGENTS.md` se agente novo.

### Subagentes Cursor (`ecosystem/canonical/agents/subagents/`)

Dois casos, conforme quem delega:

| Caso | Registo | Exemplo |
|------|---------|---------|
| O jarbas roteia o subagente (gate de pipeline) | Entrada em `registry.yaml` com `subagent_file: subagents/<name>.md`, sinais em `routing-rules.yaml` e linha na tabela de subagentes do orchestrator (coluna `subagent_type` = `<name>` (readonly; `ecosystem/canonical/agents/library/`)) | `dual-adapter-reviewer` |
| Só o Agent Cursor delega (verificação isolada) | Fora do `registry.yaml` e da tabela do orchestrator; o Agent escolhe pela `description` do `.md` | `task-verifier` |

Para workflows do segundo caso, como **Task Quality Gate** (`task-engineer` + `task-verifier`):

| Artefato | Fonte jarbas | Saída |
|----------|--------------|--------|
| Rule com globs | `ecosystem/canonical/rule/task-reliability/` | `ecosystem/canonical/rule/task-reliability/content.md` |
| Skill | `ecosystem/canonical/skills/task-engineer/` | `ecosystem/canonical/skills/task-engineer/content.md` |
| Subagent Cursor | `ecosystem/canonical/agents/subagents/<name>.md` | `ecosystem/canonical/agents/library/<name>.md` (copiado no materialize) |

Neste caso **não** registar em `registry.yaml` nem na tabela do orchestrator: o jarbas não roteia estes subagentes.

Referência espelhada (sem jarbas): repositório `sgd-cursor-governance` em `ecosystem/canonical/rule/`, `ecosystem/canonical/skills/`, `ecosystem/canonical/agents/library/`.
