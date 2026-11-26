---
name: prototype-parity-verification
description: 'Use ao planejar ou reconstruir uma aplicação a partir de protótipo: decisões, planos ligados ao catálogo, portar testes, escolher regressões e avaliar evidência visual.'
---

# Prototype parity verification

Verify observable behavior against independently established reference evidence. Superpowers remains responsible for development, TDD, review and completion.

## Execution boundary

**All browser automation runs only in the reconstructed target.** This includes screenshots, dropdown exploration, DOM, computed styles, keyboard and temporary inspection scripts. A read-only prototype URL is not permission to automate it. Never produce a dual runner with reference/target URL loops.

Reference inputs are authorized static source, previously supplied screenshots/measurements, or documented human observations, fixed to a version. If those are missing, report `SEM_COMPARACAO` or `NAO_VERIFICADO` and request the missing reference input; useful target tests may still run. Do not generate expected screenshots from target output.

## Decisions and plans from the catalog

When planning from the parity catalog, read [decisoes-e-planos](references/decisoes-e-planos.md) before writing the decisions document or a plan over the catalog, and before executing a plan that has a `**Catálogo:**` block. It covers the chat flow, the questions only the Diego answers, the library rule, the block rules and the order of `verificacao.py ligar`. The boundary above is unchanged: appearance is checked from the code, never by automating the prototype.

## Required verification packet

For each scenario, record:

1. Project, scenario, reference version/hash, target commit and comparable conditions.
2. Expected claims and source evidence per applicable dimension; `[inf]` alone is insufficient.
3. Consumers/journeys and the first executable task; focused E2E runs there, integration after dependencies exist.
4. Target test command/result, expected evidence, actual evidence and observed differences.
5. Separate discovery status, parity status and unverified dimensions/blocks/approved exceptions.

Use the project's canonical catalog; do not copy it into extra matrices. The existing validators in `ecosystem/automation/proto_env/parity/` check declared structure and linkage; they cannot discover every unknown state or authenticate a screenshot.

## Apply in the official task

Before changing a shared component/helper, consult component/impact/test-portability contracts. Reuse a canonical target for a source primitive; incompatible alternatives need variant or approved exception. Adapt upstream intent after removing unsafe dependencies and weak assertions.

Use the smallest discriminating test with independent expected. Run focused E2E as soon as behavior is testable and preserve the official final suite/review. Treat login/infra failure separately from valid RED; retries do not prove stability.

Before review and at the end of delivery, run `scripts/verificacao.py` (`stubs` finds hollow code, `sem-teste` lists delivered requirements without a test; "delivered" comes from `tasks[].status` in the catalog or from `--entregues T-1 T-2`, since a non-empty `task_ids` only means planned): [three levels](references/tres-niveis.md). Candidates are advisory; the reviewer decides.

Compare visual evidence per region/state with shared tokens and fixed viewport/font/data. Accessibility norms and reference parity have separate provenance. A screenshot cannot prove focus, persistence or permissions.

## Common mistakes

- “Only collecting measurements” on the prototype still crosses the automation boundary.
- Green target tests prove their assertions, not reference parity.
- A source URL, confidence label or file hash alone does not prove a claim.
- An uninvestigated state stays visible even if the implemented path passes.

Load only the needed reference: [target-only](references/target-only.md), [visual/accessibility](references/visual-and-accessibility.md), [evidence/triage](references/evidence-and-triage.md), [three levels](references/tres-niveis.md), [decisions and plans](references/decisoes-e-planos.md).
