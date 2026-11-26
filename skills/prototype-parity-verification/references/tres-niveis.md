# Three levels and hollow code

A screen or component counts toward parity only when it passes all three levels:

1. **Exists**: the file, route or component is present in the target.
2. **Substantive**: it renders real content and behavior, not a placeholder.
3. **Wired and receiving data**: it is connected to its consumers and gets real data and handlers.

**Hollow** means it exists but does not receive data (`dataSource={[]}`, `return null`, empty handler, TODO). Hollow does not count as parity, even when the target tests are green.

## Before review: `stubs`

Run it from the skill directory against the product checkout (`--raiz <produto>`), never against the prototype. Use it over the files the plan touches (or everything changed since a commit; `--raiz` may be a subfolder of the repository):

```
python3 scripts/verificacao.py stubs --raiz <product> --arquivos <file>...
python3 scripts/verificacao.py stubs --raiz <product> --desde <commit>
```

It prints `arquivo`, `linha`, `padrao`, `texto` for each match and exits 11 when there are candidates, 0 when there are none. Patterns: `retorno_nulo`, `lista_vazia_em_prop`, `handler_vazio`, `pendencia`, `nao_implementado`.

## End of delivery: `sem-teste`

```
python3 scripts/verificacao.py sem-teste --catalogo <catalog.json> --formato md
```

It lists delivered requirements that have scenarios not covered by `tests[].scenario_ids`; `cenarios` holds only the scenarios still without a test (a requirement with 3 scenarios and a test for one is listed with the other 2). Delivered means a task linked through the requirement's or its differences' `task_ids` is done: the linkage requires `task_ids` on every difference, so a non-empty list only says the work is planned. The catalog schema has no task state, so the script reads an optional `status` on `tasks[]` (`done`, `delivered`, `completed`, `entregue`, `concluida`, `concluída`) and the ids passed to `--entregues T-1 T-2` (from the plan ledger); with neither source and linked tasks it exits 2 instead of printing an empty list (`--entregues` with no ids also exits 2). Use `--todos` to include requirements not yet delivered. Each line is a manual checklist item: screen (surface), requirement, scenarios to check. Exit 11 means there are items.

Known misses and false alarms: it misses multiline `dataSource={\n[]\n}` and `[] as T[]`, and flags legitimate guard clauses such as `if (!rows) return null`.

## Verdict

A candidate is not a verdict: a legitimate `return null` or an intentionally empty list is fine. The reviewer decides, and records the decision with the evidence; the script never marks parity as `CONFORME` or `DIVERGENTE`.
