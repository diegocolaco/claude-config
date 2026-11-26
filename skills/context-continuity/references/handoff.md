# HANDOFF — transportar uma descoberta entre frentes

Quando: uma descoberta ou decisão desta frente muda o trabalho de outra. O utilizador não deve ter de lembrar qual chat precisa de saber.

## Procedimento

1. Confirmar o impacto: a outra frente decidiria ou faria algo diferente se soubesse? Se não, não há handoff.
2. Localizar os pontos de inserção pelo mapa de cabeçalhos (SKILL.md), sem ler o ficheiro inteiro. Acrescentar em `## Handoffs pendentes`, com o controlo de concorrência de `state-management.md`:

```markdown
### H-### · <origem> → <destino[, destino2]> · AAAA-MM-DD
Impacta: <destino[, destino2]>
- Descoberta/decisão: <o que foi identificado, 1–2 linhas>
- Por que importa: <efeito concreto na frente destino>
- Ação necessária: <o que o outro chat deve considerar ou fazer>
- Fonte: <ponteiro opcional: ficheiro, teste, D-###>
```

3. Acrescentar a linha em `## Dependências entre frentes` (`<destino> ← <origem>: <motivo> (H-###)`) e, se bloquear o destino, a coluna "Bloqueado por" no Índice.
4. Avisar o utilizador numa linha: `Handoff H-003 registado: spec precisa de rever o critério X (descoberto em playwright).`

## Consumo (no chat da frente destino)

O RESTORE do destino mostra o handoff em primeiro lugar. Depois de o integrar (decisão tomada ou pendência criada na frente destino), remover o bloco `H-###` e a dependência que deixou de valer, e anexar uma linha ao arquivo (`state-management.md` § crescimento).
