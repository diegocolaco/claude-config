---
name: wait-what
description: "Use quando o usuário chamar /wait-what porque a última resposta não ficou clara e ele quer a mesma ideia reexplicada com contexto, termos definidos e exemplo."
disable-model-invocation: true
---

# wait-what

> **Origem.** Adaptada de [mattpocock/skills `wait-what`](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/productivity/wait-what/SKILL.md) (MIT, © 2026 Matt Pocock, commit `4ae2317`). Original: «Wait, I don't understand where you've got to here. Re-pitch that: give me a little bit of context, talk in ASD-STE100 Simplified Technical English, and use the ubiquitous language from GLOSSARY.md».

A última mensagem não foi entendida. Reexplique **a mesma ideia**, sem mudar de assunto e sem só repetir a resposta anterior.

## Como reexplicar

1. **Onde estamos.** Uma ou duas frases: o objetivo da conversa, a etapa atual e por que este ponto apareceu.
2. **A ideia em uma frase**, em português simples: frases curtas, voz ativa, um termo por conceito, sem expressão figurada.
3. **Termos.** Cada termo técnico que a explicação usa recebe uma definição de uma linha, ligada a este caso. Se o repositório tiver `<repo>/GLOSSARY.md` (ou `<repo>/GLOSSARY-MAP.md` apontando para ele), use os termos de lá.
4. **Exemplo concreto**, de preferência com os nomes, arquivos ou números da própria conversa.
5. **O que muda para o usuário**: o que ele decide ou faz com isso, ou o que você fará a seguir.

Explique por inteiro, com títulos se passar de três parágrafos. Sem preâmbulo («Claro!», «Vou explicar…») e sem fecho cortês. Se ainda faltar uma informação que só o usuário tem, faça uma pergunta só, no fim.
