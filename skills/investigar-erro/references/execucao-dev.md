# Execução autônoma no DEV e usuários de QA

Ler antes do passo 2 (reprodução) e no smoke de `validar-comportamento-dev-prototipo` no DEV.

## Execução autónoma no DEV

Quando o Diego pedir investigação, smoke ou reprodução no DEV remoto, o agente **executa sozinho** — **não** pedir para
abrir navegador, janela anônima nem fazer login manual.

| Passo | Ação |
|-------|------|
| Acesso | **Personificação no Keycloak** — rule `testes-personificacao-keycloak` (profile `sgd-novo`) + keycloak-personificacao-testes.md; **sem** login CPF+senha do usuário. Credencial do console admin: doc-credenciais-acesso.md (PII mascarada em relatórios — ver rule `global`, exceção de credenciais de teste) |
| Usuários | Percorrer **todos os disponíveis** da lista abaixo; a ficha do ITEM pode indicar persona prioritária (tentar essa **primeiro**, sem saltar as demais) |
| Troca de sessão | Na aba personificada: `POST /api/auth/logout` → `window.location.href = logoutUrl` do JSON (com `id_token_hint`; encerra só esta sessão) → personificar o próximo CPF no console. Não reutilizar sessão de outro CPF; nunca «sign out all sessions» |
| Gravação | **Liberada** no DEV remoto sem pedir aprovação, **exceto na empresa Dominio**; conferir a empresa do usuário antes; prefixo `ZZ-TESTE-<trace_id>`; listar o que foi gravado |
| Escalada humana | Só se a personificação falhar após **2 tentativas por usuário**, nenhum CPF resolvido na lista, ou `[jarbas PERSONIFICACAO BLOCKED]` (sem credencial admin, console fora, usuário fora do realm) — reportar o bloqueio concreto, não pedir «vá logar» por padrão |

Vale para o **passo 2 (reprodução)** e para o smoke da `validar-comportamento-dev-prototipo` no DEV.

### Usuários de QA no DEV (lista canónica ITEM-161)

«Smoke» = **roteiro mínimo de acesso (personificação) + ação do relato** com personas documentadas — **não** significa teste sem evidência.
Fonte: sgd-novo-dev-usuarios-validacao-item-161.md + credenciais § Smoke ITEM-161 (**CPF e senha ficam só nesses docs — não
copiar para ficheiros novos**). **Disponível** = linha com CPF de 11 dígitos no doc, usuário ativo e existente no realm `sgd`
(extras da tabela incluídos; senha **não** é requisito). **Indisponível** (registar na matriz, não bloquear os outros): CPF
*pendente*, usuário inativo na base, fora do realm, ou personificação/BFF impossível após 2 tentativas.

Ordem sugerida: **#1** → extras *Vendedor SC* e *Vendedor SC — Floripa* → **#2** → **#3** → **#4** → **#5** (só se CPF resolvido).
Extras da tabela fora desta lista (ex.: *Vendedor joinville 2*) entram como disponíveis; o comando não fixa a posição — usar
depois do #2.
