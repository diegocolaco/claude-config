---
name: exportar-conversa-e-arquivos-para-revisao
description: Use quando pedir ZIP de revisão com conversa, inventário SHA-256 e artefatos permitidos.
disable-model-invocation: true
---
CTX-ID: exportar-conversa-e-arquivos-para-revisao@2

# Exportar conversa e arquivos para revisão

**Projeto:** TR Jarbas Ai Multi-agents squad

Produzir uma **fotografia fiel** do estado disponível, inclusive rascunhos, falhas e lacunas. «Tudo» significa todo o material **pertinente e permitido** da sessão/ITEM solicitado — não todo o computador ou repositório.

Esta skill **prepara o pacote**; não aprova a entrega, não corrige o produto e **não envia** o conteúdo automaticamente a terceiros.

**Fotografia fiel** refere-se ao estado **técnico e de processo** (decisões, etapas, falhas, lacunas) — **não** a reproduzir credenciais, PII, URLs internas ou segredos em claro. Tudo o que entra no ZIP é **cópia permitida**, em geral **SANITIZADO**.

## Anonimização e confidencialidade (obrigatório — não reinventar)

A política e a confirmação humana vivem na skill **`documentar-seguranca-gate`** (gate DOC-SECURITY). A transformação técnica (PII, paths, conversa sem `tool_use`) vive na skill **`exportar-chat`** (`mask_pii`, aliases de path, CHECKLIST-DOC-SECURITY.md).

| Passo | Quem | O quê |
|-------|------|--------|
| 1 | **`documentar-seguranca-gate`** | Checklist de risco, destino (git/partilha), omitir / mascarar / resumo — **antes** de gravar qualquer ficheiro do pacote |
| 2 | **global.mdc** (referência Jarbas não importada) | PII mascarada na leitura e na escrita (complementa o gate) |
| 3 | **`exportar-chat`** (CLI ou mesma lógica de `build_package.py`) | Gerar conversa e artefatos **já anonimizados**; proibido JSONL bruto com ferramentas no pacote |
| 4 | Esta skill | Inventário, `00/01/02`, SHA-256 das **cópias exportadas**, ZIP |

**Proibido** montar o pacote «completo» com dados sensíveis e «corrigir depois». **Proibido** duplicar aqui tabelas de risco ou algoritmos de máscara — apontar para as skills acima.

Exceção única: o Diego autoriza **explicitamente** no mesmo pedido um tópico concreto em claro (gate repete o risco e regista na checklist).

## Quando usar

- «Exportar conversa e arquivos para revisão», pacote para revisor humano ou agente autorizado.
- Fecho parcial de ITEM/sessão: handoff com provas, falhas e pendências explícitas.
- Quando for necessário **inventário com SHA-256**, estrutura `00/01/02` e classificação COMPLETO/PARCIAL.

**Não confundir**

| Artefato | Papel |
|----------|--------|
| `governance-export*` | Governança Jarbas (rules/skills), não sessão de produto |

**Preferir `exportar-chat`** quando o destino aceita o formato legado e só precisa de conversa + artefatos opcionais. **Preferir esta skill** quando o revisor precisa de snapshot formal (inventário, hashes, lacunas, BASE/HEAD, etapa vs evidência).

## O que não fazer

- Não executar testes novos, finalizar PRE, corrigir critérios nem alterar status para «embelezar» o export.
- Não reconstruir falas, ferramentas ou resultados como se fossem originais.
- Não chamar resumo narrativo de conversa integral.
- Não fazer commit, merge, push, publicação nem envio ao revisor por inferência.
- Não instalar regras, criar gates, editar Superpowers nem manutenção global só para produzir o pacote.
- Não prometer ausência universal de informações sensíveis.

## Ordem obrigatória (resumo)

1. **`documentar-seguranca-gate`** — sempre; sem resposta do Diego, **não gravar** o pacote.
2. **Fixar escopo e estado** (secção 1).
3. **Inventariar antes de copiar** (secção 2).
4. **Preservar conversa e resultados** (secção 3).
5. **Preparar cópias permitidas** em diretório **novo** (secção 4).
6. **Montar, conferir, ZIP** (secção 5).
7. **Entregar ao Diego** (secção 6) + índice `user-doc` + **`playground-commit-workflow`** se gravou em `user-doc/` versionado.

Templates: `references/templates-pacote.md`.

---

## 1. Fixar escopo e estado

- Identificar **ITEM/mudança**, sessão, **data/hora com fuso**, repositórios pertinentes e **etapa alcançada**. Usar contexto do chat; perguntar só se ambiguidade mudar conteúdo ou destino permitido.
- Consultar a **especificação do processo efetivamente adotada** (jarbas-par-vigente.md → 01-ESPECIFICACAO-JARBAS.md, fonte externa ausente no Squad) e regras de exportação aplicáveis (`documentar-seguranca-gate`, profile se ativo). Distinguir versão **adotada**, **proposta** e **desconhecida**; não substituir referência histórica pela versão mais recente.
- Identificar **BASE/HEAD**, alterações locais e estado das evidências quando disponíveis (`git status`, `git log`, ficha ITEM, `.tmp/<trace_id>/`). Não inferir validação só por commit; não misturar snapshots sem identificação.
- Reutilizar automação existente quando **suficiente** (ver secção «Automação parcial»).

---

## 2. Inventariar antes de copiar

Localizar ficheiros criados, alterados ou citados na sessão (incluindo não versionados e `.tmp/` pertinentes). Usar caminhos conhecidos; não vasculhar outros chats, dados pessoais do editor ou repositórios sem relação.

### Material a reunir (quando existir, acessível e permitido)

| Categoria | Exemplos |
|-----------|----------|
| Conversa | Mensagens user/assistant na ordem original |
| Definição e planejamento | Pedido, design, plano, ficha, processo adotado |
| Paridade e revisões | PRE, POST, matrizes, pareceres, independência de revisores |
| Execução | Etapas, comandos/testes/gates, falhas, skips, interrupções |
| Mudanças | Diffs/arquivos pertinentes + a que snapshot pertencem |
| Provas | Relatórios, JSON de testes, imagens/vídeos, build/ambiente |
| Configurações | Trechos **mínimos** para entender um gate — não exportar todas as skills/rules |

### Registro no inventário (antes de copiar)

Para cada item: caminho lógico seguro, estado/revisão, destino no pacote, condição:

| Condição | Significado |
|----------|-------------|
| INCLUIDO | Cópia fiel permitida |
| SANITIZADO | Cópia transformada (PII, paths) — não é original idêntico |
| OMITIDO | Proibido ou risco não aceite |
| INDISPONIVEL | Não encontrado nesta execução |
| NAO_GERADO | Etapa comprovadamente não executada |

Distinguir **inexistente** de **não encontrado**. Para OMITIDO/INDISPONIVEL: motivo e **impacto na revisão** sem reproduzir dado protegido.

Deduplicar só conteúdo equivalente; **preservar** versões intermediárias que expliquem decisão, falha ou correção.

---

## 3. Preservar a conversa e os resultados

- Transcript: `~/.cursor/projects/.../agent-transcripts/<uuid>/<uuid>.jsonl` ou bloco `transcript_location` / `agent_transcripts` no chat.
- Se só houver contexto parcial: exportar o trecho disponível; declarar início/fim, origem e **lacunas**.
- Em 01-CONVERSA.md: declarar **cobertura real**; transcrição disponível (user/assistant); separar **transcrição**, **resumo** e **inferência**.
- Incluir resultados **permitidos** de ferramentas necessários à revisão: comando/ação saneado, ambiente, exit code, origem. **Sem** raciocínio interno, instruções ocultas, ambientes completos ou metadados brutos do editor.
- Estados: planejado | iniciado | concluído com evidência | declarado pelo agente | falhou | não executado | desconhecido. PASS sem evidência permanece **relato**.

**Conversa sanitizada:** reutilizar lógica de `ecosystem/automation/export_chat/build_package.py` (sem `tool_use` no pacote externo). Pode nomear o ficheiro 01-CONVERSA.md e fundir o aviso de cobertura no topo.

---

## 4. Preparar cópias permitidas

- Diretório de saída **novo**: `user-doc/<área>/relatorios/<dir-slug>/` — slug único (ex.: `AAAA-MM-DD-item-###-export-revisao`). Não sobrescrever pacote anterior.
- Não alterar originais.
- **Preferir** a skill `exportar-chat` para conversa e `--artifact`, de forma a herdar anonimização já validada no ecossistema.
- Conteúdo copiado à mão: mesmas regras que `exportar-chat` — excluir credenciais, tokens, dumps; binário não revisável → OMITIDO; paths e PII via `build_package.py` / `mask_pii` (ver skill `exportar-chat`, secção manual).
- Aliases estáveis; **não** anexar mapa reverso sensível.
- Não mascarar erros ou contradições para parecerem resolvidos.
- Pacote **parcial** permitido quando restrição bloquear parte — declarar explicitamente.

Incluir CHECKLIST-DOC-SECURITY.md (decisões do gate) no pacote ou referência cruzada no 00-LEIA-ME.md.

---

## 5. Montar e conferir o pacote

### Estrutura mínima

```
<dir-slug>/
  00-LEIA-ME.md
  01-CONVERSA.md
  02-INVENTARIO.md
  CHECKLIST-DOC-SECURITY.md   # recomendado
  artefatos/...
```

- **00-LEIA-ME.md:** snapshot, objetivo, etapa, processo adotado, fontes, decisões, observado vs relatado, pendências, limitações, ordem de leitura, o que o revisor pode concluir (template em `references/templates-pacote.md`).
- **01-CONVERSA.md:** cobertura + transcrição permitida.
- **02-INVENTARIO.md:** inclusões, transformações, lacunas; coluna SHA-256 por ficheiro **exportado** (sanitizado = hash da cópia no pacote).

### Hashes

```bash
sha256sum <ficheiro>
```

Conferir cada INCLUIDO/SANITIZADO contra o ficheiro real; registrar tamanho em bytes. Inventário: presença e legibilidade — sem hash autorreferente.

### ZIP

Compactar **somente** a lista revisada:

```bash
cd user-doc/<área>/relatorios
zip -r <nome-pacote>.zip <dir-slug>/
```

Não incluir `.git`, dependências, backups, symlinks ou árvores inteiras por conveniência.

Reabrir o ZIP: contagem, nomes, tamanhos e hashes vs 02-INVENTARIO.md. Varredura de segredos **não** prova completude.

### Cobertura final

- **COMPLETO NO ESCOPO DECLARADO** — material pertinente incluído ou classificado com motivo.
- **PARCIAL** — história incompleta ou omitido/indisponível relevante.

Atualizar índice `user-doc/<área>/README.md`:

```markdown
| DD/MM | [Título](relatorios/<dir-slug>/00-LEIA-ME.md) · [`.zip`](relatorios/<nome-pacote>.zip) |
```

---

## Automação de anonimização (`exportar-chat`)

**Canal preferido** para conversa e artefatos em texto (anonimização + checklist):

```bash
```

Depois **renomear/reorganizar** para `00/01/02`, completar inventário com SHA-256, gerar `.zip` e classificar cobertura. O `.tar.gz` do `export-chat` pode coexistir como artefato opcional no inventário (NAO_GERADO se não produzido).

---

## 6. Entregar ao usuário

Informar:

- Caminho real: pasta do pacote + `.zip`
- Escopo, etapa, cobertura (COMPLETO/PARCIAL)
- Principais omissões e impacto
- Separar **«pacote conferido»** de **«entrega aprovada»**

Se não houver capacidade de gerar ficheiro: entregar conteúdo permitido no chat e declarar limitação — **sem** link inventado.

O Diego decide envio ao revisor. Não atualizar a especificação geral só porque houve export.

### Fecho na resposta

Uma linha: **Gate DOC-SECURITY:** … · **Cobertura:** … · **Paths:** `user-doc/.../relatorios/<dir-slug>/` e `...zip` · **Lacunas principais:** …

## Integração

| Artefato | Papel |
|----------|--------|
| `documentar-seguranca-gate` | Gate humano: o que pode sair omitido/mascarado |
| `exportar-chat` | Pipeline técnico de anonimização (`export-chat`, checklist) |
| Rule global.mdc (referência Jarbas não importada) | PII inviolável em todo o fluxo |
| `documentar-user-doc` | Área e índice em `user-doc/` |
| `playground-commit-workflow` | Commit do pacote no playground |
