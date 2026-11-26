---
name: governed-items-portfolio-analysis
description: Use com /items-panorama ou /item-relatorio, ou para resumir o portfólio de ITENS governados e seu status.
---
CTX-ID: governed-items-portfolio-analysis@1

# Análise de portfólio de ITEMs (governança)

Relatório **somente leitura** sobre fichas em `<governance_root>/items/`. Não altera código nem fecha entrega — para implementar, usar **governed-numbered-item-delivery** e (profile SGD).

**Comandos Cursor:** ver `reference.md`.

**Fonte canónica:** `ecosystem/canonical/skills/governed-items-portfolio-analysis/` → `python ecosystem/automation/jarbas.py materialize`.

---

## Quando usar

- Pedidos como: “analise os itens”, “status dos ITEMs”, “o que está em desenvolvimento / finalizado”, “tabela com evidências”, “panorama da planilha”, “impedimentos”, “fora de develop”.
- Antes de priorizar PRs, auditoria de paridade ou fecho de onda.
- **Não** substitui PARIDADE-PRE/POST nem gates jarbas.

**Quando não usar:** criar ficha, commit, branch ou implementar fix → **governed-numbered-item-delivery**.

---

## Passo 0 — Resolver paths

**REQUIRED:** seguir `governed-numbered-item-delivery` → variável `governance_root` (pasta com ITENS.md).

| Profile SGD (usual) | `governance_root` |
|---------------------|-------------------|
| `sgd-novo` | `repo/sgd-cursor-governance` |

Se o usuário pedir só “em desenvolvimento” ou “finalizados”, aplicar filtro na secção **Classificação** (abaixo). Se pedir um ITEM, uma linha detalhada + tabela resumida opcional.

---

## Passo 1 — Coletar fontes (obrigatório)

Para **cada** diretório `items/<codigo>/` que contenha `item-<codigo>.md` (ou alias documentado, ex. `1135` → planilha `135`):

| Fonte | O que extrair |
|-------|----------------|
| ITENS.md | Prompt literal / proveniência; título temático |
| `items/<codigo>/item-<codigo>.md` | Metadados (Status, Tipo, Branch, Base, trace_id, Desenvolvedor, Criticidade); definição resumida; secções Paridade / Reauditoria; Evidências |
| `items/<codigo>/evidence/README.md` | Lista de arquivos; link relativo `./evidence/` |
| `items/<codigo>/evidence/MATRIZ-EVIDENCIAS.md` | Gate DEF-EVID (referência Jarbas não importada: item-evidence-definition.mdc) |
| `items/<codigo>/evidence/` | Existência de PNG/HTML; contagem; arquivos referenciados mas ausentes |
| `items/PARIDADE-*.md`, `items/paridade-post-*.md` | Veredito por ITEM (se existir) |
| `.tmp/retest-open-items-*.md` | Retestes recentes (se existir) |

**Proibido:** inventar status; usar só memória do chat sem ler ficheiros atuais.

**Links de PR:** se o utilizador pedir coluna PR ou URLs, **não** emitir compare GitHub sem antes sincronizar a branch de entrega com `origin/develop` (regra `pr-sync-base-before-link`; automação: `jarbas.py git-env pr-preview`). Preferir URL `pull/N` da ficha ou `gh pr list`; conflito de merge → reportar bloqueio, não link.

**PII:** mascarar CPF, e-mail, senhas nos resumos (referência Jarbas não importada: global.mdc).

---

## Passo 1b — Filtro a skill `governed-items-portfolio-analysis` (excluir já em `develop`)

**Obrigatório** para o a skill `governed-items-portfolio-analysis` (salvo pedido explícito de **panorama completo** / **incluir mergeados**).

| Passo | Ação |
|-------|------|
| 1 | `git fetch origin develop` no repositório de código (`repo/ebs-dominio_sgd` ou `code_root` na ficha). |
| 2 | Por ficha com branch `feature/item-*` ou `bugfix/item-*`: `git merge-base --is-ancestor <tip-da-branch> origin/develop` → **excluir** de B1/B2 se verdadeiro. |
| 3 | Se a branch local não existir, usar `origin/<branch>`; se ambas ausentes, **não** excluir só por git — usar status da ficha (PR `#N` mergeado, SHA em `develop`). |
| 4 | **1135** / **134**: excluir quando **135** / **132** estiverem excluídos (alias). |
| 5 | ITEMs **sem** entrega de código em `ebs-dominio_sgd` (épico **129**, **5000**, **6000**, **126** paridade sem PR): **manter** no panorama salvo ficha “fechado” sem trabalho pendente. |

**Saída:** em **A)**, linha `Excluídos — já em origin/develop (N): ITEM-…` (códigos separados por vírgula). Não gerar **B2** para excluídos.

Relatório só “fora develop” com impedimentos e fila PR: comando **`/items-abertos-develop`**.

---

## Passo 2 — Classificação de status (governança)

Mapear o campo **Status** / **Status paridade** da ficha. Se ausente, inferir **apenas** com evidência explícita no markdown:

| Bucket | Sinais na ficha |
|--------|------------------|
| **Em desenvolvimento** | “Em desenvolvimento”, critérios `[ ]` abertos, “DIVERGENTE implementação”, evidência “pendente” |
| **Pronto para PR / develop** | “Pronto para PR”, “Pronto para `develop`”, “Aprovado merge `develop`” |
| **Fechado (paridade/docs)** | “Fechado”, “CONFORME proto” sem PR de código, EXCEÇÃO documentada |
| **Bloqueado** | LACUNA SDD, PARIDADE-PRE BLOCKED, N/A credencial, aguardar PO |
| **Não classificado** | Sem sinais — marcar na tabela e não assumir “feito” |

### Pronto — definição do utilizador (PR / “itens prontos”)

Quando o utilizador diz **pronto**, **prontos para PR** ou pede **abrir PR dos prontos**, aplicar **somente** o contrato em item-pronto-definition.md (não inferir só pelo campo Status da ficha):

| Requisito | Verificação |
|-----------|-------------|
| Testes | relatório de verificação (`jarbas.py check`) ou run documentado **PASS** na ficha |
| Evidência | MATRIZ-EVIDENCIAS.md **APROVADA** + README.md + ficheiros no disco |
| Git | Branch `item-*` **não** ancestral de `origin/develop` |
| PR | Só após `git-env pr-preview` com sync `develop` sem conflito |

Listar explicitamente ITEMs que **falham** algum requisito (ex.: 113 — E2E não executado; 128-1 — já em `develop`, só governança).

**Fora de `develop` (filtro comum):** incluir tudo exceto ficha que declare merge concluído em `origin/develop` com evidência git; “Aprovado merge develop” **ainda conta** como fora até PR mergeado.

**Paridade (coluna separada):** último veredito em ficha ou matriz (`CONFORME` | `DIVERGENTE` | `LACUNA` | `N/A` | `NÃO VERIFICADO` | `EXCEÇÃO APROVADA`). Citar path da fonte.

### Passo 2c — Ordenação a skill `governed-items-portfolio-analysis` (incompleto → completo)

Atribuir **tier de completude** (0 = menos avançado). Ordenar **B1 e B2** por tier **ascendente**; dentro do tier, código numérico.

| Tier | Sinais (usar o **menor** tier que aplicar) |
|------|---------------------------------------------|
| **0** | **Bloqueado** sem implementação: planilha/escopo vazio, aguardar PO, LACUNA SDD **sem** código iniciado |
| **1** | **Governança criada** — ficha + paridade pré; **sem** commit/worktree/TST; matriz “a criar” |
| **2** | **Bloqueado** com diagnóstico ou fix parcial (credencial, Keycloak, FinOps) — código pode existir mas entrega **parada** |
| **3** | **Épico / runbook / infra doc** (ex. ITEM-129 sub-fichas) — operacional, sem branch `item-*` de produto |
| **4** | **Em desenvolvimento** inicial — simulação infra CA majoritariamente PENDENTE; ou bug **sem** relatório de verificação (`jarbas.py check`) |
| **5** | **Em desenvolvimento** — código no worktree; unit OK; **E2E ou matriz DEF-EVID incompleta** |
| **6** | **Legado / duplicata funcional** — superseded por outro ITEM; “pronto revisão” sem ser fila PR atual |
| **7** | **Fechado (paridade/docs)** — sem PR de código pendente; escopo encerrado na ficha |
| **8** | **Pronto para PR** — testes + DEF-EVID **APROVADA**, mas **bloqueio de integração** (conflito merge `develop`) |
| **9** | **Pronto para PR** — testes + evidência OK; branch **não** ancestral de `develop`; **sem** conflito documentado |

Não ordenar por código planilha se contradizer tier evidente na ficha + matriz + git.

---

## Passo 3 — Contrato de saída padrão (panorama)

Responder com **três blocos**, nesta ordem. **Escopo B1/B2:** apenas ITEMs que passaram o **Passo 1b** (a skill `governed-items-portfolio-analysis`).

### A) Resumo executivo (5–10 linhas)

### B) Índice + fichas

#### B1 — Tabela índice

**8 colunas.** Ordenar por **Passo 2c** (tier ascendente: incompleto → completo); desempate numérico no código.

| Coluna | Conteúdo |
|--------|----------|
| **Código** | `ITEM-###`; alias em nota curta |
| **Definição (resumo)** | **Obrigatório:** 1–2 frases do pedido (ITENS.md ou secção Definição da ficha); PII mascarada |
| **Status** | Bucket governança |
| **Paridade** | Veredito curto |
| **Branch** | Nome ou — |
| **Evidência** | Um link: ficha ou README.md |
| **Próximo passo** | Uma frase |

#### B2 — Subsecção por ITEM (`### ITEM-<codigo>`)

Primeira linha: **Definição (resumo):** …; depois ficha, tipo, status, paridade, branch, testes, evidências, próximo passo.

### C) Lacunas e riscos


---

## Passo 3b — Contrato **relatório expandido** (a skill `governed-items-portfolio-analysis`, `/items-abertos-develop`)

Template: item-relatorio-expandido.md.

Para **cada** ITEM no escopo do comando, secção:

| Campo | Conteúdo |
|-------|----------|
| **Código** | `ITEM-###` (+ alias planilha se houver) |
| **Descrição breve** | 1–2 frases da definição (não dump verbatim longo) |
| **Status** | Texto da ficha + bucket |
| **Paridade** | Veredito + fonte |
| **Branch / ROOT de código** | Branch sugerida; worktree ou `agregado` se documentado |
| **Testes / reteste** | relatório de verificação (`jarbas.py check`), spec E2E, último run se documentado |
| **Impedimentos** | Lista factual (LACUNA, build, credencial, E2E ausente, evidência DEF-EVID, etc.) |
| **Sugestão para derrubar** | Ações concretas (PO, FinOps, PR, `bootstrap-worktree`, matriz `CA-*`, SDD) |

Opcional: secção **Impedimentos transversais** (worktree, Docker E2E root, build web).

**Persistência (só se o usuário pedir gravar):** `repo/sgd-cursor-governance/items/RELATORIO-<slug>-<YYYYMMDD>.md` — não commitar sem pedido.

---

## Passo 4 — Qualidade do relatório

- [ ] **Passo 1b** aplicado para a skill `governed-items-portfolio-analysis`; excluídos listados em A); nenhum ITEM já em `develop` em B1/B2.
- [ ] **Passo 2c:** B1 e B2 ordenados do menos completo ao mais completo.
- [ ] B1 com coluna **Definição (resumo)** preenchida para cada ITEM; B2 começa com a mesma definição resumida.
- [ ] Ficheiros lidos nesta sessão; links de evidência verificados no disco.
- [ ] PII mascarada; não declarar “entrega aprovada” em modo diagnóstico.
- [ ] Paridade ≠ pedido informal do chat.

---

## Referências

- **governed-numbered-item-delivery** · **item-evidence-definition.mdc** (referência Jarbas não importada)
- Comandos:
- Entrega SGD: 
