---
etapa: "02"
status: concluida
alvo:
  - caminho: regras-agente.md
    sha256: c234ac4685ec8d4164b22ebc2f624a543d05d83ca04327c26286638c9f6bf077
commit_base: desconhecido
data: 2026-10-30
motivo_status: ""
---

# Reescrita: regras-agente.md

## Base
Investigação concluída em 01-investigacao.md.

## Falhas críticas e pontos cegos
### F1 — exceção "urgente" libera push na main (critica)
Diretivas: D4. Cenário: o usuário diz "é urgente" e o agente faz push na `main`.
### F2 — flag inexistente (alta)
Diretivas: D7. Cenário: o agente sugere `--auto-approve-all` e o comando falha.
### F3 — carregamento de subdiretórios negado (media)
Diretivas: D6. Cenário: regras de módulo acumuladas na raiz.
### F4 — regra de testes duplicada (baixa)
Diretivas: D5, D9.

## Rastreio de mudanças
| Mudança | Diretiva | Falha | O que mudou |
|---|---|---|---|
| M1 | D4 | F1 | exceção reescrita |
| M2 | D7 | F2 | flag substituída |
| M3 | D6 | F3 | carregamento corrigido |
| M4 | D5, D9 | F4 | unificadas |

## Diretivas preservadas
D1, D2, D3, D8.

## Orçamento
Original: 26 linhas. Proposta: 25 linhas.
