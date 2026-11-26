# Etapa: um grupo ao mesmo tempo que outro

Use a skill `prototype-parity-verification` e siga `../../prototype-parity-verification/references/decisoes-e-planos.md`, com as exceções abaixo, que valem por pedido do Diego. No máximo 2 grupos, depois de aprovado o primeiro teste. Antes de planejar, leia no documento de decisões a seção «Critérios aprovados e rejeitados» e copie nas restrições globais do plano os critérios que valem para este grupo.

Escolha o primeiro grupo pendente que não esteja em curso. Se houver outro grupo em curso, ache o plano dele na branch `paridade/*` ou no worktree dessa branch. Se o outro ainda não tiver plano pronto, peça ao Diego para esperar: o segundo chat só abre depois de o primeiro plano estar revisado.

Antes de escrever o plano, faça a [auditoria do catálogo](auditoria-do-catalogo.md) nos cenários deste grupo. Neste chat, a correção não se grava: se houver correção confirmada, pare e pergunte, porque no merge o catálogo do `develop` a apagaria.

Se o pacote `@onviobr/dom-components` estiver no `package.json` do alvo, siga a seção 4 do guia. Copie nas restrições globais do plano a tabela dos componentes deste grupo, porque os implementadores não leem o guia.

Depois de escrever o plano, conte as tarefas. Se passar de 15, pare e proponha a divisão antes de executar.

Regras:
- Só comece se o documento de decisões marca o par como independente.
- Depois de escrever o plano e antes de executar, compare-o com o plano do outro grupo, se ele existir. Se houver item do bloco `**Catálogo:**` em comum, ou arquivo em comum além do catálogo, do arquivo de rotas, do documento de decisões e do `andamento.txt`, pare e pergunte.
- Não grave `disposition` nem diferença nova no catálogo neste chat. Se precisar, pare e pergunte: no merge, manter o catálogo do `develop` apagaria essa gravação.
- Se os testes usarem porta, banco ou ambiente que o outro chat também use, não rode os dois ao mesmo tempo. Avise o Diego.

Depois da última tarefa, siga esta ordem, no lugar da seção 8 do guia:
1. Traga o `develop` mais recente para a branch. Em conflito: no catálogo, mantenha a versão do `develop` (`git checkout --theirs -- .squad/contracts/parity/catalog.json`); no arquivo de rotas, no documento de decisões e no `andamento.txt`, mantenha as duas partes; em qualquer outro arquivo, pare e pergunte.
2. Releia «Critérios aprovados e rejeitados». Se o outro grupo trouxe critério que vale aqui, aplique.
3. Rode de novo os testes deste plano.
4. Rode `verificacao.py ligar` com `--ledger` e `--gravar`, depois `sem-teste`, e faça o commit. Confira no catálogo que as tarefas deste plano estão `entregue`: sem o ledger, elas ficam `planejada` e nenhum comando acusa.
5. Despache a revisão final explicitamente em Opus e peça também:
- procure sucesso vazio: teste verde numa tela sem dados, filtro que não filtra nada, comando que sai 0 sem ter lido nada;
- procure quem mais usa o que mudou;
- com o Dom DS no alvo, confira a tela pelo `dom-ds-gate`.
6. Não apague o workspace do plano ainda, porque o ledger está nele.
7. Antes de integrar, confira se o `develop` mudou. Se mudou, repita os passos de 1 a 4 e peça uma revisão só do que o merge trouxe.
8. A integração é decisão do Diego. Apague o workspace só depois dela.

Se o Diego aprovar ou rejeitar algo, registre em «Critérios aprovados e rejeitados», com a tela como exemplo e as palavras dele.

Na medição, acrescente:
- cenários do catálogo com veredito, separando aprovados e `NAO_VERIFICADO`;
- itens que o Diego rejeitou, e quantos repetem um erro já corrigido;
- achados por revisão, e quais só a revisão final pegou.
Acrescente também o horário de início e de fim do chat, os conflitos no merge com o `develop` e o que foi preciso refazer por causa deles.
