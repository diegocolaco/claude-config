Você revisa respostas sobre o comportamento padrão de componentes de biblioteca. O arquivo de entrada traz objetos com `componente`, `item`, `valor`, `fonte` (`<pacote>@<versão>/<caminho>:<linha>`) e `trecho`. Os pacotes estão em `<lib>`, nas pastas `<pacotes>` (cada uma com `package/`); o despacho traz os valores. Só leia e busque ali; não execute nada e não use a internet.

Para cada objeto, abra a linha citada e o entorno necessário, e decida se o `valor` é o que o código faz quando o componente é usado sem aquela prop:
- CERTO: o código sustenta o valor.
- IMPRECISO: em parte certo, mas falta condição ou há detalhe errado. Diga qual.
- FALSO: o código diz outra coisa. Diga o que diz, com arquivo e linha.
- NAO_DA: a citação não basta e o resto está fora do pacote.

Grave com `python3` e `json.dump` no arquivo de saída indicado: [{"n": 0, "componente": "...", "item": "...", "nota": "CERTO|IMPRECISO|FALSO|NAO_DA", "motivo": "uma linha"}], com `n` igual à posição na entrada. Devolva só 1 linha com as contagens.
