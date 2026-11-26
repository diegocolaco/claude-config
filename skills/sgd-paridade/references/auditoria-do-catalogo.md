# Auditoria do catálogo

Antes de escrever o plano, um agente novo tenta derrubar o que o catálogo afirma, lendo o código do protótipo. Motivo: a revisão final compara o código com o plano, a conferência de aparência usa o próprio `definition.agora` como referência e a leitura cega só procura o que faltou. Um erro no catálogo passaria por todas elas, com teste verde.

É uma rodada só: a correção não é auditada de novo.

## O que auditar

Os cenários `functional` e `visual` das telas deste plano, com o `definition.agora` de cada um. Num plano de correção, só os da diferença nova. Ficam fora os cenários de diferença com `disposition` e os de idioma gerados pela `U-IDIOMAS`, que o script já comparou.

Grave em `<tmp>/teses-<n>.json`, fora do repositório, até 5 teses por arquivo: `[{"cenario": "SC-1", "tela": "...", "agora": "..."}]`. Não passe ao agente o plano, o documento de decisões nem o resto do catálogo.

## Brief

Um agente `task-researcher` em `haiku`, esforço `low`, por arquivo de teses. Foi medido com 14 erros plantados: de Haiku low a Sonnet high, todas as configurações acharam 12, por US$ 0,06 a 1,47, e Haiku low gera menos alarme falso, o que barateia o verificador. Os 2 que escapam são omissões, que a passada de ausências cobre.

```text
Você tenta DERRUBAR afirmações sobre um protótipo. Cada uma é uma tese suspeita: só assine CONFIRMADO depois de tentar e falhar em derrubá-la. Só leitura: `git -C <prototipo> show <reference.version>:<arquivo>`. Não rode npm, build, servidor nem navegador. Não leia nada fora desse repositório, além do seu arquivo de teses e do que você grava.

Teses: <tmp>/teses-<n>.json. Abra os arquivos citados em `agora` e o que for preciso para decidir, sem reler o que já abriu. Para cada afirmação de `agora`, um valor, texto e condição por vez, aplique TODOS os ataques:
1. Código morto: o que a afirmação cita é alcançado, ou a função, classe ou arquivo não é usado?
2. Estreita demais: a rotina roda em todos os caminhos afirmados, ou só dentro de um `if`? Cite a condição.
3. Larga demais: a tese generaliza algo que o código só faz em um caso?
4. Recorte ignorado: há constante, guarda, `filter`, enum ou lista que recorta o comportamento e a tese não citou?
5. Valor exato: compare caractere a caractere cada número, texto literal, chave, rota, nome e número de linha citado. Um caractere diferente derruba a tese.
6. Efeito real: o estilo ou a prop se aplica mesmo ao elemento renderizado? Seletor que não casa, valor CSS inválido e classe não usada não têm efeito.
7. Existência × regra: a tese descreve só que o elemento existe e omite a regra que produz o valor dele?
8. Ausência: quando a tese diz «não há», «nenhum» ou «só», procure o contrário. Quando diz que algo existe, ache a linha.
9. Regra ausente: no trecho citado há handler, `disabled`, validação, filtro, opção, prop ou faixa de valores que muda o que se construiria e a tese não traz?
10. Tipo errado: o que a tese chama de aparência é comportamento, ou o contrário?

Veredito: CONFIRMADO (tentou derrubar e tudo bate), REFUTADO (contradiz o código), IMPRECISO (existe, mas incompleto ou vago a ponto de mudar o que se construiria; imprecisão pequena de texto ou de linha também conta, marque em `inferencia` «menor»), NAO_AVALIAVEL (não se decide pelo código).

Limite de 30 turnos. Grave com `python3 -c` e `json.dump` em <tmp>/auditoria-<n>.json, regravando a cada cenário: [{"cenario": "SC-1", "veredito": "...", "afirmacao": "...", "fato": "o que o código mostra", "fonte": "arquivo:linha", "inferencia": "", "ataque": 0}]. Em CONFIRMADO, uma linha por cenário; nos outros, uma por afirmação. Devolva só 2 linhas: quantos de cada veredito.
```

## Verificador

O auditor também erra, e o Haiku low não fica sem revisão. Um agente `task-researcher` em `sonnet`, esforço `medium`, abre a linha citada em cada `REFUTADO` e `IMPRECISO` que não seja «menor», e decide se ela sustenta o veredito:

```text
Um auditor mais barato apontou erros em afirmações sobre um protótipo. Você confere se cada apontamento é verdadeiro. Só leitura: `git -C <prototipo> show <reference.version>:<arquivo>`. Não rode npm, build, servidor nem navegador.

Entrada: <tmp>/apontamentos-<n>.json, com `cenario`, `afirmacao`, `fato`, `fonte` e `veredito`. Abra cada arquivo uma vez só e decida: PROCEDE (o código sustenta o apontamento) ou ALARME_FALSO (o código não sustenta), com `motivo` citando arquivo:linha e o trecho. Motivo genérico invalida o item.

Limite de 30 turnos. Grave com `python3` e `json.dump` em <tmp>/verificado-<n>.json: [{"i": 0, "decisao": "PROCEDE|ALARME_FALSO", "motivo": "..."}]. Devolva só 1 linha: quantos de cada.
```

## O que fazer com o resultado

`ALARME_FALSO` fica registrado e não altera o catálogo. Em cima de `PROCEDE`:

- **`REFUTADO` ou `IMPRECISO`:** corrija o `definition.agora` e, se a diferença ligada repetir o erro, o `agora` e o `produto_precisa` dela. Faça isso em commit próprio, antes do plano, e rode `parity.mjs catalog` e `parity.mjs linkage`. Se a correção mudar o escopo, contrariar uma decisão do Diego ou pedir um requisito novo, pare e pergunte. O «menor» você corrige sem verificador, abrindo a linha.
- **`NAO_AVALIAVEL`:** a afirmação segue no catálogo, e o relato do chat a mostra como `NAO_VERIFICADO`, mesmo com teste verde. Nunca vira aprovada.

O que nenhuma tese cita é da [passada de fatos](../../descoberta-em-ondas/references/passada-de-fatos.md). Se o catálogo veio de uma descoberta sem ela, leve isso ao Diego com o custo de rodá-la nas telas do grupo, antes do plano.

## Registro

Em «Medição por chat», acrescente: cenários auditados; quantos de cada veredito; correções confirmadas, e quantas mudaram o que seria construído; alarmes falsos; custo do auditor e do verificador, separados. Se um item não puder ser medido, escreva «não medido».
