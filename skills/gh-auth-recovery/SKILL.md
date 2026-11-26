---
name: gh-auth-recovery
description: Use quando gh ou git falhar por falta de autenticação (not logged into
  any GitHub hosts, credencial pedida em push/pull, 401/403 do GitHub), para seguir
  o procedimento de recuperação.
disable-model-invocation: true
---
CTX-ID: gh-auth-recovery@2

# `gh`/git sem autenticação — procedimento de recuperação

**Gatilho:** `gh` falha com `You are not logged into any GitHub hosts`, `git push`/`pull` pedindo credencial, erro 401/403 em chamada ao GitHub, ou qualquer passo de pr-sync-base-before-link.mdc que precise de `gh`. Rule **on-demand** (não always-on).

**Contexto:** `git` (push/pull HTTPS) e `gh` CLI guardam credenciais em sítios diferentes — `git` pode usar um credential helper (ex.: Git Credential Manager via `/mnt/c/...` em WSL) enquanto `gh` usa `~/.config/gh/hosts.yml`. Um a funcionar **não** implica o outro autenticado; diagnosticar sempre os dois antes de concluir "sem acesso".

## Procedimento

1. **Diagnosticar antes de agir:** `gh auth status`; se for push/pull, confirmar também o credential helper (`git config --get credential.helper`). Não assumir — confirmar qual dos dois falhou.
2. **Preferir login via browser (device flow):** `gh auth login --web` (ou equivalente). Funciona de qualquer máquina/browser e não expõe segredo nenhum no chat.
3. **Código expirou:** o código de uma tentativa expira em poucos minutos — gerar um novo e repetir **uma vez**. Não insistir indefinidamente na mesma tentativa.
4. **Device flow bloqueado por política de rede/SSO:** sinal = o humano reporta que a origem (IP/rede WSL-Linux) não consegue autorizar mesmo dentro da janela de validade, ou a organização exige SSO/IP-allowlist que o device flow não contorna. Neste caso, **parar de repetir device flow** e passar para o passo 5.
5. **Pedir Personal Access Token ao humano — só com o escopo mínimo da tarefa em curso.** Dizer explicitamente quais escopos pedir (ex.: ler PRs/repos privados de uma org → `repo` + `read:org`; não pedir `admin:*`, `delete_repo` nem outros escopos que a tarefa não precisa). Nunca sugerir "gerar um token com tudo" para evitar repetir o pedido depois.
6. **Receber e aplicar o token:**
   - Usar imediatamente via stdin — `printf '%s' '<token>' | gh auth login --hostname github.com --with-token` — nunca como argumento visível em `ps`/histórico do shell.
   - Confirmar com `gh auth status`.
   - **Nunca** ecoar o valor do token de volta ao humano (nem mascarado em excesso de contexto) — regra PII/segredos de global.mdc aplica-se a tokens, não só a CPF/CNPJ.
   - **Nunca** persistir o valor em ficheiros do repo, logs, memória ou commits.
7. **Token rejeitado por escopo em falta:** `gh` reporta o escopo exato (`missing required scope 'x'`) — repassar ao humano e pedir regeneração **acrescentando só esse escopo**, não trocando por um token genérico amplo.
8. **SAML SSO da organização** (`Resource protected by organization SAML enforcement`): falha **distinta** de escopo em falta — o login está correto e o token é válido, mas um PAT só alcança recursos de uma org com SAML depois de ser **autorizado para essa org**, token a token. Nenhum escopo, token novo ou re-login resolve; repetir o comando só repete o erro. O próprio `gh` imprime um link `https://github.com/orgs/<org>/sso?authorization_request=…` — **entregar esse link ao humano** (ou o caminho Settings → Developer settings → Personal access tokens → o token → *Configure SSO* → *Authorize* na org) e **parar até ele confirmar**. Vale igualmente para chaves SSH em orgs com SAML. O link muda a cada tentativa; se expirar, basta correr o comando outra vez para gerar outro.
9. **Depois do login bem-sucedido:**
   - Se o token aceite tiver escopos muito mais amplos do que o pedido no passo 5 (ex.: o humano gerou um token "de sempre" em vez do escopo pontual), avisar o humano — sugestão de princípio do menor privilégio, não bloqueio — e recomendar rotação para um token mais restrito quando for conveniente.
   - Se algum token foi colado em texto plano no chat e **não** foi o aceite (rejeitado, substituído), lembrar o humano de revogá-lo em GitHub → Settings → Developer settings → Personal access tokens, já que ficou exposto na conversa.
10. **Retomar a tarefa original** que disparou o diagnóstico (ex.: `gh pr view`, `gh pr diff`, `git push`) assim que a autenticação relevante estiver confirmada — não tratar a recuperação de credencial como o fim do pedido do humano.

## Não fazer

- Insistir em device flow repetidamente quando o humano já identificou bloqueio de rede/SSO.
- Pedir token com escopos acima do necessário "por garantia".
- Ecoar ou logar o valor de um token, mesmo parcialmente, além do necessário para confirmar que foi aplicado.
- Declarar a tarefa original concluída só porque o login foi resolvido — login é meio, não fim.
