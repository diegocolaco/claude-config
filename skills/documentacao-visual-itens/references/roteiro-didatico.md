# Roteiro didático — camadas do documento visual

Use este roteiro ao montar o artefato final (PROCESSO, ITEM ou REVISÃO). Cada camada é uma secção do documento; não pule camadas sem justificar no bloco de revisão.

## Camada 1 — Resumo em 30 segundos

- **Público:** gestor ou colega que só quer saber se pode confiar no resto.
- **Formato:** 3–5 frases; verbo no presente; sem siglas não explicadas.
- **Incluir:** o que é; para quem; resultado esperado ao fim do fluxo; se é AS-IS, TO-BE ou trajetória de um ITEM real.
- **Evitar:** lista de ferramentas, números de PR, nomes de agentes internos sem papel.

## Camada 2 — Mapa visual

### Rotulação dos nós

- **Português primeiro:** cada nó mostra *o que acontece*; o código do harness (`BOOT`, `TEST`, `PR-FIRST`, …) é **secundário** (segunda linha, parênteses ou glossário).
- **Proibido:** nó ou caixa de Canvas contendo **só** sigla/código (ex.: `BOOT`, `1b`, `DEF-EVID`).
- **Mermaid:** `["Descrição curta<br/>CÓDIGO"]` ou `Descrição (CÓDIGO)`.
- **Canvas:** propriedades `linha1` (pt-BR) + `linha2` (código); glossário aberto ou callout para termos novos (ex.: «O que é BOOT?»).

### Mermaid

- Um fluxograma principal (`flowchart TD` ou `LR` conforme legibilidade).
- Nós de início/fim explícitos (`([Início])`, `([Fim])` ou equivalente).
- Decisões com pergunta fechada (`{Causa confirmada?}`) e arestas `Sim` / `Não`.
- Bloqueios: nó com estilo ou legenda `BLOQUEIO` (gate, humano, infra).
- Retornos de teste falho: aresta de volta à etapa correta (correção, não “pronto”).
- Legenda curta abaixo do diagrama (símbolos, cores se usadas, significado de trace_id se citado).

### Sequência em texto (obrigatória)

Lista numerada espelhando o caminho **feliz** e, em sub-bullets, os desvios principais:

```text
1. Receber pedido → classificar (erro | melhoria | funcionalidade)
2. …
   - Se teste falhar → voltar para …
   - Se gate bloquear → parar até …
```

## Camada 3 — Etapas explicadas

Para **cada** etapa do mapa, usar o mesmo identificador (E1, E2, … ou nome estável):

| Campo | Pergunta-guia |
|-------|----------------|
| Por que existe | Que risco ou retrabalho evita? |
| O que entra | Artefatos, decisões, pré-requisitos |
| O que fazer | Ações observáveis (comandos só se conferidos) |
| O que sai | Evidência, arquivo, status |
| Como saber que terminou | Critério verificável; link para gate se houver |

Marcar cada afirmação normativa com **fonte** (rule, skill, ficha, comando) ou `NÃO VERIFICADO`.

## Camada 4 — Exemplo concreto

- **ITEM real:** usar código/identificador do item; citar paths de evidência existentes.
- **Ilustrativo:** título com `(exemplo fictício)`; nenhum dado real; cenário mínimo mas completo.
- Percorrer o mapa etapa a etapa no exemplo, sem saltar gates que existam no AS-IS.

## Camada 5 — Como ler e como agir

- **Leitura:** ordem sugerida (resumo → mapa → etapa onde está bloqueado).
- **Ação:** o que fazer com pendência `NÃO VERIFICADO`; quem decide (humano vs agente); como retomar após bloqueio.
- **Não fazer:** alterar código ou processo só porque o diagrama sugere.

## Camada 6 — Glossário curto

- Termos do domínio (ITEM, E2E, paridade, DEF-AUDIT, etc.) em uma linha cada.
- Primeira ocorrência no corpo já deve estar compreensível; o glossário consolida.

## Metadados de fecho (no documento publicado)

```markdown
---
revisado_em: AAAA-MM-DD
fontes_conferidas: [lista de paths ou "snapshot histórico — ver nota"]
limites_lacunas: …
status_revisao: APROVADO | APROVADO COM RESSALVAS | PENDENTE
---
```
