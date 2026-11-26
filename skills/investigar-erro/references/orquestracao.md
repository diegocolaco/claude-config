# Orquestração e analista

Ler ao decidir quem executa cada passo ou antes de propor correção/avançar para EXEC/TEST.

## Orquestração e analista

| Papel | Modelo / agente | Quando |
|-------|-----------------|--------|
| Orquestrador (chat) | Composer 2.5 Standard | Coordenar, browser no DEV (passo 2), validar `evidencia-erro-check`, consolidar |
| Worker | `jarbas-worker-composer` | Passos mecânicos: persistir matriz já definida, commit governance, `evidencia-erro-check` |
| **Analista** | **`task-researcher`** | **Obrigatório** antes de propor correção ou avançar para EXEC/TEST quando: matriz multi-usuário com resultados **mistos** ou traceIds **divergentes**; escolher janela/serviço dono para Datadog; veredito **`CONFIRMADO`** → plano de **regressão + matriz de variações** (tipos PF/PJ, raiz×filho, perfis, ≥1 negativo) para developer/`task-reviewer`; **`DIVERGENTE`** / **`INCONCLUSIVO`** / 2.ª rodada Datadog; trilha de **auditoria** quando PATCH/PUT 200 sem log (sgd-novo-auditoria-investigacao.md) |
| Investigador logs | `error-evidence-investigator` (Gemini 3.5 Flash) | **Só** passo 3 (Datadog), somente leitura — **não** substituído pelo especialista |

O analista **não** executa browser nem consulta Datadog no lugar do investigador; entrega plano/matriz/hipótese com evidência
por caminho (≤40 linhas) para a sessão principal integrar em EVIDENCIA-ERRO.md e na ficha ITEM (2.7).
