# SYNC — gestão do PROJECT-STATE

## O que persistir

Só o que tem valor para um chat futuro: decisões, restrições, arquitetura escolhida, problemas em aberto, descobertas importantes, dependências entre frentes e o próximo passo.

**Não persistir:** raciocínio temporário, logs, respostas completas, código recuperável do repo, investigações descartadas, trivialidades, PII ou segredos.

Teste rápido: *"Um chat novo, amanhã, tomaria uma decisão errada sem esta linha?"* Se não, não registar.

## Modelo do ficheiro (criar se não existir)

```markdown
# Project State
<!-- context-continuity · estado operacional, não histórico · alvo ≤ 200 linhas · histórico em PROJECT-STATE-ARCHIVE.md -->

## Índice
| Frente | Estado (1 linha) | Bloqueado por | Atualizado |
|---|---|---|---|

## Decisões globais
- D-001 · AAAA-MM-DD · <decisão numa linha> · afeta: <frentes|todas> · fonte: <ponteiro opcional>

## Restrições
- R-001 · <restrição> · afeta: <frentes|todas>

## Dependências entre frentes
- <frente-destino> ← <frente-origem>: <motivo> (D-/H-###)

## Problemas abertos
- P-001 · <problema> · frente: <frente> · desde AAAA-MM-DD

## Handoffs pendentes
<!-- blocos H-### (formato em handoff.md) -->

## Frentes

### frente: <slug>
Atualizado: AAAA-MM-DD HH:MM · rev 1
- Objetivo:
- Estado:
- Última decisão: D-### ou texto curto
- Pendências:
- Dependências: <slugs ou IDs>
- Próximo passo:
```

Convenções: slug da frente em kebab-case (`playwright`, `infra`, `spec`); decisões, restrições, dependências e problemas numa **linha** cada (o Grep devolve a linha inteira, sem Read extra); IDs sequenciais nunca reutilizados.

## Procedimento SYNC

1. Resolver o caminho (ver SKILL.md). Se o ficheiro não existir, criar com o modelo.
2. Decidir onde vai a informação: decisão/restrição global, linha de dependência, problema, ou campo da secção `### frente: <slug>`.
3. **Controlo de concorrência** (dois chats podem escrever ao mesmo tempo):
   1. Reler **agora** a secção alvo (Grep `-n` do cabeçalho → Read `offset`/`limit`). Não confiar na leitura do início do chat.
   2. Comparar o `rev` com o que este chat viu. Se mudou, ler a diferença:
      - campos diferentes do que vai alterar → integrar as duas coisas e dizer ao utilizador numa linha;
      - mesma decisão com valor diferente → **não sobrescrever**. Mostrar as duas versões ao utilizador e registar `P-### · divergência entre chats: <resumo>` até ele decidir.
   3. Editar com a ferramenta de edição de arquivo usando como `old_string` a **secção inteira relida**, do cabeçalho até à última linha antes do cabeçalho seguinte. Isto vale também para as secções sem `rev` (Decisões, Restrições, Dependências, Problemas, Handoffs): acrescentar uma linha substituindo só a última linha deixaria passar a escrita de outro chat. Se a edição de arquivo falhar, outro chat escreveu entretanto: voltar ao passo 3.1.
   4. Novo ID (`D-`, `R-`, `P-`, `H-`): alocar **depois** de reler, como máximo + 1 de um Grep do prefixo no estado e no arquivo (IDs nunca se reutilizam).
   5. Incrementar `rev`, atualizar `Atualizado:` na secção e a linha da frente no Índice.
4. Nova decisão que substitui uma antiga: trocar a linha no estado e mover a antiga para o arquivo com `→ substituída por D-###`.
5. Confirmar ao utilizador numa linha: `Estado: registei D-007 (afeta playwright, spec).`

## Controlo de crescimento (fazer durante qualquer SYNC)

| Limite | Ação |
|---|---|
| Ficheiro > ~200 linhas | compactar: arquivar frentes concluídas, decisões substituídas e handoffs consumidos |
| Secção de frente > ~12 linhas | resumir; detalhe vai para a fonte de verdade (SDD, ficha, plano) com ponteiro |
| Handoff já integrado na frente destino | remover do estado; uma linha no arquivo |
| Frente concluída ou abandonada | linha final no arquivo; remover secção e linha do Índice |
| Problema resolvido | remover; uma linha no arquivo se a solução tiver valor futuro |

PROJECT-STATE-ARCHIVE.md só recebe anexos no fim (`AAAA-MM-DD · <ID> · <resumo> · motivo`) e **não é lido** em RESTORE nem em STATUS.
