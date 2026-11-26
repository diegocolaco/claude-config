# Conferências do ajuste sem catálogo

Os dois agentes não alteram o código. Não sobem servidor, não abrem navegador e não instalam nada; a única execução é a montagem, na conferência que fecha o ajuste. Passe no despacho o caminho absoluto do worktree, com `cd <worktree>` em cada comando, e declare o modelo Sonnet.

## Conferência do pedido: «fez o que foi pedido, sem fazer a mais?»

Agent `task-reviewer`, em Sonnet. Passe o pedido do Diego com as palavras dele, o caminho da tela no protótipo e o commit de `develop` dele, o relatório de quem corrigiu, com a saída de `falhas_por_nome.py compara`, o intervalo de commits ou a saída de `git diff`, e, quando existirem, `<pasta>/plano.md`, `<pasta>/autorizacoes.md` e `<pasta>/testes-alterados.md`. Passe também o caminho de `<pasta>/requisitos.md`, para ele abrir só depois de escrever a lista dele, e diga:

> Trate o relatório como alegação. Antes de ler o diff, escreva os requisitos a partir do pedido e do protótipo, com `arquivo:linha`. Só então leia o diff e diga o que faltou, o que veio a mais e o que foi mal entendido. Veja se os testes conferem o comportamento real, e não só que o código existe. Só depois abra `<pasta>/requisitos.md` e compare com a sua lista: requisito que só a sua tem é achado. Com plano: confira se o que estava nele é o que foi feito, se cada item serve ao pedido e se a data do plano é anterior ao primeiro commit do ajuste. Se o tipo declarado é «só texto ou aparência», confirme que a correção não muda comportamento e que não há regra de funcionamento ao lado. Classifique cada problema como grave, importante ou pequeno, com `arquivo:linha`. O que está em `<pasta>/autorizacoes.md` não é achado. Em `<pasta>/testes-alterados.md`, julgue o motivo: teste antigo alterado ou apagado sem motivo válido é achado. Responda aprovado, pedido de correção ou BLOCKED. Sem conseguir ler ou conferir, responda BLOCKED, nunca aprovado.

**Na volta,** acrescente: «Confira só o que mudou desde o commit `<commit da conferência anterior>`: se o pedido de correção foi atendido, e se entrou algo novo». É a leitura inteira que custa, e ela já foi feita.

**Na conferência que fecha o ajuste** (a única do menor, ou a final do maior), acrescente: «Se a mudança toca a parte web ou algo que ela usa, rode a montagem da regra `sgd-novo-spa-deploy-pre` no worktree e registre a linha `spa-build:`. Fora disso, registre `spa-build: N/A` com o motivo». Se ela pedir correção, a seguinte roda a montagem de novo.

## O que ficou de fora: «o que ninguém viu?»

Agent `task-researcher`, em Sonnet. Ele não recebe o diff para aprovar; recebe a tela inteira nos dois lados, com o protótipo lido no commit de `develop` informado: a entrada da tela, o que ela importa, e o que ela usa sem importar, como rotas, tratamento geral de erro e textos. Liste os caminhos no despacho, e passe também o pedido do Diego, o commit `<inicio>`, `<pasta>/plano.md` e `<pasta>/autorizacoes.md` quando existirem, o que já foi corrigido e os achados das conferências, para ele não repeti-los. Diga:

> Compare a tela do protótipo com a do SGD. Não aceite o que já foi dito como completo. Leia os arquivos inteiros e percorra a tela uma vez para cada pergunta:
>
> 1. Em cada condição, o que acontece em cada caminho?
> 2. Qual é a origem de cada valor exibido, e ela é a mesma nos dois lados?
> 3. E em caso de falha, de dado vazio ou de demora ao carregar?
> 4. Alguma regra limita o que aparece ou o que se pode fazer?
> 5. O que vem pronto da biblioteca de componentes, e o valor é o mesmo?
>
> Para cada diferença: `arquivo:linha` dos dois lados, o que muda para quem usa, a qual pergunta ela responde, a gravidade (grave, importante ou pequeno) e uma marca. Para marcar, compare com a versão de antes (`git show <inicio>:<arquivo>`): «já existia» se está lá e não foi pedido; «pedido não feito» se foi pedido e não ficou feito; «sem pedido» se o ajuste mudou algo que nem o pedido, nem o plano para atender a ele, nem as autorizações exigem; «defeito criado» se o ajuste criou um problema ao fazer o que foi pedido. Se couber em mais de uma marca, vale «sem pedido». A proteção prevista no plano não é achado. Não corrija nada e não edite arquivo. No fim, liste o que não leu. Se não houver diferença em uma pergunta, escreva isso, e diga o que leu para concluir.

O limite vai no relato: esta conferência não garante que nada escapou, e os valores vindos da biblioteca são o ponto mais fraco.
