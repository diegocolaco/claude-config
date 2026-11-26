#!/usr/bin/env bash
# Monta um ~/projetos simulado em ./projetos: playground com remoto e worktrees em vários estados.
set -eu
B="$PWD/projetos"
R="$PWD/remote.git"
P="$B/TaxProf_brtap-integration-playground"
W="$B/worktrees"
mkdir -p "$P" "$W" "$B/.tmp" "$B/repo"
git init -q --bare -b main "$R"
git -C "$P" init -q -b main
git -C "$P" config user.email teste@exemplo
git -C "$P" config user.name teste
echo "playground" > "$P/README.md"
git -C "$P" add . && git -C "$P" commit -qm init
git -C "$P" remote add origin "$R"
git -C "$P" push -q -u origin main
add() { git -C "$P" worktree add -q -b "feat/$1" "$2/$1" main; }
publish() { git -C "$1" push -q origin "$(git -C "$1" branch --show-current)"; }
add pronto "$W"; publish "$W/pronto"
add rascunho "$W"; echo "notas importantes" > "$W/rascunho/notas.md"
add experimento "$W"; echo "x" > "$W/experimento/x.txt"
git -C "$W/experimento" add . && git -C "$W/experimento" commit -qm "experimento local"
add dentro "$P/.worktrees"; publish "$P/.worktrees/dentro"
add sessao-antiga "$P/.claude/worktrees"; publish "$P/.claude/worktrees/sessao-antiga"
add sumiu "$W"; rm -r "$W/sumiu"
mkdir -p "$W/sobra/src" && echo "print('codigo')" > "$W/sobra/src/main.py"
