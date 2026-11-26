---
name: roteiro-teste-manual
description: Use ao montar roteiro de validação manual com critérios de aceite, checklist e caminhos de evidência.
---
CTX-ID: roteiro-teste-manual@6

# Roteiro de teste manual — entrega no chat

## Composição Superpowers

Formato jarbas do roteiro no chat; o resultado só vira «validado» com evidência.

**REQUIRED SUB-SKILL:** Use `superpowers:verification-before-completion` antes de afirmar que um critério foi validado ou que a entrega está pronta.

**Projeto:** TR Jarbas Ai Multi-agents squad · profile `sgd-novo` quando aplicável

**Origem (lição curada):** `PM-20261021-b9ff` — formato aprovado pelo Diego (roteiro no chat, não só path de pasta).

**Relacionada, não substituta:** `auxilio-testes-pr-sgd` persiste ficheiro em `user-doc/novo-sgd/auxilio-testes-pr/` no fluxo de PR. Esta skill responde **no chat** quando o Diego pede validação manual ad hoc (ITEM, reteste, paridade visual).

---

## Regra de ouro (não negociável)

1. **Não** responder só com caminho de pasta nem criar documento `.md` como entrega principal. O roteiro vai **integralmente no chat** — links relativos em ficheiros não abrem para o Diego.
2. Roteiro **curto e prático** (~10 minutos). Um passo por **CA-*** da ficha ou matriz de evidências.

### Pedido Diego (2026-10-22)

1. **Acesso em cada item:** «para cada item a ser testado, no quadro onde está o item tem que ser colocado o usuário e senha também para reproduzir, não quero ter que ficar recorrendo ao cabeçalho». O bloco **Acesso** no topo da resposta continua (resumo), mas **não substitui** o quadro de reprodução **dentro de cada passo/CA** e, no PDF, o quadro **Como reproduzir** no topo de **cada página de CA**.
2. **Lista não pode abrir vazia no exemplo positivo:** «no PDF o exemplo não pode listar nada» — nunca entregar roteiro/PDF cujo passo de listagem/filtro/card abra vazio como **única** prova de um CA positivo. Antes de entregar: **verificar massa** (SQL read-only via MCP `SGDNOVO_DEV_*` no DEV remoto, ou API/slot local) e indicar **qual usuário** tem linhas na lista; se não existir massa no ambiente alvo, **criar** (`manual-seed`/ação autorizada) ou documentar como **`tipo: negativo`** / `evidencia_vazia: true` **só** em caso negativo explícito.

---

## Quando aplicar

| Sinal do Diego (verbatim ou equivalente) | Acção |
|---|---|
| «quero fazer um teste manual», «vou validar manualmente» | Montar roteiro no chat |
| «me dá um roteiro de teste», «preciso validar na mão» | Idem |
| «validação manual do ITEM-&lt;codigo&gt;» | Resolver ITEM + evidências em `repo/sgd-cursor-governance/items/` |
| Validar **app viva** (não só prints) | Secção [Aplicação viva](#aplicação-viva) abaixo |

Se o pedido for só gerar auxílio persistido para PR → **`auxilio-testes-pr-sgd`**, não esta skill.

---

## Acesso (obrigatório em todo teste manual)

Sempre que o Diego disser que quer fazer um teste manual, **abrir a resposta com o bloco «Acesso»**, antes dos passos — sem ele perguntar:

1. Ler doc-credenciais-acesso.md e escolher a persona adequada (master local `11122233396` / `Admin@123456`; outras personas na secção «usuários de teste»; DEV remoto só se o teste for no DEV).
2. Entregar no chat, em texto, **CPF e senha completos** (exceção global.mdc, referência Jarbas não importada), a **URL** da app (slot/porta reais de `slotctl status`, ex.: `http://127.0.0.1:5173`) e o **perfil** (master, gestor, colaborador) necessário para os CAs.
3. Se o teste exige papel específico (ex.: não-master, gestor), indicar a persona certa por CA.
4. Se a app **não** está no ar, subir/renovar o slot (`slotctl status`/`touch`) antes de entregar o roteiro, ou dizer claramente o que falta (ex.: banco vazio / massa inexistente).
5. Se o login falhar com «usuário ou senha incorretos», ver o conflito Keycloak × seed no mesmo doc de credenciais.

### Já logado e na tela do teste (obrigatório)

O Diego **não** deve logar nem navegar: ele só executa a etapa corrigida/implementada. Antes de responder, o agente deixa o navegador do Cursor pronto (MCP `cursor-ide-browser`: `browser_tabs` → `browser_navigate` → `browser_snapshot`):

1. Abrir a URL do slot. Se a sessão já estiver ativa com o usuário do teste (aparece o menu/«Master …»), seguir; senão, **personificar** o usuário no console admin do Keycloak do ambiente (SGD novo: rule `testes-personificacao-keycloak`, procedimento keycloak-personificacao-testes.md) — não preencher CPF e senha na tela de login.
2. Navegar **direto** à rota do primeiro CA (URL por `navigate`; se a rota não for conhecida, usar o menu). Mapear rotas na ficha/specs do ITEM; ex.: Contratos = `/gestao-clientes/contratos`, Clientes = `/gestao-clientes/clientes`.
3. Se o CA exige estado prévio (abrir modal, filtrar, selecionar registro), **deixar nesse estado** quando for seguro e não destrutivo; nunca executar a ação que será testada.
4. Confirmar com `browser_take_screenshot` que a tela certa carregou e **dizer no chat** onde o navegador está (tela + usuário logado).
5. **Massa de dados — preparar sempre, sem perguntar**. Antes de entregar o roteiro, garantir que existe o dado que cada CA precisa (cliente, contrato, minuta assinada, etc.). Se a tela abrir **vazia** ou faltar o registro do caso:
   - **Não** devolver «banco vazio» nem oferecer criar: **criar**. Usar os scripts em `ecosystem/automation/sgd-local/manual-seed/` (ver README.md; ex.: `node .../seed-contrato-assinado.mjs --tag <ca> [--clientes N]`, via API, na empresa do master, com as portas do slot).
   - Sem script para o cenário: montar o fluxo por API como os specs E2E do ITEM (`tests/e2e/<item>/`), **gravar o novo script** em `manual-seed/` + linha no README (não improvisar de novo na próxima vez).
   - Depois de criar, **recarregar a tela**, confirmar por screenshot que a linha/registro aparece e informar no chat o dado **real** gerado (ex.: número do contrato `CT-…`, nome do cliente) — nunca o do protótipo/evidência se diferir.
   - Dados sempre fictícios; nunca clientes reais. Preservar massa existente (não apagar).
   - Só pedir ajuda ao Diego se for impossível por API (ex.: integração externa real, credencial que só ele tem).
6. Se houver vários CAs em telas diferentes, deixar no primeiro e informar a rota de cada seguinte (ou o caminho de menu).
7. Falha de login ou app fora do ar: diagnosticar (credenciais doc, Keycloak, `slotctl status`) antes de devolver ao Diego; só pedir ajuda dele em bloqueio real.
8. **PDF, download, nova aba/popup, impressão:** o navegador embutido do Cursor **não** exibe PDF nem abre popup (aparece tela branca — ocorrência CA-6 do ITEM-15000, 2026-10-21; em Chromium real o clique abre a nova aba/baixa o PDF). Para esses CAs: **avisar antes** no roteiro que o resultado deve ser conferido no **Chrome/Edge do sistema** (mesma URL; login no bloco Acesso), e antes de entregar provar por Chromium real (docker `mcr.microsoft.com/playwright`, `--network host`, listeners `popup`/`download`) que o clique funciona. Nunca deixar o Diego descobrir a tela branca.

Formato:

```
**Acesso**
- URL: http://127.0.0.1:5173
- Usuário (CPF): 11122233396
- Senha: Admin@123456
- Perfil: master
- Navegador: já logado e em «Gestão de Clientes > Contratos» (/gestao-clientes/contratos)
```

---

## Procedimento

### 1. Descobrir o que validar

- **ITEM:** ficha `repo/sgd-cursor-governance/items/<codigo>/item-<codigo>.md`, CAs e MATRIZ-EVIDENCIAS.md / MATRIZ-LAYOUT-PARIDADE.md.
- **Evidências visuais** (ler o que existir; não inventar paths):

  | Tipo | Onde procurar (raiz = playground) |
  |---|---|
  | PNG por CA | `repo/sgd-cursor-governance/items/<codigo>/evidence/` |
  | Paridade dual | pares referência × SGD, `layout-*-ref`, `layout-*-sgd` |
  | PDF / páginas | `pdf-pages/` |
  | Reteste DEV | `RETESTE-DEV*` ou equivalente na pasta do ITEM |
  | Comparação visual | `evidence/comparacao-visual/` (ex.: ROTEIRO-VALIDACAO.md como **estrutura interna**, não como link para o humano) |

- Contexto do chat (PR, tela, bug) complementa quando não houver ITEM numerado.

### 2. Montar cada passo (um por CA)

Para cada **CA-*** relevante, no chat:

0. **Quadro «Como reproduzir» no próprio passo (obrigatório)** — não depender só do cabeçalho «Acesso». Em **cada** passo/CA, abrir com:

   ```
   **Como reproduzir (CA-XX)**
   - URL/rota: …
   - Usuário (CPF): … (completo — exceção global.mdc)
   - Senha: … (completa)
   - Perfil: …
   - Empresa/contexto: … (quando houver escopo de unidade/equipe)
   - Registro a abrir: … (contrato, cliente, linha da grade)
   ```

   No PDF: objeto `acesso` (`url`, `perfil`, `usuario`, `senha`, `contexto` opcional) + `registro` por página; `generate.py` **falha** sem `usuario` e `senha`.
1. **Título** — `Passo N — CA-XX: …` (frase do critério).
2. **Imagens** — markdown com **caminho absoluto** (funciona no chat do Cursor):

   ```markdown
   ![antes](~/projetos/TaxProf_brtap-integration-playground/repo/.../antes.png)
   ![referência](~/projetos/TaxProf_brtap-integration-playground/repo/.../ref.png)
   ![SGD](~/projetos/TaxProf_brtap-integration-playground/repo/.../sgd.png)
   ```

   Omitir «antes» se não existir. Ordem habitual: antes (se houver) → referência/protótipo → SGD após correção.

3. **Checklist** — `- [ ]` com o que o Diego deve **olhar** (coluna, máscara, texto, botão, scroll).
4. **Ressalvas honestas** — ex.: coluna cortada no print, diferença de máscara de documento, resolução, dado de massa distinto.
5. **Prova visual com lista preenchida** — grade/card/lista **vazia** («Não há dados», 0 linhas) **não** serve como exemplo positivo do DEPOIS; usar usuário + registro em que o cenário mostre linhas. Vazio só em caso **negativo** explícito (`tipo: negativo` no spec PDF). Nunca deixar o único exemplo de um CA positivo ser tela vazia.

**Vídeos `.webm`:** não embutir (não renderizam no chat). Citar caminho absoluto; oferecer extrair quadros com `ffmpeg` **só se já existir** no ambiente — **não instalar** sem pedido explícito.

### 3. Lacunas de evidência

Se faltar print para algum CA:

- Dizer **explicitamente** (proibido inventar ficheiro).
- Indicar prova alternativa (trecho de `RETESTE-DEV`, vídeo, spec E2E, texto da matriz).
- Oferecer gerar print novo (E2E screenshot, captura manual orientada) se o Diego quiser.

### 4. Fecho obrigatório

1. Tabela resumo:

   | Passo | CA | OK / NOK |
   |---|---|---|
   | 1 | CA-… | |
   | … | … | |

2. Instrução ao Diego:
   - **Tudo OK** → registrar «Aprovado por» (nome + data) em `MATRIZ-LAYOUT-PARIDADE` do ITEM, quando ela existir (comparação exigida); com dispensa, na seção SEM COMPARAÇÃO da `MATRIZ-EVIDENCIAS`.
   - **Algum NOK** → anotar passo + motivo (chat ou ficha, conforme pedido).

### 5. PII

- Credenciais de teste **local/DEV** documentadas em doc-credenciais-acesso.md: **podem** ser citadas completas no roteiro (exceção global.mdc, referência Jarbas não importada).
- **Nunca** dados de clientes reais, produção ou massa sensível sem máscara.

---

## Aplicação viva

Quando o pedido for validar na **aplicação em execução** (não só comparar prints):

1. Ler doc-credenciais-acesso.md — URL/slot, CPF/senha da persona adequada.
2. Espelhar navegação por menu do auxílio de testes correspondente em `user-doc/novo-sgd/auxilio-testes-pr/` (se existir `pr-*-item-<codigo>.md`).
3. Passos = jornada de menu + checkpoints alinhados aos CAs (sem substituir E2E automatizado).

---

## Exemplo de formato aprovado (ITEM-15000)

Estrutura de referência (ficheiro interno do governance; **entrega ao Diego = mesmo formato no chat**, com absolutos):

Trecho ilustrativo (adaptar paths reais ao ITEM em curso):

```markdown
## Passo 1 — CA-01: Coluna visível na grid

![referência](~/projetos/TaxProf_brtap-integration-playground/repo/sgd-cursor-governance/items/15000/evidence/comparacao-visual/layout-grid-ref.png)
![SGD](~/projetos/TaxProf_brtap-integration-playground/repo/sgd-cursor-governance/items/15000/evidence/comparacao-visual/layout-grid-sgd.png)

- [ ] Cabeçalho da coluna igual ao protótipo
- [ ] Valores alinhados; sem coluna cortada (print pode cortar à direita — conferir no browser)

*Ressalva:* no PNG do SGD a última coluna aparece parcialmente cortada; validar scroll horizontal ao vivo se duvidar.
```

Modelo completo de passos 1–6 (estrutura):  
`~/projetos/TaxProf_brtap-integration-playground/repo/sgd-cursor-governance/items/15000/evidence/comparacao-visual/ROTEIRO-VALIDACAO.md`

---

## Versão em PDF (template aprovado — padrão inviolável)

adorou o formato **REFERÊNCIA + ANTES + DEPOIS** (roteiro rodada 2 do ITEM-15000, `layout:"stack"` + `crop`). É a **referência permanente** de todo PDF de validação/teste manual, de qualquer ITEM/profile: **proibido** inventar outro layout, remover a referência (protótipo/definição) ou fundir antes/depois. Sem referência disponível → declarar a lacuna na página do CA, nunca omitir o bloco. Exemplo-modelo a imitar: `repo/sgd-cursor-governance/items/15000/evidence/ROTEIRO-VALIDACAO-MANUAL-ITEM-15000-RODADA-2.pdf`.

O chat é a entrega principal. Quando o Diego pedir **PDF** (ou «documento para guardar na pasta do item»), gerar com o template — não improvisar layout:

```bash
python3 ecosystem/shared/templates/roteiro-validacao-pdf/generate.py <spec.json> --out <items/<codigo>/evidence/ROTEIRO-VALIDACAO-MANUAL-ITEM-<codigo>.pdf>
```

- Estrutura fixa: capa (tabela CA × corrigido × prova × OK/NOK + **limites das evidências**), **1 página por CA** (quadro **Como reproduzir** com URL, perfil, CPF, senha e registro; REFERÊNCIA em largura total; ANTES | DEPOIS; caixa OK/NOK), apêndice.
- Antes de gerar o PDF: **consultar o banco** (MCP read-only do ambiente) e localizar usuário + registro em que o cenário **lista algo**; se não existir, **criar massa** (`manual-seed` local ou ação autorizada), recapturar prints; só declarar lacuna se for impossível. Rodar `generate.py ... --validate-only` (bloqueia CA sem acesso/registro ou DEPOIS vazio em CA positivo).
- Esqueleto: `spec.example.json`; exemplo real: `spec.item-15000.json`; campos e regras: README.md na mesma pasta.
- Imagens: usar **nativas** (extrair do PDF fonte/export) e `crop` na região relevante; quadros de vídeo só como último recurso (Chromium headless; o ffmpeg do Playwright não decodifica VP8) e declarados como baixa resolução.
- Declarar na capa: prints cortados, CA só com vídeo, CA sem print; **nunca** apresentar vídeo em branco como prova; conferir que o par ref×SGD mostra a **mesma tela**.
- Guardar o PDF em `items/<codigo>/evidence/` e commitar na governança; requer `pip install pymupdf`.

---

## Checklist do agente

- [ ] Bloco **Acesso** (URL + CPF + senha completos + perfil) no topo da resposta **e** repetido em cada passo/CA (URL/rota + registro a abrir)
- [ ] **Antes do PDF:** banco MCP (read-only) → usuário/registro com lista preenchida; massa criada se faltou; `--validate-only` no spec
- [ ] **Sem exemplo vazio** como prova positiva (só `tipo: negativo` ou `evidencia_vazia: true` em PAR negativo)
- [ ] **Massa com variações** (não um caso só — vale para **qualquer** teste manual, não só listagem): o seed cria **um registro por variação** (tipo de registro raiz × filho/add-on, PF/PJ, estados, sem/1/muitos valores, vazio, texto longo, **um caso de erro/negativo**) e o roteiro tem **uma linha por variação** dizendo qual registro abrir e o que conferir (rule `task-reviewer` § «Nunca só o caminho feliz» e «Paridade de UI»)
- [ ] **Antes de entregar o roteiro**, responder no chat: «qual variação ficou de fora e por quê?» — um roteiro com um único registro feliz é recusado pelo reviewer
- [ ] **Massa de dados criada** (seed em `manual-seed/`) e confirmada na tela; número/nome reais informados; script novo versionado se o cenário era inédito
- [ ] Navegador do Cursor **já logado** e **na tela do CA** (screenshot de confirmação); dado/massa em falta declarado
- [ ] **Prova de comportamento do protótipo** (print, vídeo ou PDF para o testador) vem da **jornada pela UI** (estado inicial pode ser semeado; a transição testada, não). Evidência com massa forçada por SQL **não** é entregue como comprovante.

- [ ] Se pediram PDF: usar `roteiro-validacao-pdf/generate.py` (template), não layout novo — **cada página de CA com REFERÊNCIA + ANTES + DEPOIS** (padrão aprovado pelo Diego, inviolável)

- [ ] Roteiro **no chat**, não só paths
- [ ] Um passo por CA mapeado; CAs sem prova declarados
- [ ] Imagens com caminho **absoluto**; vídeos só como path + opção ffmpeg
- [ ] Tabela Passo | CA | OK/NOK + instrução MATRIZ-LAYOUT-PARIDADE (só se a Política exigir comparação)
- [ ] ~10 min; PII conforme global.mdc (referência Jarbas não importada)
- [ ] App viva: credenciais + menu do auxílio PR quando couber

---
