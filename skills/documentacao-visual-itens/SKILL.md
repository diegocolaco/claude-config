---
name: documentacao-visual-itens
description: Use quando documentar um ITEM com diagramas e fluxos visuais verificáveis em user-doc.
---
CTX-ID: documentacao-visual-itens@1.2.0

# Documentação visual de investigação e desenvolvimento de itens

**ID:** `documentacao-visual-itens` · **versão:** `1.2.0` · **idioma:** pt-BR.

## Composição Superpowers

Documenta o processo; **não** o executa nem o substitui.

**REQUIRED BACKGROUND:** You MUST understand `superpowers:systematic-debugging` ao documentar investigação de erro (fases e evidência fiéis ao método oficial).

## Objetivo

Permitir que alguém que não acompanhou a conversa entenda **o caminho**, **o motivo das decisões**, **as evidências** e **o estado real** de uma investigação ou entrega, com um fluxograma navegável e explicações simples. **Esta skill documenta: não determina as regras da entrega nem altera código.**

## Quando aplicar

- **Modo PROCESSO:** o pedido é mapear, explicar, revisar ou melhorar o fluxo de trabalho para erros, melhorias ou funcionalidades. Entregar processo **atual (AS-IS)** e, quando solicitado, **proposto (TO-BE)**, claramente separados.
- **Modo ITEM:** o pedido é documentar como um item real foi investigado, decidido, desenvolvido ou validado. Atualizar durante os marcos, sem inventar fases que não aconteceram.
- **Modo REVISÃO:** o pedido é revisar uma documentação ou torná-la mais didática/visual, preservando os fatos e a fonte oficial.
- Se o pedido apenas exigir programação, investigação ou execução, **não assumir** que esta skill deve criar documentação paralela; seguir primeiro os comandos/gates oficiais. Usar esta skill na etapa documental quando explicitamente solicitada ou quando o fluxo vigente a requerer.

## Fontes, escopo e precedência

1. Identificar repositório, perfil, versão do processo e fontes oficiais **vigentes**. Ler apenas os arquivos necessários. Se houver apenas snapshot/export, declará-lo histórico, não atual.
2. No contexto Jarbas/Novo SGD, verificar as fontes existentes antes de criar qualquer documento: `documentar-user-doc`, `governed-numbered-item-delivery`, `item-process-changelog`, a ficha do ITEM, a skill `investigar-erro` e regras/gates do perfil **que de fato existirem na versão atual**.
3. **Não duplicar fonte de verdade:** a ficha do ITEM guarda o estado e as evidências da entrega; o histórico do processo guarda mudanças no *modo de trabalhar*; esta skill oferece representação pedagógica, referências cruzadas e, se necessário, uma visão consolidada.
4. Seguir as convenções atuais de `documentar-user-doc` para caminhos/índices e `item-process-changelog` para alterações reais do processo. **Não criar, renomear, desativar ou flexibilizar gates/rules/skills** por conta desta documentação.
5. Não modificar código, testes, configuração, deploy, PR, ou histórico da governança sem solicitação expressa e autorização/fluxo adequado. Se o usuário pedir **só documentação**, fazer só isso.
6. Gravação em `user-doc/` com conteúdo exportável: executar antes a skill **`documentar-seguranca-gate`** quando o pedido for documentar para fora do chat.

**Referências desta skill (ler sob demanda):**

| Ambiente | Base |
|----------|------|
| Cursor | `ecosystem/canonical/skills/documentacao-visual-itens/` |
| Claude Code / universal | `ecosystem/canonical/skills/documentacao-visual-itens/` |

## Rotulação didática — português primeiro, código depois (obrigatório)

**Público-alvo típico:** pessoa que **não** acompanha o harness Jarbas diariamente. Códigos como **BOOT**, **EXEC**, **PR-FIRST**, **DEF-EVID** são **rastreio interno** — não são autoexplicativos.

### Regra

1. **Proibido** usar **apenas** sigla/código de harness, gate ou comando como **único** texto visível de:
   - nó de fluxograma (Mermaid, Canvas SVG, draw.io);
   - título de secção ou cabeçalho de tabela;
   - caixa ou cartão em Canvas (`.canvas.tsx`).
2. **Obrigatório** em cada etapa **visível** ao humano:
   - **Linha principal (pt-BR):** frase curta (ideal ≤ 12 palavras) — *o que acontece* em linguagem operacional.
   - **Linha secundária (rastreio):** código oficial do harness — ex.: `BOOT · trace_id + definition.md`, `TEST (7)`, `PR-FIRST (11b)`.
3. **Mermaid:** preferir `no["Abrir sessão da entrega<br/><small>BOOT</small>"]` ou `Abrir sessão (BOOT)` — nunca nó só `BOOT`.
4. **Canvas:** duas linhas por caixa (português + código) **e** secção **Glossário** (tabela código → significado em português).
5. **Markdown (`user-doc/`):** glossário com colunas **Em português** | **Código** | **Fonte** (comando/rule) para **todos** os códigos do diagrama; referência: processo-investigar-erro-e-sgd-entrega.md (secção glossário harness).

### Exemplos

| Evitar | Preferir |
|--------|----------|
| Nó `BOOT` | `Abrir sessão da entrega` + `BOOT` |
| Nó `7 TEST` | `Testes automáticos locais (Playwright)` + `TEST (7)` |
| Título `### DEF-EVID` sem texto | `### Evidências visuais (DEF-EVID)` |

### Exceção

Documentação explicitamente pedida **só para agentes/desenvolvedores do ecossistema** e marcada como tal pode priorizar o código — **não** vale para `user-doc/`, Canvas pedagógico nem `/documentacao-visual-itens` padrão.

Detalhe operacional: `references/roteiro-didatico.md` (Camada 2) · critério **B9** em `references/revisao-qualidade.md`.

## Procedimento

### 1. Definir o alvo

Registrar: objetivo em uma frase; modo; item ou tipo de item; público-alvo; ambiente; versão/protótipo de referência **se pertinente**; data e fontes; estado (`observado`, `confirmado`, `hipótese`, `proposto`, `não verificado` ou `não aplicável`). Não assumir que o protótipo é sempre fonte válida.

### 2. Levantar evidências antes de desenhar

Construir uma tabela interna: **etapa → o que dispara → responsável/papel → ação real → decisão → saída/evidência → próxima etapa → fonte**. Conferir código, comandos, relatórios, traces ou fichas quando disponíveis. Separar explicitamente **fato observado**, **norma vigente**, **hipótese** e **sugestão**. Lacunas recebem `NÃO VERIFICADO` e um próximo passo verificável; não preencher com imaginação.

### 3. Produzir a explicação em camadas

Abrir `references/roteiro-didatico.md` (paths da tabela acima). Ordem obrigatória no documento:

1. **Resumo em 30 segundos:** finalidade e resultado esperado, sem jargão.
2. **Mapa visual:** fluxograma Mermaid com início/fim, decisões `Sim/Não`, retornos, bloqueios e caminhos alternativos; legenda e **sequência equivalente em texto** para leitores sem renderização.
3. **Etapas explicadas:** para cada etapa, *por que existe → o que entra → o que fazer → o que sai → como saber que terminou*.
4. **Exemplo concreto:** acompanhar um erro ou melhoria do começo ao fim, explicitamente marcado **fictício** se ilustrativo.
5. **Como ler e como agir:** significado das decisões, quem responde por pendências e como retomar.
6. **Glossário curto:** definir termos na primeira ocorrência e explicar os indispensáveis com palavras simples.

Para documentos de PROCESSO, usar `assets/modelo-processo.md`. Para ITEM, usar `assets/modelo-item.md`. Carregar apenas o modelo relevante. Exemplo guiado em `references/exemplo-ficticio.md` se necessário.

### 4. Desenhar respeitando o processo

- Aplicar **Rotulação didática** (secção acima) em todo mapa visual antes de revisar.
- Etapas do fluxograma devem bater com o detalhamento e as evidências. Rotular decisões objetivamente (por exemplo, `Causa confirmada?`), nunca apenas `OK?`.
- Um teste que falha volta para a etapa correta; não desenhar `falhou → pronto`.
- Ramos `erro`, `melhoria` e `nova funcionalidade` só divergem onde houver diferenças concretas; o fluxo compartilhado não deve ser triplicado.
- Mostrar **bloqueio** quando a fonte atual o exige; mostrar `não verificado` quando não há prova; não prometer que haverá PR, deploy, paridade ou E2E para todo ITEM.
- Ao documentar o Novo SGD, registrar restrições operacionais vigentes **somente após conferência**, como execução exclusiva de E2E se a regra continuar válida.
- Processo **AS-IS** descreve exclusivamente o que está demonstrado; processo **TO-BE** é recomendação e precisa de avaliação/aprovação humana antes de virar norma.

### 5. Salvar sem duplicar

- **PROCESSO:** procurar documento vivo e índices na área, atualizar o documento oficial/visão pedagógica existente. Se não houver, sugerir doc-sgd-novo-processo-investigacao-desenvolvimento-itens.md, validando as convenções reais antes de criar.
- **ITEM:** atualizar a ficha oficial e seus vínculos se esse for o destino previsto; não criar nova ficha concorrente. Uma explicação didática separada só se solicitada, com referência ao registro oficial.
- **REVISÃO:** modificar o mesmo documento, mantendo links e referências. Se for apenas uma proposta, entregar um rascunho sem apresentá-lo como publicado.
- Atualizar índices exigidos pela convenção em uso; links relativos devem apontar para arquivos existentes.

### 6. Revisar em duas passagens independentes

Ler **integralmente** `references/revisao-qualidade.md` e executar:

- **Passagem A — técnica:** fontes, versionamento, sequência, decisões, exceções, evidências, estados e compatibilidade com governança.
- **Passagem B — didática:** resumo, legenda, leitura linear, clareza, jargões, exemplo, carga cognitiva e acessibilidade sem Mermaid.

Corrigir e repetir qualquer critério crítico reprovado. Registrar no fim do documento: **revisado em**, **fontes conferidas**, **limites/lacunas**, **status da revisão** (`APROVADO`, `APROVADO COM RESSALVAS` ou `PENDENTE`). Não simular segunda revisão feita por outra pessoa ou agente: são duas passagens metodológicas, não uma revisão independente de terceiro.

### 7. Encerrar com rastreabilidade

Informar: arquivo criado/atualizado; links da fonte; o que está confirmado e o que está apenas proposto; pendências, responsáveis se conhecidos; resultado da revisão. Se não houve acesso ao projeto, dizer claramente **"modelo preparado; ainda não confrontado com a versão atual do repositório"**.

## Proibições

- Inventar causas, status de testes, número de PR, aprovação, decisão de produto ou paridade.
- Apresentar um fluxograma ilustrativo como retrato fiel da execução real.
- Executar E2E extra ou consumir modelos premium só para diagramar uma documentação.
- Colocar tokens, credenciais, dados pessoais ou informação corporativa desnecessária em exemplos.
- Introduzir uma nova regra obrigatória de processo apenas porque está no diagrama.
- Nós, títulos ou tabelas com **somente** código de harness (ex.: `BOOT`, `EXEC`, `1c`) sem descrição em português na mesma vista ou glossário adjacente.

**Atalho de uso:** `/documentacao-visual-itens` — ver.
