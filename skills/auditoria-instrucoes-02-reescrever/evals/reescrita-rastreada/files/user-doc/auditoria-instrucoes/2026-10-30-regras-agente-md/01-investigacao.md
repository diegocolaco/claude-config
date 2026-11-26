---
etapa: "01"
status: concluida
alvo:
  - caminho: regras-agente.md
    sha256: c234ac4685ec8d4164b22ebc2f624a543d05d83ca04327c26286638c9f6bf077
commit_base: desconhecido
data: 2026-10-30
motivo_status: ""
---

# Investigação: regras-agente.md

## Escopo e runtimes

- Material: regras-agente.md (carregado pelo Claude Code como CLAUDE.md da raiz), commit sintético.
- Runtime: Claude Code. Frentes: carregamento de instruções; CLI; Git e qualidade. Fontes acessadas em 2026-10-30.

## Inventário de diretivas

| ID | Linhas | Diretiva (resumo) |
|---|---|---|
| D1 | L3 | O arquivo é o CLAUDE.md da raiz; Node.js 22; testes com `npm test` |
| D2 | L7 | Responder em português do Brasil |
| D3 | L11 | Branch própria; não commitar na `main` |
| D4 | L12 | Não fazer push para a `main`, salvo tarefa urgente |
| D5 | L13 | Rodar os testes antes de commitar |
| D6 | L17 | CLAUDE.md em subdiretórios é ignorado |
| D7 | L21 | Usar `claude --auto-approve-all` para não pedir confirmações |
| D8 | L25 | Ser cuidadoso e escrever código de qualidade |
| D9 | L26 | Rodar os testes antes de commitar (repetida) |

## Achados por tema

### Carregamento de instruções

#### Conclusão
D6 está errada: o Claude Code também carrega CLAUDE.md de subdiretórios, sob demanda.

#### Achados citados
- CLAUDE.md em subdiretórios abaixo do diretório de trabalho é carregado quando o Claude lê arquivos nesses subdiretórios — [Claude Code: memory](https://code.claude.com/docs/en/memory), acesso 2026-10-30. Diretivas: D6.

#### Inferências
- Seguir D6 leva a concentrar regras de módulo na raiz, aumentando o contexto carregado em toda sessão (certeza alta).

#### Lacunas
- Nenhuma.

### CLI

#### Conclusão
A flag de D7 não existe.

#### Achados citados
- A referência da CLI não lista `--auto-approve-all`; o modo sem confirmações é controlado por `--permission-mode` (valores como `acceptEdits` e `bypassPermissions`) ou `--dangerously-skip-permissions` — [CLI reference](https://code.claude.com/docs/en/cli-reference), acesso 2026-10-30. Diretivas: D7.

#### Inferências
- Um agente que siga D7 sugere ao usuário um comando que falha (certeza alta).

#### Lacunas
- Nenhuma.

### Git e qualidade

#### Conclusão
D3, D4 e D5 são políticas locais sem fonte externa; D4 tem exceção indefinida; D5 e D9 duplicam a mesma regra; D8 não tem ação observável.

#### Achados citados
- `package.json` do projeto define `npm test` (comportamento local). Diretivas: D1, D5.

#### Inferências
- "Urgente" em D4 não tem critério; o agente pode classificar qualquer tarefa como urgente (certeza alta).
- D8 não muda nenhum comportamento verificável (certeza média).

#### Lacunas
- Não há fonte sobre o motivo de proteger a `main` (política local).

## Práticas genéricas ou obsoletas

- D6: supõe carregamento só da raiz × a documentação descreve carregamento sob demanda de subdiretórios.
- D8: boa intenção genérica sem ação observável.

## Cobertura

| ID | Status | Achado ou motivo |
|---|---|---|
| D1 | sustentada | Git e qualidade, achado 1 |
| D2 | fora-de-escopo | preferência explícita do usuário |
| D3 | sem-fonte | política local |
| D4 | sem-fonte | política local; exceção sem critério |
| D5 | sem-fonte | política local; duplicada por D9 |
| D6 | contrariada | Carregamento, achado 1 |
| D7 | contrariada | CLI, achado 1 |
| D8 | sem-fonte | sem ação observável |
| D9 | sem-fonte | duplicata de D5 |

Totais: 1 sustentada, 2 contrariadas, 5 sem-fonte, 1 fora-de-escopo.

## Implicações para a etapa 02

- D4 não impede push na `main` sob alegação de urgência.
- D7 orienta um comando inexistente.
- D6 induz a concentrar regras na raiz.
