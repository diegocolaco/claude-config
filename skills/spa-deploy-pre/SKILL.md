---
name: spa-deploy-pre
description: Use quando o diff tocar apps/web do SGD novo, antes de merge ou PR, para
  o pré-deploy da SPA.
---
CTX-ID: spa-deploy-pre@1

# Gate SPA-DEPLOY-PRE — build do Deploy Web antes de merge (SGD novo)

**Projeto:** TR Jarbas Ai Multi-agents squad · profile `sgd-novo`

Vitest e Playwright/paridade-dual **não** rodam `tsc --noEmit`; o build da SPA roda (`pnpm --filter @sgd/web run build` = `tsc --noEmit && vite build`) (deploy remoto não verificado: não há workflow de CI no repositório). Incidente: PR #280 com `disabled="true"` passou nos testes locais e quebrou o CI (TS2322); fix no PR #282.

Quando o diff toca `apps/web/**` (ou dependência da SPA: `packages/**` usado pelo web, lockfile, `tsconfig*`, `vite.config.*`), **antes de pedir merge, abrir/atualizar PR ou encerrar o ITEM**:

1. Carregar **spa-deploy-pre.md** (gatilhos, atalho `tsc -b`, evidência).
2. No **worktree do ITEM**, executar **`pnpm --filter @sgd/web run build`** (depois do último commit e após cada sync com a base).
3. O **`task-reviewer`** registra `spa-build: PASS|FAIL|N/A` no relatório de verificação (`jarbas.py check`); `FAIL` bloqueia REVIEW, PR e merge.

```text
[jarbas SPA-DEPLOY-GATE BLOCKED] trace_id=<id> | motivo=<build da SPA ausente ou falhou> | acao=pnpm --filter @sgd/web run build
```
