---
name: item-process-changelog
description: Use quando alterar o processo de implementação ITEM (sgd-local, harness, gates) e registrar o histórico em user-doc.
---
CTX-ID: item-process-changelog@5

# Histórico do processo de ITEM — manter sempre atualizado

**Documento:** doc-sgd-novo-processo-item-historico.md (fonte única, legível por humanos).
**Obrigatoriedade:** regra `item-process-docs`. Se o Diego pediu a mudança de etapa, gate ou ordem, o campo **Impacto** copia o delta da skill `impacto-tempo-entrega-item` (mostrado no chat antes de editar). Esta skill de histórico não calcula o tempo.

## Quando usar

Qualquer alteração que mude **como um ITEM é implementado, testado, validado ou publicado**:

| Área | Exemplos de caminhos |
|---|---|
| Infraestrutura local | `ecosystem/automation/sgd-local/**` (slotctl, deploy por slot, `e2e-run.sh`, orquestração, patches locais), `SDD/sgd-local-slot-controller/**`, compose, certificados, infra partilhada |
| Testes E2E | workers, reporter, vídeo/screenshot, `playwright.config.ts`, suporte de teste (`tests/e2e/support`), patches locais, paridade dual |
| Gates e publicação | `ecosystem/automation/git_env/**`, gates de paridade, PR-first, DEF-EVID, TEST/REVIEW |
| Regras e comandos | `governed-numbered-item-delivery`, regras do profile `sgd-novo`, e as partes de `task-reviewer`, `mandatory-change-validation` e `orchestrator` que mudam o pipeline de ITEM do SGD |
| Decisões do Diego | mudança de padrão (ex.: workers), aceitação de risco, algo que deixa de ir para o `develop` |

Não usar para: código de produto de um ITEM (vai na ficha), incidente isolado sem mudança de processo (vai em
`SDD/sgd-local-slot-controller/incidents/`), notas pessoais (diário a skill `diario-experiencias-atividades-sgd` →
doc-experiencias-atividades-diarias-sgd-novo.md, skill `diario-experiencias-atividades-sgd`).

## Procedimento (no mesmo commit da alteração)

1. **Ler** o documento: secções 1 (estado atual), 2 (patches locais), 3 (registo), 4 (pendências) e o glossário.
2. **Acrescentar uma entrada no topo da secção 3** (a secção 3 está em ordem do mais recente para o mais antigo) com o
   modelo abaixo. ID `PROC-AAAA-MM-DD-NN` (data da alteração + sequencial do dia). Termo técnico novo → uma linha no
   glossário.
3. **Atualizar a secção 1** se o comportamento vigente mudou (ex.: workers, etapas do `item-test`, gate novo). A
   secção 1 descreve sempre o processo **como está hoje**, sem histórico.
4. **Atualizar a secção 2** se um patch local foi criado, alterado, regenerado ou retirado (nome, sha8, o que faz,
   como desligar).
5. **Atualizar a secção 4**: abrir pendências novas; fechar (com data e PROC) as resolvidas.
6. **Validar:** links para ficheiros existem; nenhum CPF, e-mail ou token (referência Jarbas não importada: global.mdc); UTF-8 sem U+FFFD; números
   medidos com a fonte (job/trace); estimativas marcadas como estimativa.
7. **Commit** junto com a alteração (worktree do playground). Se a alteração foi
   noutro repositório (produto, governança), o registo vai num commit do playground na mesma entrega.

Esta skill **complementa** o SPEC-GATE (`sgd-slot-spec-governance`: SPEC, manifesto e CHANGELOG no mesmo commit de
qualquer mudança no controlador) e os incidentes (`SDD/sgd-local-slot-controller/incidents/`); não os dispensa.

### Modelo de entrada

```markdown
### PROC-AAAA-MM-DD-NN — <título curto em linguagem simples>

- **Área:** infraestrutura local | testes E2E | gates/publicação | regras/comandos | decisão
- **O que mudou:** <1–3 frases, o que passa a acontecer>
- **Porquê:** <problema medido ou pedido; citar o pedido do Diego verbatim quando houver>
- **Impacto:** <medido (fonte: job/trace) ou esperado (marcar estimativa)>
- **Onde está:** <commit(s)/merge, versão da SPEC, regra/skill, ITEM>
- **Como desligar/reverter:** <variável, comando ou commit a reverter>
- **Riscos/pendências:** <ou "nenhum">
```

## Fontes para preencher

- CHANGELOG.md (detalhe técnico do controlador; o histórico **resume e aponta**, não
  copia).
- `git log` do playground nos caminhos da tabela acima; fichas de ITEM (`repo/sgd-cursor-governance/items/`).
- Evidência de runs: `.tmp/evidence/<trace>/` (summary.md, `playwright-results.json`, `local-patches.txt`),
  `.tmp/sgd-orq-sim/<trace>/runs/<job_id>/` (summary.md, `logs/e2e.log`) e `.runtime/sgd/jobs/<job>/` (`job.json`,
  logs dos serviços).

## Anti-padrões

| Errado | Certo |
|---|---|
| Registar só no CHANGELOG da SPEC ou no chat | Entrada no histórico + link para o CHANGELOG |
| Secção 1 com "antes era…" | Secção 1 só com o vigente; o "antes" fica na entrada da secção 3 |
| Entrada sem como desligar | Toda a entrada diz como reverter |
| Número sem fonte | Job/trace ao lado do número; estimativa marcada |
