# Etapa: adoção do catálogo

Use a skill `atualizacao-versao-prototipo` e siga a seção «Adoção» de `../../atualizacao-versao-prototipo/references/adocao-e-baseline.md`. Ache a branch do catálogo pelo `andamento.txt` e a do descritor do protótipo pelas branches não integradas do protótipo. Se não der para ter certeza, pergunte.

1. Mostre as exceções antigas que o resumo da descoberta listou, com o ID antigo e o novo, e peça a reaprovação por ID. «Ok, segue» não aprova.
2. Registre as reaprovadas em «Exceções reaprovadas». Não grave `disposition`: quem grava é a etapa de decisões.
3. Traga o `develop` do produto para a branch do catálogo. Este é o caso do refazer do zero: o catálogo fica o novo, e nada do catálogo antigo volta, nem tarefas, testes, evidências, diferenças ou requisitos. Liste o que trouxer do `develop`.
4. Rode de novo a validação de `catalog` e `linkage` e confira que `baseline` é `{trusted: false}`.
5. Marque «adoção: concluído» e peça ao Diego o merge das duas branches. A integração é decisão dele.
