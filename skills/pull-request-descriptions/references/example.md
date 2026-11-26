# Exemplo fictício de descrição de PR

O exemplo abaixo ilustra a forma de explicar uma mudança. Os fatos e testes são sintéticos, não evidência deste repositório.

## Resumo e objetivo

Adiciona expiração aos links de convite para limitar o período em que um convite pode ser aceito, conforme o requisito informado na tarefa.

## Mudanças detalhadas

### Convites expiram após sete dias

Antes, um convite podia ser aceito enquanto continuasse pendente, sem limite de tempo. Agora, convites criados após esta mudança podem ser aceitos por sete dias contados da criação. Após esse prazo, a pessoa vê “Convite expirado” e precisa solicitar um novo convite ao administrador.

Convites antigos permanecem com o comportamento anterior; este PR não faz expiração retroativa. O prazo é verificado no servidor, portanto não depende do relógio do navegador.

### Reenvio substitui o convite pendente

Ao reenviar, o administrador gera um novo link com outro prazo de sete dias. O link anterior é invalidado imediatamente, mesmo que ainda estivesse dentro do prazo. Isso impede que dois links de um mesmo convite continuem utilizáveis.

## Verificação realizada

- `npm run test -- invites`: 9 testes passaram, cobrindo aceitação dentro do prazo, expiração, convites antigos e invalidação no reenvio, conforme o log fornecido na tarefa.
- Fluxo completo por e-mail: não executado, pois não havia serviço de e-mail disponível no ambiente de verificação.

## Limitações e pontos de atenção

- Convites anteriores à mudança não recebem prazo retroativo.
- A entrega real do e-mail continua sem verificação ponta a ponta.

## Como conferir

Sugestão de revisão manual ainda não executada: em ambiente de testes com e-mail disponível, criar um convite e aceitá-lo dentro do prazo; depois reenviar outro convite e confirmar que apenas o link novo funciona. Para conferir expiração, usar os dados de teste com prazo vencido, sem alterar o relógio de produção.
