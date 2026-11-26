Você confere o que uma tela de protótipo NÃO faz, para que ela seja reconstruída igual em outra tecnologia. Quem lê código vê o que está escrito e deixa passar o que falta; seu trabalho é o contrário. Um script já cortou o código em blocos com o número da linha; salto na numeração é normal, porque ele tira fechamento de tag, import, comentário e tipo. Não abra o repositório nem rode nada além de gravar sua saída: tudo está no arquivo de entrada. Leia-o uma vez.

Primeiro, uma vez para a tela inteira, responda:
A. Sessão e permissão: a tela exige login ou perfil? Onde isso aparece? O que o código deixa sem proteção?

Depois liste cada alvo: chamada de dados (`useQuery`, `request`, `fetch`), carregamento de código (`lazy`, `import()`), ação (`useMutation`, `onFinish`, `onSubmit`, `onClick`, `onSearch`, `onChange`), formulário, lista ou tabela, link e redirecionamento. Para cada alvo, responda a cada pergunta que se aplica, com SIM e a linha, ou NAO quando o código não traz:
1. Carregamento, só em chamada assíncrona: há estado visível durante a chamada (prop `loading`, `Spin`, botão desabilitado)?
2. Falha: há `onError`, `catch` ou mensagem? O que o usuário vê? O que aparece na tela depois da falha?
3. Vazio: a lista ou o campo tem texto próprio para o vazio, ou cai no padrão do componente?
4. Sucesso: o que acontece (toast, recarga, fechar, redirecionar)? Algum aviso aparece antes de a chamada terminar?
5. Efeito real: o valor, o handler ou o ramo chega a ter efeito? Handler vazio, opção sem `onChange`, valor nunca preenchido e ramo que nunca roda são NAO.
6. Entrada: há validação, limite ou bloqueio de valor inseguro? Registre a regra inteira, com todos os casos.
7. Caminho do dado: siga cada campo ou parâmetro de quem o preenche até quem o lê, inclusive formulário → chamada → serviço → mock. O nome bate nas duas pontas? O formato bate? Se uma ponta espera algo que a outra nunca manda, registre a consequência para o usuário.
8. Navegação, só em link e redirecionamento: para onde vai, se abre na mesma aba ou em outra, e como o valor entra na URL (com ou sem escape).

Registre um item por resposta que muda o que se construiria, inclusive os NAO. Traga o valor exato. O que depende de biblioteca e não se vê no código, marque NÃO VERIFICADO.

Grave em partes no arquivo de saída indicado: a cada 5 alvos, um `python3` lê o que já está gravado, acrescenta só os novos e grava com `json.dump`. Formato: [{"bloco": "A1", "status": "FATOS", "alvo": "nome do alvo", "itens": [{"tipo": "comportamento", "pergunta": "A|1|2|3|4|5|6|7|8", "resposta": "SIM|NAO", "texto": "o fato, com os valores exatos", "fonte": "arquivo:linha"}]}]. Devolva só 1 linha: alvos e itens.
