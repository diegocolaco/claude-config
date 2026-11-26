# Templates — pacote de revisão

Copiar para a pasta do pacote e preencher. Não commitar dados sensíveis nos templates vazios.

## 00-LEIA-ME.md (esqueleto)

```markdown
# Pacote de revisão — <título>

| Campo | Valor |
|-------|--------|
| Snapshot | <ISO-8601 com fuso> |
| trace_id | <id ou N/A> |
| ITEM / mudança | <ITEM-### ou descrição> |
| Repositórios | <playground / worktree / outros pertinentes> |
| BASE / HEAD | <refs ou «desconhecido»> |
| Etapa alcançada | <em palavras> |
| Processo adotado | <versão/ref — distinguir adotada vs proposta> |
| Cobertura | COMPLETO NO ESCOPO DECLARADO \| PARCIAL |

## Objetivo

<1–3 frases>

## Ordem de leitura

1. `02-INVENTARIO.md`
2. `01-CONVERSA.md`
3. `artefatos/…` conforme inventário

## Decisões relevantes

- …

## Observado vs relatado

| Tema | Relatado | Observado (evidência) |
|------|----------|------------------------|
| … | … | … |

## Pendências e limitações

- …

## O que o revisor pode / não pode concluir

- Pode: …
- Não pode (sem material): …

*Pacote preparado pela skill `exportar-conversa-e-arquivos-para-revisao` — não implica entrega aprovada.*
```

## 02-INVENTARIO.md (esqueleto)

```markdown
# Inventário do pacote

| # | Material lógico | Origem (alias) | Destino no pacote | Condição | SHA-256 (bytes exportados) | Notas |
|---|-----------------|----------------|-------------------|----------|----------------------------|-------|
| 1 | … | … | `artefatos/…` | INCLUIDO \| SANITIZADO \| OMITIDO \| INDISPONIVEL \| NAO_GERADO | `…` ou — | … |

**Condições:** INCLUIDO (cópia fiel permitida); SANITIZADO (transformado — não é byte-a-byte do original); OMITIDO (proibido ou risco); INDISPONIVEL (não encontrado nesta execução); NAO_GERADO (etapa ainda não executada).

**Lacunas com impacto:** …
```
