---
name: investigar-erro
description: Use quando houver erro no DEV remoto do SGD novo (404, toast, traceId) ou /investigar-erro, antes de propor correção.
---
CTX-ID: investigar-erro@10

# Investigar erro — reprodução primeiro, depois evidência (SGD novo, DEV remoto)

## Composição Superpowers

Esta skill **soma** obrigações jarbas/domínio (DEV remoto, Datadog, EVIDÊNCIA-ERRO) ao processo oficial; **não** dispensa nem substitui o Superpowers (jarbas-superpowers-fronteira.md).

**REQUIRED BACKGROUND:** You MUST understand `superpowers:systematic-debugging` — fases 1–3 (evidência e hipótese) antes de propor correção; esta skill detalha **como** recolher prova no SGD novo (matriz DEV, investigador, veredito).

## Visão geral

Um erro só é investigado quando foi visto acontecer: reproduzir no DEV com todos os usuários de QA disponíveis gera os traceIds que tornam a busca no Datadog precisa e impede que uma hipótese vire «causa» sem prova. Cada etapa alimenta a seguinte (matriz → ficha → janela de logs → veredito) e a correção só começa depois do veredito.

Profile **`sgd-novo`**. Este ficheiro espelha o conteúdo normativo do comando `JCMD-INVESTIGAR-ERRO-001`, para a política valer **mesmo sem o comando carregado** (gate 1c e 11c da skill `validar-comportamento-dev-prototipo`). Os gates invioláveis estão na rule investigar-erro.md — ler junto; em conflito, vale a autoridade/vigência canônicas (jarbas-superpowers-fronteira.md).

Fontes: spec 2026-10-01-investigar-erro-evidencia-design.md (emenda 2026-10-15: reprodução antes do Datadog) · mapa do DEV sgd-novo-dev-datadog.md · auditoria sgd-novo-auditoria-investigacao.md · usuários QA sgd-novo-dev-usuarios-validacao-item-161.md + doc-credenciais-acesso.md § «Smoke ITEM-161» · ficha investigar-erro-registro-ficha-item.md (passo 2.7).

## Quando usar

Erro do SGD novo no **DEV remoto** (`env:dev`, `https://dev.sgd.dominiosistemas.com.br`): sintoma de tela, aviso com `traceId`, 5xx/403/404, «no DEV não funciona», retorno de testador com falha. Uso: `investigar-erro <sintoma, tela, ação, horário, traceId do aviso se houver, ITEM se houver>`.

## Regras que valem sempre

- **Ambiente:** «investigar um erro» = **DEV remoto**. Nunca os slots locais, salvo pedido explícito do humano.
- **Ordem fixa:** relato → (opcional `localizador-cenarios-teste` se faltar registro/usuário) → reprodução multi-usuário no DEV (gravar matriz) → ficha ITEM passo 2.7 → Datadog → só então correção de código.
- **Trava:** nenhuma proposta de correção, edição de código ou hipótese apresentada como causa **antes** do veredito do investigador (rodada Datadog), com a matriz de reprodução já registrada. `SEM_EVIDENCIA`: hipótese de correção só com ok explícito. Pedido de «corrija já» não suspende a trava.
- **Autonomia:** o agente reproduz **sozinho**; não pede ao humano que abra navegador, janela anônima ou faça login. Acesso por **personificação no Keycloak** (rule `testes-personificacao-keycloak`), sem login CPF+senha.
- **Usuários:** percorrer **todos os usuários de QA disponíveis** (a ficha pode indicar um prioritário: tentar esse primeiro); os indisponíveis entram na matriz. Escalar ao humano só após 2 tentativas por usuário, nenhum CPF resolvido ou `[jarbas PERSONIFICACAO BLOCKED]`.
- **Gravação no DEV:** liberada sem aprovação, **exceto na empresa Dominio**; prefixo `ZZ-TESTE-<trace_id>`; listar o que foi gravado.
- **PII mascarada** em tudo (`global`); CPF completo em qualquer ficheiro falha a validação. Nos eventos do Keycloak o `username` é CPF e os caminhos logados trazem a query string.
- **Smoke** = roteiro mínimo de acesso + ação do relato com personas documentadas, **não** teste sem evidência. E2E automatizado complementa a reprodução em DEV, não a substitui.

Detalhe de personificação, troca de sessão e lista de usuários: `references/execucao-dev.md` (ler antes de reproduzir).

## Referência rápida

| Etapa | Artefato de prova | Bloqueio |
|---|---|---|
| 1 Relato | `trace_id` + horário BRT (pergunta única se faltar) | — |
| 2 Reprodução multi-usuário | `## Reprodução DEV (multi-usuário)` no início de EVIDENCIA-ERRO.md (ou `.tmp/<trace_id>/evidencia-erro.md`) | `[jarbas EVIDENCIA-ERRO BLOCKED]` (todos bloqueados por infra/login) |
| 2.7 Registro na ficha (com ITEM) | subsecção «Reprodução DEV — contexto QA» + commit de governança | `[jarbas EVIDENCIA-ERRO BLOCKED] motivo=registro_ficha_item_ausente` |
| 3 Investigador (Datadog) | relatório iniciado por `[evidencia-erro]`, com janela BRT e UTC no pedido | `[jarbas EVIDENCIA-ERRO BLOCKED]` (Datadog/modelo indisponível) |
| 5 Veredito | `CONFIRMADO` / `DIVERGENTE` / `SEM_EVIDENCIA` / `INCONCLUSIVO` | trava: sem hipótese de causa antes do veredito |
| 5b ANALYSIS-COMPLETENESS | <!-- GATE-1D-DESATIVADO-ITEM: início -->**Só fora do ITEM**<!-- GATE-1D-DESATIVADO-ITEM: fim --> · `.tmp/<trace_id>/auditoria-completude-analise.md` (`PASS`) após `CONFIRMADO` | `[jarbas ANALYSIS-COMPLETENESS BLOCKED]` (só fora do ITEM) |
| 6 Encerrar | resposta em linguagem simples + passo 2.7 confirmado | `[jarbas EVIDENCIA-ERRO BLOCKED]` |

## Procedimento (agente principal)

1. **Relato.** Extrair sintoma, horário BRT, traceId e ITEM; faltando horário ou ação, perguntar **uma vez**, tudo junto. Gerar `trace_id` (`jarbas-YYYYMMDD-HHMMSS-xxxx`). Relato com quantificador («alguns», «vários», «todos», exemplo) descreve uma **classe**: levantar o universo afetado antes de reproduzir (`## Universo afetado`, sem PII). Detalhe: `references/reproducao-e-ficha.md`.
2. **Reprodução multi-usuário no DEV** (obrigatória, antes do Datadog): para cada usuário disponível, personificar → conferir `/api/auth/me` → repetir a ação do relato → registrar na matriz (reproduziu? sim/não/n.a. · traceId UI/rede · nota/screenshot · bloqueio). Persistir a matriz **no início** de `repo/sgd-cursor-governance/items/<codigo>/evidence/EVIDENCIA-ERRO.md` (ou `.tmp/<trace_id>/evidencia-erro.md`) sob `## Reprodução DEV (multi-usuário)` **antes** de despachar o investigador. Todos bloqueados por infra/login → `[jarbas EVIDENCIA-ERRO BLOCKED] trace_id=<id> | motivo=<...> | acao=...`; senão seguir mesmo com repro parcial.
   - **2.7 Registro na ficha** (obrigatório com `ITEM-<codigo>`): subsecção «Reprodução DEV — contexto QA» em `item-<codigo>.md`, espelho no README da pasta `evidence` do ITEM e **commit** na governança **antes do passo 3**. Sem ITEM: `.tmp/<trace_id>/reproducao-dev-contexto.md`. Detalhe: `references/reproducao-e-ficha.md`.
3. **Investigador (rodada 1 — Datadog).** Despachar `error-evidence-investigator`, somente leitura, com traceIds e horário da reprodução e janela em **BRT e UTC**; não trocar de modelo nem consultar no lugar dele. Pedido-modelo e fallback: `references/investigador.md`.
4. **Validar e guardar.** Relatório vai ao mesmo ficheiro do passo 2 (após `---`); validar (`evidencia-erro-check`); redespachar uma vez se falhar. Detalhe: `references/investigador.md`.
5. **Agir pelo veredito.** `CONFIRMADO` → `task-researcher` monta plano de regressão + matriz de variações, causa explicada em linguagem simples, depois developer + `task-reviewer`; `DIVERGENTE` e `INCONCLUSIVO` → mostrar a lacuna e perguntar como seguir; `SEM_EVIDENCIA` → rodada 2 só com o traceId da matriz, ou parar e perguntar. Tabela completa, auditoria de cadastro e 5b: `references/vereditos-e-encerramento.md`.
6. **Encerrar** em linguagem simples (formato da rule `communication-context`; veredito em palavras simples, matriz e relatório Datadog como evidência no fim) e confirmar o passo 2.7: caso contrário `[jarbas EVIDENCIA-ERRO BLOCKED] trace_id=<id> | motivo=registro_ficha_item_ausente | acao=completar passo 2.7`. Falhas (Datadog/modelo indisponível): `references/vereditos-e-encerramento.md`.

## Referências (ler só quando o passo pedir)

- `references/execucao-dev.md` — personificação, troca de sessão, gravação, escalada, lista de usuários de QA.
- `references/reproducao-e-ficha.md` — relato, universo afetado, matriz, passo 2.7.
- `references/investigador.md` — pedido ao investigador, fallback, validação do relatório.
- `references/vereditos-e-encerramento.md` — ação por veredito, 5b, encerramento, falhas.
- `references/orquestracao.md` — papéis (orquestrador, worker, `task-researcher`, investigador); analista obrigatório antes de propor correção em casos mistos, `CONFIRMADO`, `DIVERGENTE`/`INCONCLUSIVO`.
- `references/glossario-e-composicao.md` — glossário, relação com `/sgd-entrega` (1c, 11c), `/diagnostico-causa-raiz`, `validar-comportamento-dev-prototipo`, erros comuns.

Erros comuns: tratar 2.7 como «consultar a ficha» (é escrever e commitar antes do Datadog); parar após «mais de um perfil» (percorrer todos os disponíveis); despachar o investigador sem janela UTC e sem validar.

Relacionado: investigar-erro.md (gates) · `analysis-completeness-audit` (5b) · validar-comportamento-dev-prototipo.md · subagente `error-evidence-investigator` (`ecosystem/canonical/agents/library/`).
