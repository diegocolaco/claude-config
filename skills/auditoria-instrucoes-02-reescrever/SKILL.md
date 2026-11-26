---
name: auditoria-instrucoes-02-reescrever
description: Etapa 2 de 3 da auditoria de instruções de agente. Use quando houver uma pasta em user-doc/auditoria-instrucoes/ com a investigação da etapa 01 concluída e o usuário pedir o diagnóstico de falhas, a blindagem ou a versão reescrita do AGENTS.md, CLAUDE.md, rule, skill, subagente ou prompt auditado. Entrega falhas críticas rastreadas e uma versão proposta completa, sem aplicá-la. Não use sem a investigação da etapa 01.
---

# Auditoria de instruções — etapa 02: reescrever

Esta etapa transforma o diagnóstico da etapa 01 em duas entregas: as falhas que importam na prática do projeto e uma versão reescrita completa do material. Ela fica entre duas outras:

1. `auditoria-instrucoes-01-investigar` — diagnóstico fundamentado.
2. **`auditoria-instrucoes-02-reescrever`** — falhas críticas e versão reescrita (esta skill).
3. `auditoria-instrucoes-03-atacar` — ataque independente, versão final e aplicação.

Nada desta etapa altera o material auditado. A versão proposta ainda vai ser atacada por um auditor independente; aplicar agora colocaria no lugar um texto que ninguém estressou.

## Começar

1. **Localizar a pasta.** O script de estado fica na skill irmã; abaixo, `<script>` é `<diretório-desta-skill>/../auditoria-instrucoes-01-investigar/scripts/auditoria_estado.py`, executado a partir da raiz do repositório (no Windows, `python` no lugar de `python3`). Use o caminho que o usuário passou. Sem caminho, liste as auditorias e pergunte qual continuar:

   ```bash
   python3 <script> listar
   ```
2. **Verificar o gate:**

   ```bash
   python3 <script> verificar <pasta> --etapa 02
   ```

   Se o código de saída for diferente de 0, pare e mostre a mensagem ao usuário. Os motivos possíveis são a etapa 01 ausente ou inacabada, ou o alvo ter mudado desde a investigação. Nos dois casos, reescrever agora significaria corrigir um arquivo com base num diagnóstico que não existe ou que descreve outra versão dele. Se a 01 estiver `parcial`, mostre o motivo e só continue com `--aceitar-parcial` se o usuário aceitar; registre o aceite no relatório.
3. **Marcar o início:** `python3 <script> marcar <pasta> --etapa 02 --status em_andamento`. O comando cria 02-reescrita.md com o cabeçalho herdado da 01.
4. **Ler** 01-investigacao.md, as notas em `01-frentes/` e o material auditado inteiro.

## Fronteira: não pesquisar de novo

Trabalhe com o que a etapa 01 estabeleceu. Se uma mudança depender de um fato que a investigação não levantou, não busque às pressas nem complete com memória: o fato entraria sem a conferência de citações da 01. Registre-o em "Lacunas para a etapa 01" e siga sem a mudança que depende dele, ou recomende rodar a 01 de novo naquela frente.

Achados marcados `NAO_VERIFICADO` na 01 não sustentam mudança.

## Entrega 1 — falhas críticas e pontos cegos

Responda: onde a versão atual falha no dia a dia deste projeto? Para cada falha:

- **ID** `F1`, `F2`…
- **Diretivas afetadas** (`D4`, `D9`) e o **achado da 01** que sustenta a falha.
- **Cenário concreto:** a situação real do projeto e o que o agente faria de errado nela. "A diretiva é vaga" não é cenário; "ao abrir um worktree novo, o agente aceita o detached HEAD e commita sem branch, porque D4 só fala em criar worktree" é.
- **Severidade:** `critica` (causa dano ou viola uma política central), `alta`, `media` ou `baixa`.

Ponto cego é o que nenhuma diretiva cobre, mas a 01 mostrou ser necessário (lacunas da investigação com fonte).

Diretivas `sustentada` na 01 ficam como estão. Reescrever o que já funciona por preferência de estilo cria diff sem falha, e a etapa 03 vai tratá-lo como suspeito.

## Entrega 2 — versão reescrita completa

Grave o material inteiro reescrito em `02-versao-proposta/`, com os mesmos nomes e a mesma estrutura de pastas do alvo, para que a etapa 03 possa comparar arquivo a arquivo. Em 02-reescrita.md, a tabela de rastreio:

| Mudança | Diretiva | Falha | O que mudou |
|---|---|---|---|
| M1 | D4 | F1 | ... |

Toda mudança aponta para uma falha. Uma mudança sem falha não entra.

### Tom: eliminar ambiguidade sem gritar

O objetivo do protocolo original é uma redação que não deixe margem para interpretação. Linguagem enfática (caixa alta, "CRÍTICO", "NUNCA" repetido) não é o meio para isso nos modelos atuais. A orientação da Anthropic para Claude recente é suavizar linguagem agressiva, porque esses modelos respondem mais ao system prompt e passam a acionar em excesso o que antes precisava de ênfase, e explicar a motivação das instruções, porque o modelo generaliza a partir da explicação ([Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices), seções "Tool usage" e "Add context to improve performance"). Se a etapa 01 levantou o contrato de outro runtime, siga o que ele recomenda.

Escolha a forma de cada instrução pelo tipo de falha:

| Falha | Forma da instrução |
|---|---|
| Formato ou saída errada | Receita positiva: o formato esperado, com exemplo |
| Omissão de um passo ou campo | Campo estrutural: o item obrigatório no template ou checklist |
| Comportamento que depende do contexto | Condição observável: "quando X acontecer, faça Y" |
| Violação sob pressão (urgência, pedido para pular) | Regra explícita e restritiva, com o motivo e o cenário de pressão nomeado |

É na última linha que o tom imperativo e restritivo do protocolo original resolve o problema. Nas outras, a precisão vem do formato, não da ênfase.

### Contrato do runtime

A versão proposta precisa continuar válida para quem a carrega, conforme a 01 levantou: frontmatter de skill com `name` e `description` alinhados ao `meta.yaml` quando houver, frontmatter válido de subagente, limite de tamanho do arquivo de instruções do runtime, links relativos que resolvem. Se o alvo for skill ou rule deste repositório, a proposta é do conteúdo canônico (`ecosystem/canonical/...`), não da cópia gerada.

### Orçamento

Registre linhas e bytes do original e da proposta. Cada instrução fica no contexto do agente em toda sessão que a carrega; se a proposta crescer, justifique cada acréscimo pela falha que resolve. A etapa 03 ataca acréscimos sem justificativa como peso morto.

## Formato de 02-reescrita.md

```markdown
# Reescrita: <alvo>

## Base
Investigação usada, status dela e aceite de parcial, se houver.

## Falhas críticas e pontos cegos
### F1 — <título> (critica)
Diretivas: D4. Achado: <tema/achado da 01>.
Cenário: <situação e erro do agente>.

## Rastreio de mudanças
| Mudança | Diretiva | Falha | O que mudou |

## Diretivas preservadas
D1, D2, ... (sustentadas ou sem falha associada)

## Lacunas para a etapa 01
- <fato necessário que a 01 não levantou> → mudança adiada.

## Orçamento
Original: <n> linhas, <n> bytes. Proposta: <n> linhas, <n> bytes. Acréscimos: <M3: motivo>.
```

## Encerrar

1. `python3 <script> marcar <pasta> --etapa 02 --status concluida` (ou `parcial`/`bloqueada` com `--motivo`).
2. Resuma para o usuário: as falhas críticas e altas, quantas mudanças, o que ficou para a 01 e a variação de tamanho.
3. Termine com:

   ```
   Próxima etapa: /auditoria-instrucoes-03-atacar <pasta>
   ```

   Recomende um chat novo para a etapa 03: o auditor precisa olhar a proposta sem o raciocínio que a produziu.
