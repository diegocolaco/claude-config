# RESTORE e STATUS — recuperar contexto por relevância, não por volume

## RESTORE

Quando: chat novo, retomada de assunto, mudança de frente, ou resposta que depende de decisões anteriores.

1. **Frente.** Deduzir o slug pelo pedido ("continuar o Playwright" → `playwright`). Sem pista: ler só o Índice (do `## Índice` até ao cabeçalho seguinte) e perguntar qual frente, ou seguir se só houver uma ativa.
2. **Localizar** com um único Grep `-n` no caminho do ficheiro, combinando o mapa e a frente: `^#{2,3} |\b<slug>\b|afeta: todas` (ex.: `^#{2,3} |\bplaywright\b|afeta: todas`; o `\b` evita que `spec` case com "especificação"). As linhas de decisões, restrições, dependências e problemas já chegam completas no resultado; os cabeçalhos dão os números de linha para o passo seguinte.
3. **Ler só blocos:** Read da secção `### frente: <slug>` e dos `### H-###` cujo `Impacta:` cita a frente, com `limit` até ao cabeçalho seguinte. Não abrir secções de outras frentes; uma dependência entra pela linha de decisão ou handoff que a descreve.
4. **Fontes externas** (SDD, ficha ITEM, plano) só se o próximo passo precisar delas; abrir o ponteiro, não procurar às cegas.
5. **Guardar** o `rev` das secções lidas (serve para o SYNC detetar concorrência).
6. **Resumir e continuar o trabalho** sem esperar confirmação, salvo frente ambígua:

```markdown
**Retomando `<frente>`** (estado de AAAA-MM-DD, rev N)
- Objetivo: …
- Estado atual: …
- Decisões relevantes: D-003 (de `infra`: …)
- Pendências: …
- Dependências / handoffs: H-002 de `playwright` → rever critério X
- Próximo passo: …
```

No máximo ~10 linhas. Handoffs pendentes para esta frente vêm primeiro, porque são o que o utilizador não se lembraria de trazer. Se o `Atualizado:` da frente tiver mais de 7 dias, marcar "estado possivelmente desatualizado" e confirmar com o utilizador antes de agir sobre ele.

Se o ficheiro não existir ou a frente não tiver secção: dizer que não há estado registado, perguntar o essencial (objetivo e ponto atual) e criar a secção via SYNC.

## STATUS

Quando: "onde estamos", "o que está bloqueado", "quais frentes estão ativas", ou **supervisão periódica** (tick de `/loop`) — usar o mesmo fluxo; incluir **Subagentes (runtime)** abaixo sem abrir cada chat de subagente no UI.

1. Ler só o Índice (do `## Índice` até ao cabeçalho seguinte), mais um Grep `-n` de `^- P-|^### H-|^Impacta:|^- D-` no caminho do ficheiro (problemas, handoffs e decisões).
2. Responder com:
   - frentes ativas e estado numa linha cada (marcar as com `Atualizado` > 7 dias);
   - o que está bloqueado e por quê;
   - handoffs pendentes (origem → destino);
   - as 3 decisões mais recentes (pela data);
   - próximos passos;
   - **Subagentes (runtime)** — secção seguinte (obrigatória em supervisão; opcional se o utilizador só perguntou por uma frente isolada).
3. Detalhar uma frente só se o utilizador pedir (aí é um RESTORE dessa frente).

Quando ajudar, mostrar a posição no processo com o **painel compacto** da rule `communication-context` (Objetivo / Etapa / Status / Próxima / Com você).

### Subagentes (runtime) — só STATUS, não persistir

**Proibido** copiar esta tabela para PROJECT-STATE.md. Só evidência legível nas transcrições; se não houver, dizer explicitamente.

1. **Localizar** (sem nova skill/loop): pasta do projeto Cursor  
   `~/.cursor/projects/<workspace-slug>/agent-transcripts/`  
   Preferir `.../<id-conversa-atual>/subagents/*.jsonl`. Sem id da conversa: os `.jsonl` em `**/subagents/` desse projeto com `mtime` nas últimas **2 h**, mais recentes primeiro (máx. **5**).
2. **Por ficheiro** (Read `offset` negativo ~40 linhas ou Shell `tail -n 30`):
   - **Agente + tarefa:** primeira mensagem `user` (ex. `[jarbas → …]`, título `Task`, `description` do spawn).
   - **Agora:** última mensagem `assistant` com texto ou último `tool_use` / `tool_name` (só o que estiver escrito).
   - **Último progresso:** último resultado observável citado (path, commit, veredito PASS/FAIL, ficheiro criado) — uma linha.
   - **Bloqueio / próximo:** veredito final se existir; senão «em curso» ou «sem visibilidade» se o ficheiro não permitir inferir.
3. **Excluir** da lista subagentes claramente **encerrados** (última linha assistant com entrega fechada: veredito EXEC DONE, PARIDADE-PRE PASS, relatório de verificação (`jarbas.py check`), etc., sem `tool_use` aberto depois).
4. **Nenhum elegível:** uma linha `Subagentes: sem visibilidade (transcrições ausentes ou vazias).` — não inventar nomes nem estado.

Formato (compacto):

```markdown
### Subagentes (runtime)
| Agente | Tarefa | Agora | Último progresso | Bloqueio / próximo |
|--------|--------|-------|------------------|-------------------|
| task-implementer | EXEC ITEM-1041 | … | … | … |
```

Em ticks de supervisão, esta tabela vem **depois** do resumo de frentes/bloqueios e **antes** de decidir delegar ou interferir.
