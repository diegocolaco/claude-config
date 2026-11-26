# Etapa: marcar a baseline

Use a skill `atualizacao-versao-prototipo` e siga a seção «Baseline» de `../../atualizacao-versao-prototipo/references/adocao-e-baseline.md`. Trabalhe num worktree próprio do produto, a partir do `develop`.

- Pergunte ao Diego qual é o marco e se ele foi atingido, salvo se já estiver no pedido. Testes verdes, merge ou integração numa branch não bastam.
- Levante você mesmo o commit testado, as evidências e o que continua `NAO_VERIFICADO` ou `SEM_COMPARACAO`. Se houver pendência, pergunte se o aceite é parcial, como a seção descreve.
- Mostre exatamente o que vai gravar e espere o sim do Diego antes de escrever `trusted: true`.
- Grave em commit próprio e rode de novo a validação de `catalog` e `linkage`.
- A integração é decisão do Diego.
