---
name: sgd-paridade
description: "Use quando o Diego chamar /sgd-paridade para tocar a próxima etapa da reconstrução do SGD a partir do protótipo, ou para corrigir algo numa tela já pronta."
disable-model-invocation: true
---

# Próxima etapa da paridade do SGD

Pedido do Diego, que pode vir vazio: $ARGUMENTS

O Diego só chama este comando. Não peça a ele o que o repositório responde.

## 1. Descobrir a etapa

Resolva o produto e o protótipo em `repositories` de `ecosystem/ecosystem-config.yaml`, salvo se o pedido indicar outro caminho. O estado fica em `.squad/contracts/parity/andamento.txt`, no produto. Leia só com git, sem alterar nada:

- `git -C <produto> show develop:.squad/contracts/parity/andamento.txt`
- `git -C <produto> log --all --format=%D -1 -- .squad/contracts/parity/andamento.txt`, para achá-lo fora do `develop`
- `git -C <produto> branch --no-merged develop --list 'paridade/*' 'feature/ajuste-*'`, para achar etapa ou ajuste em curso

O que o Diego escreveu no pedido vale mais que a tabela: correção numa tela é `ajuste`, e pedir paralelo é `paralelo`, com um grupo por chat. Modelo e esforço indicados: Sonnet, esforço Medium em `ajuste`; Sonnet, esforço High em `paralelo`.

| O que o estado mostra | Etapa | Modelo e esforço indicados |
|---|---|---|
| O arquivo não existe em nenhuma branch | `descoberta` | Sonnet, High |
| Só existe fora do `develop`, com a descoberta concluída e sem «adoção: concluído» | `adocao` | Sonnet, Medium |
| Só existe fora do `develop`, com «adoção: concluído» | Nenhuma: falta o merge das duas branches. Pergunte se o Diego faz ou se você faz. Depois, `decisoes` em chat novo | Opus, High |
| No `develop`, sem «decisões: concluído» | `decisoes` | Opus, High |
| Há grupo pendente em «Grupos» | `grupo`, com o primeiro pendente que não esteja em curso | Sonnet, High |
| Nenhum grupo pendente, sem «conferência: concluído» | `conferencia` | Opus, High |
| «Divergências abertas» com item | `grupo`, para a primeira divergência | Sonnet, High |
| Conferência concluída, sem divergência aberta | `baseline` | Sonnet, Medium |
| «baseline: concluído» | Nenhuma: diga que o ciclo terminou | |

Se houver branch `paridade/*` ou `feature/ajuste-*` não integrada, diga qual é e pergunte se retoma, antes de abrir outra etapa. Se o arquivo não bater com nenhuma linha, diga o que viu e pergunte.

## 2. Confirmar

Diga em até três linhas o que viu, a etapa, o modelo e o esforço indicados, e pergunte se pode seguir. Não confira o modelo nem o esforço sozinho: só o Diego vê o que está selecionado. Pare até ele responder.

## 3. Executar

Leia só o arquivo da etapa, em `references/<etapa>.md`, e siga. Na etapa `ajuste`, sem `.squad/contracts/parity/catalog.json` no `develop` do produto, o arquivo é `references/ajuste-sem-catalogo.md`. Cada etapa roda em chat novo: se este chat já fez outra, peça para abrir outro. Worktrees novos do produto usam a branch `paridade/<etapa>`, com o número do grupo quando houver; no ajuste sem catálogo, `feature/ajuste-<tela>`.

## 4. Encerrar

Antes de encerrar, na branch da etapa, atualize `.squad/contracts/parity/andamento.txt` e faça o commit:

- marque a etapa em «Etapas» ou em «Grupos»;
- acrescente a «Medição por chat» o custo do controlador e dos subagents, com o total, o pico de contexto do controlador e o maior entre os subagents, quantos agentes passaram de 100 mil de contexto e quais passaram do teto de 150 mil, com a unidade. Rode `python3 ecosystem/automation/jarbas.py usage --cost --since <data de início deste chat> --top 1000` na raiz do playground e use em `runs` só as linhas com `session` igual a `$CLAUDE_CODE_SESSION_ID`.

Se não conseguir medir um item, escreva «não medido». Não estime. Em conflito neste arquivo, mantenha as duas partes.

Termine dizendo a próxima etapa, lida na tabela com o `andamento.txt` já atualizado, neste formato: abra um chat novo, em <modelo>, esforço <esforço>, e chame `/sgd-paridade`. Se faltar merge do Diego, diga antes que ele vem primeiro.

## Formato de andamento.txt

```text
# Andamento da paridade

## Etapas
- descoberta: concluído em AAAA-MM-DD

## Exceções reaprovadas
- <ID antigo> → <ID novo>: <mensagem do Diego, com data>

## Grupos
- grupo 1, listagens: pendente

## Divergências abertas

## Medição por chat
```
