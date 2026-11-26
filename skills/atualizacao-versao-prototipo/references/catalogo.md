# Catálogo da versão

O catálogo é `.squad/contracts/parity/catalog.json` no produto, validado por `ecosystem/automation/proto_env/parity.mjs`. Ele é a única fonte: nada de arquivo de baseline, lista de correções ou pasta de candidatos à parte. O motor aceita campos adicionais nos registros.

## Formato mínimo

Parta deste esqueleto; não abra o código do motor para descobrir o formato. Erro de validação se corrige pelo código que o validador devolve.

```json
{
  "schema_version": "1.0", "project_uid": "<do .squad/project.yaml do produto>",
  "mode": "FULL", "scope_claim": "KNOWN_SCENARIOS",
  "reference": {"version": "<checkout_commit>", "digest": "<fingerprint>"},
  "target": {"commit": "<commit analisado do produto>"},
  "baseline": {"trusted": false},
  "surfaces": [{"id": "SF-PEDIDOS"}],
  "regions": [{"id": "RG-PEDIDOS-ACOES", "surface_id": "SF-PEDIDOS", "discovery_status": "INVESTIGADO", "provenance_refs": ["EV-P1"]}],
  "states": [{"id": "ST-PEDIDOS-LISTA", "region_id": "RG-PEDIDOS-ACOES", "discovery_status": "INVESTIGADO", "provenance_refs": ["EV-P1"]}],
  "scenarios": [{"id": "SC-PEDIDOS-ACOES", "region_id": "RG-PEDIDOS-ACOES", "state_id": "ST-PEDIDOS-LISTA", "dimensions": ["functional"], "definition": {}}],
  "evidence": [{"id": "EV-P1", "kind": "src", "locator": "prototipo@<commit>:src/pages/Pedidos.tsx"}],
  "differences": [{"id": "DF-1", "surface_id": "SF-PEDIDOS", "requirement_ids": ["REQ-1"], "task_ids": []}],
  "requirements": [{"id": "REQ-1", "scenario_ids": ["SC-PEDIDOS-ACOES"], "difference_ids": ["DF-1"], "task_ids": []}],
  "journeys": [], "tasks": [], "tests": []
}
```

IDs são únicos no catálogo inteiro. Ligações valem nos dois sentidos (diferença ↔ requisito). `NAO_INVESTIGADO` exige `owner`, `risk` e `resume_trigger`.

## Fatos para o modo

Só com catálogo anterior. Mostre ao Diego, com sua recomendação:

| Fato | Como conferir |
|---|---|
| Baseline anterior | `trusted`, marco registrado, `baseline.reference_version` igual à `reference.version` do catálogo (o motor não confere isso, e o fingerprint não distingue versões) |
| Catálogo anterior válido | `parity.mjs catalog <manifest> <catalogo>`, com `reference` de `reference inspect` no commit vigente e `target.commit` = commit testado do registro do marco, conferido no git |
| Ancestralidade | versão vigente ancestral da candidata; `baseline.target_commit` ancestral do commit do produto |
| O que o diff tocou | áreas do diff |
| O que o produto mudou desde a baseline | `git diff --stat <baseline.target_commit>..HEAD` no produto |

Desfavorável ao INCREMENTAL: baseline sem marco ou sem `baseline.reference_version`; catálogo anterior inválido; ancestralidade que falha; produto alterado desde `baseline.target_commit`.

## Atualizar no lugar

- Catálogo anterior: `git show <ramo-principal>:.squad/contracts/parity/catalog.json`. Sem catálogo anterior, crie no mesmo caminho.
- Pedido explícito de refazer do zero ([SKILL.md §3](../SKILL.md#3-modo-quem-decide-é-o-diego)): o catálogo é novo, no mesmo caminho, e nada se herda. O antigo fica só para consulta e para a lista de `disposition` do resumo.
- **Tudo permanece**, com os mesmos IDs: diferenças, decisões, requisitos protegidos, testes, tarefas, jornadas. Exceção aprovada em área tocada volta para revalidação: a `disposition` vai para `previous_disposition`.
- **INCREMENTAL:** reinvestigue as áreas do diff, as áreas do produto alteradas desde `baseline.target_commit` e os gaps conhecidos (diferenças abertas, `inherited_unknowns`, tarefas pendentes, «Fora do relato»). O resto fica com `carried_from` = versão anterior; a evidência dele é da referência antiga.
- **FULL:** reinvestigue todas as rotas do protótipo novo e do produto, reusando o ID do cenário que renderiza a mesma rota e região.
- Ao reinvestigar, registre por cenário os arquivos do protótipo e do produto (rota, região, dependências importadas): a próxima rodada seletiva depende disso. Mantenha `region_id`, `state_id` e `dimensions`.
- Cenário com ausência comprovada no protótipo novo sai, salvo se citado por requisito protegido: aí fica e vai às decisões como «correção protegida em tela removida».
- `scope_claim` fica `KNOWN_SCENARIOS` enquanto houver lacuna. Segundo pedido para a mesma versão: continue na mesma branch.

## Superfície do layout comum e das molduras

Menu, cabeçalho, rodapé, tema e página de erro entram como superfície própria (por exemplo `SF-LAYOUT`), com regiões, cenários, diferença e requisito, como qualquer tela. O motivo: toda tela aparece dentro deles, e nenhuma evidência de tela os alcança. Sem a superfície, o plano reconstrói as telas sem a moldura e a conferência final não a enxerga. Ela se descobre pelos arquivos de moldura que o `inventario` recebe em `--moldura` (abaixo). Tela ou moldura fora do escopo só por decisão do Diego, nomeada no catálogo: sem a decisão, fica no escopo.

## O que o cenário traz

Em `definition.agora` de cada cenário, com a fonte (`arquivo:linha`) de cada item:

- **Textos literais visíveis,** copiados como estão no protótipo, sem paráfrase nem tradução: os fixos no código, os de locale (o texto resolvido da chave, não a chave) e, quando conhecidos, os que a biblioteca renderiza sozinha (botões e mensagens padrão de formulário, de tabela, de calendário). O que a biblioteca renderiza e não se conhece fica dito como não conhecido; não se inventa.
- **Dados:** o endpoint e a forma da resposta (campos e tipos), com valores só quando são fixos.
- **Mock:** o que ele faz e o que ignora (por exemplo, parâmetro recebido e não usado, lista que muda a cada chamada). Comportamento de mock é fato do protótipo; se ele vale como regra é decisão do Diego, não do catálogo.
- **Interação,** em cenário `functional` de controle interativo (seletor de data, select, modal, gaveta, dropdown, formulário em etapas): onde o controle fica, como abre e fecha, quando habilita e qual valor confirma. Cite a linha da prop ou do handler; o que vem da biblioteca e não aparece no código fica dito como não conhecido. Motivo: trocar o componente pode mudar o comportamento sem mudar a aparência.
- **Aparência:** o componente da biblioteca, as props que mudam o visual e o tema (token, `variant`, cor) que se aplica.

Um cenário tem ou a dimensão `functional` ou a `visual`, nunca as duas. Motivo: `verificacao.py ligar` trata o cenário misto inteiro como visual, e a metade funcional ficaria sem teste. Se a tela precisa dos dois, são dois cenários: o comportamento vai num cenário `functional` e a aparência noutro, `visual`, cada um com o seu `definition.agora`. O integrador cria um de cada a partir das frases separadas do achado.

## Arquivos e componentes por tela

`surfaces[].arquivos` e `surfaces[].componentes` vêm do `cobertura.py inventario` ([cobertura.md](cobertura.md#inventário-por-tela)), copiados pelo integrador; ninguém os escreve à mão. Passe as molduras por `--moldura` (por exemplo o arquivo do `app` e o do tema): elas saem em `molduras[]` e alimentam a superfície do layout comum. A saída traz também `elementos` (tags de Web Component) e `nao_resolvidos`; o que estiver em `nao_resolvidos` vira leitura manual do arquivo, nunca silêncio. `barris` lista os arquivos de reexportação que o script seguiu inteiros porque não deu para filtrar por símbolo: a lista da tela pode ter arquivos a mais, e o que sobrar se confere à mão. `avisos` traz o que não se resolveu (por exemplo import dinâmico não literal) e também exige leitura. `--moldura` deve cobrir os layouts-pai das rotas e os arquivos de convenção do framework, não só o arquivo do `app` e o do tema; o `--moldura` está descrito em [cobertura.md](cobertura.md#inventário-por-tela).

## Diferença com `disposition`

A diferença com `disposition` (exceção aprovada) não gera requisito próprio. Motivo: `parity.mjs linkage` exige tarefa em todo requisito, e exceção aprovada não recebe tarefa. Se um requisito é compartilhado com outras diferenças, ele segue ligado por elas.

## `delta` (opcional)

Só se a baseline anterior era confiável, uma vez, depois da reinvestigação: `node ecosystem/automation/proto_env/parity.mjs delta <anterior> <atual> <target>`, com o `target` num arquivo temporário fora do repositório. Sem baseline confiável o motor responde `UNTRUSTED_BASELINE` (saída 11): registre e siga pelo código.

## Validação

- `node ecosystem/automation/proto_env/parity.mjs catalog <manifest.json> <catalog.json>` sem erros. O manifesto é `{"project_uid": …, "reference": {"version": …, "digest": …}, "target": {"commit": …}}`, de fontes independentes: `project_uid` do `.squad/project.yaml`, `reference` de `python3 ecosystem/automation/jarbas.py reference inspect --project-root <worktree da candidata>` (`checkout_commit` e `fingerprint`), `target.commit` = commit analisado. Grave-o fora do repositório; nunca o copie do próprio catálogo.
- `node ecosystem/automation/proto_env/parity.mjs linkage <catalog.json>` tolera só:
  - `MISSING_TASK_OWNER`;
  - `MISSING_TEST`, exceto em cenário de requisito protegido;
  - `MISSING_REQUIREMENT`, só em diferença do inventário inverso pendente de decisão, em diferença do cruzamento (`classe: INCONSISTENCIA-PROTO` com `cruzamento`) ou em revalidação, listada no resumo.

  Qualquer outro código é defeito do catálogo, não «esperado».
