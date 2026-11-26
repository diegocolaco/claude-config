---
name: analises-documentadas
description: Use quando pedirem análise (gargalo, causa, comparação, auditoria, levantamento) com conclusões em user-doc/analises-documentadas.
---
CTX-ID: analises-documentadas@5

# Análises documentadas em `user-doc/novo-sgd/`

## Composição Superpowers

Grava a análise; **não** a substitui. Análise de causa ou lentidão segue o método do Superpowers antes de ser documentada.

**REQUIRED BACKGROUND:** You MUST understand `superpowers:systematic-debugging` — documentar só causa com evidência, não hipótese.

**Projeto:** TR Jarbas Ai Multi-agents squad

Escolha do modelo (resposta do Diego, verbatim, mesmo dia, ao saber que o Sonnet 5.5 medium não estava disponível):
*"Use um modelo eficiente em documentar de baixo custo, mas eficiente para esse tipo de tarefa. Verifique no
benchmark do cursor ide atualizado"* — ver secção **Modelo**.

Esta skill decide **quando** e **o quê**. **Onde** gravar e o formato base vêm da skill `documentar-user-doc`.

Se o rascunho tocar segurança, negócio confidencial, PII ou infra sensível, aplicar também a skill **`documentar-seguranca-gate`** (mesmo sem o pedido «documente») antes de gravar.

## Quando usar

Análise = resposta que tira uma conclusão de medição, leitura de código/logs ou investigação. Exemplos:

- gargalos de um processo (ponta a ponta, E2E, fila de ITEMs, deploy, build, publicação);
- "por que demora", "onde está o tempo", "vale a pena", "é eficiente?", comparação antes × depois;
- causa de erro ou de regressão, auditoria, levantamento, inventário, análise de recursos da máquina.

Vale **sem** o Diego dizer "documente". Não se aplica a: pergunta trivial respondida em 1–2 linhas, conversa, ou
implementação sem análise (essa fica na ficha do ITEM e no commit).

Se outra skill já conduz a análise (`wsl-ubuntu-resource-analysis`,
`governed-items-portfolio-analysis`, a skill `investigar-erro`, …), ela continua a mandar no
método; esta skill entra para gravar o resultado. Relatórios técnicos que essas skills já gravam (ex.:
EVIDENCIA-ERRO.md) não mudam: o documento em `user-doc/` é a versão legível e aponta para eles.

## Quando gravar (marcos)

O chat pode ser apagado a meio, por isso o documento nasce cedo:

1. **Análise curta** (uma rodada): gravar no fim, **antes** da resposta final.
2. **Análise longa** (várias rodadas, medições demoradas, pausa à espera do Diego): gravar logo que houver o
   primeiro achado com número, e atualizar o **mesmo** documento a cada marco (nova medição, causa confirmada,
   decisão do Diego, fecho).
3. **O Diego pausa** ("depois continuamos"): gravar o estado e como retomar antes de parar.

## Antes de implementar a partir da análise

Se as conclusões do documento (ou do chat que o alimentou) vão orientar **código**, **processo** ou **correção**:
aplicar a rule always-on **`analysis-completeness-audit`** e a skill homónima **depois** de gravar em `user-doc/` e
**antes** de EXEC / developer / plano de correção fechado. O relatório em `user-doc/` não dispensa o artefato
`.tmp/<trace_id>/auditoria-completude-analise.md` quando a rule aplicou.

## Procedimento

### 1. Destino

Seguir a ordem da skill `documentar-user-doc` (documento vivo → tema existente → tema novo → relatório). Antes de
criar ficheiro novo, procurar se o mesmo processo já foi analisado:

```bash
rg -il "<processo ou palavra-chave>" user-doc/novo-sgd/relatorios user-doc/novo-sgd/temas
```

- **Mesmo processo já analisado** (ex.: desempenho do ponta a ponta → `temas/e2e-desempenho/`): documento novo
  datado no tema, com secção **Comparação com a análise anterior** (o que melhorou, piorou ou ficou igual, em
  números), e o README.md do tema atualizado. Não criar um segundo relatório solto sobre o mesmo assunto.
- **Segunda análise de um assunto que só tinha relatório solto** → criar o tema, mover o relatório antigo para lá
  (com as referências atualizadas, regra de "não mover" da `documentar-user-doc`).
- **Primeira análise** → `relatorios/AAAA-MM-DD-<assunto>.md`.

### 2. Pacote de análise (o agente principal monta)

Tudo o que só existe no chat perde-se com ele. O pacote leva **todo** o conteúdo necessário para entender, refazer
ou continuar a análise, com PII já mascarada (referência Jarbas não importada: global.mdc):

| Campo | Conteúdo |
|---|---|
| Pedido | texto do Diego **verbatim** e a pergunta que a análise responde |
| Método | o que foi medido, comandos ou consultas, janela de tempo, ambiente (slot, DEV remoto, máquina) |
| Números | todas as medições com a fonte (comando, log, job, relatório) — sem arredondar o que muda a conclusão |
| Achados | cada gargalo ou conclusão por ordem de impacto: impacto medido, evidência, causa; fato separado de inferência |
| Recomendações | ação, quem faz, ganho estimado (dizer que é estimativa), risco, esforço |
| Decisões | pergunta feita e resposta do Diego verbatim |
| Estado | vocabulário da `communication-context` · o que falta · quem faz · como retomar |
| Anterior | se o processo já foi analisado: caminho do documento anterior e os números dele a comparar |
| Repetir | comandos e caminhos para refazer a medição e comparar depois |
| Evidência | commits, jobs, trace_id e o **caminho** de cada relatório e log citado (código de job sem caminho não se localiza depois) |
| Destino | caminho do documento, se é novo ou atualização, e o README.md a atualizar |

### 3. Escrita pelo subagente

Um único subagente leve (sem medição de capacidade):

```
Task(subagent_type="generalPurpose", model="<slug da secção Modelo>", description="Documentar análise")

[jarbas → documenter]
trace_id: <id>
Idioma: pt-BR
Task: gravar a análise abaixo em <caminho> no worktree <.worktrees/wt-...>, seguindo a skill
  ecosystem/canonical/skills/documentar-user-doc/content.md e o modelo de documento da skill analises-documentadas;
  atualizar <README.md da área e do tema>. Não commitar.
Regras: documento autocontido (entende-se sem o chat); copiar números e citações sem alterar; não inventar
  nada que não esteja no pacote — lacuna vira "não medido"; PII mascarada; UTF-8 sem U+FFFD.
Pacote: <pacote da etapa 2>
Expected output: caminhos gravados e lista de lacunas encontradas no pacote.
```

O worktree do playground é criado (ou reutilizado) pelo agente principal antes de despachar:
`bash ecosystem/automation/playground/bootstrap-playground-worktree.sh <slug> feature`.

### 4. Conferência (agente principal)

Ler o documento gravado e conferir: números e citações iguais ao pacote; entende-se sem o chat; achados por
impacto; estado e próximos passos explícitos; README.md atualizado; PII mascarada; sem U+FFFD. Divergência →
devolver ao mesmo subagente com a lista do que corrigir (uma vez); persistindo, corrigir diretamente.

### 5. Commit e integração

Commit no worktree (regra `playground-commit-required`, sem pedir permissão); merge local com `merge-worktree-to-agregado.sh` quando o humano escolher integrar.
Documento que fica para trás sem commit não sobrevive à limpeza de worktrees — o commit faz parte da garantia.

### 6. Resposta ao Diego

A resposta continua autocontida (`communication-context`); no fim, uma linha com o caminho do documento. Na
Evidência técnica:

```
[jarbas ANALISE-DOC] trace_id=<id> | doc=<caminho> | acao=<novo|atualizado> | modelo=<nome> | commit=<sha do merge>
```

## Modelo do subagente

Escolhido pelo CursorBench 4.0 (benchmark oficial do Cursor, <https://cursor.com/cursorbench>, atualizado em
10/09/2026; consultado em 07/10/2026), cruzado com os modelos que o runtime oferece para subagentes:

| Modelo | Disponível como subagente | CursorBench | Custo / tarefa |
|---|---|---|---|
| **Sonnet 5.5 Medium** (pedido original do Diego) | não (07/10/2026) | 39,2% | US$ 0,70 |
| **Sonnet 5.5 High** (`claude-sonnet-5-5-high`) | sim | 47,8% | US$ 1,67 |
| Composer 2.5 (`composer-2.5-fast` é a variante rápida, mais cara por token) | sim | 27,7% | US$ 0,68 (variante normal) |
| Sonnet 5 Medium (`claude-sonnet-5-thinking-medium`) | sim | 28,0% | US$ 2,31 |
| GPT-5.6 Luna Medium (`gpt-5.6-luna-medium`) | sim | 22,2% | US$ 0,08 |

Regra:

1. Usar **Sonnet 5.5 Medium** quando aparecer na lista de modelos do runtime.
2. Enquanto não aparecer, usar **Sonnet 5.5 High** (`claude-sonnet-5-5-high`): mesma família pedida, melhor nota
   entre os disponíveis com custo baixo. O Composer 2.5 Fast custa US$ 3 / US$ 15 por milhão de tokens (entrada /
   saída), acima do Sonnet 5.5 (US$ 2 / US$ 10), e tem nota menor; o Luna Medium é barato mas fraco para texto
   autocontido com regras de formato.
3. Nenhum dos dois disponível: **não trocar em silêncio** — perguntar ao Diego (AskQuestion) qual usar.
4. Benchmark novo com outra ordem de custo × nota: propor a troca ao Diego antes de mudar esta tabela.

## Modelo de documento

Base da `documentar-user-doc`, com estas secções:

```markdown
# <Processo analisado> — <pergunta respondida> (<DD/MM/AAAA>)

Projeto: TR Jarbas Ai Multi-agents squad · trace: `<trace_id>`

Pedido do Diego (verbatim): «…»

## Resumo
<3–6 linhas: os maiores gargalos/conclusões com o número principal de cada um e o estado atual>

## Como foi analisado
<método, ambiente, janela, comandos; o que ficou de fora>

## Achados (por impacto)
| # | Achado | Impacto medido | Evidência | Causa (fato / inferência) |

## Recomendações
| Prioridade | Ação | Quem | Ganho estimado | Risco / esforço |

## Comparação com a análise anterior
<só se o processo já foi analisado: antes × agora em números>

## Estado atual e próximos passos
<estado · o que falta · quem faz · como retomar>

## Como repetir esta análise
<comandos/passos para medir de novo e comparar>

## Onde está a evidência
<commits, jobs, traces, caminhos>

```

## Exceções

- O Diego pede para não documentar → `[jarbas WARN] analise sem documentacao por pedido do utilizador | trace_id=<id>`.
- Quem fez a análise é um **subagente**: não documenta; devolve o pacote (etapa 2) no relatório ao jarbas, que
  aplica esta skill.
- Ferramenta Task indisponível → o agente principal escreve seguindo o mesmo modelo e regista
  `modelo=agente-principal (Task indisponível)` na linha `[jarbas ANALISE-DOC]`.
- Análise de outra área (ex.: SGD legado) → área decidida pela `documentar-user-doc`; o resto desta skill vale igual.
