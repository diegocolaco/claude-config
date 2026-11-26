# Modelo — documentação visual de PROCESSO

Copiar a estrutura abaixo para o destino em `user-doc/` (após `documentar-seguranca-gate` se exportável).

```markdown
# [Título] — processo de investigação e desenvolvimento (AS-IS)

> Versão do processo: … | Perfil: … | Atualizado: AAAA-MM-DD

## Resumo em 30 segundos

…

## Escopo deste documento

- **Modo:** PROCESSO (AS-IS) | TO-BE (se secção separada existir)
- **Tipos cobertos:** erro | melhoria | nova funcionalidade (marcar)
- **Público-alvo:** …

## Mapa visual (AS-IS)

**Rotulação:** em cada nó do fluxograma, **português primeiro** (o que acontece) e **código do harness** em seguida — nunca nó só com `BOOT`, `EXEC`, etc. Ver skill `documentacao-visual-itens` § Rotulação didática.

### Fluxograma

```mermaid
…
```

### Glossário — códigos do harness (se aplicável)

| Em português | Código | Fonte |
|--------------|--------|-------|
| Abrir sessão da entrega | BOOT | … |
| … | … | … |

### Legenda

…

### Sequência em texto

1. …

## Etapas explicadas

### E1 — …

…

## Ramificações por tipo (somente onde diverge)

### Erro

…

### Melhoria

…

### Nova funcionalidade

…

## Exemplo concreto

…

## Como ler e como agir

…

## Glossário

| Termo | Significado |
|-------|-------------|
| … | … |

## TO-BE (opcional — proposta, não norma)

> Requer aprovação humana antes de virar processo oficial.

…

## Rastreabilidade e revisão

- **Fontes conferidas:** …
- **Limites / lacunas:** …
- **Revisado em:** …
- **Status da revisão:** …
```
