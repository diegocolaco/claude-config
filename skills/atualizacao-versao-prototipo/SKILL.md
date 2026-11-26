---
name: atualizacao-versao-prototipo
description: 'Use quando chegar uma nova versão do protótipo (novo commit, branch ou release do repositório de referência) e for preciso saber o que mudou e o que a reconstrução precisa mudar, mesmo que o pedido diga só «ver o diff» ou «sincronizar com o protótipo»; também ao adotar a versão analisada ou ao fechar a onda e marcar a baseline do catálogo de paridade.'
---

# Atualização de versão do protótipo

Complementa `prototype-parity-verification` no momento em que chega uma versão nova da referência. O resultado é um catálogo de paridade atualizado e um resumo para o Diego; o plano e a execução continuam no Superpowers. Nada aqui muda o motor de paridade (`ecosystem/automation/proto_env/parity/`).

A leitura ampla (telas inteiras, menus inteiros) acontece **uma vez por versão**, aqui. Os ITENS depois recebem só os IDs do catálogo.

Leia cada reference quando a etapa chegar a ela, não todas no início. Para fechar a onda basta [references/adocao-e-baseline.md](references/adocao-e-baseline.md).

## 1. Identidades

- **Protótipo:** compare pelo commit do checkout (`checkout_commit` de `jarbas.py reference inspect`), não pelo `commit_sha`. Em repositório público, `commit_sha` é o upstream de `upstream.json`, e o fingerprint só cobre package, lock e `upstream.json`; versões com o mesmo `commit_sha` podem ter código diferente.
- **Candidata:** registre num worktree próprio do protótipo. Confira antes com `git -C <worktree> rev-parse --show-toplevel` que não é o checkout principal nem worktree de outra tarefa. Comandos em [references/registro-e-diff.md](references/registro-e-diff.md). Registrar a candidata não pede pergunta.
- **Vigente:** a `reference.version` do catálogo do produto ou a versão que o Diego nomear. Sem as duas, é a primeira sincronização: `mapear --sem-vigente`, e não escolha commit do histórico como vigente. Pedido explícito de refazer do zero também usa `mapear --sem-vigente`, mesmo com catálogo no produto (§3). O registro do próprio protótipo (`reference inspect` no checkout principal) não é a vigente do produto.
- **Produto:** repositório, branch e commit analisados; `project_uid` do `.squad/project.yaml` do produto.

Candidata e vigente se resolvem pelo git e pelo pedido; não pergunte ao Diego o que o repositório responde.

## 2. Diff entre versões

Rode o mapa antes de qualquer pergunta ao Diego sobre escopo, modo, tamanho ou limite de telas, e cite na pergunta os números dele: `telas`, `peso_total`, `peso_sem_tela` e as unidades propostas. Se `peso_sem_tela` passar de metade do `peso_total`, o peso vem de arquivo que não é tela: veja `ignorados`, `avisos` e os maiores `arquivos[].tokens_estimados` antes de perguntar ou dividir. O orçamento do mapa é o padrão; mudar `--orcamento` é decisão do Diego, não um jeito de fechar a conferência.

`git log --first-parent --oneline` entre o checkout vigente e o da candidata, e o **mapa de cobertura** (`cobertura.py mapear`, comando em [references/cobertura.md](references/cobertura.md)): ele corta o diff em trechos e diz que telas cada trecho atinge, inclusive as que mudam sem diff próprio (componente compartilhado, chave de texto, mock). Leia por tela a partir do mapa, não pelo patch inteiro. As rotas vêm de presets JSON (Umi, React Router, TanStack); convenção nova se descreve num preset e `--rotas`, sem código ([references/cobertura.md](references/cobertura.md#presets-de-rotas)). O diff localiza áreas; linha alterada não vira requisito. Não altera nada vigente.

Se o mapa disser `cabe_em_um_agente: false`, ou se o Diego pedir ondas, a leitura das telas segue a skill `descoberta-em-ondas`, que devolve o controle aqui no inventário inverso. Se o Diego disser para não usar ondas, siga com um agente e diga no resumo.

## 3. Modo: quem decide é o Diego

- Sem catálogo anterior no produto: FULL, sem perguntar.
- Pedido explícito de refazer do zero (descartar o que há e redescobrir tudo): FULL sem perguntar o modo, porque o Diego já decidiu ao pedir. O catálogo é novo, sem herança: nada do anterior é copiado, e o antigo serve só de leitura. O resumo lista as `disposition` do catálogo antigo, cada uma com `kind`, `reason` e `decision_ref`, para o Diego reaprovar, e liga cada uma à diferença correspondente do catálogo novo, com os dois IDs; sem correspondente, diz isso. Nada é herdado em silêncio, e a diferença nova fica aberta até a reaprovação (quem grava a `disposition` depois é o controlador do chat de decisões, conforme [decisoes-e-planos.md](../prototype-parity-verification/references/decisoes-e-planos.md)). O catálogo antigo só é substituído no merge, pela adoção ([references/adocao-e-baseline.md](references/adocao-e-baseline.md)).
- Com catálogo anterior: levante a tabela de fatos de [references/catalogo.md](references/catalogo.md#fatos-para-o-modo).
  - Pedido sem modo: recomende FULL ou INCREMENTAL e **pare para o Diego escolher**.
  - Pedido que já nomeia o modo: essa é a escolha. Siga sem parar e, no resumo, ligue cada fato desfavorável ao risco desse modo. Não recomende nem ofereça o modo contrário depois de executar, nem como alternativa numa pergunta; pergunte pelo fato que falta (por exemplo, registrar o marco).

## 4. Catálogo da versão (a branch é a candidata)

Num worktree do produto com branch própria, atualize no lugar `.squad/contracts/parity/catalog.json`: `reference` passa à candidata e `baseline` vira `{trusted: false}`. Tudo o que já existe fica, com os mesmos IDs, exceto no refazer do zero (§3), em que o catálogo é novo e nada se herda. É a única escrita no produto; sem push nem merge. Regras de herança, INCREMENTAL × FULL e validação: [references/catalogo.md](references/catalogo.md).

## 5. Gaps e inventário inverso

- **Gaps** (protótipo novo → produto): tela inteira e dependências das áreas no escopo do modo; gaps conhecidos do catálogo e da seção «Fora do relato» das fichas de ITEM. Cada gap vira diferença com fonte nos dois lados e requisito com `scenario_ids`.
- **Inventário por tela:** depois do mapa, rode `cobertura.py inventario` (comando e saída em [references/cobertura.md](references/cobertura.md#inventário-por-tela)) e copie `arquivos` e `componentes` de cada tela e moldura para `surfaces[]`; é daí que o plano sabe do que a tela é feita.
- **Layout comum e molduras:** menu, cabeçalho, rodapé, tema e página de erro são uma superfície obrigatória do catálogo, com cenários, diferença e requisito, como qualquer tela. Toda tela depende deles e nenhum import da tela os revela, então sem essa superfície o plano não os enxerga. Tela fora do escopo só por decisão do Diego, nomeada no catálogo ([references/catalogo.md](references/catalogo.md#superfície-do-layout-comum-e-das-molduras)).
- **Inventário inverso** (produto → protótipo novo): rotas e navegação dos dois lados, pelo que cada rota renderiza. Cada controle sem par recebe uma classe com prova; sem prova, `NAO_COMPROVADA` vai às decisões do Diego. Classes e leitura independente: [references/inventario-inverso.md](references/inventario-inverso.md).
- **Aprovação de classe** é por ID: `disposition` exige `kind`, `reason`, `decision_ref` e `approved_by`, e `decision_ref` aponta registro verificável (mensagem do Diego com data e IDs, commit ou ficha). «Ok, segue», «pode seguir» ou aprovar o plano não aprovam classes; até lá a diferença fica aberta.
- **Correções preservadas:** requisito existente marcado como protegido, com os testes que o travam. Cruze à mão com os arquivos do diff. Lista vazia é «nenhuma correção protegida registrada».
- **Rastreio:** cada trecho do mapa recebe um destino na tabela de rastreio (diferença, `SEM_IMPACTO` com motivo ou `NAO_INVESTIGADO` com local). Antes do resumo, rode `rastreio`. Todo trecho que sair em `faltantes`, `ids_inexistentes`, `sem_motivo`, `local_invalido` ou `desconhecidos` volta uma vez à leitura (`desconhecidos` é mapa de outra versão: refaça o mapa; `identidade` com `MAPA_DESATUALIZADO` ou `MAPA_OUTRA_VERSAO` também manda refazer o mapa e a leitura); o que sobrar entra `NAO_INVESTIGADO` e vai ao resumo. A leitura cega é a [passada de fatos](../descoberta-em-ondas/references/passada-de-fatos.md): copie o catálogo antes de integrar e rode `omissoes` depois. Depois do `omissoes`, rode o cruzamento entre telas e registre cada suspeita forte como diferença `INCONSISTENCIA-PROTO`, sem descartar nenhuma ([cobertura.md](references/cobertura.md#cruzamento-entre-telas-em-avaliação)). O `rastreio` final leva `--cruzamentos`. Formatos e comandos: [references/cobertura.md](references/cobertura.md).
- O esperado vem do protótipo novo; código do produto nunca vira `definition`.

## 6. Lado do protótipo

Só leitura de arquivos e `git` (o «Execution boundary» de `prototype-parity-verification`, já resumido aqui; não é preciso abrir aquela skill neste ciclo). Nada de Playwright (nem o MCP), HTTP, install, build, dev server ou testes no protótipo. Pedido de print vira `SEM_COMPARACAO` e pedido de captura ao Diego.

## 7. Não examinado e pulos

O que não foi examinado entra `NAO_INVESTIGADO` com `owner`, `risk` e `resume_trigger`. Pedido para pular uma etapa: cumpra, registre assim e diga no resumo. Limite de telas («no máximo N»): as demais entram `NAO_INVESTIGADO`, nomeadas; quais ficam fora é do Diego, com a lista do mapa.

## 8. Entrega e parada

Resumo com quatro listas separadas: mudanças versão anterior → nova; gaps protótipo → produto; sobras produto → protótipo; correções protegidas tocadas. Acrescente a linha de cobertura, gerada pelo comando `resumo` ([references/cobertura.md](references/cobertura.md#linha-de-cobertura-do-resumo)), não examinados, cenários herdados sem reinvestigação, códigos de linkage presentes, a decisão do modo e as decisões que só o Diego toma, inclusive as inconsistências entre telas do cruzamento: cada suspeita forte com a pergunta, as telas e as diferenças afetadas, mais a contagem de fracas e preexistentes. Na primeira sincronização, diga «vigente: árvore vazia (sem catálogo nem versão nomeada)»; a lista versão anterior → nova é «não se aplica» e sobra sem prova na vigente é `NAO_COMPROVADA`. A conferência de paridade do entregue vem depois da implementação, pelo Superpowers com `prototype-parity-verification` (`verificacao.py stubs` e `sem-teste`). **Pare aí**: o plano começa depois da adoção.

## Depois: adoção e baseline

Adotar é o merge da branch, por decisão do Diego. Marcar a baseline como confiável só no encerramento da onda, com o marco confirmado. Os dois rodam em outra sessão: siga [references/adocao-e-baseline.md](references/adocao-e-baseline.md).

## Precedência

Para protótipo em repositório Git público, este procedimento prevalece sobre as rules de import Lovable (`sgd-novo-lovable-proto`, `sgd-novo-proto-diff-revisao`). Este ciclo não abre DEF-AUDIT, PRE/POST nem gates. Detalhes do SGD: [references/sgd.md](references/sgd.md).
