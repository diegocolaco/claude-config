---
name: localizador-cenarios-teste
description: Use quando precisar de registro e persona em teste/homologação para validação manual ou E2E.
---
CTX-ID: localizador-cenarios-teste@4

# Localizador de cenários de teste — playground jarbas

**Projeto:** TR Jarbas Ai Multi-agents squad · **escopo:** workspace (qualquer profile ativo)

## Composição Superpowers

Localiza registro/usuário; **não** fecha causa nem propõe correção.

**REQUIRED BACKGROUND:** You MUST understand `superpowers:systematic-debugging` — usar só na fase 1 (preparar cenário); investigação completa: `investigar-erro` + SP.

## Missão e limite

Entregar rapidamente um **par utilizável (registro, usuário)** para que o agente executor reproduza o erro ou teste uma correção **sem refazer todo o fluxo**. Esta skill **não reproduz o defeito, não executa a ação de negócio e não valida a correção**. Não é sessão principal, não substitui E2E nem skills de investigação/roteiro do produto.

| Skill vizinha (exemplos) | Divisão |
|---|---|
| **`localizador-cenarios-teste`** | Encontrar registro + identidade + pré-condições na UI (**sem** clicar ação mutável) |
| **`roteiro-teste-manual`** | Roteiro no chat, login na tela, massa quando o alvo é local |
| **`investigar-erro`** (SGD novo) | Reprodução multi-usuário + Datadog + veredito — **depois** de ter cenário ou sintoma |

Registrar `trace_id`: `jarbas-AAAAMMDD-HHMMSS-xxxx`.

---

## Escolher produto e ambiente

1. Carregar rule **`playground-profiles`** e o `profile.yaml` do produto (ex.: `sgd-novo`).
2. Fixar **ambiente** (DEV remoto, homologação, slot local) — nunca produção salvo pedido explícito e autorizado.
3. Abrir o **anexo do profile** em `references/` desta skill, se existir (hoje: `references/anexo-sgd-novo-dev.md`). Sem anexo nem documentação de MCP/credenciais → estado **`BLOQUEADO`** até o humano indicar fonte.
4. **Incerteza de versão:** código no `repo/` pode divergir do deploy remoto; sinalizar na entrega.

---

## Procedimento

### 1. Descobrir o cenário necessário

A partir do relato, ficha governada, SDD/spec e código:

- Tela/ação, rota, API e serviço dono.
- Estado do registro, transições anteriores, flags, dependências (tenant, unidade, papel).
- Regras de autorização no código e na documentação do profile.
- Separar **confirmado** de **hipótese**.

Rule **`contexto-antes-de-alterar`**: esta skill **não altera** código.

### 2. Buscar registros via MCP (somente leitura)

- Usar namespaces MCP documentados no anexo do profile (`GetDynamicTool` + tool de query read-only).
- Consultas **seletivas** com `LIMIT` — começar com **até 5 candidatos**.
- Priorizar pré-condições completas, não só status final.
- Registros primeiro; vínculos/usuários nos melhores candidatos.
- **PII:** rule `global` — IDs técnicos no chat; credenciais de teste DEV só conforme exceção do doc do squad.

### 3. Determinar a identidade adequada

- Contas de teste **documentadas** no profile/`user-doc` têm prioridade.
- Correlacionar identidade na base com login no IdP por mapeamento verificável — não presumir equivalência de nome/e-mail/ID.
- Escopo depende do **registro e da ação**, não só do perfil nominal.
- Admin IdP **não** substitui autorização de negócio.

### 4. Estabelecer sessão (somente se necessário)

| Ordem | Método |
|-------|--------|
| 1 | Reutilizar sessão já correta no browser |
| 2 | Login com persona documentada (browser integrado / Playwright conforme política do profile) |
| 3 | **Impersonate** no console IdP — último recurso, sessão isolada e descartável |

Se o anexo do profile fixar outra política, ela prevalece. **SGD novo:** personificação é o **único** método (sem login com senha) — anexo § «Acesso por personificação».

**Proibido:** alterar senha, MFA, roles, grupos; persistir cookies/tokens em ficheiros versionados.

Confirmar na **aplicação** quem está autenticado.

### 5. Validar navegabilidade sem executar a ação

1. Abrir o registro (rota ou menu; anotar caminho).
2. Confirmar identidade, tenant/escopo, pré-condições na tela.
3. Ação correta **visível e habilitada** (ou motivo se desabilitada).
4. **Não** clicar aprovações, envios, integrações financeiras nem outras ações mutáveis.
5. Até **3 pares** na UI; descartar com justificativa curta.

### 6. Entregar ou encerrar

Fechar contexto de impersonate; não derrubar sessões globais de terceiros.

---

## Estados (somente três)

| Estado | Significado |
|--------|-------------|
| **`CANDIDATO`** | Banco/código prometem; UI incompleta |
| **`VALIDADO`** | Identidade + registro + pré-condições + ação disponível **sem executá-la** |
| **`BLOQUEADO`** | Sem par confiável nos limites de acesso/tempo |

`VALIDADO` não prova defeito nem aceitação pelo backend.

---

## Resposta curta ao agente executor

`ESTADO | ambiente | tela/ação | registro (ID mínimo) | identidade + escopo | pré-condições confirmadas/pendentes | como abrir | descarte/bloqueio | tempo (opcional)`

---

## Restrições essenciais

- MCP **somente leitura**.
- Personificação só teste/homologação, identidades permitidas, sessão não compartilhada entre workers/Task.
- Não manter impersonate entre agentes.

---

## Referências por profile

| Profile | Anexo |
|---------|--------|
| `sgd-novo` | `references/anexo-sgd-novo-dev.md` |

Novos profiles: acrescentar anexo nesta pasta + linha na tabela (skill `jarbas-author-skills-rules`).
