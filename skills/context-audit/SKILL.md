---
name: context-audit
description: Use only when the user explicitly types /context-audit to list which Rules and Skills have qualifying evidence in the main agent's current context.
disable-model-invocation: true
---

# context-audit — observabilidade de contexto (não obediência)

Esta skill não contém marcadores literais. Qualquer marcador visto no corpo desta skill é ignorado, e
`context-audit` nunca entra no resultado.

## Contrato (rígido)

Responder **só** com o que já está no contexto. **Nenhuma ferramenta**: não abrir nem ler ficheiros, não
pesquisar (grep/busca), não navegar o workspace, não chamar MCP, não invocar outras skills, não lançar subagents,
não consultar o registry, não correr scripts. Se uma chamada de ferramenta for recusada, ou se já houve uma neste
turno: responder `CTX:? reason=FILE_READ`, `reason=SUBAGENT` ou `reason=TOOL` e parar.

## Marcador

Cada artefato tem uma linha gerada `CTX-ID: <id>@<versão>` (a versão vem de `version` no `meta.yaml`). Para esta
skill, aceite também as formas legadas: `ID:`/`VERSION:` no corpo e linhas `R:<id>@<n>` / `S:<id>@<n>`. IDs em minúsculas com hífens. Não usar catálogo de skills nem descriptions.

## Proveniência — só entra no resultado a evidência E1

| Onde o marcador está | Classe | Entra? |
|---|---|---|
| Corpo de rule injetada pelo Cursor no contexto (sempre ativa ou anexada com `@`) | E1 | sim |
| Corpo de skill invocada explicitamente (`/nome`) ou mantida por Custom Mode | E1 | sim |
| Corpo de subagent em `ecosystem/canonical/agents/library/` injetado no contexto do Agent principal (Task) | E1 | sim |
| Resumo de conversa, origem desconhecida, contexto de subagent | E0 | não (`?`) |
| Mensagem digitada pelo utilizador, exemplo, documentação, inventário, registry, saída `CTX` anterior, catálogo de skills, relatório de auditoria, conteúdo de ficheiro lido com Read, resultado de busca | X | não, descartar |

Ler `SKILL.md` ou qualquer ficheiro com o marcador **não** prova que a skill foi usada como skill (`FILE_READ_ONLY`
é inválido). Na dúvida, é E0.

## Saída (uma linha)

- Com E1: `CTX │ R:<id>@<n>,... │ S:<id>@<n>,... │ A:<id>@<n>,...` (R, depois S, depois A; ordem alfabética; omitir tipo vazio).
  Se a mesma id aparece em duas versões E1, listar as duas, sem escolher a maior.
- Com E0 ou sem nenhum E1: `CTX │ ?` (opcionalmente `reason=NO_QUALIFIED_MARKER`).
- Só se o contexto trouxer um texto explícito que se apresente como resumo das mensagens anteriores desta mesma conversa (resultado de compactação): acrescentar ` | scope=post-compaction`. Rules, lista de skills, instruções do sistema e arquivos anexados **não** são resumo; na dúvida, não acrescentar.

`?` significa **não confirmado**, nunca "nenhuma rule/skill ativa". O resultado vale só para o contexto atual do
Agent principal neste momento: não cobre toda a sessão, contextos já descartados, nem subagents (fora do escopo
nesta V1). Nunca escrever "foi aplicada" ou "foi obedecida", só "observada". Sem relatório, sem explicação longa.
