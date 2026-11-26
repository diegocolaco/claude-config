# Investigador de logs (Datadog) e validação do relatório (passos 3 e 4)

Ler ao despachar o `error-evidence-investigator` ou ao validar o relatório recebido.

### 3. Despachar o investigador (rodada 1 — Datadog)
Incluir na entrada os traceIds e o horário da reprodução.

- **Direto:** `Task(subagent_type="error-evidence-investigator")` com o pedido abaixo.
- **Se esse tipo não estiver na lista do `Task`** (worktree, janela não recarregada):
  `Task(subagent_type="generalPurpose", model="gemini-3.5-flash")` com, antes do pedido: «Leia e siga integralmente
  `<pasta base>/.cursor/agents/error-evidence-investigator.md`. Modo SOMENTE LEITURA: não edite nem crie ficheiros, não use
  browser. Devolva APENAS o relatório, começando pela linha `[evidencia-erro]`.» O `Task` não tem parâmetro de só-leitura:
  a instrução no texto é obrigatória.
- **Não** trocar de modelo nem fazer a consulta no lugar do subagente (spec §11).

```text
[jarbas → error-evidence-investigator · JCMD-INVESTIGAR-ERRO-001]
trace_id: <trace_id> · Idioma: pt-BR
Pasta base: <raiz do checkout onde estão ecosystem/canonical/agents/library/ e a ficha>
Sintoma: <sem PII>
Janela BRT: <dd/mm/aaaa hh:mm> → <hh:mm> · Janela UTC: <ISO from> .. <ISO to>   (±10 min do relato ou da reprodução; sem horário: últimas 24 h)
Ação esperada: <MÉTODO + caminho no bff e no serviço dono, se conhecido>
Serviço suspeito: <dono da rota, se conhecido>
traceId: <do aviso/rede na reprodução, ou do relato humano, ou n/a>
Reprodução DEV: <resumo da matriz — quais usuários reproduziram e traceIds>
ITEM: <ITEM-<codigo> + ficha, ou n/a>
Rodada: <1|2>
```

### 4. Validar e guardar
Acrescentar o relatório do investigador ao **mesmo ficheiro do passo 2** (após `---` se já existir matriz). Rodada seguinte:
acrescentar ao fim uma linha `---` e a resposta nova **tal como veio** (a começar pela linha `[evidencia-erro]`). Depois validar:

Validação do relatório (checagem `evidencia-erro-check`; não há subcomando equivalente no `jarbas.py`, conferir o conteúdo manualmente): começa por `[evidencia-erro]`, traz Janela BRT e UTC, não contém CPF completo.

Validação falhou (exit 1 no check) → redespachar **uma vez** com os erros; segunda falha → tratar como `INCONCLUSIVO`. Ler também o conteúdo:
`## Lacunas de cobertura` com «nenhuma» quando o serviço dono não tem spans é erro do subagente → redespachar com essa correção.
