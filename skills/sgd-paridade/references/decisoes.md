# Etapa: decisões e primeiro teste

Use a skill `prototype-parity-verification` e siga `../../prototype-parity-verification/references/decisoes-e-planos.md`.

- Grave cada resposta do Diego no documento de decisões assim que ele responder, para ela não depender da memória do chat.
- Grave como `disposition` as exceções de «Exceções reaprovadas» do `andamento.txt`, como manda a seção 5 do guia.
- Crie no documento a seção «Critérios aprovados e rejeitados». Depois do primeiro teste, registre o que o Diego aprovou e rejeitou, com a tela como exemplo e as palavras dele. Copie nas restrições globais de cada plano os critérios que valem para ele, porque os implementadores não leem o documento inteiro.

Antes de levar as perguntas ao Diego, procure os riscos:
1. Rode `python3 ../../prototype-parity-verification/scripts/riscos.py --repo <protótipo> --commit <versão>` e grave a saída num arquivo.
2. Despache um `task-researcher` em `sonnet`, só leitura e git, sem ler tentativas anteriores desta etapa. Ele parte desse arquivo, abre o código do protótipo, inclusive o servidor publicado, e lista com arquivo:linha o que exporia dados ou acesso se fosse copiado. Ele também lê `git log` e `git diff develop...<branch>`, inclusive os planos, de cada branch não integrada, e diz o que ela contém.
3. Confira na fonte e leve cada risco como pergunta própria. Motivo: o guia traz exemplos, e seguir só a lista deixa risco para a revisão.

Julgue a branch pelo que ela muda, não pelo commit de onde nasceu. Branch cujo conteúdo usa IDs, rotas ou planos do catálogo antigo não recebe a recomendação «entra», porque eles significam outra coisa no catálogo novo; reaproveitar o código é decisão do Diego. Branch que nasceu de commit antigo, mas não toca em nada disso, recebe recomendação normal, com o que foi conferido.

Na divisão das telas em grupos:
- Cada grupo deve ser uma entrega funcional verificável, com previsão de 5 a 12 tarefas. Se a previsão de um grupo, ou do primeiro teste, passar de 15, proponha dividir antes de planejar, sem separar itens que compartilham requisito ou cenário.
- Liste os arquivos do SGD que cada grupo deve tocar e marque os pares de grupos independentes. Um par é independente quando não tem requisito, cenário ou biblioteca nova em comum, nem arquivo em comum além do catálogo, do arquivo de rotas, do documento de decisões e do `andamento.txt`. Essa marcação é uma previsão: os planos a confirmam.
- Na previsão de tarefas, conte à parte a base comum (pacotes, caminhos de dados, layout). Mais de 6 cenários por tarefa indica previsão baixa: refaça a conta ou proponha dividir.
- Grave a divisão em JSON e rode `python3 ../../prototype-parity-verification/scripts/grupos.py --catalogo <catálogo> --grupos <json> --inventario <inventário>`. Formato no início do script. Resolva cada item acusado ou diga no documento por que ele não procede.
- Registre os grupos em «Grupos» do `andamento.txt`, como pendentes.

Antes de pedir a aprovação do documento, confira e registre nele:
- cada diferença sem `requirement_ids` tem `disposition` prevista, ou requisito e cenário a criar;
- cada item que expõe dados ou acesso teve resposta do Diego pelo nome, ou está atrás de trava;
- `git -C <produto> branch --no-merged develop`: o que fazer com cada branch, sobretudo as feitas sobre catálogo antigo. Código delas só entra por decisão do Diego.

Depois dessa conferência e antes de pedir a aprovação, despache um `task-reviewer` novo, explicitamente em `opus`, esforço `high`, sem os seus raciocínios. Motivo do Opus: o erro desta etapa se repete em todos os grupos, e parte da revisão é julgamento. Ele só lê o documento, o catálogo e as branches, cita a evidência de cada apontamento e marca como grave o que expõe dados ou acesso, ou muda o que seria construído:
- decisão ou recomendação que contradiga a regra geral do Diego ou outra decisão;
- diferença sem grupo nem `disposition` prevista;
- diferença sem `requirement_ids`, e sem requisito e cenário previstos;
- item que expõe dados ou acesso sem resposta do Diego pelo nome e sem trava;
- destino de branch que não combine com o que ela contém, em `git log` e `git diff` contra o `develop`;
- previsão de tarefas irreal, comparando os cenários e a base comum de cada grupo.

Isso não substitui o builder check, que procura o que falta para construir, nem a aprovação do Diego. Confira cada apontamento na fonte. Corrija o que for erro seu e leve a ele o que depender de decisão. Registre no documento o que o revisor apontou e o que você fez, e inclua o custo dele na medição. Se a correção mudar uma decisão, diga isso ao Diego.

A etapa só fica pronta para a aprovação sem apontamento grave em aberto. Se o revisor trouxer apontamento grave, corrija, rode o `grupos.py` de novo se a correção mexeu nos grupos e despache uma segunda rodada, só sobre o que mudou. Se ainda restar apontamento grave, pare e leve ao Diego, sem nova rodada. Registre na medição os graves de tipo que a busca de riscos e o `grupos.py` não cobrem: são eles que dizem o que falta no processo.

Para não encher o contexto, meça com contagens e leia só os trechos que a pergunta cita, sem abrir a lista inteira de diferenças. Depois da aprovação, grave o documento e peça para compactar antes da auditoria.

Depois das respostas do Diego e da divisão em grupos, e antes de escrever o plano do primeiro teste, faça a [auditoria do catálogo](auditoria-do-catalogo.md) nos cenários desse plano.

Depois de escrever o plano, conte as tarefas. Se passar de 15, pare e proponha a divisão antes de executar.

Ao apresentar o resultado do primeiro teste, conte os erros que o Diego e as revisões acharam e que o catálogo não previa, e leve o número junto da pergunta: seguir para os grupos ou refazer parte da descoberta. Quem decide é o Diego.

Na revisão final, peça também:
- procure sucesso vazio: teste verde numa tela sem dados, filtro que não filtra nada, comando que sai 0 sem ter lido nada;
- procure quem mais usa o que mudou.

Na medição, acrescente:
- cenários do catálogo com veredito, separando aprovados e `NAO_VERIFICADO`;
- itens que o Diego rejeitou, e quantos repetem um erro já corrigido;
- erros que o catálogo não previa, por tela;
- achados por revisão, e quais só a revisão final pegou.
