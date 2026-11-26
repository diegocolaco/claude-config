# Revisão de qualidade — duas passagens

Executar **A** e **B** na íntegra após o rascunho. Critérios **críticos** (marcados ⚠) exigem correção antes de `APROVADO`.

## Passagem A — técnica

| ID | Critério | Crítico |
|----|----------|---------|
| A1 | Cada etapa do Mermaid aparece na secção “Etapas explicadas” com o mesmo nome/ID | ⚠ |
| A2 | Decisões têm pergunta objetiva; arestas batem com o texto | ⚠ |
| A3 | Falha de teste/gate retorna à etapa correta (sem atalho para “concluído”) | ⚠ |
| A4 | AS-IS e TO-BE separados; TO-BE não misturado como norma | ⚠ |
| A5 | Afirmações de processo têm fonte citada ou `NÃO VERIFICADO` | ⚠ |
| A6 | Não inventa PR, merge, aprovação de produto, paridade ou status de E2E | ⚠ |
| A7 | Compatível com governança vigente (não cria gate/rule/skill nova) | ⚠ |
| A8 | Links relativos resolvem para arquivos existentes | |
| A9 | Datas, versão de protótipo e perfil declarados quando relevantes | |
| A10 | PII, tokens e credenciais ausentes ou mascarados | ⚠ |

## Passagem B — didática

| ID | Critério | Crítico |
|----|----------|---------|
| B1 | Resumo em 30 s compreensível sem ler o resto | ⚠ |
| B2 | Sequência em texto cobre o caminho principal e desvios importantes | ⚠ |
| B3 | Legenda do diagrama explica símbolos usados | |
| B4 | Jargão definido na primeira ocorrência ou no glossário | |
| B9 | Nenhum nó/título/cabeçalho usa **somente** código de harness (BOOT, EXEC, PR-FIRST, …); português na mesma caixa ou glossário imediato | ⚠ |
| B5 | Exemplo marcado fictício quando não for caso real | ⚠ |
| B6 | Secção “como agir” responde bloqueio e retomada | |
| B7 | Carga cognitiva: uma ideia principal por parágrafo nas etapas | |
| B8 | Leitor sem render Mermaid consegue seguir só pelo texto | ⚠ |

## Veredito

| Status | Condição |
|--------|----------|
| `APROVADO` | Nenhum critério ⚠ reprovado |
| `APROVADO COM RESSALVAS` | Só critérios não críticos falharam; ressalvas listadas |
| `PENDENTE` | Qualquer ⚠ reprovado ou lacuna bloqueante sem próximo passo |

Registrar o veredito e a data no rodapé do documento (ver `roteiro-didatico.md`).
