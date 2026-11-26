# Etapa: um grupo de telas

Use a skill `prototype-parity-verification` e siga `../../prototype-parity-verification/references/decisoes-e-planos.md`. Antes de planejar, leia no documento de decisões a seção «Critérios aprovados e rejeitados» e copie nas restrições globais do plano os critérios que valem para este grupo.

Se a etapa veio de «Divergências abertas», o plano é de correção: a diferença nova já deve estar no catálogo, e o plano é dono dela. Ao encerrar, tire a divergência da lista.

Antes de escrever o plano, faça a [auditoria do catálogo](auditoria-do-catalogo.md) nos cenários deste grupo ou da divergência. Ainda antes do plano, calcule o raio de alcance e a matriz de variações, como manda a seção 7 de decisões e planos.

Se o pacote `@onviobr/dom-components` estiver no `package.json` do alvo, siga a seção 4 do guia. Copie nas restrições globais do plano a tabela dos componentes deste grupo, porque os implementadores não leem o guia.

Depois de escrever o plano, conte as tarefas. Se passar de 15, pare e proponha a divisão antes de executar.

Despache a revisão final explicitamente em Opus e peça também:
- procure sucesso vazio: teste verde numa tela sem dados, filtro que não filtra nada, comando que sai 0 sem ter lido nada;
- procure quem mais usa o que mudou;
- com o Dom DS no alvo, confira a tela pelo `dom-ds-gate`.

Se o Diego aprovar ou rejeitar algo, registre em «Critérios aprovados e rejeitados», com a tela como exemplo e as palavras dele.

Na medição, acrescente:
- cenários do catálogo com veredito, separando aprovados e `NAO_VERIFICADO`;
- itens que o Diego rejeitou, e quantos repetem um erro já corrigido;
- achados por revisão, e quais só a revisão final pegou.
