---
name: pull-request-descriptions
description: Use quando redigir ou atualizar a descrição de um PR deste repositório ou do playground, não a do SGD novo.
---

# Descrições de PR autossuficientes

Escreva para quem precisa entender e avaliar a entrega sem abrir o diff. A descrição explica as mudanças e suas consequências; nomes de arquivos e commits são referências de apoio, não substitutos da explicação.

Use o idioma pedido pelo usuário ou exigido pelo projeto. Na ausência de orientação, use português do Brasil.

## Estabelecer o escopo real

1. Identifique o repositório, a branch-base e o head do PR. Use os metadados do PR quando ele já existir. Não presuma que a base é `main`.
2. Leia as instruções e o template de PR do projeto. Para um PR existente, leia também a descrição atual e preserve links, contexto e seções obrigatórias ainda válidos.
3. Examine o diff completo entre a base e o head, incluindo alterações de código, testes, documentação, skills, configuração e dependências. Use ferramentas conectadas ou Git em modo somente leitura. Em Git, consulte o resumo e o diff com comparação de três pontos entre as referências confirmadas. Mensagens de commit ajudam a encontrar contexto, mas não comprovam o conteúdo final.
4. Relacione cada alteração relevante ao comportamento ou contrato que muda. Confira evidências de testes e decisões disponíveis na tarefa. Um arquivo de teste adicionado não comprova que o teste foi executado.

Se faltar acesso ao diff ou a identificação da base, produza somente um rascunho com o escopo conhecido e explicite a lacuna. Não apresente como revisão completa. Mudanças locais não incluídas no PR não fazem parte dele; se a tarefa incluir alterações ainda não commitadas, identifique a descrição como rascunho pendente de conferência após o commit.

## Explicar por mudança, não por arquivo

Agrupe por capacidade, problema corrigido ou tema. Para cada grupo relevante, explique:

- **O que mudou:** a ação ou regra concreta, com condições, limites e exceções importantes.
- **Antes → depois:** o comportamento anterior e o novo. Para capacidade nova, explique o que antes não era possível. Em refatoração, explique a mudança interna e diferencie-a de mudança funcional.
- **Por quê:** o problema ou objetivo documentado. Quando não houver fonte para a motivação, indique que ela não foi informada; não invente justificativas de negócio ou ganhos de desempenho.
- **Impacto:** quem ou o que é afetado, inclusive consumidores de API, agentes, processos e operação. Se houver ação necessária, diga qual.

Comece pela explicação prática; acrescente detalhes técnicos necessários para entender decisões e consequências. Explique siglas pouco familiares. Use caminhos somente para orientar investigação posterior. Agregue mudanças mecânicas, como arquivos gerados, sem ocultar alterações relevantes de dependências.

Dimensione o texto à entrega: um ajuste pequeno pede poucos parágrafos; um PR com vários temas precisa de um grupo por tema. Um pedido de brevidade reduz repetição, não elimina mudanças importantes ou verificações pendentes.

Para mudanças apenas em documentação, skills ou infraestrutura, explique o fluxo, contrato ou orientação antes e depois, sem inventar uma tela ou efeito para usuário final. Se a manutenção de comportamento for intenção ainda não verificada, escreva isso como intenção, não como garantia.

## Estrutura da descrição

Adapte os campos abaixo ao template existente, sem duplicar seções. Use Markdown. Inclua resumo, mudanças, verificação e limitações; acrescente instruções operacionais quando aplicáveis. Remova placeholders. Confira marcações herdadas do template e marque checkboxes somente quando houver evidência de cumprimento; mantenha desmarcados os itens não executados ou não comprovados.

### Resumo e objetivo

Uma ou duas frases sobre a entrega e o problema/objetivo conhecido. Se a motivação não estiver disponível, sinalize essa ausência.

### Mudanças detalhadas

Um subtítulo por tema relevante, com o que mudou, antes/depois e impacto. A motivação pode estar no resumo quando for comum aos temas. Inclua adições, correções, remoções e mudanças de contrato. Evite itens genéricos como “melhorias no sistema”, “ajustes diversos” e “atualização de arquivos”.

### Verificação realizada

Para cada verificação, registre comando ou procedimento, resultado observado e escopo coberto. Separe claramente:

- Executado e aprovado, com a evidência disponível.
- Executado com falha, com o resultado e o que continua sem comprovação.
- Não executado ou bloqueado, com motivo conhecido.

Quando só houver relato anterior, atribua-o à fonte em vez de fingir uma execução nesta etapa. Não invente comandos, contagens, screenshots, resultados de CI ou evidência. Se não houver registro de execução, diga isso. Não execute uma nova campanha de testes só para preencher a descrição; use evidências disponíveis e o workflow de desenvolvimento já autorizado.

### Limitações e pontos de atenção

Registre riscos identificados, limites implementados, pendências e dimensões não verificadas. Não transforme “não identificado” em “não existe”. Se não houver limitação adicional conhecida, diga isso sem alegar ausência de risco.

### Como conferir / ações necessárias — quando aplicável

Descreva passos reproduzíveis, pré-requisitos e resultado esperado para a revisão manual. Identifique-os como sugestão quando não tiverem sido executados. Inclua migrações, variáveis de ambiente, incompatibilidades, rollout e recuperação somente quando houver mudanças ou evidência que os justifiquem. Para mudanças visuais, vincule imagens disponíveis; não afirme que foram capturadas sem evidência.

## Conferência e entrega

Antes de concluir, confronte a descrição com o diff final: todos os temas relevantes estão explicados? É possível entender o antes/depois, o impacto e o estado de validação sem abrir os arquivos? Há promessas sem fonte? Remova conteúdo obsoleto e repetido.

Reconfira a descrição quando novos commits alterarem o escopo do PR. Uma explicação de uma versão anterior não descreve automaticamente a versão atual.

Entregue o corpo pronto para o PR. Quando criar ou atualizar o PR já fizer parte da tarefa autorizada, use esse corpo na descrição real, preserve o contexto válido e confira o texto salvo. Se a tarefa for apenas redigir, ou faltar acesso de escrita, entregue o rascunho e informe que ele não foi publicado. Esta skill não autoriza, por si só, abrir PR, fazer push, enviar comentários ou alterar outro repositório.

Para um exemplo de nível de detalhe, consulte [exemplo de descrição](references/example.md). O exemplo é fictício: não reutilize seus fatos ou resultados como evidência.
