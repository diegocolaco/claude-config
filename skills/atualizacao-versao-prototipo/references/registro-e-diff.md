# Registro da candidata e diff

## Registrar a candidata

Os comandos abaixo estão completos; não é preciso `--help`.

1. Crie um worktree do protótipo no commit novo, com branch própria.
2. Confira:
   - `git -C <worktree> rev-parse --show-toplevel` é diferente do checkout principal e de worktree de outra tarefa;
   - `git -C <worktree> rev-parse HEAD` é diferente da versão vigente (sem vigente, na primeira sincronização, não se aplica).
3. `python3 ecosystem/automation/jarbas.py reference register-version --project-root <worktree> --kind public-repository --dry-run --overwrite`. Sem `--overwrite`, até o dry-run falha (`ARTIFACT_CONFLICT`), porque `reference-version.json` é versionado.
4. Registro real: mesmo comando sem `--dry-run`. Ele grava o descritor e `.squad/artifacts/operations/<uuid>.json`. Commite os dois nesse worktree e use esse commit como `reference.version`.
5. `jarbas.py reference inspect --project-root <worktree>` devolve `checkout_commit` e `fingerprint`: no catálogo, `reference.version` = `checkout_commit`; `reference.digest` = fingerprint.

Na adoção, o Diego faz também o merge dessa branch no ramo principal do protótipo; até lá, a ancestralidade da versão seguinte falha.

O commit da versão precisa refletir arquivos removidos: extraia o zip numa pasta limpa (ou apague a árvore antes de copiar) para que o arquivo que saiu do protótipo apareça como `D` no diff e como trecho no mapa.

## Diff

- `git -C <prototipo> log --first-parent --oneline <vigente>..<candidata>`; sem vigente, `git -C <prototipo> log --first-parent --oneline <candidata>`
- `git -C <prototipo> diff --stat <vigente> <candidata>` e `--name-status`; leia por área, não o patch inteiro de uma vez.
- `commit_sha` (upstream) vai à parte no relatório. Igual dos dois lados com checkout diferente é mudança local, não «nada mudou».

Relatório: identidade dos dois lados (checkout, `commit_sha`, fingerprint), áreas tocadas e lidas, o que não foi examinado, inconsistências.
