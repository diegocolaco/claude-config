---
name: diario-experiencias-atividades-sgd
description: Use com /registro-atividades, /experiencia-sgd ou ao atualizar o diário de experiências e atividades do SGD novo.
---
CTX-ID: diario-experiencias-atividades-sgd@1

# Diário — experiências e atividades diárias (SGD novo)

**Ficheiro (único):** doc-experiencias-atividades-diarias-sgd-novo.md

**Comandos Cursor:** a própria skill `diario-experiencias-atividades-sgd` — este skill é a **fonte de procedimento**; os comandos só disparam o fluxo.

## Gatilhos (invocar este skill **antes** de editar o ficheiro)

- Utilizador aciona a skill `diario-experiencias-atividades-sgd` com texto na mesma mensagem.
- Pedido explícito: «atualiza o diário», «regista no diário», «experiências e atividades», «resumo do dia».
- Fecho de sessão quando o utilizador pediu **registo automático** do que foi feito no chat (só factos desta conversa; **não inventar**).

**Fora de escopo deste skill:** abrir ITEM, corrigir código, alterar processo ou specs — só append no diário.

## Classificar cada bullet

| Prefixo | Quando usar |
|---|---|
| **`EXP-`** | Experiência, percepção, impedimento, padrão recorrente, gap, lição, risco observado |
| **`ATD-`** | Atividade concreta do dia: PR mergeado, foco, daily preparada, investigação feita, entrega, logística |

Uma mensagem pode gerar **vários** bullets (EXP e ATD separados). Melhorar redação; **nunca** acrescentar factos que o utilizador não disse.

## Pendências comigo (início do ficheiro)

- A secção **`## Pendências comigo`** (logo após a introdução) é a **lista viva** do que depende do utilizador.
- **Atualizar** quando ele pedir novas pendências, fecho de item ou o acionamento desta skill com foco em pendências — **sem apagar** o histórico por data.
- Entradas `EXP-` / `ATD-` por dia continuam no **fim** (append cronológico).

## Procedimento (sempre igual)

1. **Ler** o ficheiro completo (ou desde a última secção `## AAAA-MM-DD`).
2. **Data** da entrada: hoje (timezone do utilizador) ou a data que ele indicar.
3. **Secção:** se não existir `## AAAA-MM-DD` (opcional: «— manhã/tarde/noite»), criar **no fim** do ficheiro.
4. **Subsecção** `### …` curta (tema), só se agrupar vários bullets; senão usar subsecção genérica «Experiências» ou «Atividades do dia».
5. **Próximo id:** para cada prefixo (`EXP` / `ATD`), `NN` = maior `NN` já usado **nessa data** nesse prefixo + 1 (ler o ficheiro; não adivinhar).
6. **Append** bullets no formato: `- **\`EXP-2026-10-07-03\`** — …`
7. **PII:** mascarar CPF, CNPJ, e-mail, token (referência Jarbas não importada: global.mdc).
8. **Não editar** entradas antigas (corrigir typo só se o utilizador pedir explicitamente).
9. **Commit** no playground (worktree + merge agregado; regra `playground-commit-required`) — o pedido de registo **autoriza** commit só deste ficheiro e artefactos desta skill/comando se tocados.

## Modo automático a partir do chat

Quando o gatilho for «regista o que fizemos» / resumo do dia **sem** texto longo do utilizador:

1. Listar só **factos verificáveis** da conversa ou comandos corridos (ex.: «criou skill X», «merge PR #N») — **ATD**.
2. Se houver **conclusão ou padrão** novo sobre o projeto → **EXP** (uma linha).
3. Se não houver conteúdo registável, **perguntar uma vez** o que registar (não append vazio).

## Ligações opcionais (uma linha no bullet, sem abrir outro fluxo)

- Regressão após paridade/sync → sugerir livro-razão **`PRG-*`**.
- Não criar PRG nem ITEM daqui.

## Verificação antes de encerrar

- [ ] Ficheiro certo (doc-experiencias-atividades-diarias-sgd-novo.md)?
- [ ] Ids `EXP`/`ATD` com sequência correta na data?
- [ ] Nenhum PII em claro?
- [ ] Commit playground feito?
