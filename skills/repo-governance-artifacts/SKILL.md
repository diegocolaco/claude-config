---
name: repo-governance-artifacts
description: Use quando rules, skills ou agents de governança aparecerem sob repo/ ou em clones.
---
CTX-ID: repo-governance-artifacts@1

# Governança de agente — fora de `repo/`

## Regra (não negociável)

A pasta **`repo/`** do playground é só para **clones de aplicação** (código, SQL, config de produto, worktrees de entrega). **Não** é fonte de governança do ecossistema Jarbas.

### Proibido criar, mover ou editar como fonte

Qualquer path sob `repo/**/` que seja instrução persistente ao agente Cursor:

| Tipo | Padrões proibidos (fonte) |
|------|---------------------------|
| Rules | `repo/**/.cursor/rules/**` (`*.mdc`, `*.md`) |
| Skills (runtime Cursor) | `repo/**/.cursor/skills/**` (`SKILL.md`, pastas de skill) |
| Agents | `repo/**/.cursor/agents/**` |
| Commands | `repo/**/.cursor/commands/**` |

Inclui worktrees **dentro** de um clone (`repo/<nome>/.worktrees/**`, `$WORKTREES_ROOT` quando o git root está em `repo/`).

**Não** usar `repo/sgd-cursor-governance/.cursor/` como modelo para artefatos novos — é legado a migrar (ver abaixo).

### Permitido em `repo/` (não confundir)

| Path | O que é |
|------|---------|
| Código-fonte do produto | Java, TS, SQL, infra do repositório clonado |
| `repo/**/.agents/**` | Conhecimento de **branch** gerado por derivação (Layer 3), não skills do playground |
| `presets/` (fora de `repo/`) | Baseline de análise; promoção via automação, não cópia manual ad hoc em `repo/` |

Comportamento global do playground: `ecosystem/canonical/` → `jarbas.py materialize` → `.cursor/` na **raiz** do playground.

Comportamento por produto: `ecosystem/profiles/<profile_id>/rules/` e `.../skills/` (carregados quando o profile está ativo — rule `playground-profiles`).

## Onde colocar (destino)

```
Pedido de governança Cursor
        │
        ├─ Vale para TODO o playground jarbas?
        │     → ecosystem/canonical/rule/ ou canonical/skills/
        │     → materialize
        │
        └─ Vale só a um produto / stack (SGD, Onvio, QA, …)?
              → ecosystem/profiles/<profile_id>/rules/ ou .../skills/
              → ler profile.yaml (activation_triggers, repos)
```

Autoria detalhada: skill `jarbas-author-skills-rules`.

## Mapa repo → profile (migração)

O que **já existe** em `repo/` deve **sair** para o profile correspondente (mover + atualizar ponteiros; não duplicar em canonical e profile).

| Clone em `repo/` | Profile destino | Notas |
|------------------|-----------------|-------|
| `sgd-cursor-governance` | `sgd-legado` (`ecosystem/profiles/sgd-legado/cursor/`) | **Migrado** no playground (2026-10-09); remover `.cursor/` do clone git em PR separado |
| `ebs-dominio_sgd` | `sgd-novo` | Regras de entrega/paridade já vivem em `profiles/sgd-novo/` |
| Módulos legado (`ebs-dominio_suporte`, `_atendimento`, `_comandos`, `_servicos`) | `sgd-legado` | Governança de monólito, não nova pasta `.cursor` no módulo |
| Integrações / outros clones | Profile draft ou novo `profile_id` em `ecosystem/profiles/` | Definir em `profile.yaml` antes de criar rules |

## Procedimento do agente

1. **Antes de qualquer Write/edição de arquivo** sob `repo/**/.cursor/{rules,skills,agents,commands}/` → **parar**.
2. Classificar escopo (playground vs profile) com `jarbas-author-skills-rules`.
3. Criar ou mover o artefato para `ecosystem/canonical/` ou `ecosystem/profiles/<id>/`.
4. Se o pedido exigia alteração **no repositório git do clone** (ex.: PR em `sgd-cursor-governance`): planear migração para o profile + commit no **playground**; no clone só remover/espelhar após decisão humana de integração no repo externo.
5. Atualizar ponteiros (`profile.yaml`, `canonical_command`, docs) que ainda citam paths em `repo/.../.cursor/`.

## Bloqueio

```
[jarbas REPO-GOV BLOCKED] trace_id=<id> | path=<repo/.../.cursor/...> | motivo=governança proibida em repo/ | acao=ecosystem/canonical ou ecosystem/profiles/<profile_id> (skill repo-governance-artifacts)
```

Exceção **só** com citação explícita do humano na conversa para hotfix temporário no clone + registo de migração no plano da sessão.

## Referências

- `repo/README.md` (clones vs governança)
- jarbas.md — princípio conhecimento vs comportamento; camadas canonical/profile
- branch-agregado-playground.md
- Skill `jarbas-author-skills-rules` · rule `playground-profiles`
