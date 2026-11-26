Você faz o inventário do código de uma tela de protótipo, para que ela seja reconstruída igual em outra tecnologia. Um script já cortou o código em blocos numerados [B1], [B2]... Todo bloco precisa de uma resposta sua: bloco sem resposta é falha do trabalho, e um script confere isso depois. Não abra o repositório nem rode nada além de gravar sua saída: tudo está no arquivo de entrada. Leia-o uma vez.

Para cada bloco, em ordem, olhe linha a linha e registre cada coisa que muda o que se construiria:
- literal: cada texto exibido, rótulo, placeholder, mensagem, título, opção de lista;
- aparencia: cada medida, cor, espaçamento, grade, tamanho, fonte, ícone, valor de estilo;
- comportamento: cada estado inicial, condição, regra de validação, handler, ação, filtro, ordenação, valor padrão, chamada de API, e o que acontece em cada ramo do `if` ou do ternário;
- dado: cada valor de mock que chega à tela, com a quantidade de itens e como ele é gerado.

Traga o valor exato e o que o valor faz. Se dois caminhos fazem coisas diferentes, registre a diferença. Um `if` pode começar num bloco e terminar no vizinho: leia os dois antes de afirmar o que acontece.

Salto na numeração das linhas é normal: o script tira fechamento de tag, import, comentário e declaração de tipo. Não comente salto. Só aponte corte quando um valor aparece pela metade.

Status do bloco: FATOS (há itens) ou SEM_EFEITO (só tipos, nomes internos ou código não usado). Não resuma, não agrupe blocos, não pule mock nem estilo.

Grave em partes no arquivo de saída indicado: a cada 15 blocos, um `python3` lê o que já está gravado, acrescenta só os blocos novos e grava com `json.dump`. Não repita os blocos já gravados no comando. Formato: [{"bloco": "B1", "status": "FATOS|SEM_EFEITO", "itens": [{"tipo": "literal|aparencia|comportamento|dado", "texto": "o fato, com os valores exatos", "fonte": "arquivo:linha"}]}]. Devolva só 1 linha: blocos e itens.
