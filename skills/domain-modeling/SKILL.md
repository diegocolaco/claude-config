---
name: domain-modeling
description: "Use quando um termo do projeto ou do negócio tiver mais de um sentido ou estiver em disputa (ex.: «conta» como cliente e como login), ao fixar o vocabulário antes de mexer no código, ao criar ou editar um GLOSSARY.md ou ao registrar uma ADR. Não use para explicar conceitos gerais de programação."
---

# domain-modeling

> **Origem.** Adaptada de [mattpocock/skills `domain-modeling`](https://github.com/mattpocock/skills/tree/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/domain-modeling) (MIT, © 2026 Matt Pocock, commit `4ae2317`). Os formatos originais estão em [references/GLOSSARY-FORMAT.md](references/GLOSSARY-FORMAT.md) e [references/ADR-FORMAT.md](references/ADR-FORMAT.md); neles, a única mudança é o prefixo `<repo>/` nos nomes de arquivo do projeto do usuário, para o lint de links não os tomar por arquivos da skill.

Construa e afie o vocabulário do domínio **deste** projeto ou negócio enquanto a conversa acontece: questione termos, invente cenários de borda e registre o que ficou decidido. Ler um glossário só para usar os termos não é esta skill; ela serve quando o modelo de domínio está mudando ou em dúvida. Não é aula de programação: conceito técnico geral se explica em uma frase e segue.

## Durante a conversa

- **Confronte com o glossário.** Se o usuário usa um termo de um jeito que contradiz o `<repo>/GLOSSARY.md`, diga na hora: «O glossário define "cancelamento" como X, mas você parece querer Y. Qual vale?»
- **Afie termos vagos.** Para termo sobrecarregado, proponha um termo canônico para cada sentido. «Quando você diz "conta", é o Cliente (quem paga) ou o Usuário (quem faz login)? São coisas diferentes.»
- **Cenários concretos.** Teste as fronteiras com casos específicos: «Um Cliente com três Usuários; um Usuário sai da empresa. A cobrança muda?»
- **Confira o código.** Quando o usuário afirma como algo funciona, verifique se o código concorda e aponte a contradição com o arquivo.
- **Termine com o que ficou decidido e o que falta decidir**, mais uma pergunta objetiva se a decisão for do usuário.

## Registro (só quando necessário)

- Glossário: crie ou atualize `<repo>/GLOSSARY.md` só quando um termo for resolvido e o usuário quiser o registro; um repositório com vários contextos usa `<repo>/GLOSSARY-MAP.md`. Formato: [references/GLOSSARY-FORMAT.md](references/GLOSSARY-FORMAT.md). O glossário não leva detalhe de implementação.
- ADR: ofereça só quando as três condições valerem: difícil de reverter, surpreendente sem contexto e resultado de um trade-off real. Formato: [references/ADR-FORMAT.md](references/ADR-FORMAT.md).
- Gravar arquivo é alteração: siga o `AGENTS.md` (worktree próprio) e confirme o local com o usuário antes. Se ele pediu para não criar arquivos, não crie.
