# Vereditos, encerramento e falhas (passos 5 e 6)

Ler quando o investigador devolver o relatório, ao encerrar a resposta ou se Datadog/modelo falhar.

### 5. Agir pelo veredito

| Veredito | Ação |
|----------|------|
| `CONFIRMADO` | **`task-researcher`:** plano de regressão + matriz de variações para TEST/EXEC; explicar causa em linguagem simples (prova no relatório). <!-- GATE-1D-DESATIVADO-ITEM: início -->**Exceto** como etapa 1c de ITEM em: 1d/5b **desativado**, este passo não se aplica.<!-- GATE-1D-DESATIVADO-ITEM: fim --> Fora do ITEM, **antes** de tratar causa/correção como fechada: skill **`analysis-completeness-audit`** (rule homónima always-on) sobre o pacote veredito + relatório Datadog + plano do `task-researcher` → auditoria-completude-analise.md com `PASS` ou dispensa. Próximo passo: developer no worktree + `task-reviewer` com cobertura da matriz (ou fase 2). **Auditoria cadastro:** se PATCH/PUT 200 sem log, `task-researcher` ou sessão principal consulta UI/`GET /api/auditoria/eventos` (sgd-novo-auditoria-investigacao.md) e anexa eventos mascarados ao EVIDENCIA-ERRO.md |
| `DIVERGENTE` | Mostrar a diferença entre o relatado, a reprodução e os logs; perguntar como seguir (AskQuestion) |
| `SEM_EVIDENCIA` | Reprodução **sem** traceId: repetir **uma** ação focada com o usuário que mais se aproximou do sintoma; já há traceId na matriz → investigador **rodada 2** só com esse id. Ainda vazio → parar e perguntar (AskQuestion). Hipótese de correção só com ok explícito |
| `INCONCLUSIVO` | Explicar a lacuna; perguntar como seguir (AskQuestion) |

### 6. Encerrar
Resposta ao humano no formato da rule `communication-context` (coordenador) + modelo-investigacao.md
e investigacao-e-entrega.md. O veredito entra no texto em **palavras simples**; matriz de reprodução e relatório Datadog
são evidência complementar, **no fim**. EVIDENCIA-ERRO.md continua a ser gravado e validado como no passo 4. Com ITEM,
confirmar que o passo **2.7** (ficha + commit governance) foi feito — caso contrário:

```
[jarbas EVIDENCIA-ERRO BLOCKED] trace_id=<id> | motivo=registro_ficha_item_ausente | acao=completar passo 2.7
```

## Falhas

| Situação | Ação |
|----------|------|
| Datadog indisponível / autenticação / subagente sem conector | Entregar mesmo assim a **matriz de reprodução**; `[jarbas EVIDENCIA-ERRO BLOCKED] trace_id=<id> \| motivo=<falha> \| acao=humano decide`; AskQuestion: repetir Datadog / agente principal consulta e o subagente só analisa / seguir só com repro (`[jarbas WARN] evidencia-erro skipped by user`) |
| Gemini 3.5 Flash indisponível | **Não** trocar de modelo em silêncio; perguntar qual usar |

PII mascarada em tudo (`global`). Nos eventos do Keycloak o `username` é CPF; os caminhos logados trazem a query string.
