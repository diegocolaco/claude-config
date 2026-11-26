---
name: e2e-coverage-reuse-guard
description: Use quando criar, estender, mover, apagar ou enfraquecer spec Playwright em tests/e2e, escolher --journey/--dual-spec ou o PREFLIGHT acusar este guard.
---

# E2E coverage reuse guard (SGD novo)

## Composição Superpowers

Decide **se** um teste novo é necessário; **como** escrevê-lo segue o Superpowers.

**REQUIRED BACKGROUND:** You MUST understand `superpowers:test-driven-development` — teste novo só quando nenhum existente cobre o comportamento, escrito RED→GREEN.

## Visão geral

Teste novo só quando nenhum existente cobre o comportamento. A prova não é prosa: é o **plano** `.tmp/<trace_id>/e2e-coverage-plan.json`, conferido contra o diff pelo gate de cobertura. Sem esse PASS, a decisão de cobertura não está feita.

**Não usar** para teste unitário (vitest/jest em `apps/**`) nem para a regressão de versão completa (nível 4 da rule `task-reviewer`).

## Receita (nesta ordem, no worktree do ITEM)

```bash
$J scan --worktree <wt>                       # specs que já passam pelas rotas alteradas
$J init-plan --worktree <wt> --item ITEM-<n> --kind <feature|bugfix|improvement|test-only> \
   --out .tmp/<trace_id>/e2e-coverage-plan.json
# editar o plano: decidir cada pending_*, depois apagar as chaves pending_candidates/pending_routes
$J check --worktree <wt> --plan .tmp/<trace_id>/e2e-coverage-plan.json \
   --journey <spec> ... --dual-spec <spec> ...   # as mesmas do item-test
```

Rodar `scan` **antes** de escrever qualquer teste. O plano descreve o estado final: enquanto o developer não aplicar as mudanças, o `check` falha nas linhas ainda por fazer — corrigir o diff, nunca o plano para calar o erro. O `item-test` repete o `check` no PREFLIGHT e bloqueia se o plano existir e falhar.

## O plano — o que cada situação exige

| Se… (observável) | Então o plano tem |
|---|---|
| comportamento já afirmado por teste existente, que **não muda** | `decisions[]` `REUSE` com `spec` + `tests` (títulos exatos) |
| spec existente adequada para receber o comportamento, ou spec existente que muda (asserção, dado, título) | `EXTEND` desse spec — mesmo que o nome dele seja legado (`item-2000-29/…`) |
| comportamento sem spec adequada após busca, inclusive em tela/jornada existente | `CREATE` em pasta de domínio/tela + `rationale` + `rejected_candidates` (spec + reason; `[]` só se o scan não listou nada); explicar por que não cabe estender os candidatos |
| conteúdo de um spec passa para outro | `CONSOLIDATE` no spec **que fica**, `consolidates: [os que saem]`; os que saem vão em `removed_specs` |
| `kind=bugfix` | `regression_for` num spec que **fica**, com o teste escrito neste diff; REUSE só com `failing_before` (evidência do teste vermelho) |
| rota em `pending_routes` | `regression_journeys` (spec + `touched_paths` do diff + rationale) **ou** `excluded_routes` (route + reason) |
| spec em `pending_candidates` (usa `data-testid` alterado) | decisão, `regression_journeys` ou `excluded_candidates` com reason — um a um |
| diff tira `expect`, troca matcher de valor ou põe `skip/fixme` | `assertion_changes` (spec, reason `refactor/product-change/sdd-approved/obsolete`, `source`); dual só `sdd-approved` |
| spec apagado ou cenário excluído por redundância | `covered_by` identifica o teste sobrevivente e o mapa de substituição por cenário: critério, pré-condições/dados, papel, ação, resultado/asserções, dependências e modo em que executa; a existência do título não basta |
| cenário coberto no dual | Usar a prova do lado produto quando propriedade, condições e run forem equivalentes; com dual desligado, selecionar a execução produto do mesmo cenário. Não remover a obrigação de regressão nem criar execução apenas para repetir PNG |

O nome `paridade-dual/item-<n>.dual.spec.ts` é a convenção do harness (o check não acusa), mas a decisão vale igual: ID que o dual da tela já mede → `REUSE` dele, não dual novo.

## Specs legadas fora da regressão

O registro `ecosystem/profiles/sgd-novo/knowledge/e2e-specs-legadas.yaml` identifica candidatos a exclusão. Rota UI/endpoint API compartilhado localiza candidatos; não prova substituição. Antes de excluir pasta, spec ou cenário, mapear cada propriedade protegida ao teste sobrevivente conforme a tabela acima e comprovar que ele é descoberto, selecionado e executa as asserções no modo corrente. Sem essa prova, conservar a cobertura anterior. O resultado de legacy-regen/legacy-verify que verifica apenas rota não autoriza a exclusão sem a revisão semântica documentada. Remoção física continua exigindo removed_specs.covered_by. Não chamar esse mapa de garantia universal: ele cobre as propriedades identificadas e examinadas.

## Evidência (um lugar só)

No `[`task-reviewer`] relatório de verificação (`jarbas.py check`): `e2e-coverage: PASS plan=.tmp/<trace_id>/e2e-coverage-plan.json` (saída do `check`). O reviewer reexecuta o mesmo `check --plan`; tabela em markdown não substitui.

## Racionalizações (vistas nos baselines)

| Desculpa | Realidade |
|---|---|
| «Fica fora do fecho pelo custo de fila» | Custo não é motivo de exclusão: `excluded_routes`/`excluded_candidates` dizem por que o diff **não** afeta aquela jornada. |
| «Não há spec listada para essa tela» | Lista no prompt ≠ suíte. Rodar `scan`; rota sem spec vira `CREATE` justificado ou `excluded_routes`. |
| «Criar `comercial/x.spec.ts` se não existir» | «Se» sem busca é CREATE sem `rejected_candidates` — o `check` bloqueia. |
| «O dual já tem esse CA, posso apagar a jornada» | Só eliminar execução duplicada se a propriedade permanecer executável no modo produto e houver prova válida para o modo corrente; ID igual não demonstra cobertura |
| «Só corrijo a asserção do teste antigo e ponho o CA no título» | Teste antigo cuja asserção muda por `product-change` mantém o título dele; o CA fica no dual. `assertion_changes.source` liga a mudança ao ITEM. |
| «O plano descreve o commit atual; consolido depois» | O plano é o estado **final**. Spec com nome de ITEM que vai sair entra em `removed_specs` agora, não num «próximo passo». |
| «Preciso do teste de jornada para o print do CA» | O `dual.run` grava `<ID>-sgd.png`; é essa a evidência. |
| «REUSE do spec e corrijo a asserção que falha» | Spec que muda é EXTEND; REUSE com `assertion_changes` é contradição (`PLAN_CONTRADICTION`). |
| «Removo o dual do ITEM após migrar» | Sem `covered_by` apontando o teste que recebeu cada asserção, é remoção de paridade. |
| «A tabela no plano.md / auxílio de testes já explica» | Prosa não é conferida. O plano JSON é. |

## Red flags — parar e rodar `scan`/`check`

- Escrever teste antes do `scan`.
- `--journey` escolhida «por afinidade» sem `touched_paths` do diff.
- Apagar a chave `pending_*` sem decidir cada entrada.
- Mudar asserção para o teste passar sem `assertion_changes.source`.

## Limites do check (julgamento seu)

O check atual não comprova equivalência de cenários, asserções realizadas, navegação sem literal de rota nem impacto completo de BFF/serviços. Registrar esses limites. No fluxo migrado, plano aplicável ausente ou sem mapa suficiente bloqueia fechamento e sua execução terminal. Exploração, reprodução e RED podem ocorrer com seleção provisória identificada, sem stamp ou aceite final. Compatibilidade legada deve ser explícita e não equivale a aprovação pelo contrato novo. Até o validador implementar esse contrato, cumprir a revisão documental exigida e registrar a lacuna mecânica; não afirmar que um PASS antigo verificou a semântica.
