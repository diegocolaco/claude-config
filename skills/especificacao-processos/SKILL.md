---
name: especificacao-processos
description: Use quando for mudar qualquer processo (fluxo, regra, script, gate, rule ou skill que muda o que ele faz), como ajuste de telas ou deploy, ou quando pedirem para criar ou consultar a especificação de um processo.
---
CTX-ID: especificacao-processos@1

# Especificação dos processos

Cada processo tem em `user-doc/spec/processos/<processo>/` um arquivo por versão, `v<N>-<AAAA-MM-DD>.md`. O índice é a página inicial de `user-doc/spec/processos/`. A maior versão é a atual, e as outras são o histórico.

## Antes de mudar

1. Ache o processo no índice. Se a mudança atinge mais de um, faça isto para cada um.
2. Leia a versão atual inteira.
3. Leia o «O que mudou» de todas as versões anteriores. Abra o texto de uma versão antiga quando ele tratar do trecho que vai mudar.
4. Escreva no plano, antes de editar:
   - **O que muda.**
   - **Quem usa:** procure com `rg` as skills, rules, programas e outros processos que dependem disso.
   - **Impacto esperado.**
   - **As decisões anteriores** que a mudança afeta. Se ela desfaz uma decisão do usuário, pare e pergunte.

**Sem especificação:** antes de mudar, leia as instruções e os programas reais e escreva a v1, com como ele funciona hoje, sem a mudança. Marque o que não conseguiu confirmar. Acrescente o processo ao índice. Assim, a v2 mostra o que a mudança alterou.

## Ao mudar

1. Copie a versão atual para `v<N+1>-<data de hoje>.md`, na mesma pasta, e altere a cópia. Não edite a versão anterior, mesmo para corrigir um erro: a correção é outra versão. A exceção é a versão ainda não integrada, que é rascunho.
2. Atualize no início do arquivo novo:
   ```markdown
   **Versão:** <N+1> · **Data:** <DD/MM/AAAA>
   **Substitui:** `v<N>-<data>.md`
   **O que mudou:** <o que mudou no processo, em linguagem simples>
   **Por quê:** <o motivo, com o pedido do usuário nas palavras dele>
   **Impacto:** <quem usa e o que muda para eles>
   ```
3. Aponte o índice para o arquivo novo.
4. Coloque tudo na mesma entrega: instruções, programas, versão nova e índice. Se outra entrega integrou o mesmo número antes, renumere a sua.
5. No encerramento, informe a versão criada e o que mudou.

Se a mudança não altera o que o processo faz, como erro de digitação numa instrução, não crie versão.

## Divergência

Se a especificação e as instruções não baterem, pare e diga o que cada uma afirma. Não ajuste a especificação para justificar o que já foi feito: mudança de regra é decisão do usuário.

## Limite

Isto não substitui a especificação geral do Jarbas (skill `aplicar-especificacao-nas-configuracoes`), o histórico do processo de ITEM (skill `item-process-changelog`), nem as regras próprias de deploy (`deploy-change-test-gate`). Quando elas se aplicam, valem junto.
