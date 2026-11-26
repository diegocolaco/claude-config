---
name: auditoria-instrucoes-01-investigar
description: Etapa 1 de 3 da auditoria de instruções de agente. Use quando o usuário pedir para investigar, auditar ou fazer um raio-x de AGENTS.md, CLAUDE.md, rule, skill, definição de subagente ou prompt confrontando com documentação oficial e restrições reais do projeto, ou para iniciar uma auditoria de instruções. Entrega diagnóstico com fontes conferidas, sem propor correções. Não use para auditoria de código de produto nem para conformidade com a especificação Jarbas.
---

# Auditoria de instruções — etapa 01: investigar

Esta etapa produz um raio-x do material de instrução de um agente: o que cada diretiva afirma, o que as fontes oficiais e o projeto real dizem sobre ela, e o que falta. A família tem três etapas, cada uma num chat próprio se o usuário quiser:

1. **`auditoria-instrucoes-01-investigar`** — diagnóstico fundamentado (esta skill).
2. `auditoria-instrucoes-02-reescrever` — falhas críticas e versão reescrita.
3. `auditoria-instrucoes-03-atacar` — ataque independente, versão final e aplicação.

O estado passa de uma etapa para outra por arquivos, não pela conversa. Por isso o relatório desta etapa precisa ser compreensível sem o chat que o produziu: fontes com URL e seção, trechos e linhas do material.

## Por que esta etapa não propõe solução

Quem pensa na correção cedo começa a procurar evidência para ela e deixa de enxergar o resto. A etapa 02 precisa de um mapa neutro para decidir o que mudar. Quando um achado sugerir uma correção, registre a consequência como **implicação** ("a diretiva D4 não impede X"), sem escrever texto novo para o material. Se o usuário pedir a versão corrigida agora, explique que ela é produto da etapa 02 e entregue o diagnóstico.

## Preparar

1. **Isolamento.** Siga a regra de isolamento do projeto onde a auditoria vai ser gravada. Neste repositório, isso significa um worktree Git exclusivo da tarefa, com branch própria, antes de criar qualquer arquivo.
2. **Delimitar o alvo.** Uma auditoria cobre um arquivo ou um conjunto pequeno e coerente (uma skill com suas referências, por exemplo). Se o pedido for maior, proponha dividir em auditorias separadas.
3. **Criar a pasta da auditoria** com o script desta skill (no Windows, `python` no lugar de `python3`):

   ```bash
   python3 <diretório-desta-skill>/scripts/auditoria_estado.py iniciar --alvo <caminho> [<caminho>...]
   ```

   O comando imprime a pasta `user-doc/auditoria-instrucoes/<AAAA-MM-DD>-<alvo>/` e grava o cabeçalho de 01-investigacao.md com o commit de base e o sha256 de cada alvo. Esses hashes são o que permite à etapa 02, em outro chat, saber se o alvo mudou depois da investigação. Não edite o cabeçalho à mão; use `marcar` (ver Encerrar).
4. **Ler o material inteiro** com números de linha.

## Investigar

### 1. Inventariar as diretivas

Dê um ID a cada instrução do material (`D1`, `D2`…) com o intervalo de linhas e um resumo de uma frase. Diretiva é tudo que pretende mudar o comportamento do agente: ordem, proibição, preferência, fluxo, formato, referência a outro arquivo. O inventário garante cobertura — no fim, toda diretiva precisa ter um status.

### 2. Identificar runtimes e fontes candidatas

- **Quem carrega o material e como.** Para cada ferramenta que lê esse tipo de arquivo (Claude Code, Codex, Cursor ou outra), o contrato de carregamento: quando entra no contexto, precedência, limites de tamanho, frontmatter aceito, como referências a outros arquivos são tratadas. Esse contrato decide se uma diretiva tem efeito.
- **Tecnologias citadas pelas diretivas:** Git, linguagens, frameworks, CLIs, serviços.
- **Restrições reais do projeto:** AGENTS.md, specs, ADRs e o código e a configuração que de fato executam. Para comportamento local, o código vale mais que a documentação do projeto.

### 3. Pesquisar por frentes

Agrupe as diretivas em 2 a 4 frentes temáticas (por exemplo: contrato de carregamento; fluxo Git; avaliação e testes). Cada frente responde perguntas concretas sobre as diretivas que contém.

- **Com subagentes:** despache uma frente por subagente, no mesmo turno, com contexto limpo, usando o modelo em [references/frente-de-pesquisa.md](references/frente-de-pesquisa.md). Contexto limpo importa: cada frente investiga sem herdar as hipóteses das outras.
- **Sem subagentes** (ferramenta sem delegação, ou quando esta skill já roda dentro de um subagente): investigue as frentes em sequência e registre no relatório que não houve isolamento entre elas.

Cada frente lê o corpo das páginas, não só o trecho mostrado pela busca, e grava suas notas em `01-frentes/<tema>.md`.

### 4. Conferir as citações

Antes de consolidar, reabra cada citação que sustenta um achado e confirme três coisas: a página abre, a seção existe e o texto diz o que foi afirmado. Subagentes também erram e resumem demais. O que não se confirmar recebe `NAO_VERIFICADO`, vai para Lacunas e não conta como fato.

### 5. Classificar cada diretiva

| Status | Quando |
|---|---|
| `sustentada` | Fonte oficial ou comportamento local confirma que a diretiva é correta e tem efeito |
| `contrariada` | Fonte oficial ou comportamento local mostra que a diretiva é falsa, obsoleta ou sem efeito no runtime |
| `sem-fonte` | Não há fonte primária que a sustente nem que a contrarie; é escolha local ou "boa intenção" genérica |
| `fora-de-escopo` | Não depende de fonte externa (preferência explícita do usuário, convenção declarada do projeto) |

`sem-fonte` não é defeito por si só: uma política local pode ser legítima. Diga o que ela é.

### 6. Consolidar

Escreva 01-investigacao.md abaixo do cabeçalho, no formato de [references/formato-relatorio.md](references/formato-relatorio.md). Ele cobre os três pontos do protocolo original:

1. **Mapeamento de fontes:** para cada crítica, a documentação, spec ou comportamento que a sustenta.
2. **Práticas genéricas ou obsoletas:** diretivas apoiadas em achismo ou em padrão inadequado para esta stack, contrapostas ao que a fonte determina.
3. **Lacunas:** o que falta especificar, considerando as restrições documentadas das tecnologias e do projeto.

Separe sempre **achado citado** (o que a fonte diz, com link) de **inferência** (o que você conclui a partir disso, com o grau de certeza). Essa separação diz à etapa 02 o que é sólido.

## Hierarquia de fontes

1. Documentação oficial do fornecedor ou especificação, com versão ou data de acesso.
2. Código e configuração que executam no projeto, para comportamento local.
3. Código-fonte upstream oficial.

Blogs, fóruns, respostas de IA e a sua própria memória não sustentam achado. Servem como pista para encontrar uma fonte primária; se a fonte não aparecer, o ponto vai para Lacunas. Isso existe porque o objetivo da metodologia é justamente eliminar análises baseadas em "boas intenções de internet".

## Quando a etapa não pode ser cumprida

- **Sem acesso à web:** não preencha com memória. Marque a etapa como `bloqueada` e pergunte ao usuário se aceita uma auditoria só local. Se aceitar, registre `parcial` com o motivo; todas as afirmações sobre ferramentas externas ficam em Lacunas.
- **Material grande demais para uma auditoria:** proponha a divisão antes de começar.

## Encerrar

1. Grave o status:

   ```bash
   python3 <diretório-desta-skill>/scripts/auditoria_estado.py marcar <pasta> --etapa 01 --status concluida
   ```

   Use `parcial` ou `bloqueada` com `--motivo "<texto>"` quando for o caso.
2. Responda ao usuário com um resumo curto: quantas diretivas, quantas em cada status, os achados mais graves e as lacunas que limitam a análise.
3. Termine com a linha pronta para o próximo chat:

   ```
   Próxima etapa: /auditoria-instrucoes-02-reescrever <pasta>
   ```

   Diga que a etapa 02 roda melhor num chat novo, no mesmo worktree, e que revisar o relatório antes é o ponto onde um erro factual é barrado antes de virar instrução.
