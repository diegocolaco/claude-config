# Etapa: ajuste numa tela já pronta, sem catálogo

O pedido do Diego traz as correções. Se ele não disser a tela ou o que corrigir, pergunte só isso. Modelo e esforço indicados: Sonnet, Medium. Trabalhe em worktree próprio do produto, com a branch `feature/ajuste-<tela>`, a partir do destino: a branch da onda em andamento, se o pedido ou as regras do produto indicarem uma, ou `develop`, dito no relato. Nos comandos, `<destino>` é essa branch e `<inicio>` é o commit de onde o ajuste partiu. O Diego confere e decide a integração.

Execute os passos na ordem, a partir do passo 1, sem pular. Você mesmo faz os passos: só os passos 9 e 10 despacham agentes, mesmo em tela grande. Passo que não rodou fica escrito no relato como não verificado, nunca como aprovado. Nada do processo entra no produto: `andamento.txt`, lista, relatórios e comparações ficam fora do worktree, numa pasta temporária por ajuste, aqui chamada `<pasta>`. Por isso, ignore a seção «Encerrar» do arquivo principal. Nos comandos, `<scripts>` é `../../prototype-parity-verification/scripts`; os dois programas novos são `../../prototype-parity-verification/scripts/falhas_por_nome.py` e `../../prototype-parity-verification/scripts/paradas.py`.

**Protótipo:** leia sempre a branch `develop`, com `git -C <prototipo> show develop:<arquivo>`, sem depender da branch aberta na pasta. Sem `develop` no protótipo, pare e pergunte. Escreva o commit dele no topo de `<pasta>/requisitos.md`.

## Regras de todos os passos

- **Passou:** siga.
- **Falhou:** veja «o que fazer» abaixo.
- **Não conseguiu conferir** (não rodou, travou ou veio vazio): tente mais uma vez, se a causa for simples. Se continuar: nos passos 1, 3, 7 e 8 e na entrega, pare e diga. No passo 9, pare e pergunte se houver sinal aceso, parte compartilhada, permissão, servidor ou regra de negócio; senão, vai ao relato como «não conferido». No passo 10, vai ao relato como «não conferido». No passo 11, veja as regras dele.

**Quem causou.** O que foi pedido e não ficou feito, ou ficou errado, é defeito deste ajuste, mesmo que o problema já existisse. Para o resto, pergunte: isso existe na versão de antes, em `<inicio>`? Se existe, já estava lá. Se não, veio deste ajuste, inclusive de um bloco já guardado.

**Alteração sem pedido** é o que você mudou sem que o pedido exija, nem o plano, para atender ao pedido. Não contam: o que a correção exige para funcionar, como o teste novo e uma importação; a proteção das outras telas; o que o Diego autorizou numa parada; e o que veio do destino.

**O que fazer:**
- **Falha nova no passo 7, ou defeito grave ou importante deste ajuste, apontado nos passos 9 ou 10:** volte ao passo 6 e repita 7, 8 e 9. Se o defeito está num bloco já guardado, reabra esse bloco e repita nele e nos seguintes.
- **Alteração sem pedido, mesmo pequena:** remova e repita 7, 8 e 9. Se achar que precisa ficar, pare e pergunte.
- **Outro defeito pequeno:** não volta. Vai ao relato.
- **O que já existia:** não corrija. Vai ao relato, com a quantidade.
- **Trabalho novo pedido pelo revisor, ou o que este processo proíbe, como um teste que só repete um texto:** não aplique. Vai ao relato, com o motivo.

**Voltas.** Cada retorno dos passos 7 a 11 ou da entrega para corrigir ou remover algo conta 1; o pedido de mudança do passo 14 tem contagem própria. Limite de 2 por bloco, e 2 para a conferência final; o menor é um bloco só. Estourou: pare, e o Diego escolhe dar mais 1 volta ou encerrar e levar o que há ao relato. Na volta, o passo 9 confere só o que mudou desde a conferência anterior, para não repetir a leitura inteira.

**Pare e pergunte** também quando a conferência final apontar algo que não pertence a um bloco só, propondo um bloco a mais, e em qualquer caso não previsto aqui.

## Passos

Antes do passo 1, leia `~/projetos/.medicoes-ajuste.jsonl`. Se alguma linha tiver `checar_em` vencido e nenhuma linha com `checado_em` para a mesma integração, avise no relato que aquela checagem de 14 dias está pendente.

1. **Estado de antes.** Um worktree novo não tem dependências nem pacotes internos. Prepare-o com os comandos do produto e rode a verificação de tipos por eles, nunca direto dentro do app. No SGD: `pnpm install --frozen-lockfile` e `pnpm turbo run typecheck --filter=<pacote do app>...`, com os nomes lidos no `package.json` de cada app. Erro de módulo não encontrado é falha de preparo: é «não conseguiu conferir», nunca o estado de antes. Com o worktree ainda sem alteração, rode a verificação de tipos e os testes e extraia os nomes do que já falha:

   `<comando de tipos> > <pasta>/tipos.txt 2>&1; echo $?`

   `python3 <scripts>/falhas_por_nome.py extrai --testes <relatório> --tipos <pasta>/tipos.txt --tipos-codigo <o número que saiu> --raiz <worktree> --saida <pasta>/antes.json`

   Grave tudo fora do worktree. No Vitest, o relatório sai de `--reporter=json --outputFile=<pasta>/testes.json`. Se a verificação não rodar ou o relatório vier vazio, pare e diga: sem o antes, não há como saber o que o ajuste quebrou.

   No SGD, rode também o lint dos apps que o ajuste vai tocar, a partir do controlador e nunca com `pnpm lint` ou `eslint` dentro do produto, que estoura a memória:

   `python3 ecosystem/automation/sgd_lint/lint_sgd.py roda --worktree <worktree> --app <app> --saida <pasta>/lint-antes.json; echo $?`

   Saída 0 ou 1 é o estado de antes, com ou sem erro. Saída 2 é «não conseguiu conferir».
2. **Requisitos.** Antes de editar, ache a tela no protótipo e no SGD e leia as duas. Escreva em `<pasta>/requisitos.md` cada requisito do pedido, com `arquivo:linha` do protótipo. O esperado vem do protótipo, salvo decisão registrada; citação em mock não define o esperado sem decisão do Diego. O protótipo só se lê: não suba, não automatize e não instale nada nele. Com `@onviobr/dom-components` no `package.json` do alvo, mantenha a seção 4 de `../../prototype-parity-verification/references/decisoes-e-planos.md`; não troque a biblioteca de uma tela sem perguntar.
3. **Alcance.** Ainda antes de editar, rode `<scripts>/raio_alcance.py <worktree> <inicio> <arquivo>` para cada arquivo que deve mudar. Ele não segue pacotes do workspace; com o arquivo fora da pasta de `--src`, complemente com `git grep`. Resultado 0 ou `alias_sem_uso` não prova isolamento.
4. **Classificação.** Conte os itens do pedido, um a um, e escreva no início de `<pasta>/requisitos.md` a contagem, o tipo e o motivo:
   - **Maior**, se outra tela usa o arquivo que vai mudar; se a mudança altera o comportamento de uma parte compartilhada; se a previsão passa de 5 arquivos ou 300 linhas; ou se o pedido tem de 4 a 10 itens.
   - **Menor, com regra**, se não é maior, e a correção muda comportamento ou há regra de funcionamento ao lado. Rótulo de campo com validação ao lado entra aqui.
   - **Menor, só texto ou aparência**, nos demais casos.
   - **Mais de 10 itens, ou correções pedidas em 2 ou mais telas:** pare e proponha um ajuste e um PR por tela. As telas do alcance ampliam os testes e não contam. A tela que precisa mudar junto, pela mesma parte compartilhada, também não conta, em qualquer momento que entre.

   Na dúvida, escolha maior. O tipo só sobe. Se ele subir depois de já ter alterado código: faça commit do que fez, pare e avise. Se o Diego mandar seguir, escreva o plano e a proteção; o que já foi feito vira o bloco 1, que ganha teste e proteção antes de continuar. Para ver o teste falhar, desfaça esse trecho por um momento e reaplique. Esse trecho vale pela resposta do Diego, registrada em `<pasta>/autorizacoes.md`, e não pelo plano, que veio depois.
5. **Plano e proteção, só no maior.** Antes de qualquer alteração, em `<pasta>/plano.md`, com a data, a hora e o commit da cópia no topo, divida em até 3 blocos, numerados como «Bloco 1», cada um com seu teste. Se a correção não se divide, fica em 1 bloco. Se outra tela usa a parte compartilhada, escreva como ela vai continuar igual: o normal é uma opção nova, com o comportamento atual como padrão, usada só pela tela corrigida. Aqui nada é alterado: a opção entra no passo 6, com o teste antes. Se não der para proteger, ou se o certo for mudar todas as telas, pare antes de corrigir e pergunte, dizendo o que as outras telas sofreriam.
6. **Correção.** Corrija só o pedido. No maior, um bloco por vez, com os passos 6 a 9 para cada bloco. Ao terminar, faça commit: o alcance do passo 7 lê a versão guardada.
   - **Com comportamento:** primeiro o teste, com o esperado tirado da citação do protótipo, nunca do código novo. Veja falhar pelo motivo certo, corrija e veja passar.
   - **Só texto ou aparência:** não crie teste falso; confira pelo código.
   - **Teste antigo que contraria o protótipo:** altere ou apague só se nenhuma decisão registrada o sustentar, e escreva o motivo em `<pasta>/testes-alterados.md`, que vai ao revisor e ao relato. Na dúvida, pare e pergunte.
7. **Resultado.** Faça os itens, sempre, inclusive em ajuste só de texto:
   1. Rode de novo a verificação de tipos, guardando a saída e o código como no passo 1.
   2. Rode `git diff --name-only <destino>` e, de novo, `<scripts>/raio_alcance.py <worktree> HEAD <arquivo>` para cada arquivo listado, mesmo que já tenha rodado no passo 3: é aqui que aparece o arquivo que não estava previsto. Arquivo apagado: use `<inicio>` no lugar de `HEAD`.
   3. Rode de novo os testes e extraia: `python3 <scripts>/falhas_por_nome.py extrai ... --saida <pasta>/depois.json`.
   4. Compare: `python3 <scripts>/falhas_por_nome.py compara <pasta>/antes.json <pasta>/depois.json`.
   5. No SGD, rode o lint dos mesmos apps do passo 1, com `--saida <pasta>/lint-depois.json`, e compare: `python3 ecosystem/automation/sgd_lint/lint_sgd.py compara <pasta>/lint-antes.json <pasta>/lint-depois.json`. Erro de lint novo é falha nova.

   Teste que sumiu conta como problema, salvo o teste antigo do passo 6. Tela do alcance sem teste vai ao relato como não verificada. Se apareceu outra tela e o tipo era menor, siga a regra do passo 4.
8. **Sinais de parada.** `python3 <scripts>/paradas.py <worktree> <base>`, com os arquivos já no estado final do bloco. A `<base>` é `<destino>`; a partir do segundo bloco, é o último commit do bloco anterior, para o sinal já respondido não voltar. Saída 2 ou «Nenhuma alteração» é não conseguiu conferir.
   - **`permissao`:** pare e pergunte, sempre. Permissão que falta não se copia do protótipo.
   - **`dados`:** siga só se o pedido do Diego incluiu essa mudança; o plano não basta, porque é você quem o escreve.
   - **`compartilhado`, com outra tela atingida:** siga se a mudança estava no plano antes de alterar, ou no pedido, e há proteção das outras telas, com teste.
   - **`compartilhado`, sem outra tela atingida:** siga se o alcance, completado com `git grep` pelo nome do arquivo, mostra só essa tela.
   - **Fora disso:** pare e pergunte.

   Todo sinal vai explicado ao relato. Seguir é provisório: se o passo 9 não confirmar, pare e pergunte. A resposta do Diego fica em `<pasta>/autorizacoes.md`, com o arquivo e o que ele decidiu, e o mesmo sinal não pergunta de novo enquanto aquele trecho não mudar. Se ele recusar, remova a alteração e repita os passos 7 e 8, o que conta como volta. Ao revisor, o ponto vai como «fora do pedido, por decisão do Diego», e o relato o lista como não feito.
9. **Conferência do pedido.** Sempre, em todo tipo. Despache `task-reviewer` em Sonnet com o brief de [ajuste-conferencias.md](ajuste-conferencias.md). Quantas: no menor, 1; no maior, 1 ao fim de cada bloco e mais 1 sobre a soma, ou seja, 3 despachos com 2 blocos e 4 com 3. Com 1 bloco, a dele já é a final. Não junte. A conferência que fecha o ajuste faz também a montagem, quando a mudança toca a parte web.
10. **O que ficou de fora.** Depois do último bloco, uma vez: `task-researcher` em Sonnet, com o brief de [ajuste-conferencias.md](ajuste-conferencias.md). Roda quando a correção muda comportamento, quando há regra de funcionamento ao lado e em todo maior. Enquanto durar o piloto de 5 ajustes, roda também em ajuste só de aparência. Fica fora do ajuste só de texto. Cada achado segue a marca que recebeu: «já existia» não se corrige e vai ao relato; «pedido não feito» e «defeito criado» voltam ao passo 6 se forem graves ou importantes, e vão ao relato se forem pequenos; «sem pedido» sai, de qualquer tamanho. Depois de uma volta, este passo só roda de novo se a mudança tocar regra ou comportamento. Se a tela e o que ela usa passarem de 5.000 linhas, pergunte ao Diego antes de despachar, informando as linhas, porque o custo nesse tamanho não foi medido.
11. **Subir e testar.** Só no SGD, depois do último bloco e dos passos 9 e 10, uma vez. Pule no menor só de texto ou aparência, o tipo do passo 4, e diga no relato que pulou. Depois de uma volta ou de um pedido de mudança que altere código, rode de novo, como diz o item 3. Comandos a partir do controlador, com `<sgd-work>` = `node ecosystem/automation/sgd-local/sgd-work.mjs`, e as saídas em `<pasta>`:
   1. `<sgd-work> up --worktree <worktree> > <pasta>/up.json 2> <pasta>/up.log; echo $?`. Ele escolhe o slot livre; se o job entra na fila, espera sozinho até 30 minutos, com o motivo na saída de erro. Sem slot livre, sai na hora com `NO_FREE_SLOT`: veja «Sem vaga». Anote o `slot` do JSON e o tempo.
   2. `<sgd-work> test --slot <slot> --base <inicio> > <pasta>/e2e.log 2>&1; echo $?`. Ele roda as jornadas que o ajuste afeta; sem nenhuma, roda o conjunto mínimo e diz no início. Para ver só a escolha, acrescente `--list`. Anote as jornadas, o código de saída e o tempo.
   3. Deixe o slot de pé até a resposta do Diego no passo 14, e dê no relato o endereço `web` do JSON, para ele ver no navegador. A cada `up` que sobe, grave em `<pasta>/up-head.txt` a saída de `git -C <worktree> rev-parse HEAD`: é o código que o bff e os serviços do slot rodam. Ao repetir este passo depois de uma volta ou de um pedido de mudança, com o slot ainda de pé, liste o que mudou desde esse `up` com `git -C <worktree> diff --name-only <commit do up-head.txt>`, que pega os commits e o que não foi commitado, e `git -C <worktree> ls-files --others --exclude-standard`. Se tudo está sob `apps/web/` e nada é `package.json`, a mudança já vale no slot, porque o web roda no servidor de desenvolvimento do Vite, e basta o `test`. Se algo fica fora, ou na dúvida, `down` e `up` de novo antes do `test`. Dê `<sgd-work> down --slot <slot>` quando o Diego responder «entra» ou «não entra» no passo 14, ou antes, se o ajuste parar. No «pede mudança», o slot fica de pé para a repetição. O `up` que falha já libera sozinho.

   **Sem vaga** (`NO_FREE_SLOT` ou o motivo de fila) não é falha: tente o `up` de novo depois de 2 minutos, até 30 minutos no total, dizendo o motivo. Passou disso, vai ao relato como «não conferido», com o motivo. **O `up` falhou** (`BUILD_FAILED` ou o job terminou em `FAILED`): tente mais uma vez; se continuar, pare e diga, com o resumo da falha. **Jornada falhou:** a falha do `smoke/health` em slot 2 ou maior já existia, porque o spec usa as portas fixas do slot 1, e vai ao relato assim. Para as outras, anote o nome de cada spec que falhou e confira na versão de antes: `down` do slot; `git -C <worktree> switch --detach <inicio>`, e enquanto isso a cópia fica sem a alteração; o mesmo `up`; `test --slot <slot> --journey <jornada>`, uma chamada por jornada que falhou, sem `--base`, que em `<inicio>` não acha diferença; `down`; e `git -C <worktree> switch -` para voltar; por fim, o mesmo `up` de novo, que deixa o slot de pé como diz o item 3, e o relato leva o `slot` e o `web` deste último `up`. Compare pelo nome do spec: o que falha nos dois lados já existia; o que falha só com o ajuste é falha nova do passo 7, e vale a regra dele. O spec que não rodou de um dos lados («did not run») vai ao relato como não conferido. Os tempos dessa conferência vão ao relato à parte.
12. **Medição.** Antes de dar o relato, acrescente uma linha JSON a `~/projetos/.medicoes-ajuste.jsonl`, fora de qualquer repositório: data, tela, tipo, correções, arquivos, custo (de `python3 ecosystem/automation/jarbas.py usage --cost`, com as linhas do `$CLAUDE_CODE_SESSION_ID`), minutos, voltas, sinais, quantos achados a conferência do passo 10 trouxe e, do passo 11, os segundos do `up` e do `test`, as jornadas e o resultado. Item sem medida leva `null`, sem estimar. Mudar esta referência por causa disso é tarefa própria, em outro worktree.
13. **Relato.** Em até 5 linhas por tema, em linguagem simples:
    - o que foi corrigido e o teste que comprova, ou «conferido pelo código»;
    - o tipo escolhido e o motivo, o destino e o commit do protótipo comparado;
    - as telas do alcance: testadas e sem teste;
    - falhas novas, e as que já existiam, em número;
    - os sinais de parada, o que foi feito com cada um e as autorizações;
    - o resultado de cada conferência, com quantas rodaram de quantas o tipo pede, e o da montagem;
    - o passo 11: o slot, as jornadas, passou ou falhou, os tempos do `up` e do `test`, ou por que foi pulado ou ficou sem conferir;
    - o que o revisor pediu e não foi aplicado, com o motivo, e os testes antigos alterados ou apagados;
    - o tempo e o custo, avisando se passaram do limite do tipo, sem contar a entrega nem o passo 11, que vai à parte: 20 minutos ou US$ 1 no só de texto; 1 hora ou US$ 3 no menor com regra e no só de aparência; 2 horas ou US$ 8 no maior. O Diego decide se muda o limite ou o processo;
    - o que ficou fora do pedido, numerado, para o Diego responder com os números;
    - o que não foi conferido, para «não olhei» nunca virar «está igual». Nunca diga que a tela está igual ao protótipo por inteiro.

    O achado fora do pedido não se corrige sem a escolha do Diego. O que ele escolher vira ajuste novo, depois da entrega deste.
14. **Decisão do Diego.** Três respostas:
    - **«entra»:** siga [ajuste-entrega.md](ajuste-entrega.md). Vale só para o código que ele viu.
    - **Pede mudança:** some os itens, arquivos e linhas do ajuste inteiro e refaça o passo 4. Volte ao passo 6 e repita 7, 8 e 9, com a conferência final no maior, e o 11. O passo 10 roda se o tipo novo o pede e ele ainda não rodou; se já rodou, só quando a mudança toca regra ou comportamento. Depois, novo relato. Depois de 2 pedidos de mudança, dele ou de quem revisa o PR, sugira encerrar e abrir um ajuste novo.
    - **«não entra»:** encerre sem entregar e acrescente uma linha de medição com o motivo.

    Cada resposta acrescenta uma linha de medição, com a mesma tela e data: `decisao`, `achados_aceitos`, `achados_voltaram` e `diferencas_abertas`, o que ele não escolheu do que ficou de fora. O que escapar e aparecer depois entra como outra linha, com a tela e o que escapou.
