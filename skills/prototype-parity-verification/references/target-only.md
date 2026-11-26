# Alvo e rede

Resolver o projeto/worktree ativo e a origem exata da aplicação reconstruída. Toda navegação, subrequest e redirect precisa respeitar essa origem; `baseURL` sozinha não restringe URLs absolutas. Usar `createGuardedContext(browser, policy, options)` de `ecosystem/automation/proto_env/parity/target-policy.mjs` e fechar `guarded.close()` em finally. O factory cria um proxy local por contexto Chromium/Edge, bloqueia service workers/WebSocket e confere cada request e destino de redirect. Redirects internos mantêm URL e semântica do browser; destinos externos são negados antes de conexão. `installTargetGuard` isolado recusa contextos sem esse transporte, pois routing Playwright sozinho pode ignorar saltos posteriores.

Fonte estática nunca participa de `webServer`, workspace, build, instalação ou descoberta de testes. `validateBoundaries` é uma checagem conservadora de inputs estáticos, não parser completo nem sandbox. Import dinâmico não resolvido exige revisão explícita. Código e ferramentas Node do projeto continuam confiáveis: o guard protege o browser, não todo processo do sistema.

Sem captura autorizada da referência, não criar script que a abra para obter screenshot, CSS ou dropdown. Registrar a falta e continuar apenas os testes internos do target. Uma observação humana já documentada pode sustentar expected no limite do que realmente demonstra.

O fixture usa Playwright instalado indicado por `PARITY_PLAYWRIGHT_DIR`, versão verificada em `tests/parity/e2e/runtime-lock.json`. Ele executa só o projeto `reconstructed`, com target de brinquedo independente. Nenhum teste externo real foi portado nesse ensaio.
