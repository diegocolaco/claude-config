# Anexo — Novo SGD, DEV remoto (`profile sgd-novo`)

Carregar rule `playground-profiles` + `sgd-novo` quando o cenário for o Novo SGD.

## URLs

| Item | Valor |
|------|--------|
| SPA | `https://dev.sgd.dominiosistemas.com.br` |
| Keycloak | `https://auth.dev.sgd.dominiosistemas.com.br` (realm `sgd`) |

Slot local: só se o humano pedir — credenciais e seed em doc-credenciais-acesso.md e `ecosystem/automation/sgd-local/manual-seed/`.

## MCP (read-only)

| Serviço | Namespace | Banco lógico |
|---------|-----------|--------------|
| Plataforma / IAM | `user-SGDNOVO_DEV_PLATAFORMA` | `plataforma_db` |
| Comercial | `user-SGDNOVO_DEV_COMERCIAL` | `comercial_db` |
| Gestão | `user-SGDNOVO_DEV_GESTAO` | `projetos_db` |

Tool `query` — apenas `SELECT` com `LIMIT`. Mapa de tabelas: mapa-tabelas-servicos.md. Exemplos SQL: sgd-novo-dev-usuarios-validacao-item-161.md.

Auth/onboarding pontual: `user-SGDNOVO_DEV_AUTH`, `user-SGDNOVO_DEV_ONBOARDING`.

## Personas DEV

doc-credenciais-acesso.md § Smoke ITEM-161 + espelho sgd-novo-dev-usuarios-validacao-item-161.md.

## Acesso por personificação

No SGD novo o passo 4 da skill usa **só** o método 3: personificar o usuário no console admin do Keycloak (realm `sgd`), **sem** login CPF+senha. Rule testes-personificacao-keycloak.md; procedimento keycloak-personificacao-testes.md; credencial do console admin no doc de credenciais.

Só contas de teste permitidas; browser isolado; **não** Admin REST como atalho de sessão. Não alterar senha/MFA/roles. Troca de usuário: na aba personificada `POST /api/auth/logout` → `window.location.href = logoutUrl` do JSON (com `id_token_hint`; encerra só esta sessão); nunca «logout all sessions» global.

## Skills vizinhas (SGD)

`investigar-erro`, `roteiro-teste-manual`, `sgd-novo-sgd-observabilidade`.
