---
name: auxilio-testes-pr-sgd
description: Use quando abrir ou atualizar PR do SGD novo, git-env publish/pr-create, ou pedir auxílio de testes por PR (profile sgd-novo).
disable-model-invocation: true
---
CTX-ID: auxilio-testes-pr-sgd@3

# Auxílio de testes por PR — SGD novo

## Composição Superpowers

Passo jarbas do fecho de branch com PR.

**REQUIRED SUB-SKILL:** Use `superpowers:finishing-a-development-branch` — este auxílio é gerado quando a opção escolhida inclui PR; não substitui o menu oficial.

**Projeto:** TR Jarbas Ai Multi-agents squad · profile `sgd-novo`

## Obrigatoriedade (não opcional)

Sempre que existir ou for criada uma PR do **`tr/ebs-dominio_sgd`** no fluxo de entrega (ITEM, bugfix, `git-env publish`, `pr-create`, `gh pr create`):

1. **Antes** de `pr_aberta` / encerrar entrega → gerar o ficheiro de auxílio.
2. Rule **`pr-auxilio-testes-obrigatorio`** (materializada em Cursor e Claude Code).
3. Ordem: **`pr-descricao-detalhada-sgd`** (descrição no GitHub) **depois** esta skill (roteiro manual).

Pedidos explícitos do Diego (verbatim):

1. «Gere auxilio de testes para o PR X Y Z»
2. «Gere auxilio de testes para os PRs em que ainda não pedi para gerar arquivo de teste»
3. «Gere auxilio de testes para os 3 ultimos PR do branch develop»

## Artefato e pastas

| O quê | Caminho (raiz = playground) |
|-------|-----------------------------|
| **Roteiro** | `user-doc/novo-sgd/auxilio-testes-pr/pr-<numero>-item-<codigo>.md` |
| Sem ITEM | `user-doc/novo-sgd/auxilio-testes-pr/pr-<numero>-sem-item.md` |
| **Índice** | `user-doc/novo-sgd/auxilio-testes-pr/registro.yaml` |
| Documentação | README.md |

Template: auxilio-testes-pr-template.md

Opcional: link na ficha `items/<codigo>/item-<codigo>.md` (secção Evidências ou Metadados) apontando ao ficheiro em `user-doc/`.

**Não** substitui MATRIZ-EVIDENCIAS.md nem relatório de verificação (`jarbas.py check`). **Não** criar spec Playwright nova (AP-10).

## Pré-requisitos

- Profile `sgd-novo` activo; em Claude Code, activar profile de produto em paralelo (`jarbas-claude-code`).
- GitHub: `python3 ecosystem/automation/jarbas.py git-env check` ou `git_auth.ensure_gh_token_for_cli()`.

## Fluxo por PR

### 1. Resolver lista de PRs

```bash
gh pr view N --repo tr/ebs-dominio_sgd --json number,title,headRefName,baseRefName,body,url
gh pr list --repo tr/ebs-dominio_sgd --base <integration_target do lote> --state open --limit 50 --json number
gh pr list --repo tr/ebs-dominio_sgd --base <integration_target do lote> --state merged --limit 3 --json number,mergedAt
```

«Sem arquivo ainda»: PRs abertas para esse mesmo `integration_target` cujo `number` **não** está em `registro.yaml` → `entries[].pr`.

### 2. Mapear PR → ITEM

Branch `feature/item-*` / `bugfix/item-*`, título/corpo, ou ficha governance.

### 3. Contexto

Ficha ITEM, MATRIZ-EVIDENCIAS.md, `gh pr diff`, corpo da PR (se genérico → `pr-descricao-detalhada-sgd` primeiro).

### 4. Redigir

Objetivo, ambiente (DEV vs slot), roteiro por menu (espelhar `## Descrição para PR`), tabela CA → passo, specs E2E/unit tocados, fora de escopo.

### 5. Persistir (playground — worktree)

1. Write UTF-8 no path `user-doc/novo-sgd/auxilio-testes-pr/…`
2. Actualizar `registro.yaml` (`pr`, `repo`, `item`, `path`, `generated`, `trace_id`)
3. Commit no **worktree** do playground; merge agregado (`playground-commit-required`)

## Checklist

- [ ] Cada tela da PR tem passo manual reproduzível
- [ ] CA da ficha mapeados ou N/A justificado
- [ ] PII mascarada
- [ ] `registro.yaml` actualizado

## Bloqueio

```
[jarbas PR-AUXILIO-TESTES BLOCKED] trace_id=<id> | pr=<n> | acao=gerar user-doc/novo-sgd/auxilio-testes-pr/pr-<n>-item-<codigo>.md
```
