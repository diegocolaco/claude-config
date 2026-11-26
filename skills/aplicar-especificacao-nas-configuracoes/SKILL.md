---
name: aplicar-especificacao-nas-configuracoes
description: Use quando mudar o processo Jarbas ou importar pacote externo e for preciso reconciliar com a especificação aprovada.
---
CTX-ID: aplicar-especificacao-nas-configuracoes@4

# Aplicar especificação nas configurações Jarbas

Mantenha requisito autorizado, implementação real e evidências rastreáveis. Uma melhoria pode começar no Cursor ou em outro contexto; o local da conversa não define sua validade. Preserve integralmente as fontes e o fluxo oficial do Superpowers instalado.

## 1. Identificar a base

- Delimite pedido, autorização já existente e componentes afetados. Pedido de análise não autoriza instalar propostas. Não peça confirmação genérica para trabalho já autorizado.
- Leia 01-ESPECIFICACAO-JARBAS.md (fonte externa ausente no Squad) e confirme versão/identidade com jarbas-par-vigente.md (`sha256` registrado). Envelope externo só para reconciliar divergência entre cópias. O documento 02, pacotes e roteiros anteriores são histórico; manual é apenas consulta opcional.
- Leia PAR08, requisitos afetados e somente fontes, referências e dependências do recorte. Planos, diffs, detalhes técnicos e evidências ficam nos registros existentes do projeto; não carregue o catálogo inteiro nem exija segundo documento normativo ativo.
- Antes de editar configuração, consulte os requisitos afetados na especificação.
- Registre fontes editáveis, geradores, consumidores, versão/modo oficial do Superpowers e estado real, incluindo alterações não commitadas. Use comandos identificados no projeto; não invente paths ou interfaces.
- Confira integridade de pacote recebido antes da aplicação dependente; em M0 use ferramentas locais verificadas, sem executar código recebido ou alterar instruções ativas. Compare base recebida, atual e proposta. Fonte ausente ou conflito bloqueia só o conjunto dependente; avance no trabalho independente autorizado.

## 2. Preparar e aplicar a mudança

- Registre no mecanismo existente: origem/destino, requisito e decisão autorizadora, antes/depois, arquivos, dependências, testes, resultado esperado e recuperação. Reutilize o plano/registro oficial; não crie outro controlador ou ledger.
- Separe mudança de obrigação de ajuste de implementação. A primeira exige decisão autorizada e atualização da especificação (versão e resumo da alteração); editar a especificação para justificar retrospectivamente uma violação não a aprova.
- Divergência material ainda não autorizada: não aplique nem ative o recorte conflitante; apresente requisito, mudança, impacto e decisão (preservar requisito, evoluir especificação ou exceção explicitamente permitida). Ausência do nome de uma skill na especificação não é, por si só, conflito.
- Confira a base imediatamente antes de escrever. Preserve mudanças concorrentes e conteúdo omitido; ausência no export não autoriza exclusão. Reconcilie com evidência ou mantenha o recorte em conflito.
- Edite a fonte canônica e produza os derivados pelo mecanismo confirmado (`jarbas.py materialize`). Verifique os runtimes pertinentes e evite cópias duplicadas descobertas pelo mesmo runtime. Preserve adaptações técnicas legítimas.
- Ao aplicar uma atualização da especificação (0.7), localize produtores e consumidores de critérios, planos, PRE, testes, POST, revisões e encerramento (skills, rules, agents, hooks, comandos, perfis, templates, materializadores e destinos Cursor/Claude) e corrija as fontes reais para orientarem as condições de «Aplicação dos requisitos em cada ITEM». Não duplique o controlador nem modifique o Superpowers oficial; a revisão de uma entrega de produto segue nos pontos PRE, implementação e final, e esta skill não é acionada a cada ITEM.
- Retome por operação: PENDENTE, APLICADA, JA_PRESENTE, CONFLITO ou REVERTIDA, com verificações separadas. Não duplique conteúdo já presente. Reverta somente alterações próprias ainda identificáveis no estado atual.

## 3. Verificar no fluxo existente

- Execute testes focados e regressões pertinentes à mudança, preservando os gates oficiais. Para instruções, confira descoberta, links, acionamento e comportamento: (a) mudança de configuração, (b) conflito conhecido com a especificação, (c) caso já autorizado, (d) entrega de produto que não deve acionar manutenção global.
- Para mudança nas instruções que sustentam a entrega, use casos pertinentes ao impacto: PRE incompleto mantém a implementação dependente pendente; PRE suficiente e revisado permite continuar sem nova confirmação genérica; critério sem prova ou POST obrigatório ausente impede aceite; entrega de produto sem mudança de configuração não inicia manutenção global. Identifique o que foi só conferido no documento e o que foi exercitado no Cursor; nome de skill no log ou arquivo presente não prova comportamento.
- Verifique reaplicação sem duplicação e retomada quando afetadas. Reuse provas válidas; mudança relevante invalida apenas a prova afetada. Piloto PAR08 e execuções finais permanecem exigidos quando aplicáveis pela especificação adotada.
- No ponto de revisão existente, use `auditar-configuracoes-contra-especificacao` para confrontar diff final e evidências com a especificação, preservando independência (inclusive ao alterar esta skill ou o auditor). Se o conflito só aparecer depois da edição, não aprove o recorte; preserve o estado e encaminhe correção ou reversão controlada das alterações próprias. Ausência do auditor deixa o gate pendente; não acrescente ciclo paralelo.
- Relate passou, falhou e não executado com estado testado e evidência. Teste documental não prova ativação no Cursor, paridade do produto nem economia de tokens, tempo ou custo.

## 4. Reconciliar diferenças do ambiente

- Ao constatar diferença material durante qualquer tarefa, registre no mecanismo existente: previsto, executado, causa/limitação do ambiente, evidência, impacto e tratamento. Uma falha transitória resolvida sem alterar o processo permanece no log da execução; não exige revisão documental global.
- Adaptação técnica mantém obrigação e resultado esperado: com equivalência comprovada, registre o caminho/comando/capacidade real e prossiga no escopo autorizado. Limitação que impeça teste, revisão ou prova obrigatórios mantém o gate dependente pendente; não a converta em exceção automática.
- Mudança de obrigação exige decisão autorizada. Registre a divergência observada mesmo sem autorização para corrigi-la, mantendo o requisito vigente. Se afetar o procedimento reutilizável, registre a atualização necessária e aplique-a somente no escopo autorizado; mantenha o restante como proposta ou pendência.

## 5. Atualizar estado e retorno

- Após mudança efetiva, atualize jarbas-par-vigente.md (identificação, versão da especificação, estado, rastreio, `sha256` do arquivo versionado). Atualize 01-ESPECIFICACAO-JARBAS.md (fonte externa ausente no Squad) somente quando o requisito mudar (versão e resumo da alteração); ajuste técnico equivalente não exige mudar o texto normativo.
- Preserve hashes e identidades necessários a provas de commit, build e snapshot; não exija identidade de par nem hashes cruzados de dois documentos normativos nas instruções ativas.
- Separe proposto, autorizado, aplicado e verificado; copie fatos observados para o retorno, nunca o candidato como se estivesse instalado. Documentos indisponíveis ou sincronização incompleta ficam pendentes.
- Exporte somente conteúdo permitido, com omissões explícitas. Devolva a especificação ao usuário somente se ela tiver mudado; caso contrário, confirme a versão mantida. Não exija documento 02 nem manual como anexos. Push, merge e publicação dependem da autorização pertinente, não desta skill.

Exemplo: reorganizar referências de uma skill sem mudar obrigações altera a implementação e o registro de estado. Dispensar uma revisão altera a política e exige decisão autorizada; teste verde sozinho não concede essa dispensa.

---
