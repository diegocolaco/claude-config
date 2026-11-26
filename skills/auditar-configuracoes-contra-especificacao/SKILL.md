---
name: auditar-configuracoes-contra-especificacao
description: Use na revisão de um diff que alterou configuração do processo Jarbas, para conferi-lo contra a especificação.
---
CTX-ID: auditar-configuracoes-contra-especificacao@2

# Auditar configurações contra a especificação

Confronta o diff final e as evidências de uma mudança nas configurações Jarbas com os requisitos vigentes em 01-ESPECIFICACAO-JARBAS.md (fonte externa ausente no Squad; versão e `sha256` em jarbas-par-vigente.md). Nome anterior: `auditar-padrao-jarbas` (especificação 0.6). Na 0.7, confira também que os derivados orientam as condições de «Aplicação dos requisitos em cada ITEM» (PRE/revisão independente antes da implementação dependente, POST na revisão final, marcos DEV), separando checagem documental de acionamento real.

## Independência (inviolável)

- **Não** aprova o próprio trabalho de quem aplicou a mudança (`aplicar-especificacao-nas-configuracoes` ou equivalente).
- **Não** altera requisitos na especificação para eliminar divergência.
- **Não** cria sessão principal, sequência paralela de revisões nem exige leitura integral repetida da especificação quando só um recorte foi afetado.

## Quando acionar

| Acionar | Não acionar |
|---------|-------------|
| Revisão de diff que cria, altera ou remove skills, rules, agents, hooks, perfis, templates de instrução ou materializadores pertinentes | Entrega rotineira de produto sem mudança de configuração Jarbas |
| Fechamento de manutenção do processo no ponto de revisão já usado pelo jarbas (`reviewer` ou subagente independente) | Consulta ou auditoria de produto sem diff de config |

## Procedimento

1. Confirme versão adotada da especificação e autorização já válida para o recorte (sem nova confirmação genérica quando explícita).
2. Liste requisitos afetados (PAR08 e IDs citados no diff ou no registro da mudança).
3. Confronte diff final, derivados materializados e evidências de teste com esses requisitos.
4. Emita veredito: **CONFORME**, **DIVERGENTE_NAO_AUTORIZADA** ou **PENDENTE_EVIDENCIA** (teste ou revisão impedida por limitação real).
5. **DIVERGENTE_NAO_AUTORIZADA** bloqueia ativação do recorte; preserve o estado e encaminhe decisão (preservar requisito, evoluir especificação ou exceção permitida) — não reescreva a spec.

## Saída mínima

- Versão da spec usada na auditoria
- Requisitos verificados
- Veredito e achados por severidade
- Pendências que mantêm gate aberto

---
