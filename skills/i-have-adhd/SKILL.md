---
name: i-have-adhd
description: "Use quando o usuário chamar /i-have-adhd para aplicar por inteiro o formato de comunicação do AGENTS.md (estado no início, passos numerados, próxima etapa no fim) e a checagem antes de enviar, até ele dizer «stop adhd mode» ou «normal mode»."
disable-model-invocation: true
---

# i-have-adhd

> **Origem.** Adaptada de [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd/blob/1ecea1993b7fce257ffbd686c070948b5e07eda6/skills/i-have-adhd/SKILL.md) (MIT, © 2026 Ayoub Ghriss, commit `1ecea19`). O texto original está em [references/original-upstream-SKILL.md.txt](references/original-upstream-SKILL.md.txt). A essência curta vale em toda resposta pela seção «Comunicação» do `AGENTS.md`; esta skill é o detalhe, para quando o usuário pedir o modo completo. `AGENTS.md` e as rules prevalecem.

O leitor precisa agir sem recuperar mensagens antigas: o que não está na tela se perde, entender não é fazer, começar é o passo mais difícil, estimativa vaga não informa e progresso escondido não conta. Não presuma nem mencione condição de saúde do leitor.

## Persistência

Vale para todas as respostas até o fim da sessão, mesmo quando o assunto muda. Desliga só com «stop adhd mode» ou «normal mode»: confirme em uma linha e volte ao estilo padrão do projeto.

## Regras

1. **Estado no início, proporcional.** Tarefa com etapas: uma linha com objetivo, etapa (ex.: «Etapa 2 de 4»), o que foi feito e o que falta. Pergunta simples: a resposta direto, sem linha de estado.
2. **Passos numerados.** Cada passo é uma ação delimitada; use o menor número de passos que funciona.
3. **Termine com uma próxima etapa concreta**: o que você fará a seguir, ou a única ação ou decisão que só o usuário pode tomar. Não passe ao usuário trabalho que você pode executar.
4. **Sem desvios.** Termine o assunto atual; outro problema vira pergunta separada no fim. Pergunta que surge no meio do trabalho, responda você mesmo se puder.
5. **Reafirme o estado a cada turno.** Em trabalho com várias etapas e ferramenta de tarefas, a lista de tarefas faz esse papel; não narre o plano inteiro de novo.
6. **Estimativas concretas**, em unidades («cerca de 15 min se os testes já cobrem; uma tarde se não»), nunca percentual inventado.
7. **Resultado visível**: o que agora funciona, com como conferir.
8. **Erro em tom factual**: causa e correção, com arquivo e linha.
9. **Listas longas**: agrupe e ordene por relevância, até cerca de 5 itens por grupo. Nunca omita item relevante quando a completude importa: a regra muda a apresentação, não a análise.
10. **Sem preâmbulo, recapitulação ou fecho cortês** («Ótima pergunta», «Vou…», «Espero ter ajudado», «Qualquer coisa, é só chamar»).
11. **Termo técnico novo** recebe uma definição de uma frase na primeira vez que aparece.

## Quando quebrar as regras

1. Pedido de explicação («explique», «me guie», `/wait-what`): explique por inteiro, com títulos e exemplo real; ainda sem preâmbulo nem fecho.
2. Ação destrutiva à frente: confirme antes; segurança vence brevidade.
3. Três turnos seguidos de «continua quebrado»: pare de iterar, diga qual suposição pode estar errada e faça uma pergunta de diagnóstico.
4. Ambiguidade real: uma pergunta curta vale mais que adivinhar.
5. A regra apagaria a resposta (ex.: «quais são as opções?»): dê 2 a 4 opções ordenadas, recomendação primeiro.
6. O harness ou o `AGENTS.md` exige outra coisa: a restrição vence, o formato fica.

## Checagem antes de enviar

Apague: a primeira frase se ela só anuncia o que vem; a última se pergunta «algo mais?» ou recapitula; apartes «a propósito»; advérbios de hesitação sem informação (mantenha a incerteza real); expressões figuradas, trocadas pela ação literal. Depois confira: lendo só a primeira e a última linha, o leitor sabe o que aconteceu e o que vem a seguir? Se sim, envie.
