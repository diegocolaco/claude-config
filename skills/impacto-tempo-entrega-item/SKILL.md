---
name: impacto-tempo-entrega-item
description: Use quando mudar o fluxo de entrega ITEM (etapa, gate, /sgd-entrega) e for preciso estimar o impacto no tempo.
---
CTX-ID: impacto-tempo-entrega-item@3

# Impacto em tempo — mudança no processo de entrega de ITEM

Profile `sgd-novo`. Complementa `item-process-changelog` (o histórico regista o delta; esta skill calcula-o). Não substitui o harness nem autoriza saltar gate.

## Quando usar

Sempre que o Diego pedir para **mudar o processo** de entregar um ITEM do SGD novo, **antes de editar**:

| Pedido | Entra nesta skill |
|---|---|
| Etapa nova no fluxo de entrega, no harness ou no `item-test` | sim |
| Etapa, gate, regra ou comando **que já existe** e vai mudar (obrigatório, mais longo, mais curto, outra ordem, outro dono) | sim |
| Remover ou fundir etapa | sim |
| Paralelizar ou voltar a serializar | sim |
| Mudança que só corre quando o processo muda (documentar, estimar) e **não** entra em cada ITEM | sim — delta do ITEM = 0, com o motivo |
| Código de produto de um ITEM, bug de tela, ficha | não |

Alteração trivial e isolada (erro de digitação num doc de processo, sem etapa nem gate novo): uma linha «delta 0 no ITEM» chega. Não montar a tabela inteira.

## O que estimar

O número que o Diego pediu é o **tempo total de uma entrega de ITEM** no caminho feliz, não o tempo para escrever a rule.

| Conta | Entra no total do ITEM? |
|---|---|
| Etapa nova ou alterada que o ITEM passa **em série** no caminho crítico | sim |
| Etapa que corre **ao mesmo tempo** que outra já no caminho | só o que ultrapassa a etapa acompanhada |
| Remoção ou encurtamento | sim, delta negativo |
| Retrabalho **se** a etapa falhar e o ITEM voltar atrás | não — linha à parte, condicional |
| Fila: o passo segura a vaga de E2E e atrasa **outros** ITEMs | não no total deste ITEM — linha «fila» |
| Custo único de implementar a mudança de processo | não |
| Análise desta skill (só quando se pede mudança de processo) | não |

**Caminho crítico vigente** (harness, uma atrás da outra):

`BOOT → 1c EVIDÊNCIA-ERRO → DEF-AUDIT → ITEM → PARIDADE-PRE → EXEC → XPLAT → TEST (item-test, inclui deploy; dual conforme a Política de paridade) → DBGATE → GUARD → PARIDADE-POST → 11a DEF-EVID → REVIEW → 11b PR-FIRST → 11c DEV-REMOTO → HLTH`

DBGATE e XPLAT só entram no total quando o ITEM toca banco ou automação. 1c só em bugfix. DEF-AUDIT só com definição recebida. A etapa **1b CONFLICT-CHECK** saiu do caminho crítico em 2026-10-23 (desativada; só a pedido explícito). Dizer qual destes se aplica ao pedido.

## Procedimento

1. **Nomear cada mudança** do pedido (uma linha por etapa nova e uma por etapa que já existe e muda). Não juntar tudo num número só.
2. **Colocar no caminho** acima: onde entra, se é série, paralelo, condicional, fila ou custo único.
3. **Buscar base medida**, nesta ordem. Parar na primeira que existir:
   1. Duração medida de job, evidence ou PROC (citar `trace_id`, `job_id` ou `PROC-*` e o ficheiro). Fontes: `.tmp/evidence/<trace>/`, `.runtime/sgd/jobs/<job>/job.json`, `playwright-results.json`, secção 3 do histórico do processo.
   2. Etapa análoga já medida (dizer qual e a fonte).
   3. Nenhuma base → escrever **sem base medida**. Não converter «parece alguns minutos» em número. Dizer o efeito qualitativo (soma em série, sobrepõe, encurta, só na mudança de processo) e o que medir no próximo ITEM.
4. **Somar só o caminho crítico** do caminho feliz. Retrabalho, fila e custo único ficam fora dessa soma.
5. **Mostrar o bloco no chat** antes de editar. Se a mudança já está autorizada e é o próprio pedido em curso, o bloco sai na mesma resposta em que a alteração começa — não pedir confirmação só por causa do número.
6. **Copiar o total** para o campo **Impacto** da entrada PROC (`item-process-changelog`), com a base ou «sem base medida».

Proibido inventar minutos. A rule `mandatory-change-validation` e o fecho HLTH do harness também proíbem métrica sem fonte.

## Bloco para o chat

```markdown
### Impacto em tempo da entrega

| Mudança | Onde entra | No caminho crítico? | Delta por ITEM (caminho feliz) | Base |
|---|---|---|---|---|
| <etapa nova ou etapa alterada> | <gate ou fase> | série / paralelo / não | +N min, −N min, ou sem base medida | <fonte ou «sem base medida»> |

**Total no caminho crítico de um ITEM:** <soma, ou «sem base medida» se alguma linha da soma não tiver número>
**Fora desse total:** <fila de outros ITEMs / retrabalho se falhar / custo único de implementar — ou «nenhum»>
```

Várias mudanças: uma linha cada. O total é a soma das linhas «série» (e do excesso das linhas «paralelo»). Se uma linha da soma estiver «sem base medida», o total também fica «sem base medida» — não somar só as linhas que têm número e tratar isso como o total.

## Anti-padrões

| Errado | Certo |
|---|---|
| Inventar «+15 min» sem job, trace ou PROC | «sem base medida» + efeito qualitativo |
| Somar o tempo de escrever a rule ao tempo de cada ITEM | Custo único fora do total |
| Estimar só a etapa nova e calar a etapa que o mesmo pedido altera | Uma linha por mudança |
| Tratar retrabalho condicional como certeza no caminho feliz | Linha à parte |
| Esconder o bloco no histórico e não mostrar no chat | Chat primeiro; PROC copia o mesmo delta |
| Bloquear a mudança à espera de um «pode seguir?» | Mostrar o número e seguir, salvo o Diego ter pedido aprovação |

## Bloqueio

Mudança de processo de entrega de ITEM sem este bloco no chat:

```
[jarbas PROCESSO-TEMPO BLOCKED] trace_id=<id> | motivo=mudança de processo sem estimativa de tempo | acao=aplicar skill impacto-tempo-entrega-item e mostrar o delta do caminho crítico
```
