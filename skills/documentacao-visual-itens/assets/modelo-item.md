# Modelo — documentação visual de ITEM (trajetória)

Vincular sempre à **ficha oficial** do ITEM; este modelo é camada didática, não substitui `item-<codigo>.md` / plano governado.

```markdown
# Trajetória visual — ITEM-###

> Ficha oficial: [link relativo] | trace_id principal: … | Atualizado: AAAA-MM-DD

## Resumo em 30 segundos

…

## Contexto

- **Objetivo do item:** …
- **Tipo:** erro | melhoria | funcionalidade
- **Estado atual (ficha):** …

## Mapa visual da trajetória

### Fluxograma (o que de fato ocorreu)

```mermaid
…
```

### Legenda

…

### Sequência em texto

1. …

## Marcos com evidência

| Marco | Data | O que aconteceu | Evidência (path / comando) | Estado |
|-------|------|-----------------|----------------------------|--------|
| Investigação | | | | confirmado / não verificado |
| Implementação | | | | |
| Testes | | | | |
| Revisão | | | | |
| E2E / DEV remoto | | | | só se aplicável e verificado |

## Etapas explicadas (alinhadas ao mapa)

### …

## Exemplo / walkthrough

Usar dados reais do ITEM ou marcar `(trecho fictício para clareza)`.

## Como retomar

- Pendências: …
- Próximo passo oficial (harness): …

## Glossário

…

## Rastreabilidade e revisão

- **Fontes conferidas:** ficha, EVIDENCIA-ERRO, PR, logs — só os existentes
- **Limites / lacunas:** …
- **Revisado em:** …
- **Status da revisão:** …
```
