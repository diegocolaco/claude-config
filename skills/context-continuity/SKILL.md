---
name: context-continuity
description: Use ao retomar trabalho em chat novo, para recuperar o estado sem reler a conversa anterior.
---
CTX-ID: context-continuity@6

# Context Continuity

O utilizador não é a memória que liga os chats. Persistir pouco → recuperar sob demanda → carregar só o relevante.

## Estado partilhado

- Ficheiro: `<raiz>/.runtime/context/PROJECT-STATE.md`. `<raiz>` = a pasta aberta no Cursor (Workspace Path), não o repositório onde a shell está. Se essa pasta for um worktree, usar a raiz principal: pasta pai de `git -C <workspace> rev-parse --path-format=absolute --git-common-dir`. Nunca criar o estado dentro de `repo/` ou de worktrees de ITEM.
- Histórico: PROJECT-STATE-ARCHIVE.md na mesma pasta. Só ler se o utilizador pedir histórico.
- Não versionado (`.runtime/` no `.gitignore`). Se não existir, criar com o modelo de `references/state-management.md`.
- **Nunca ler o ficheiro inteiro.** Navegar assim:
  1. Mapa: Grep `-n` com `^#{2,3} ` (ou o termo procurado) passando o **caminho do ficheiro**, não a pasta. Numa pasta, Grep e Glob saltam ficheiros ignorados pelo git. Se vier vazio, usar Shell `rg -n --no-ignore '<padrão>' <ficheiro>`.
  2. Read com `offset` = linha do cabeçalho e `limit` = até ao cabeçalho seguinte, sem margem.
  3. Para saber se o ficheiro existe, usar Read (o Glob não o vê).
- Se já existe fonte de verdade (ficha ITEM, SPEC, SDD, ADR, plano), o estado guarda o **ponteiro**, não uma cópia.

## Operações — ler só a referência da operação em curso

| Operação | Quando | Referência |
|---|---|---|
| RESTORE | chat novo, retomada, mudança de frente, resposta depende de decisão anterior | `references/restore-context.md` |
| STATUS | "onde estamos", "o que está bloqueado", visão geral das frentes, **ticks de supervisão** (`/loop`) | `references/restore-context.md` § STATUS (+ subagentes runtime) |
| SYNC | decisão, restrição, descoberta ou pendência com valor futuro | `references/state-management.md` |
| HANDOFF | descoberta desta frente afeta outra | `references/handoff.md` |
| Explicar | orientação no processo, resposta com vários termos novos, ou o utilizador mostra que não entendeu | rule `communication-context` (fonte única da comunicação) |
| Entrega numerada governada | retomada «onde parou», «o que falta», «preciso fazer algo?» | rule `communication-context-produto` (interno); modelo-sgd-entrega-item.md se E2E/bloqueio ambíguo |

## Regras

1. Identificar a frente atual pelo pedido ou pelo Índice. Se for ambígua, perguntar mostrando as frentes do Índice.
2. Carregar só o que muda a análise atual: a secção da frente + decisões, dependências e handoffs que a citam. Outras frentes ficam de fora.
3. Fazer SYNC/HANDOFF sem pedir licença quando o valor futuro é claro, e avisar numa linha (ex.: "Registei D-004 no estado").
4. Antes de alterar uma secção: reler, comparar `rev`, substituir o bloco exato. Nunca sobrescrever uma divergência em silêncio.
5. Não persistir raciocínio, logs, respostas completas, código nem PII/segredos (máscaras de global.mdc, referência Jarbas não importada).
6. **Subagentes:** estado de subagentes é **só leitura em STATUS** (transcrições Cursor). **Nunca** SYNC/HANDOFF nem PROJECT-STATE.md para progresso transitório de subagente.
