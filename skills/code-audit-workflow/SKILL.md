---
name: code-audit-workflow
description: Use quando pedirem auditoria de código ou revisão estruturada de um escopo (Mapeamento, Inspeção, Consolidação).
---
CTX-ID: code-audit-workflow@2

# Code Audit Workflow — Auditoria em 3 Fases

## Composição Superpowers

Auditoria jarbas em 3 fases; se o achado virar defeito ou causa raiz, o diagnóstico segue o Superpowers.

**REQUIRED BACKGROUND:** You MUST understand `superpowers:systematic-debugging` quando a auditoria passar de inventário para investigação de falha ou correção.

## Princípio

Antes de iniciar qualquer análise de auditoria, siga **obrigatoriamente** as três fases abaixo. Não pule nenhuma fase. Não encerre a análise sem completar o mapa de cobertura.

---

## FASE 1 — MAPEAMENTO (antes de ler qualquer código)

1. Liste todos os arquivos do escopo informado.
   **Escopo mínimo obrigatório (TaxProf/Onvio):** Controllers, Producers, Consumers, Interceptors,
   **e Services de domínio** (*Service.java) que contenham catch+throw.
   **Grep para descobrir:** `rg "catch.*throw new" --type java -l` — incluir todos os arquivos listados.
2. Para cada arquivo, crie uma entrada no mapa de cobertura com status: `[ ]` não inspecionado.
3. Defina quais categorias serão auditadas (cada uma com skill de referência):
   - `[ ]` **Error handling** — catch blocks, stack trace, cause preservada → `slf4j-catch-block-audit`, `business-logic-safety-audit`
   - `[ ]` **Logging** — Throwable como último arg, contexto estruturado → `slf4j-catch-block-audit`, `logging-pattern`
   - `[ ]` **Persistência** — status alterado é salvo? → `business-logic-safety-audit`, `logging-observability-gaps`
   - `[ ]` **Retornos silenciosos** — método retorna sem logar nem lançar? → `business-logic-safety-audit` (R2.4)
   - `[ ]` **Validação** — falha silenciosa ou com feedback? → `defensive-api-pattern`
   - `[ ]` **Cause no re-wrap** — exceção relançada passa original como cause? → `slf4j-catch-block-audit` (R2.3)
   - `[ ]` **Contexto em deserialização** — falha de parsing externa: status HTTP + preview do corpo? → `logging-pattern` (infra)
   - `[ ]` **Log em formato inválido** — catch de UUID/formato: há log para rastreabilidade? → `defensive-api-pattern` (Pattern 1)
   - `[ ]` **Dados sensíveis** — token, chave: hash/máscara, nunca expor? → `pii-log-safety`, `slf4j-catch-block-audit` (perg. 3)
     **Escopo obrigatório:** *RedisService, *CacheService, *AuthService, SmbCenterService, OauthInterceptor.
   - `[ ]` **Rethrow após log** — logar e relançar vs engolir; log.warn sem throw = swallow → `slf4j-catch-block-audit` (R2.1), `business-logic-safety-audit` (R2.4)
   - `[ ]` *[adicione categorias conforme o contexto]*

   **Skills em:** `ecosystem/shared/skills/<nome>/SKILL.md`

---

## FASE 2 — INSPEÇÃO SISTEMÁTICA

Para cada célula do mapa (arquivo × categoria):

- Inspecione o trecho relevante do arquivo.
- Marque a célula com um dos status:
  - `✅ ok` — sem problema
  - `⚠️ issue` — problema encontrado (descreva o problema e a linha/método)
  - `⏭️ skip` — fora do escopo (justifique)

**Condição de parada:** Só pode avançar para a Fase 3 quando **todas** as células tiverem um status. Células em branco não são permitidas.

---

## FASE 3 — CONSOLIDAÇÃO

Gere um relatório com:

1. Lista de issues encontrados, agrupados por categoria e severidade.
2. Mapa de cobertura final (arquivo × categoria × status).
3. Percentual de cobertura: `(células ✅ + ⚠️) / total de células`.
4. Itens que precisam de ação imediata (issues críticos).

---

## CHECKLIST DE ENCERRAMENTO

Antes de finalizar, responda sim ou não para cada item:

- Todos os catch blocks foram inspecionados?
- Todo log passa Throwable como último argumento onde aplicável?
- Todo retorno silencioso foi verificado?
- Toda exceção construída preserva a cause?
- Todo log de erro tem contexto estruturado?
- Todo status alterado é persistido?
- Toda exceção relançada passa a original como cause?
- Toda falha de deserialização externa loga status HTTP e preview do corpo?
- Todo catch de formato inválido tem log (mesmo em debug)?
- Nenhum log expõe dados sensíveis (token, chave) sem hash/máscara?
- Após log de erro, o código relança (não engole) a exceção?
- Em interceptors de HTTP: catch que não relança BusinessException — faz rethrow da exceção original (ou wrap com cause)?

**Se qualquer resposta for "não", retorne à Fase 2 e complete a cobertura.**

---

## Integração com o ecossistema

- **Regra:** `ecosystem/canonical/rule/code-audit-agent/content.md` — aplicada quando o utilizador pede auditoria sistemática.
- **Sentinel:** Este workflow é executado pelo Sentinel em tarefas de `review` com sinal de auditoria.
- **Logging/Controllers:** Alinhado a `ecosystem/canonical/rule/logging-observability-controllers/content.md`.

### Skills de referência (por categoria)

| Categoria | Skill(s) |
|----------|----------|
| Error handling, Logging, Cause re-wrap, Rethrow | `slf4j-catch-block-audit` |
| Persistência, Retornos silenciosos, Rethrow | `business-logic-safety-audit` |
| Validação, Log formato inválido | `defensive-api-pattern` |
| Contexto deserialização | `logging-pattern` (infra) |
| Dados sensíveis | `pii-log-safety` |
| Checklist geral L1/L2/L3 | `logging-observability-gaps` |

**Caminho:** `ecosystem/shared/skills/<nome>/SKILL.md`
