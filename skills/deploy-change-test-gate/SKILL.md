---
name: deploy-change-test-gate
description: Use quando alterar o pipeline de deploy/E2E do SGD local ou o harness item-test, para exigir os testes obrigatórios.
---
CTX-ID: deploy-change-test-gate@5

# Deploy change test gate — mudança no processo de deploy só entra com testes documentados

## Composição Superpowers

Gate jarbas de deploy/E2E local; fecho exige prova reproduzível alinhada ao Superpowers.

**REQUIRED SUB-SKILL:** Use `superpowers:verification-before-completion` antes de declarar o gate PASS ou pedir merge no agregado.

**Projeto:** TR Jarbas Ai Multi-agents squad · `@platform: wsl-bridge` (a maior parte do `sgd-local/` é linux-only)

**Doc único de procedimento (ler primeiro):** deploy-process-test-matrix.md —
tiers T0–T5 com comando exacto, matriz de variações × teste (com lacunas), mapa path→tiers (com catch-all), execução segura,
template do relatório, baseline de vermelhos. Esta skill é só o **fluxo**; não duplica comandos — se divergirem, vale o doc.
Baseline máquina-legível: `docs/diagnostics/evidence/deploy-change-tests/baseline-spec-2.13.0.tsv`; runner/comparador:
`ecosystem/shared/knowledge/operational/deploy-test-baseline-compare.py` (`run`, `compare`, `tested-commit`, `selftest`).

## Estado do gate — hoje é PROCEDURAL

Nada em `merge-worktree-to-agregado.sh` verifica o relatório. O gatilho é só a `description` desta skill (o agente decide
carregá-la) e os ficheiros de processo protegidos (sgd-entrega.md, sgd-slot-controller.md) **ainda não a referenciam** — por
serem protegidos não foram editados. O texto proposto para cada um
e a proposta **P5** (enforcement no merge script) estão no doc §0, **pendentes do «sim» do Diego**. Até lá, a sessão principal e o
revisor têm de exigir o relatório; não afirmar que o processo está «protegido».

**Porque está em canonical e não no profile `sgd-novo`:** o deploy/controlo vive em `ecosystem/automation/sgd-local`
(playground), as rules de governança do slot-controller estão no canonical, e a skill é transversal a todos os ITENs e
protegida pelo mesmo guard — não é só do produto SGD novo.

## Quando usar

- Qualquer diff em paths de `ecosystem/shared/protected/infra-deploy-paths.txt` (ler o ficheiro; é a fonte): `sgd-local/**`,
  `SDD/sgd-local-slot-controller/**`, `git_hooks/**`, `playground/**`, `.cursor/hooks/**`, `hooks.json`,
  sgd-entrega.md, sgd-slot-controller.md, rules do processo.
- Adjacentes (mesmo gate): handler `sgd-env` em `jarbas.py`, `capacity/**`, `local-patches/`.
- Frases: «mudei o deploy», «alterei o processo de deploy», «testar o deploy ponta a ponta», «posso mergear isto?».
- **Não** usar para código de ITEM do produto (é o fluxo `governed-numbered-item-delivery`).

## Pré-requisitos (não saltar)

1. «Sim» do Diego para editar paths protegidos — o pedido que cita o ficheiro conta.
2. Trabalhar num **worktree** (`bootstrap-playground-worktree.sh <slug>`), nunca na raiz; SPEC + manifesto + CHANGELOG no
   mesmo commit.
3. `trace_id` da entrega (`jarbas-<AAAAMMDD>-<HHMMSS>-<4hex>`).
4. Caminhos `$HOME/projetos/…` do doc são o layout **desta máquina**; noutro host usar `SGD_MONOREPO_ROOT`/`WORKTREES_ROOT`.

## Procedimento

1. **Classificar a mudança** — `git diff --name-only <base>..HEAD`; tipo **D-doc** | **D-teste** | **D-script** |
   **D-comportamento** (doc §8). Na dúvida, o tipo mais exigente; path de `sgd-local/**` não listado no mapa = D-comportamento
   (catch-all). Registar componentes/INV em risco (SPEC §5/§10/§15).
2. **Escolher os tiers pelo mapa** do doc (§8): T0 **sempre** (inclui **todos** os hook tests e os `git_env`); somar T1…T5
   por cada grupo de path tocado. Ler a baseline (§5 e `baseline-spec-*.tsv`) para saber o que já está vermelho **antes** da mudança.
3. **Segurança antes de executar:** conferir o estado dos slots;
   para T2/T3 slots `FREE` e sem listener nas portas; para T3 real/T5 conferir a vaga pela fila nativa do `sgd-env item-test` (`SGD_E2E_SLOT_COUNT`, `E2E_WORKERS`). Nunca contra o runtime/stack de outro agente (doc §9).
4. **Executar, registar e comparar:** cada tier exigido com o comando **exacto** do doc (ou `deploy-test-baseline-compare.py run`);
   copiar duração e resultado reais (PASSOU/FALHOU/PARCIAL/não executado). `SKIP` ≠ PASSOU. Vermelho que passa à 2.ª = flaky:
   re-executar até 3× e registar todas (flaky conhecido `FLAKY…` não é silenciado como PASSOU). **Comparar com a baseline:**
   `deploy-test-baseline-compare.py compare <baseline> <actual.tsv>` — exige **T0 e T1** por omissão (`--require-tiers`; reduzir só
   com `--justificacao`, que fica na saída); REGRESSAO (incl. PARCIAL→FALHOU), FLAKY a falhar, FALTA, TIER-AUSENTE ou NOVO-VERMELHO
   = exit 1, o gate falha; exit 2 = erro de entrada (TSV em falta/inválido), nunca «passou». Correção de bug: provar que o teste **falha antes** e passa depois.
5. **Fixar o «commit testado» e escrever o relatório:** commitar a mudança, confirmar a árvore limpa e `SHA=$(git rev-parse HEAD)`
   **antes** de correr os tiers; o «commit testado» é este HEAD **antes de acrescentar o relatório**. Depois escrever
   `docs/diagnostics/evidence/deploy-change-tests/AAAAMMDD-<slug>.md` pelo template (doc §11, campo `commit_testado`) e commitar
   **só** relatório + evidências (mesma branch/PR, commit posterior). Algo falhou no processo → `incidents/INC-…` (SPEC §17.1).
6. **Auditoria independente (obrigatória antes do merge):** o **jarbas** delega **`deploy-process-auditor`** (`claude-sonnet-5-5-high`,
   read-only) com worktree, diff, relatório e `commit_testado`. O auditor reexecuta amostra dos tiers, confere os 7 pontos
   «auditável» (doc §11), `tested-commit` e `compare`. Só com **`DEPLOY-AUDIT APPROVE`** pode haver merge. O implementador **não**
   substitui o auditor.
7. **Gate:** **não** declarar «pronto» nem `merge-worktree-to-agregado.sh` sem relatório **PASSOU** (ou PARCIAL com lacunas aprovadas
   pelo Diego) **e** `DEPLOY-AUDIT APPROVE`. Depois, o merge segue o pré-requisito 1 (path protegido só com o «sim» do Diego).

## Checklist copiável

```
- [ ] «sim» do Diego para os paths protegidos; worktree (não a raiz); trace_id
- [ ] git diff --name-only → tipo (D-doc|D-teste|D-script|D-comportamento) + grupos do mapa §8 (catch-all = D-comportamento)
- [ ] Baseline §5 e baseline-spec-*.tsv lidas (vermelhos pré-existentes identificados)
- [ ] capacity registado (classe, permitido); slots FREE; sem listener nas portas (T2/T3); vaga E2E (T3 real/T5)
- [ ] árvore limpa; SHA=$(git rev-parse HEAD) fixado ANTES dos tiers (= commit_testado)
- [ ] T0 completo (T0.1 com pipefail, spec sync, TODOS os hook tests, git_env, test_jarbas_sgd_env, platform-check --strict, lint --docs)
- [ ] T1 relevantes · T2 (slotctl run.sh) · T3 (char + acceptance) · T4 (infra) · T5 (E2E real) — conforme o mapa
- [ ] compare da baseline (T0+T1 exigidos; OVERRIDE só com --justificacao): sem REGRESSAO / FLAKY a falhar / FALTA / TIER-AUSENTE / NOVO-VERMELHO (linha «compare:» colada no relatório)
- [ ] Teste novo/corrigido: red → green demonstrado
- [ ] SPEC + spec-manifest + CHANGELOG + guia operacional no mesmo commit (test_spec_sync verde)
- [ ] Relatório commitado em commit POSTERIOR ao commit_testado (só relatório + evidências)
- [ ] Lacunas L-xx com substituto manual executado e aprovação do Diego; erros → incidents/INC-…
- [ ] deploy-process-auditor (Sonnet 5.5 High): DEPLOY-AUDIT APPROVE + tested-commit exit 0 + compare coerente
- [ ] Só então merge-worktree-to-agregado.sh
```

## Anti-padrões

| Errado | Certo |
|---|---|
| «Testei manualmente», sem comando nem resultado | Comando exacto + duração + resultado no relatório |
| Correr só `bash -n`/`test_spec_sync` numa mudança de slotctl/deploy/e2e-run | Seguir o mapa: T0–T3 + T5 para D-comportamento |
| Dois T2/T3 ao mesmo tempo, ou T2 com stack/`item-test` de outro agente activo | Slots `FREE` + portas livres; esperar (doc §9) |
| Contar `SKIP`/`skip=suite`/`OK (skipped=N)` como PASSOU | Registar PARCIAL e voltar a correr com o ambiente certo |
| Ignorar um vermelho «já estava assim» sem o declarar | Comparar com a baseline; declarar no §5 do relatório; corrigir se a mudança toca a área |
| Alterar os testes para ficarem verdes sem justificar | Mudar o teste com a causa documentada (red/green) e SPEC/CHANGELOG |
| Código ou baseline alterados depois do `commit_testado`, ou `commit_testado` = commit que já contém o relatório | `commit_testado` = HEAD antes do relatório; `tested-commit` exit 0 |
| Compare só com T0 (ou só com o tier que passou) para obter PASSOU; flaky conhecido dado como verde | T0+T1 exigidos; reduzir só com `--justificacao`; flaky: re-executar até 3× e registar todas |
| Esconder código num rename para `…/deploy-change-tests/*.md` depois do commit testado | `tested-commit` usa `--no-renames` e recusa (lista origem e destino) |
| Relatório escrito depois do merge ou noutra PR | Mesma branch/PR, commit posterior ao testado, antes do merge |
| Dizer que o deploy está «protegido» por esta skill | O gate é procedural até a P5/recomendações serem aprovadas (doc §0) |
| Esquecer o tier só porque é caro (T5 `pesada`) | `capacity` + vaga; ou lacuna **aprovada pelo Diego** |

## Referências

- Doc de testes: deploy-process-test-matrix.md
- Baseline: `docs/diagnostics/evidence/deploy-change-tests/baseline-spec-2.13.0.tsv` · script: `ecosystem/shared/knowledge/operational/deploy-test-baseline-compare.py`
- SPEC: SPEC.md (§14 catálogo, §15 matriz de impacto, §17 lacunas, §18 procedimento)
- Rules: `cross-platform` (`platform-check --strict`)
- Precedente de relatório: slotctl-lifecycle-report.md
- Guia operacional: sgd-slot-controller.md
- Subagente de auditoria: `deploy-process-auditor` (`ecosystem/canonical/agents/library/deploy-process-auditor/content.md`)
- Skills relacionadas: `cross-platform-verify`, `playground-commit-workflow`
