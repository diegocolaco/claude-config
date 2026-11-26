---
description: Evita turno de 1M+ tokens com cache frio no Composer; não substitui as
  outras rules.
---

CTX-ID: composer-token-spike@1

# Pico de tokens (Composer e Claude)

Investigação e leitura: modo Ask (Cursor) ou plan/read-only (Claude Code), uma resposta. Agent só para editar arquivo.

- Não liste o catálogo MCP inteiro. Escolha um namespace e uma ferramenta.
- No máximo 6 chamadas de ferramenta; em seguida responda com o que já tiver.
- Arquivo grande: só o intervalo de linhas. Não cole transcrição, log nem diff bruto.
- Várias rodadas de ferramenta no mesmo fio: abra chat ou sessão nova, em vez de continuar o fio longo (no Claude Code, `/compact` ou `/clear`).
- Não reescreva rules no meio do chat. Prefixo estável é o que permite cache.

