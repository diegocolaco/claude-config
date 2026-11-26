---
name: exportar-chat
description: Use quando montar pacote sanitizado de conversa e artefatos em user-doc/ para revisão externa ou arquivo.
disable-model-invocation: true
---
CTX-ID: exportar-chat@1

# Exportar chat — pacote sanitizado para agente externo

**Projeto:** TR Jarbas Ai Multi-agents squad

## Quando usar

- "exporta o chat", "exportar conversa", "pacote para agente externo revisar", "exportar sessão".
- Depois de spec/plano/entrega: juntar **documentos da sessão** + **histórico legível** num único handoff.

**Não confundir** com o backup incremental de **todas** as conversas Cursor, nem com `governance-export*` (governança Jarbas).

Para **fotografia fiel** de sessão/ITEM com inventário SHA-256, estrutura `00/01/02`, ZIP e cobertura COMPLETO/PARCIAL → skill **`exportar-conversa-e-arquivos-para-revisao`** (esta skill permanece o atalho para exportar a conversa).

## Ordem obrigatória

1. **`documentar-seguranca-gate`** — se o Diego **não** disse explicitamente "sanitizado / sem segredos / para revisor autorizado", parar com checklist de risco e destino (git + partilha fora).
2. Inventariar **artefatos** a incluir (spec, plano, ficha, `.tmp/<trace_id>/…`) — **nunca** `doc-credenciais-acesso`, `.env`, dumps com PII.
3. Gerar o pacote com `python3 ecosystem/automation/jarbas.py export-consolidated` + índice `user-doc/<área>/README.md`.
4. **`playground-commit-workflow`** se alterou ficheiros versionados no playground.

## Automação (fonte da verdade do formato)

```bash
```

| Flag | Uso |
|------|-----|
| `--trace-id` | Rastreio da sessão (`jarbas-…` ou harness) |
| `--dir-slug` | Pasta em `user-doc/<área>/relatorios/` |
| `--artifact` | Repetível: foo.md |
| `--transcript-id` | UUID em `~/.cursor/projects/.../agent-transcripts/<id>/` |
| Sem id | Usa o `.jsonl` mais recente do workspace (ou do projeto) |

**Saída do pacote** (sempre):

| Ficheiro | Conteúdo |
|----------|----------|
| README.md | Ordem de leitura + aviso TR |
| CHECKLIST-DOC-SECURITY.md | Decisões omitir/mascarar |
| CONVERSA-EXTERNAMENTE-SEGURA.md | Turnos user/assistant, **sem** `tool_use` |
| RESUMO-NARRATIVO-SESSAO.md | Opcional (`--resumo`) |
| `artefatos/` | Cópias `--artifact` (texto passa por `mask_pii` + mascaramento de paths) |
| `../<tar-name>` | Tarball na pasta `relatorios/` |

**Proibido no pacote externo:** `CONVERSA-CURSOR-TRANSCRIPT.jsonl`, credenciais, transcript bruto com metadados de ferramentas.

## Procedimento manual (se CLI falhar)

1. Resolver transcript: `agent-transcripts/<uuid>/<uuid>.jsonl` (ver bloco `transcript_location` no chat Cursor).
2. Gerar CONVERSA-EXTERNAMENTE-SEGURA.md só com `role` user/assistant e texto (mesma lógica que `export_chat/build_package.py`).
3. Mascarar paths: `$PLAYGROUND_JARBAS`, `$WORKTREE_ITEM`, `$REPOS`, `$CURSOR_HOME` (nunca `/home/<user>/…`).
4. Aplicar `mask_pii` de `ecosystem/automation/backup/export_cursor_chats.py` em markdown copiado.
5. `tar -czf` da pasta; atualizar índice em `user-doc/<área>/README.md` (linha datada + link README do pacote + `.tar.gz`).

## Índice user-doc

Acrescentar em `user-doc/<área>/README.md`:

```markdown
| DD/MM | [Título](relatorios/<dir-slug>/README.md) · [`.tar.gz`](relatorios/<tar-name>) |
```

## Fecho na resposta ao Diego

Uma linha: **Gate DOC-SECURITY:** aplicado; **paths:** `relatorios/<dir-slug>/` e `relatorios/<tar-name>`; **omitido:** transcript JSONL e tool_use.

## Integração

| Artefato | Papel |
|----------|--------|
| `documentar-seguranca-gate` | Antes de gravar/exportar |
| `documentar-user-doc` | Convenção de pastas `relatorios/` |
| `playground-commit-workflow` | Commit do pacote em `user-doc/` |
