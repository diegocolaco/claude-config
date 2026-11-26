---
description: Ao criar ou alterar task executável de desenvolvimento (.vscode/tasks.json),
  exige validar a execução real e nunca declarar sucesso sem evidência.
paths:
- '**/.vscode/tasks.json'
---

CTX-ID: task-reliability@1

# Task Reliability Gate

When creating or modifying an executable development task:

1. Never consider the task complete based only on static inspection.
2. Discover and verify the real command, runtime, cwd, environment and dependencies before changing the task.
3. After modification, validate syntax and execute the resulting behavior.
4. Verify the task reaches its intended final state, not merely that the process starts.
5. For background services, verify readiness and lifecycle/cleanup.
6. For compound tasks, verify dependency order and readiness between steps.
7. Preserve unrelated configuration, encoding and line endings.
8. Never report SUCCESS without execution evidence.

If execution cannot be performed, report the task as UNVERIFIED, explain the blocker, and do not claim completion.

After creating or materially modifying a task, use the task-verifier subagent.

Não há hook instalado para isso; rode o `task-verifier` manualmente.
