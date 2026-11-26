---
name: descoberta-em-ondas
description: 'Use quando a skill atualizacao-versao-prototipo indicar descoberta em ondas: o mapa de cobertura da versão não cabe na leitura de um agente (cabe_em_um_agente false) ou o Diego pediu ondas. Divide a leitura das telas em unidades lidas por agentes em paralelo e integra os achados no catálogo de paridade.'
---

# Descoberta em ondas

Uma versão com dezenas de telas alteradas não cabe na leitura de um agente: ele lê umas e esquece outras. Aqui a leitura é dividida em **unidades** que cabem no orçamento, lidas por agentes em paralelo; você é o **integrador**, o único que escreve no catálogo. Nenhum papel segura a versão inteira: a onda 0 só lê o mapa, cada agente só a sua unidade, e você só os achados compactos de cada onda.

Esta skill substitui a leitura de telas da `atualizacao-versao-prototipo` (gaps e mudanças, §5). Identidades, modo, worktree do catálogo, inventário inverso, validação e resumo continuam lá; ao terminar, volte para ela.

`<versao>` é o diretório da skill `atualizacao-versao-prototipo` (irmão deste) e `<ondas>` é o desta skill; o CLI é `python3 <versao>/scripts/cobertura.py`. Arquivos de trabalho vão num diretório temporário `<tmp>` e são descartados: o único registro é o catálogo. Formatos dos arquivos e brief dos agentes: [references/formatos.md](references/formatos.md).

## Onda 0: unidades, sem ler o patch

Você já tem `<tmp>/mapa.json` do `mapear`. Monte as unidades só com ele: nomes, rotas, trechos, importadores e pesos. Abrir o diff aqui para «entender» devolve o problema do agente único sobrecarregado.

```bash
python3 <versao>/scripts/cobertura.py unidades --mapa <tmp>/mapa.json --propor --saida <tmp>/unidades.json
python3 <versao>/scripts/cobertura.py unidades --mapa <tmp>/mapa.json --unidades <tmp>/unidades.json
```

- A proposta já junta telas ligadas pelo mesmo componente ou chave e o mesmo grupo de rotas, e enche até o orçamento. Ajuste só por coesão (telas sem relação não ficam juntas só porque cabem) e confira de novo.
- Unidade com `dividir_por_regiao`: uma tela acima do orçamento. Preencha `regioes` com as regiões do catálogo dessa tela; sem catálogo, nomeie as regiões pela estrutura de topo do arquivo da tela (seções, abas, tabela, formulário, modais), sem ler o diff, em nomes sem espaço nem barra (`RG-tabela`), que vão ao nome do arquivo. Precisa de **pelo menos `ceil(peso / orçamento)` regiões**: uma unidade de 500 mil com orçamento de 100 mil pede 5, e uma região só não tira a unidade do orçamento. A flag vale só para unidade de uma única tela. Na onda, despache um agente por região da unidade, cada um com o brief e a região dele (campo `regiao` do despacho); cada um grava `achados/<U-xx>-<regiao>.json`, e os arquivos **não são juntados**: a conferência lê todos ([regra de junção](references/formatos.md#unidade-dividida-por-região)).
- **Idiomas:** o `--propor` deixa os trechos de locale fora do idioma de referência (`--idioma-referencia`, padrão `pt-BR`) numa `U-IDIOMAS` com `sem_agente: true`, fora do orçamento. Nenhum agente a lê, nem como contexto. Os agentes leem só o idioma de referência. Sem a referência entre os trechos, nada se separa e os locales seguem nas unidades. Rode, antes da onda 1:

  ```bash
  python3 <versao>/scripts/cobertura.py idiomas --mapa <tmp>/mapa.json --unidades <tmp>/unidades.json --repo <prototipo> --saida <tmp>/achados/U-IDIOMAS.json
  ```

  Ele compara cada idioma com a referência (chaves faltando, chaves a mais, texto igual ao da referência) e grava os achados da unidade, uma proposta por idioma. Não julga a qualidade da tradução. Saída 11 (`status: FALHA`): a referência não tem chave legível; nada foi comparado, e a unidade segue como unidade em falha.
- **Só siga para as ondas com a conferência em 0.** Saída 11: corrija `unidades.json` e confira de novo até 0, sem subir `--orcamento` (mudar o orçamento é decisão do Diego, e «conferir até 0» não se cumpre assim). `trechos_sem_unidade` ou `telas_sem_unidade`: acrescente à unidade da tela ou a uma `U-COMP`; `arquivos_sem_unidade`: acrescente o arquivo à unidade que o lê. `trechos_duplicados`, `telas_duplicadas` ou `unidades_duplicadas`: deixe numa só. `acima_do_orcamento` com várias telas: separe; com uma tela: `dividir_por_regiao`. `desconhecidos` ou `telas_desconhecidas`: a proposta é de outro mapa, refaça-a a partir deste. `U-COMP` acima do orçamento, ou achado que esses ajustes não zeram: **pare antes da onda 1** e leve ao Diego a saída da conferência, os arquivos e os pesos. Nenhum agente é despachado com a conferência em 11, nem com aval genérico para seguir.

## Ondas de leitura

- Com a conferência em 0, grave um arquivo por unidade: `python3 <versao>/scripts/cobertura.py fatiar --mapa <tmp>/mapa.json --unidades <tmp>/unidades.json --pasta <tmp>/unidades`. Cada agente lê só o da unidade dele. Motivo: na descoberta de 02/11, 8 de 11 agentes abriram o `unidades.json` inteiro, e cerca de 37 mil caracteres entraram no contexto de cada um, em boa parte sobre outras unidades.
- Até 6 agentes `task-researcher` ao mesmo tempo, uma unidade cada; as demais na onda seguinte. Declare o modelo e o esforço em cada despacho: `haiku` com esforço `high`, decisão do Diego em 02/11/2026, ainda sem medição em material real. A avaliação de 01/11 usou esforço médio e deu 20/20 diferenças em duas execuções, numa versão sintética. A unidade que voltar com problema é refeita **uma vez** em `sonnet`, e na segunda falha segue o que «Conferir antes de integrar» e «Integrar» mandam (`NAO_INVESTIGADO`, sem terceira tentativa em outro modelo). A recomendação está em avaliação até o piloto real. A conferência de achados confere a forma e a cobertura dos trechos; ela não julga se o conteúdo está certo.
- O despacho é o brief de [references/formatos.md](references/formatos.md#brief-do-agente-de-unidade), com os caminhos preenchidos. O agente grava os achados num arquivo e devolve 2-3 linhas; o que vale é o arquivo.
- **Agente que parou (limite de turnos ou arquivo com `status: PARCIAL`): não o retome.** Retomar soma contexto ao que ele já tem: no piloto de 02/11, os agentes pararam perto de 140 mil tokens e, retomados, foram a até 194 mil. Despache um agente novo com a mesma unidade, o arquivo parcial e a ordem de completar só os trechos sem destino. Isso conta como a única nova tentativa da unidade.
- **Teto de 150 mil tokens de contexto por agente.** A ferramenta não corta por tokens; o teto se mede depois, em `max_context` do `jarbas.py usage`. Agente acima dele vai ao resumo: a unidade precisava ser menor.

## Conferir antes de integrar

Para cada unidade da onda:

```bash
python3 <versao>/scripts/cobertura.py achados --unidades <tmp>/unidades.json --unidade <U-xx> --arquivo <tmp>/achados/<U-xx>.json
```

Unidade dividida por região: informe o par `--regiao`/`--arquivo` de cada região (a cobertura é a união dos arquivos):

```bash
python3 <versao>/scripts/cobertura.py achados --unidades <tmp>/unidades.json --unidade <U-xx> --regiao <R1> --arquivo <tmp>/achados/<U-xx>-<R1>.json --regiao <R2> --arquivo <tmp>/achados/<U-xx>-<R2>.json
```

Saída 11 (arquivo ausente, cortado, trecho sem destino, proposta sem campo, falha declarada; na unidade dividida também destinos divergentes entre regiões, região sem arquivo ou declarada em outro): devolva os `problemas` **à mesma unidade uma vez, num agente novo** (na dividida, só às regiões citadas após o `@` de cada problema; `DESTINO_DIVERGENTE` e `TRECHO_SEM_DESTINO` voltam às duas regiões ou à que deveria ter lido o trecho), sem integrar nada dela. Na segunda falha, nada desse arquivo é integrado (nem as propostas que estavam válidas): todos os trechos da unidade entram `NAO_INVESTIGADO`, como abaixo, e vão ao resumo. Não integre um arquivo que não passou.

## Integrar (fim de cada onda)

Só você escreve no catálogo, no worktree que a skill da versão abriu:

- Cada proposta vira diferença com ID novo e único (e requisito com `scenario_ids`, como na skill da versão). Propostas de unidades diferentes sobre o mesmo componente ou chave viram **uma** diferença com as telas afetadas.
- Cada proposta da `U-IDIOMAS` vira uma diferença do idioma, na moldura comum (a superfície da casca, como `SF-LAYOUT`), com o que o idioma tem no produto em `antes` e a fonte no produto.
- Acumule a tabela de rastreio em `<tmp>/rastreio.json` ([formato](../atualizacao-versao-prototipo/references/cobertura.md#tabela-de-rastreio)): cada trecho com a diferença em que entrou, ou `SEM_IMPACTO` com o `motivo` do agente.
- `NAO_INVESTIGADO` (do agente ou da segunda falha) não se copia: o rastreio exige `local`. Crie no catálogo uma região (ou estado) com `discovery_status: NAO_INVESTIGADO`, `owner`, `risk` e `resume_trigger` (formato em [catalogo.md](../atualizacao-versao-prototipo/references/catalogo.md)), uma por tela ou região, com o `motivo` do agente no `risk`, e grave o ID em `local` de cada trecho dela. Trechos da mesma região repartem o mesmo `local`.
- Depois da integração, rode `cobertura.py inventario` e copie `arquivos` e `componentes` de cada tela e moldura para `surfaces[]` ([comando](../atualizacao-versao-prototipo/references/cobertura.md#inventário-por-tela)); passe as molduras por `--moldura`, arquivo por arquivo.
- Rode `rastreio` sobre o acumulado, com `--repo <prototipo>`: se a `identidade` do mapa reprovar (`MAPA_DESATUALIZADO`: a branch andou depois dele), refaça o mapa e as unidades. Todo trecho que sair em `faltantes`, `ids_inexistentes`, `sem_motivo`, `local_invalido` ou `desconhecidos` volta à unidade dele uma vez; depois, `NAO_INVESTIGADO` como acima.

## Leitura cega: passada de fatos

Depois da última onda, siga [references/passada-de-fatos.md](references/passada-de-fatos.md), em todas as etapas. Ela lê as telas sem o catálogo nem os achados e grava o que ele não trazia. **O Diego não aceita o Haiku sem a revisão de um modelo melhor:** a etapa de revisão não se pula.

O resultado alimenta `<tmp>/itens-omitidos.json` ([formato](references/formatos.md#itens-omitidos)) e o `resumo`. Depois do `omissoes`, rode o cruzamento entre telas com `--unidades <tmp>/unidades.json`. Ele aponta também a suspeita que junta telas de unidades diferentes ou de fora do mapa. Registre e resuma como em [cobertura.md](../atualizacao-versao-prototipo/references/cobertura.md#cruzamento-entre-telas-em-avaliação), sem agente verificador e sem descartar suspeita.

## Voltar para a skill da versão

Siga no inventário inverso, validação e resumo da `atualizacao-versao-prototipo`. Gere a linha de cobertura com o comando `resumo` ([cobertura.md](../atualizacao-versao-prototipo/references/cobertura.md#linha-de-cobertura-do-resumo)), sem contar à mão; o caminho é «ondas» com o número de unidades e de ondas e o motivo (peso total × orçamento, ou pedido do Diego). Unidade que terminou em `NAO_INVESTIGADO` aparece pelo ID.
