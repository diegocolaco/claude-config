# Entrega do ajuste, depois do «entra»

Aprovar a cópia separada não é entregar: a correção só está entregue depois destes passos. As regras do produto continuam valendo, e este arquivo só as liga ao ajuste: `sgd-novo-entregas`, `sgd-novo-pr-sync-base-before-link`, `sgd-novo-spa-deploy-pre` e `sgd-novo-pr-auxilio-testes-obrigatorio`. Se uma checagem delas pedir o registro de um ITEM que este ajuste não tem, escreva «não aplica» e o motivo. Não invente evidência. Aqui, «passo N do ajuste» é o passo de [ajuste-sem-catalogo.md](ajuste-sem-catalogo.md), e o resto é a numeração desta lista. Essas regras e skills podem não vir carregadas na sessão: antes de começar, leia no repositório de instruções `ecosystem/canonical/rule/<nome>/content.md` de cada regra, `ecosystem/canonical/skills/pr-descricao-detalhada-sgd/content.md` e `ecosystem/canonical/skills/auxilio-testes-pr-sgd/content.md`. Sem achar algum deles, pare e relate qual faltou.

1. **Autorização.** O «entra» aprova a correção, mas não autoriza enviar nem abrir o PR, salvo autorização já em vigor. Pergunte uma vez, e o Diego pode responder tudo junto: «entra e abre o PR». Sem autorização, pare aqui.
2. **Atualizar a cópia.** Traga a versão mais recente de `<destino>` para a branch. Conflito: pare e pergunte, sem resolver. Depois de resolvido, repita também o passo 9 do ajuste, e o Diego decide de novo.
3. **Repetir.** Se a atualização criou uma versão nova na cópia, repita os passos 7 e 8 do ajuste.
4. **Só se aparecer falha nessa repetição:** rode os mesmos testes numa cópia de `<destino>`, sem a correção, para saber quem causou. Falha da correção volta ao passo 6 do ajuste, repete as conferências, e o Diego decide de novo. Falha de código de outra pessoa: pare e pergunte.
5. **Montagem.** Quando a mudança toca a parte web, rode a montagem da regra `sgd-novo-spa-deploy-pre` na cópia, depois da atualização, e registre a linha `spa-build:`. Falhou por causa da correção: volte ao passo 6 do ajuste. Falhou por código de outra pessoa, ou não rodou: pare e diga.
6. **PR.** Envie a branch e abra o PR contra `<destino>`, com o corpo da skill `pr-descricao-detalhada-sgd`. Com o número do PR, gere o roteiro pela skill `auxilio-testes-pr-sgd`, em worktree próprio do repositório dele; o ajuste sem ITEM usa o nome `pr-<numero>-sem-item.md`. Sem o roteiro, a regra `sgd-novo-pr-auxilio-testes-obrigatorio` bloqueia. Nada é enviado direto para o destino. Se o programa que publica recusar o nome `feature/ajuste-<tela>`, ou o PR não puder ser aberto, pare e diga o erro.
7. **Integrar.** O Diego integra, e o agente só integra se ele pedir expressamente. Se ele integrar por fora, ele informa a versão integrada, para você seguir.
8. **Conferir de novo.** Numa cópia nova da versão integrada, nunca na pasta principal do projeto: olhe o resultado da montagem automática do servidor, rode a verificação de tipos e os testes da tela e das telas atingidas, e compare por nome com o antes. Se aparecer falha, faça o passo 4 desta lista.
9. **Confirmar.** Envie o link do PR, a versão integrada, o resultado de cada conferência, «Não conferido: a tela rodando» e «Aceite no ambiente: pendente». Acrescente uma linha de medição com `integrado`, a versão, e `checar_em`, 14 dias depois.

## Se der problema

- **Antes de integrar, a pessoa que revisa o PR pediu mudança:** conta como pedido de mudança do passo 14 do ajuste. A mudança vai no mesmo PR, e a autorização continua valendo.
- **Antes de integrar, o PR ficou parado e o destino mudou:** repita os passos 2 a 5 desta lista.
- **Antes de integrar, o Diego desistiu:** feche o PR e acrescente uma linha de medição com o motivo.
- **Depois de integrar, a correção quebrou algo:** avise e sugira desfazer ou fazer um ajuste novo. O Diego decide. Desfazer é um PR novo, com montagem e verificação de tipos e testes, sem a conferência do que ficou de fora. O PR já integrado não é reaberto.
- **Depois de integrar, o problema já existia:** vai ao relato, sem culpa da correção.
- **Erro no ambiente de desenvolvimento:** antes de propor conserto, siga a skill `investigar-erro`.
- **Não conseguiu conferir a versão integrada:** fica «integrado, sem conferência», nunca «entregue». É pendência do Diego até alguém conferir, e vai na linha de medição.

## Checagem de 14 dias

Quando o Diego pedir, ou quando um ajuste novo avisar que ela venceu: rode a verificação de tipos e os testes na versão de destino e acrescente uma linha de medição com `checado_em` e o resultado. Sem ela, o resultado do piloto para aquele ajuste é «não verificado». Silêncio não conta como «nada escapou».
