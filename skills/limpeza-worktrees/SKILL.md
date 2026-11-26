---
name: limpeza-worktrees
description: "Use para limpar ou remover worktrees git em ~/projetos (velhos, mergeados, órfãos, de sessões fechadas ou ocupando disco), ao encerrar tarefa feita em worktree e ao achar worktree dentro do playground. Remove o seguro sem perguntar e põe o duvidoso na quarentena ~/projetos/.tmp. Não use para branches, stash, node_modules ou git clean."
---

# Limpeza de worktrees

Regra do usuário: **nenhum worktree dentro de `~/projetos/TaxProf_brtap-integration-playground`** (nem `.worktrees/`, nem `.claude/worktrees/`) e nenhum sobrando no workspace. A autorização é permanente: o seguro sai **sem perguntar**; o duvidoso vai para a quarentena `~/projetos/.tmp` (Windows: `\\wsl.localhost\Ubuntu\home\diego\projetos\.tmp`), nunca é apagado.

Worktree novo nasce em `~/projetos/worktrees/<nome>`; no Claude Code o hook `WorktreeCreate` já faz isso. Se aparecer um dentro do playground mesmo assim, avise o usuário.

## Como limpar

Script: `scripts/worktree_cleanup.py`, ao lado deste arquivo. Rode com o cwd **fora** dos worktrees que vão sair. Escolha o alcance pelo pedido:

- **Limpeza geral**, só quando pedirem limpeza, remoção ou disco: `python3 <skill>/scripts/worktree_cleanup.py apply --format resumo`.
- **Fim de tarefa**: só o worktree dela, `apply --only <caminho> --format resumo`; nunca sem `--only`. O da sessão atual fica em uso; ele sai pelo `WorktreeRemove` ao fechar a sessão.

Não peça confirmação. Para ver antes sem mexer, use `plan` no lugar de `apply`. No relatório, mostre os totais, o que foi para a quarentena e por quê, o que segue em uso dentro do playground e qualquer erro, com a mensagem real. Para veredictos, quarentena e restauração: `worktree_cleanup.py --help`.

## Nunca

- `rm -rf`, `git worktree remove --force`, `git reset`, `git clean` ou `git stash drop`: são as perdas que a quarentena evita.
- Apagar branch, ou qualquer coisa na quarentena, sem pedido explícito.
- Mexer em worktree `IN_USE` (processo dentro ou lock de sessão viva).

`@platform: linux-only` (WSL incluso): a detecção de uso lê `/proc`.
