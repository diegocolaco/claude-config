---
name: auditoria-instrucoes-03-atacar
description: Etapa 3 de 3 da auditoria de instruções de agente. Use quando houver uma pasta em user-doc/auditoria-instrucoes/ com a etapa 02 concluída e o usuário pedir red team, auditoria hostil, teste de burla, corte de peso morto ou a versão final do AGENTS.md, CLAUDE.md, rule, skill, subagente ou prompt reescrito; também para aplicar essa versão final ao arquivo real. Ataca a proposta com um auditor em contexto limpo e só aplica com o sim do usuário. Não use sem a etapa 02.
---

# Auditoria de instruções — etapa 03: atacar e aplicar

Esta etapa estressa a versão proposta pela etapa 02 antes que ela chegue ao arquivo real: procura como um agente burlaria as regras, o que está tecnicamente errado, o que ocupa contexto sem mudar comportamento e o que se perdeu do original. Depois monta a versão final e, com o sim do usuário, aplica.

1. `auditoria-instrucoes-01-investigar` — diagnóstico fundamentado.
2. `auditoria-instrucoes-02-reescrever` — falhas críticas e versão reescrita.
3. **`auditoria-instrucoes-03-atacar`** — ataque independente, versão final e aplicação (esta skill).

## Começar

1. **Localizar a pasta e o script.** `<script>` é `<diretório-desta-skill>/../auditoria-instrucoes-01-investigar/scripts/auditoria_estado.py`, executado a partir da raiz do repositório (no Windows, `python`). Sem caminho do usuário, use `python3 <script> listar` e pergunte qual auditoria continuar.
2. **Verificar o gate:** `python3 <script> verificar <pasta> --etapa 03`. Código diferente de 0: pare e mostre a mensagem. O gate recusa quando a 01 ou a 02 não estão concluídas, quando `02-versao-proposta/` está ausente ou vazia, ou quando o alvo mudou desde a investigação. Atacar uma proposta feita sobre outra versão do arquivo produziria uma versão final que sobrescreve mudanças que ninguém analisou. `parcial` só avança com o aceite do usuário (`--aceitar-parcial`), registrado no relatório.
3. **Marcar o início:** `python3 <script> marcar <pasta> --etapa 03 --status em_andamento`.

## Dois papéis, separados de propósito

**Auditor hostil.** Um subagente com contexto limpo, despachado com o modelo em [references/auditor-hostil.md](references/auditor-hostil.md). Ele recebe só:

- os arquivos de `02-versao-proposta/`;
- o material original, para encontrar regressões;
- a lista de URLs citadas em 01-investigacao.md, como ponto de partida.

Ele **não recebe** 02-reescrita.md nem as conclusões da 01, e o prompt pede que não os abra ao explorar o repositório. Quem lê as justificativas de quem reescreveu tende a concordar com elas; a utilidade do auditor está em não compartilhar esse raciocínio. Use o modelo da sessão, a menos que o usuário peça outro; registre o modelo usado.

**Integrador.** Você, o agente principal desta etapa, com acesso a todos os artefatos. O auditor também erra e alucina. Cabe a você conferir cada achado contra o original, a investigação e o repositório, e decidir.

**Sem subagentes** (ferramenta sem delegação, ou esta skill rodando dentro de um subagente): peça ao usuário para abrir um chat novo, de preferência com outro modelo, e colar o prompt do auditor. Se ele preferir seguir no mesmo contexto, faça o ataque você mesmo e registre em "Configuração do auditor" que a independência ficou reduzida.

## Protocolo de ataque

O prompt do auditor pede quatro ataques, cada um com saída concreta:

| Ataque | O que se espera |
|---|---|
| **Burla** | Por diretiva, uma leitura que cumpre a letra e viola a intenção. Cenários de pressão — urgência, "pula essa parte", instrução conflitante de outra fonte, ferramenta indisponível — em que o agente racionalizaria o desvio. |
| **Alucinação técnica** | Cada caminho, comando, flag, campo de frontmatter ou afirmação sobre runtime conferido no repositório ou na fonte oficial. O que não existe ou não funciona como descrito é achado. |
| **Peso morto** | Por diretiva: "se eu remover, que cenário muda?". Sem cenário, é peso morto. Inclui duplicatas, repetição do comportamento padrão do runtime e frases de boa intenção sem ação observável, com linhas e bytes economizáveis. |
| **Regressão** | O que o original garantia e a proposta perdeu ou enfraqueceu. |

## Integrar

O auditor grava os achados e a versão que sugere em `<pasta>/03-auditor/`. Para cada achado (`A1`, `A2`…), confira a evidência e registre `aceito` ou `rejeitado` com o motivo. Achado rejeitado continua no relatório: o usuário precisa ver o que foi levantado e por que não entrou. Rejeite com fundamento — "a diretiva D3 foi sustentada na 01 com fonte X" é motivo; "parece exagero" não é.

Monte `03-versao-final/` a partir da proposta com os achados aceitos aplicados, e gere o diff contra o original:

```bash
git diff --no-index -- <alvo-original> <pasta>/03-versao-final/<arquivo> > <pasta>/03-versao-final/diff.patch
```

`git diff --no-index` sai com código 1 quando há diferenças; isso é o esperado.

**Rodada extra.** Se algum achado `critica` foi aceito, a versão final mudou de forma relevante e não foi atacada. Despache uma segunda rodada, com outro subagente limpo, só sobre `03-versao-final/`. Faça no máximo essa rodada extra: o objetivo é pegar o que a correção introduziu, não iterar até o auditor não ter mais opinião.

## Formato de 03-ataque.md

```markdown
# Ataque: <alvo>

## Configuração do auditor
Modelo, contexto (subagente limpo, chat novo ou mesmo contexto), rodadas, aceite de parcial.

## Achados
| ID | Tipo | Diretiva | Evidência | Severidade | Decisão | Motivo |
|---|---|---|---|---|---|---|
| A1 | burla | D4 | ... | critica | aceito | ... |

## Peso morto removido
Linhas e bytes: proposta <n> → final <n>.

## Verificações
O que foi conferido no repositório e nas fontes, e o que ficou sem verificação.

## Aplicação
Pendente de aprovação | aplicada em <arquivos> | recusada pelo usuário.

## Limites
Auditoria documental: mostra que o texto resiste aos ataques acima, não que o comportamento do agente melhorou.
```

## Aplicar

1. Mostre ao usuário o resumo dos achados aceitos e o `diff.patch`, e pergunte se pode aplicar. Sem um sim explícito, a etapa termina com "Aplicação: pendente de aprovação" — a versão final continua disponível na pasta.
2. Com o sim, rode de novo `python3 <script> verificar <pasta> --etapa 03`. O sim pode chegar muito depois do ataque, e o alvo pode ter mudado nesse intervalo; código diferente de 0, pare e mostre a mensagem. Com o gate liberado, aplique no worktree da tarefa:
   - **Skill ou rule deste repositório:** edite a fonte em `ecosystem/canonical/` e execute `python3 ecosystem/automation/materialize/materialize.py`. A cópia em `.claude/skills` ou `.agents/skills` é gerada e seria sobrescrita.
   - **AGENTS.md, CLAUDE.md, definição de subagente ou prompt:** edite o arquivo.
3. Execute as verificações que o projeto do alvo oferece (materializador, testes de skills, checagens de plataforma) e informe as que não existem ou não rodaram, sem declará-las aprovadas.
4. Faça commit só se o usuário pedir.

Para uma skill, diga que esta auditoria é documental e que a mudança de comportamento se demonstra com uma avaliação (neste repositório, pela Creator, conforme o AGENTS.md).

## Encerrar

1. `python3 <script> marcar <pasta> --etapa 03 --status concluida`.
2. Resuma: achados por tipo e decisão, variação de tamanho, se aplicou e o que foi verificado.
