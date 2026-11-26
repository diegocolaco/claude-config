---
name: documentar-user-doc
description: Use quando pedirem apenas documentar ou registrar algo em user-doc/.
---
CTX-ID: documentar-user-doc@3

# Documentar em `user-doc/`

**Projeto:** TR Jarbas Ai Multi-agents squad

## Quando usar

- "documente", "apenas documente", "documente isso", "registre na documentação", "deixe documentado".
- O Diego pausa uma tarefa e pede só a documentação ("vou continuar depois, apenas documente").

"Apenas documente" = **não implementar nem continuar a execução**; só registar o estado, as decisões e como retomar.

## Gate de segurança (antes de gravar)

1. Ler e executar a skill **`documentar-seguranca-gate`**: parar e perguntar ao Diego sobre exportar conteúdo que possa comprometer segurança ou confidencialidade da Thomson Reuters. Sem gravar nada até a resposta.
2. Se o material traz PII, credencial ou segredo, apontar cada item na pergunta e usar as máscaras `CPF:***`, `CNPJ:***`, `TOKEN:[REDACTED]`, `EMAIL:[REDACTED]` no documento.
3. **Só depois** da confirmação explícita do Diego, seguir as seções abaixo (destino, conteúdo, fecho).

## Onde gravar

```
user-doc/
├── README.md                     convenção + áreas
└── <área>/                       ex.: novo-sgd/
    ├── README.md                 índice da área (obrigatório manter)
    ├── <doc vivo>.md             manuais, definição, histórico, diário, runbooks (raiz da área)
    ├── relatorios/               análise/relatório pontual: AAAA-MM-DD-<assunto>.md
    ├── planos-ecossistema/       plano de mudança no ecossistema: AAAA-MM-DD-<assunto>.md
    └── temas/<tema>/             dossiê de um assunto com vários documentos ao longo do tempo
        ├── README.md             estado atual + linha do tempo + índice do tema
        └── AAAA-MM-DD-<assunto>.md
```

**Regra Canónica Inviolável:** Tudo o que diz respeito ao ecossistema, playground, workspace, regras e ferramentas do jarbas/jarbinhas deve ser documentado exclusivamente em `user-doc/ecossistema-jarbas/`.

**Especificação de processo** fica em `user-doc/spec/processos/`, com versões, conforme a skill `especificacao-processos`.

Escolha, por esta ordem:

1. **Já existe um documento vivo que é a fonte** (ex.: o histórico do processo de ITEM
   doc-sgd-novo-processo-item-historico.md, o diário, o manual) → actualizar esse documento. Se o assunto
   também tem tema, acrescentar uma linha no README.md do tema a apontar para lá.
2. **O assunto já tem pasta em `temas/`** → documento novo datado nessa pasta + actualizar o README.md do tema
   (estado atual e linha do tempo).
3. **Assunto com mais de um documento previsto** (investigação → decisão → implementação) → criar
   `temas/<tema-em-kebab-case>/` com README.md + o documento.
4. **Análise única** → `relatorios/AAAA-MM-DD-<assunto>.md`. **Plano de ecossistema** → `planos-ecossistema/`.
5. **Área nova** (outro produto/frente, ex.: legado) → criar `user-doc/<área>/README.md` (índice da área) e acrescentar uma linha no README.md da raiz de `user-doc/`.

Depois de criar ou mover: actualizar **sempre** o README.md da área (e o do tema).

**Não mover** documentos existentes que regras, skills ou comandos citam (procurar com
`rg -l "<nome-do-ficheiro>" -g '!user-doc/**' -g '!.tmp/**' -g '!repo/**' -g '!.worktrees/**'`); mover só com as
referências actualizadas no mesmo commit.

## Conteúdo (cada documento)

Regra de comunicação `communication-context`: o documento tem de se entender **sozinho**, sem o chat e sem abrir
outros ficheiros.

```markdown
# <Assunto em palavras> — <área> (<DD/MM/AAAA>)

Projeto: TR Jarbas Ai Multi-agents squad · trace: `<trace_id>`

Pedido do Diego (verbatim): «…»

## Resumo
<3–6 linhas: o que se descobriu/decidiu e o estado atual>

## <Secções do assunto: contexto, medições, causa, decisão, riscos…>
<fato, inferência e proposta separados; números com a fonte>

## Estado atual e próximos passos
<estado (vocabulário de communication-context) · o que falta · quem faz · como retomar>

## Onde está a evidência
<commits, jobs, traces, caminhos — complementar, não substitui o texto>

```

- Citações do Diego **verbatim**; decisões com a pergunta e a resposta.
- PII sempre mascarada, como no gate de segurança.
- Códigos (ITEM, PROC, GAP, DEC, SHA) sempre com o significado ao lado.
- UTF-8: depois de gravar, confirmar que não há U+FFFD.

## Análises sem pedido de documentar

Análises (gargalos, lentidão, causa, comparação, eficiência, auditoria) são gravadas mesmo sem "documente": skill
`analises-documentadas`, que usa esta skill para o destino e o formato base.

## O que esta skill não substitui

- O histórico do processo de ITEM continua obrigatório quando o processo muda (regra `item-process-docs`, skill
  `item-process-changelog`); o documento em `temas/` aponta para a entrada `PROC-…` correspondente.
- SPEC/CHANGELOG do controlador de slots (`sgd-slot-spec-governance`), fichas de ITEM e `docs/execucao/` seguem as
  suas regras; quando houver ficha de sessão, o documento em `user-doc/` é a versão legível para o Diego.

## Fecho

1. Editar num worktree do playground e commitar lá (regra `playground-commit-required`); o commit não pede permissão; integrar em
   `agregado/local` com `merge-worktree-to-agregado.sh` quando o humano escolher merge local.
2. Responder ao Diego com o caminho do documento e, em 2–4 linhas, o que ficou registado.
