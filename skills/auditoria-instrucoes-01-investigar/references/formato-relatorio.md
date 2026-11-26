# Formato de 01-investigacao.md

O cabeçalho é gravado pelo script; escreva o corpo abaixo dele, nesta ordem.

```markdown
# Investigação: <alvo>

## Escopo e runtimes

- Material: <caminhos>, commit <sha>.
- Runtimes que o carregam e contrato de carregamento resumido (com fonte).
- Frentes pesquisadas e se rodaram isoladas (subagentes) ou em sequência.
- Data de acesso às fontes.

## Inventário de diretivas

| ID | Linhas | Diretiva (resumo) |
|---|---|---|
| D1 | L3–L5 | ... |

## Achados por tema

### <Tema 1>

#### Conclusão
<uma ou duas frases>

#### Achados citados
- <fato> — [<fonte>](<url#secao>), acesso <AAAA-MM-DD>. Diretivas: D2, D5.

#### Inferências
- <conclusão derivada>, certeza <alta|média|baixa>, porque <...>.

#### Lacunas
- <o que não foi confirmado>; `NAO_VERIFICADO` quando a citação não se confirmou.

<repetir por tema>

## Práticas genéricas ou obsoletas

- D<n>: <o que a diretiva supõe> × <o que a fonte determina> — [fonte](url).

## Cobertura

| ID | Status | Achado ou motivo |
|---|---|---|
| D1 | sustentada | Tema 1, achado 2 |
| D2 | contrariada | Tema 2, achado 1 |
| D3 | sem-fonte | política local; nenhuma fonte primária encontrada |
| D4 | fora-de-escopo | preferência explícita do usuário |

Totais: <n> sustentadas, <n> contrariadas, <n> sem-fonte, <n> fora-de-escopo.

## Implicações para a etapa 02

- <consequência observada, sem texto de correção> (D<n>).
```
