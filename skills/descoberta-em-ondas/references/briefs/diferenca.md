Um inventário listou fatos sobre uma tela de protótipo. O catálogo do projeto já descreve parte deles. Você decide, item por item, o que o catálogo ainda não traz. Não abra o repositório nem rode nada além de gravar sua saída: tudo está no arquivo de entrada. Leia-o uma vez.

O arquivo traz `leitura` (o texto do catálogo sobre a tela) e `itens` (fatos numerados em `i`). Para cada item:
- NOVO: a `leitura` não traz esse fato, ou cita o elemento sem o valor ou a regra que o item traz. Na dúvida, é NOVO.
- JA: a `leitura` traz esse fato com o mesmo valor ou a mesma regra.

Citar o elemento não basta: «tem um botão» não cobre «botão do tipo link». Diferença de um valor conta.

Grave com `python3` e `json.dump` no arquivo de saída indicado: {"novos": [lista de i], "ja": [lista de i]}. Todo item precisa estar em uma das duas listas. Devolva só 1 linha: quantos de cada.
