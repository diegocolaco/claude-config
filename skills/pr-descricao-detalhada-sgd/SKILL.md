---
name: pr-descricao-detalhada-sgd
description: Use quando o PR do SGD novo precisar de corpo legível (Menu Comercial, Corrigido/Removido) na ficha ou no gh.
---
CTX-ID: pr-descricao-detalhada-sgd@3

# Descrição detalhada de PR — SGD novo (obrigatória)

## Composição Superpowers

Passo jarbas do fecho de branch com PR.

**REQUIRED SUB-SKILL:** Use `superpowers:finishing-a-development-branch` — a descrição detalhada entra quando a opção escolhida inclui PR.

**Projeto:** TR Jarbas Ai Multi-agents squad · profile `sgd-novo` · **Cursor + Claude Code** (skill materializada).

## Quando usar (gatilhos)

- Antes de `git-env publish` / `pr-create` / primeira abertura da PR.
- PR já aberta com corpo genérico ou só mensagens de commit.
- Frases do utilizador: «coloque a descrição no padrão», «descrição detalhada da PR», «atualizar corpo da PR #…».

## Contrato — não declarar PR pronta sem isto

1. Ficha `repo/sgd-cursor-governance/items/<codigo>/item-<codigo>.md` com secção **`## Descrição para PR`** preenchida (modelo: pr-body-sgd-novo.md).
2. Corpo no GitHub com blocos **Contexto**, **O que mudou (por menu / tela)** e, se aplicável, **Critérios de aceite** / checklist.
3. Cada subsecção de menu usa `### Menu … > …` e bullets **Corrigido:** / **Adicionado:** / **Ajustado:** / **Removido:** — comportamento observável, não lista de ficheiros.
4. **Em seguida (mesma entrega):** skill **`auxilio-testes-pr-sgd`** — rule `pr-auxilio-testes-obrigatorio`.

Complemento técnico (commits, diffstat, gates) pode vir do `git-env`; não substitui o texto por menu.

## Fluxo (ordem fixa)

### 1. Identificar ITEM e worktree

- Código na branch (`item-10045`, `8016`, …) ou na ficha ligada à PR.
- Worktree do ITEM em `$WORKTREES_ROOT/wt-item-<codigo>` (não o agregado `repo/ebs-dominio_sgd` na raiz).

### 2. Preencher a ficha (fonte da verdade)

Escrever ou actualizar `## Descrição para PR` **antes** de gerar o markdown final.

### 3. Gerar o corpo

```bash
python3 ecosystem/automation/jarbas.py git-env pr-preview \
  --repo-root <worktree-item> --base <integration_target da ficha>
```

**Se `pr-preview` falhar com PARIDADE-POST ausente** mas o pedido é **só melhorar a descrição**: montar body a partir da ficha + pr-body-sgd-novo.md ou `.tmp/pr-bodies/ebs-dominio_sgd-pr-*.md`.

### 4. Publicar no GitHub

Autenticação: `jarbas.py git-env` / `git_auth.ensure_gh_token_for_cli()`.

```bash
gh pr edit <n> --repo tr/ebs-dominio_sgd --body-file <ficheiro>
# ou: gh api -X PATCH repos/tr/ebs-dominio_sgd/pulls/<n> -f body="$(cat <ficheiro>)"
```

Guardar cópia em `.tmp/pr-bodies/ebs-dominio_sgd-pr-<n>-body.md`.

### 5. Verificação da descrição

- [ ] Body no GitHub com **Contexto** e `### Menu` ou `### Backend`.
- [ ] Ficha governance commitada (worktree, não agregado directo).

### 6. Auxílio de testes (obrigatório na mesma PR)

Invocar **`auxilio-testes-pr-sgd`** com o número da PR. Sem ficheiro em `user-doc/novo-sgd/auxilio-testes-pr/` → `[jarbas PR-AUXILIO-TESTES BLOCKED]`.

## Relação com outras skills

| Artefato | Papel |
|----------|--------|
| `pr-body-sgd-novo` (profile) | Formato resumido + `git-env` |
| `auxilio-testes-pr-sgd` | Roteiro manual **obrigatório** por PR |
| `governed-numbered-item-delivery` | Entrega ITEM + PR-first |

## Memória curada

- `PM-20261009-43da` — `gh pr edit` vs `gh api PATCH`.
- `PM-20261006-c67e` — auth GCM / `git-env`.
- `PM-20261006-30f1` — `git-env publish` / POST no HEAD.
