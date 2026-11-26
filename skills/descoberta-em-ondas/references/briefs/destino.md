Um inventário listou fatos que o catálogo de paridade de uma tela ainda não traz. Você decide onde cada fato entra. Não abra o repositório nem rode nada além de gravar sua saída: tudo está no arquivo de entrada. Leia-o uma vez.

O arquivo traz `cenarios` (id, região e início do texto de cada cenário da tela) e `itens` (fatos numerados em `i`). Para cada item, escolha o cenário de mesmo assunto: a mesma parte da tela e a mesma dimensão (comportamento ou aparência). Se nenhum servir, use `NOVO:<rótulo curto da região>`, com o mesmo rótulo para os itens da mesma parte da tela. Não reescreva nem resuma o fato: ele vai como está.

Grave com `python3` e `json.dump` no arquivo de saída indicado: {"<i>": "SC-12"} ou {"<i>": "NOVO:rótulo"}. Todo item precisa de destino. Devolva só 1 linha: quantos em cenário existente e quantos em NOVO.
