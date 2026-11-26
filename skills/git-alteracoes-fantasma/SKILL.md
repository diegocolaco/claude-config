---
name: git-alteracoes-fantasma
description: Use quando git status mostrar centenas de arquivos modificados sem edição intencional.
---
CTX-ID: git-alteracoes-fantasma@2

# Alterações fantasma no git — diagnóstico e correção

## Composição Superpowers

Diagnóstico jarbas de comportamento inesperado do git; segue o método do Superpowers.

**REQUIRED BACKGROUND:** You MUST understand `superpowers:systematic-debugging` — distinguir ruído de alteração real com evidência antes de corrigir.

Contexto medido deste workspace (topologia, números, histórico dos dois casos já
resolvidos): git-topologia-workspace.md.

## Princípio

**Contagem alta não é prova de alteração.** Antes de propor qualquer correção, provar por
conteúdo se o ficheiro mudou. Há casos reais escondidos no meio do ruído — neste workspace,
o `ebs-dominio_suporte` tinha 184 alterações verdadeiras enquanto outros quatro clones
tinham 3.586 falsas.

E o inverso também: **nunca declarar «limpo» a partir de um `git status` que pode estar a
ler cache** (ver Armadilha 2).

---

## Passo 1 — Mapear o que está sob git

```bash
# @platform: wsl-bridge
find . -maxdepth 5 -name .git -print | sort        # repositórios em disco
git check-ignore -v <pasta>/<um-filho-real>        # confirmar se está ignorada
```

Um repositório aninhado só pesa no painel se **não** estiver ignorado pelo repositório pai
e se o VS Code abrir uma pasta dentro dele. Worktrees **partilham o `.git/config` da raiz**:
configurar a raiz cobre todos.

> **Testar o filho, não a pasta.** Com o padrão `pasta/*` — a forma usada aqui para
> `repo/*` e `.worktrees/*`, que permite reincluir um filho com `!` — o `check-ignore`
> responde «não casa» tanto para `.worktrees` como para `.worktrees/`, porque o padrão
> cobre os filhos e não a pasta em si. Só `git check-ignore -v .worktrees/wt-algo` devolve
> a regra. Padrões `pasta/` (como `.tmp/`) casam com a própria pasta. Na dúvida, a prova
> final é o `git status`, não o `check-ignore`.

## Passo 2 — Medir como o VS Code mede

```bash
git status --porcelain | wc -l            # colapsa pastas não rastreadas — ESCONDE o problema
git status --porcelain -uall | wc -l      # o que o VS Code realmente vê
```

Se os dois números divergirem muito, o problema é **não rastreado**; siga para o Caso A.
Se forem parecidos e altos, é **modificado**; siga para o Caso B.

Agrupar por pasta de topo para achar a origem:

```bash
git status --porcelain -uall | awk '{print $NF}' | awk -F/ '{print $1"/"$2}' | sort | uniq -c | sort -rn | head -20
```

---

## Caso A — enxurrada de não rastreados

Uma pasta de artefactos saiu do `.gitignore`. Confirmar que nada dela está versionado antes
de a ignorar de volta:

```bash
git ls-files <pasta> | wc -l      # 0 = ignorar não perde nada
```

Ao repor a linha no `.gitignore`, lembrar que a pasta desaparece também da pesquisa do
Cursor. Para manter a busca, negar no `.ignore`, que tem precedência sobre o `.gitignore`
no ripgrep:

```
!<pasta>/
!<pasta>/**
```

Os quatro ficheiros de ignore fazem coisas diferentes — a tabela está no documento de
topologia citado no topo. Em resumo: `.gitignore` tira do git e da busca; `.ignore` devolve
à busca; `.cursorindexingignore` tira do índice mas mantém o `Read` do agente;
`.cursorignore` esconde até do `Read`.

---

## Caso B — modificados que não mudaram

### B1. Confirmar que é fim de linha

```bash
git diff --name-only | wc -l                      # o que o git acusa
git diff --ignore-cr-at-eol --name-only | wc -l   # o que resta ignorando CR no fim da linha
```

A diferença entre os dois é ruído de CRLF. O que resta é candidato a alteração real.

### B2. Provar por conteúdo (não confiar no status)

```bash
git hash-object --path <ficheiro> <ficheiro>      # hash do disco, com os filtros aplicados
git rev-parse HEAD:<ficheiro>                     # hash do commit
```

Hashes iguais ⇒ conteúdo idêntico, a diferença é só de fim de linha.

### B3. Identificar a origem Windows

Três marcadores independentes; dois bastam para concluir:

```bash
git config --get core.symlinks     # false  ⇒ auto-detetado no Windows
git config --get core.filemode     # false  ⇒ idem
git config --get core.ignorecase   # true   ⇒ idem
stat -c '%y' <ficheiro>            # .xxxxxx00 (100 ns) ⇒ NTFS; nanossegundos cheios ⇒ ext4
git reflog show --date=iso | tail -1   # data do clone; mtime anterior ⇒ a pasta foi copiada
```

O `core.autocrlf=true` que gerou o CRLF vive no `~/.gitconfig` do Windows e **não** viaja
com a pasta `.git` copiada. É por isso que o efeito só aparece depois de a pasta chegar ao WSL.

### B4. Corrigir

Antes de aplicar, testar **em cada repositório** que a configuração não piora (um repo com
ficheiros commitados em CRLF ganharia falsos positivos novos):

```bash
git -C <repo> diff --name-only | wc -l
git -C <repo> -c core.autocrlf=input diff --name-only | wc -l    # tem de ser <= ao anterior
```

Aplicar local, nunca global:

```bash
git -C <repo> config core.autocrlf input
```

Se o `git status` continuar a acusar depois disso, e `git update-index --refresh` repetir
«needs update» sem convergir, o cache de stat está preso. Reconstruir o índice:

```bash
git -C <repo> diff --cached --name-only | wc -l    # tem de ser 0 (nada em staging a perder)
cp <repo>/.git/index /tmp/index.bak                # rede de segurança
git -C <repo> read-tree HEAD                       # recria o índice; NÃO toca em ficheiros
```

### B5. Validar o risco, não só o número

O perigo real é um `git add -A` gravar CRLF em milhares de ficheiros. Provar que acabou,
usando um índice descartável que não mexe no real:

```bash
cp <repo>/.git/index /tmp/idx-teste
cd <repo> && GIT_INDEX_FILE=/tmp/idx-teste git add -A
GIT_INDEX_FILE=/tmp/idx-teste git diff --cached --stat HEAD | tail -3
rm -f /tmp/idx-teste
```

Deve aparecer só a alteração real. Confirmar também que os ficheiros não foram tocados:
`stat -c '%y %s'` mantém mtime e tamanho de antes.

---

## Armadilhas (medidas neste workspace)

1. **`git status --porcelain` sem `-uall` esconde o problema.** Colapsa cada pasta não
   rastreada numa linha; o VS Code não colapsa.
2. **`git -c core.autocrlf=input diff` não é só leitura.** Ele atualiza o cache de stat do
   índice: repositórios passam a reportar «limpo» sem que nenhum ficheiro tenha mudado, e o
   CRLF continua lá. Depois de correr este teste, validar por `hash-object`, não por `status`.
3. **`git diff` e `git status` podem discordar.** O `diff` compara conteúdo (com filtros);
   o `status` e o `diff-files` reportam divergência de stat. Divergência entre os dois é
   sinal de cache preso, não de alteração.
4. **Loop de shell com nomes de ficheiro com espaços dá falsos «DIFERENTE».** O git devolve
   esses caminhos entre aspas e com escapes; usar `-z` e `read -d ''` ou tratar as aspas.
5. **`git check-ignore <pasta>` diz «não ignorado» para padrões `pasta/*`** — e acrescentar a
   barra final não resolve. Testar um filho real (`<pasta>/<algo>`).

---

## Proibido (regra `cross-platform`, ADR 0012-cross-platform-governance.md)

Nunca automatizar nem sugerir como atalho:

- conversão em massa de CRLF/LF ou de encoding;
- `git add --renormalize .`;
- `core.autocrlf` ou `core.ignorecase` **global**;
- `.gitattributes` ou `.editorconfig` global sem ADR;
- `chmod` em massa sobre ficheiros versionados.

`git restore` / `git checkout -- .` sobre milhares de ficheiros para «limpar os CRLF» cai na
primeira proibição: só com decisão explícita do humano. A rota de `core.autocrlf=input` +
`read-tree` resolve o sintoma sem tocar no disco.

---

## Encerramento

Reportar sempre, na evidência técnica: contagem antes e depois por repositório, prova de
conteúdo (`hash-object` vs `HEAD`), e a confirmação de que nenhum ficheiro do disco foi
alterado. Distinguir o que é ruído do que é alteração real pendente — e dizer de quem é
essa pendência.
