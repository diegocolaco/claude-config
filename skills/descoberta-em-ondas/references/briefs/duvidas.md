Um inventário de tela de protótipo deixou itens com uma dúvida marcada como NÃO VERIFICADO. Você resolve a dúvida lendo o código. Só leia e busque; não instale, não execute nada do projeto e não use a internet.

`<prototipo>`, `<commit>`, `<lib>` e `<pacotes>` vêm no despacho.

Onde ler:
- Protótipo: `git -C <prototipo> show <commit>:<arquivo>` e `git -C <prototipo> grep -n <texto> <commit>`. Nunca rode nem abra o protótipo no navegador.
- Bibliotecas, na versão travada: `<lib>/<pacote>@<versão>/package`, com `grep -rn` e leitura de trecho. Os pacotes disponíveis são `<pacotes>`; o despacho traz a lista. Prefira `es/`.

O arquivo de entrada é uma lista de objetos `{tela, texto, fonte}`, em que `n` é a posição (começa em 0). Para cada um, ache a parte marcada como não verificada e decida:
- RESOLVIDO: o código responde. Diga em `resposta` o que acontece, com o valor exato, e cite. Se a resposta muda o item, diga como.
- CONTINUA: depois de 5 buscas não há resposta no código lido (por exemplo, depende do ambiente de build ou de pacote ausente). Diga o que falta.

Cada resposta RESOLVIDO traz `fonte` `arquivo:linha` e `trecho`, a linha copiada como está. Para o protótipo, o caminho é o do repositório (`src/pasta/arquivo.tsx:12`); para biblioteca, o caminho a partir da pasta do pacote, com o nome dela (`pacote@1.2.3/package/es/caixa/index.js:10`). Um script confere: citação fora desse formato é recusada e o item segue aberto. Siga o dado até o fim: se a dúvida é o que chega numa função, leia quem chama. Não complete com memória.

Grave com `python3` e `json.dump` no arquivo de saída indicado, a cada 4 itens: [{"n": 0, "estado": "RESOLVIDO|CONTINUA", "resposta": "...", "fonte": "...", "trecho": "..."}]. Devolva só 1 linha: quantos RESOLVIDO e quantos CONTINUA.
