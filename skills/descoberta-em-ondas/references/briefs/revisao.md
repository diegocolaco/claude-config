Agentes mais baratos listaram fatos sobre telas de protótipo. Você confere se são verdadeiros. Só leitura: `git -C <prototipo> show <commit>:<arquivo>` (`<prototipo>` e `<commit>` vêm no despacho). Não rode npm, build, servidor nem navegador. Não leia nada fora desse repositório, além do arquivo de entrada e do que você grava.

Cada item traz `texto`, `fonte` (arquivo:linha, pode ser abreviado) e `arquivo` (o caminho completo, quando se conseguiu resolver; se vier nulo, procure com `git -C <prototipo> ls-tree -r --name-only <commit>`). Abra cada arquivo uma vez só, com um comando por arquivo, e confira todos os itens daquele arquivo juntos. Decida:
- CORRETO: o código mostra exatamente isso, incluindo valores e regras. Valor derivado de uma conta certa também é correto.
- IMPRECISO: o fato existe, mas com valor, linha ou explicação incompleta ou um pouco errada, sem mudar o que se construiria.
- FALSO: o código não mostra isso, mostra outra coisa, ou a afirmação levaria a construir errado.
Afirmação sobre o que o código NÃO faz conta como FALSA se você achar o contrário no arquivo citado ou nos arquivos diretamente chamados por ele. Se depender de biblioteca e não der para ver no código, marque CORRETO só se o item disser NÃO VERIFICADO; senão, IMPRECISO.

Grave com `python3` e `json.dump` no arquivo de saída indicado: [{"i":1,"decisao":"CORRETO|IMPRECISO|FALSO","motivo":"arquivo:linha e o trecho do código que decide, entre aspas"}]. Motivo genérico, como «conferido», invalida o item. Limite de 30 turnos. Devolva só 1 linha: quantos de cada decisão.
