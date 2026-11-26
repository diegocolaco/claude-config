---
description: Preferências gerais do usuário que valem em todo chat e em todo contexto.
---

CTX-ID: rule-user-global@23

É proibido fazer `git push`, enviar commits, branches ou qualquer alteração para remoto Git (`origin`, `diegocolaco`, GitHub ou equivalente) e contornar o hook `.githooks/pre-push` (por exemplo com `--no-verify`); agentes não publicam nada — todo o workspace permanece só local.

Quando eu pedir para finalizar uma tarefa, quero que também no final atualizar o branch develop origem e o branch local develop

Ao concluir uma etapa que encerra um bloco de trabalho (por exemplo, após o write-plan do Superpowers, o spec aprovado ou uma fase executada), sugira em uma linha que eu compacte o contexto antes de seguir para a próxima etapa.

Ao final de cada resposta, informe qual é a próxima etapa a ser executada, com uma breve descrição.

Responder sempre em PT-BR, exceto termos técnicos.

Sempre que possível, ao referenciar branch ou commit, gerar o link do git web correspondente para eu visualizar.

Sempre que possível, ao referenciar um branch que tenha upstream no remoto (tracking publicado), incluir o link do pull request (PR) em Markdown para eu fazer code review — por exemplo com `gh pr view` naquele branch/repo ou pela URL do PR no git web quando já existir.

**Caminhos locais clicáveis:** em texto corrido (listas, explicações, próxima etapa), sempre que mencionar um caminho de arquivo ou de pasta do workspace, formate como hiperlink Markdown `[texto](/caminho/absoluto/ou/relativo)` com o mesmo caminho no destino, para abrir no IDE com um clique. Ex.: [/home/diego/.claude.json](/home/diego/.claude.json) em vez de só `/home/diego/.claude.json`. Isso vale também para caminhos dados como valores (por exemplo `cd /projeto/foo`). Exceção: dentro de blocos de código onde o conteúdo deva ser copiado literalmente, mantenha o caminho puro, sem Markdown de link.

**Deploy: controlador antes do produto:** sempre que possível, coloque configurações e artefatos de deploy (orquestração, slots, env local, scripts de pipeline do laboratório, composição que não seja parte do build do app) no repositório **controlador** (este playground / TR Jarbas), não no repositório do **produto** sob `repo/` (por exemplo `repo/ebs-dominio_sgd`, `repo/sgd-novo-lovable`). O que for exigência do produto em si — Dockerfile ou entrypoint do app, variáveis só do runtime da aplicação, manifest de K8s que acompanha o release do binário, etc. — fica no repositório do produto; quando não for óbvio, prefira controlador e documente em uma linha por que precisou ir ao produto.

Os repositórios que estão na raiz do workspace (o próprio TR, `repo/ebs-dominio_sgd` e `repo/sgd-novo-lovable`) devem estar sempre no branch `agregado/local` no checkout principal. Trabalho de tarefa continua em worktree próprio, com branch própria; ao terminar, se o checkout principal tiver saído de `agregado/local`, volte-o para lá. Se o checkout principal não puder trocar (alteração local que conflita ou o branch preso a outro worktree), pare e relate em vez de forçar.

O `agregado/local` deve estar sempre atualizado com o `develop`: depois que um PR for mergeado no `develop` (por mim ou por outra pessoa), integre o `develop` atualizado (após `git fetch`) no `agregado/local` dos repositórios da raiz que tenham `develop`, num worktree próprio, e leve o resultado ao checkout principal. Preserve o overlay local do agregado ao resolver conflitos e liste no fim cada decisão. O `agregado/local` fica só local: sem push. Se o merge tiver conflito que eu não consiga resolver com segurança, pare e relate.

Se eu chamar um comando (`/nome`) que não existir, pare sem fazer a tarefa, mostre o nome mais parecido e pergunte. Não faça a tarefa sem o comando. Se eu pedir, sem comando, uma correção em tela do SGD, pergunte antes se é um ajuste para ficar igual ao protótipo.

Antes de mudar qualquer processo, como ajuste de telas ou deploy, leia a versão atual e o histórico da especificação dele em `user-doc/spec/processos/`. Ao mudar a especificação, crie um arquivo novo e nunca edite o anterior, que fica como histórico. Siga a skill `especificacao-processos`.

**Shell e política do ambiente:** não use Bash para percorrer o repositório com `find`, `grep -r` na árvore inteira, `ls -R` nem para ler configurações com `cat`/`head` em arquivos de settings ou hooks (por exemplo [.claude/settings.json](/home/diego/projetos/TaxProf_brtap-integration-playground/.claude/settings.json), hooks em `.githooks/`, programas auxiliares do Jarbas) quando isso puder ser negado pelo harness ou for redundante. Para localizar arquivos ou trechos, use as ferramentas do workspace `Glob`, `Grep` e `Read`. Se o usuário pedir explicitamente um comando que foi negado, relate o bloqueio uma vez e ofereça a alternativa com essas ferramentas ou peça que ele execute o comando localmente — não insista repetindo o mesmo comando Bash negado.

Não rode lint direto no produto (`repo/ebs-dominio_sgd` e os worktrees dele): nada de `pnpm lint`, `turbo run lint` ou `eslint` lá dentro, porque estoura a memória. Rode a partir do controlador: `python3 ecosystem/automation/sgd_lint/lint_sgd.py roda --worktree <worktree do produto>` (ou `--branch <branch>`), e compare antes e depois com `lint_sgd.py compara`. O hook `block-sgd-lint.py` bloqueia o lint direto.
