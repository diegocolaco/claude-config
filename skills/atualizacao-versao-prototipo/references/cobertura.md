# Cobertura da descoberta

O mapa diz **onde** a versão mudou, trecho a trecho; o rastreio confere que cada trecho teve um destino. Os dois não decidem o que é requisito: isso continua sendo a leitura da tela. Os arquivos ficam num diretório temporário (`mktemp -d`) e são descartados no fim: o único registro é o catálogo.

Os comandos abaixo estão completos; não é preciso `--help`. `<skill>` é o diretório desta skill.

## Mapa

```bash
python3 <skill>/scripts/cobertura.py mapear --repo <prototipo> --vigente <checkout vigente> --candidata <checkout candidata> --saida <tmp>/mapa.json
```

Sem catálogo nem versão nomeada (primeira sincronização), troque `--vigente <checkout vigente>` por `--sem-vigente`: a vigente é a árvore vazia, toda tela entra como nova e o mapa avisa. Uma das duas flags é obrigatória, nunca as duas. O orçamento é o padrão do mapa; `--orcamento` só muda com o Diego.

O mapa liga trecho a tela pelas rotas e reconhece três formatos de protótipo, cada um descrito por um preset JSON em `<skill>/scripts/rotas/` (ver «Presets de rotas»):

- **Umi Max** (Ant Design) (`umi.json`): `config/routes.ts`;
- **React Router** (`react-router.json`): `<Route path element>` e `createBrowserRouter([...])` em `src/App.tsx`, `src/main.tsx`, `src/routes.tsx`, `src/router.tsx` ou `index.tsx` dessas pastas;
- **TanStack Router** (`tanstack.json`; export Lovable: Vite + TanStack Router + shadcn): um arquivo por rota em `src/routes/` (ou no `routesDirectory` do `tsr.config.json`), pelas convenções do roteador (`.` separa segmentos, `index` é a raiz da pasta, `$param` é segmento dinâmico, `_x` e `(grupo)` não geram caminho, `x_` tira o aninhamento, `-x` é ignorado, `.lazy` é a mesma rota). Sem `tsr.config.json`, a pasta só vale se algum arquivo dela usar o TanStack (`src/routes/` também existe em outros roteadores). `route.tsx`, `__root.tsx`, o arquivo `_x.tsx` e o pai com `<Outlet />` e filhas são layout: não são tela e entram como dependência de toda tela abaixo deles, junto com o que eles importam (mudar o layout põe essas telas em `afetada_por` e o arquivo em `compartilhados`). Se a rota só aponta para um componente de outro arquivo (`component: Foo` com `import Foo from '../pages/Foo'`), a tela é esse arquivo e o de rota vira dependência. Rota de servidor (`server: { handlers }` sem `component`, ex.: `api.health.ts`) não é tela. Também lê `createRoute({ getParentRoute, path, component })`, com o caminho resolvido pelo pai. Não lê: `routesDirectory` só do plugin do Vite, `[.]` para escapar ponto e `getParentRoute` com alias de import.

Com mais de um formato no mesmo protótipo, o mapa usa as rotas de todos (a primeira rota repetida vale, na ordem Umi, React Router, TanStack) e avisa quando o TanStack está entre eles. O mapa grava em `presets_de_rotas` os presets detectados ou impostos por `--rotas`: `nome`, `origem` (`skill` ou o caminho do `--rotas`), as `revisoes` (`vigente`, `candidata`) em que a marca do preset casou e `rotas`, quantas rotas ele deu ao mapa em cada uma. `routeTree.gen.ts` é arquivo de build do TanStack: fica fora do mapa e dos trechos, listado em `ignorados` e num aviso.

Imprime um resumo em JSON de poucas linhas (`peso_total`, `cabe_em_um_agente`, `trechos`, `telas`, `peso_sem_tela`); o mapa inteiro fica em `mapa.json`. Leia dele só o que a etapa precisa:

- `telas[]`: `id`, `rota`, `arquivo`, `nova`, `removida`, `trechos`, `afetada_por` (arquivo alterado que a tela usa sem diff próprio), `acoplamentos` (chave de texto, mock, rota ou config compartilhada), `peso`.
- `compartilhados[]` e `acoplamentos[]`: o arquivo ou a chave, as telas atingidas e os trechos. Em locale, a chave também vale quando o valor trocado está na linha seguinte (`'p.centro':` e, abaixo, `'Centro de resultado',`), o formato do ant-design-pro.
- `arquivos[]`: caminho, status e `tokens_estimados` (custo de ler o arquivo inteiro; falta em binário).
- `presets_de_rotas`: os presets de rotas detectados ou impostos (nome, origem, revisões e `rotas` por revisão). Lista vazia, ou `rotas` 0, junto de «Nenhuma rota reconhecida» é o sinal de que nenhum preset leu rota.
- `vigente_sha` e `candidata_sha`: os commits em que `vigente` e `candidata` apontavam ao gerar o mapa. É a identidade do mapa; o `rastreio` a confere (abaixo). Com `--sem-vigente`, `vigente` e `vigente_sha` guardam o hash da árvore vazia (não é commit).
- `peso_total` é o peso das telas mais `peso_sem_tela`: trechos que nenhuma tela usa, pesados pelo tamanho do arquivo (se couber no orçamento) ou pelas linhas alteradas. Arquivo que é o da própria tela não entra de novo (o peso da tela já o contém); o de acoplamento (locale, mock) entra inteiro, pois nenhuma tela o contém. `cabe_em_um_agente` olha esse total.
- `avisos`: rota sem arquivo, rota repetida, orçamento excedido e os dois abaixo. Cada aviso vai ao resumo. Lockfile (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` e afins, em qualquer pasta) não fica fora: é lido como **um trecho só** (`<lock>#arquivo`, peso 100 se passar do orçamento), com aviso próprio («N lockfile(s) lido(s) como um trecho só…»): dependência direta se lê no `package.json`, e troca de versão de biblioteca de UI se confere à mão; sem `package.json` alterado em nenhuma pasta, o aviso diz que só mudou dependência transitiva. Ele ainda precisa de destino no rastreio (por exemplo `SEM_IMPACTO` com motivo). Metadados `.squad/` e a árvore `routeTree.gen.ts` ficam fora do mapa e aparecem em `ignorados`, cada um com o seu aviso; o de «Rotas de mais de um formato» diz que Umi ou React Router convivem com o TanStack.
  - «Nenhuma rota reconhecida … (mas N arquivos de página/tela mudaram)»: os presets em uso (detectados ou de `--rotas`) deram zero rotas numa revisão (o aviso diz «na vigente» ou «na candidata» se for só uma) e o diff não é vazio; vale em qualquer pasta de páginas, e o trecho «mas N arquivos…» só aparece se arquivos em `pages/`, `views/`, `screens/` ou `telas/` mudaram. As rotas não estão onde os presets procuram (com os da skill: `config/routes.ts`, `src/App.tsx`, `src/main.tsx`, `src/routes.tsx`, `src/router.tsx`, `index.tsx` dessas pastas ou `src/routes/` e o `routesDirectory` do TanStack Router; o aviso lista os locais do preset em uso). Nenhum trecho se liga a tela e o peso vem do tamanho dos arquivos. Não confie em `cabe_em_um_agente`: veja onde estão as rotas e leia por tela à mão, ou siga em ondas.
  - «Rota dinâmica em <arquivo>:<linha>»: um `<Route>` cujo `path` tem interpolação (`` path={`${base}/x`} ``) ou expressão não é lido, nem as filhas dele. A tela fica fora do mapa até você conferi-la à mão; `path={`/x`}` sem `${}` é lido normalmente.
  - «Arquivo volumoso <caminho> (<N> tokens): dê destino pelo cabeçalho e pelas chaves, sem ler inteiro»: arquivo alterado, fora das telas e acima de um quarto do orçamento (mock, dado, config gerada). Só avisa: o trecho continua no mapa e precisa de destino. Lockfile não recebe este aviso, tem o seu.
  - «Primeira sincronização: vigente é a árvore vazia; toda tela entra como nova»: aparece só com `--sem-vigente`.
  - «N trechos de M arquivos não se ligam a nenhuma tela»: código solto, texto sem consumidor, config. Cada um precisa de destino no rastreio como os demais; se forem muitos, é sinal de rota não reconhecida.

Trecho é um bloco contíguo de linhas alteradas (`arquivo#L10-24`), uma chave de texto (`arquivo#pedido.status`), uma remoção dentro do arquivo (`arquivo#del:L3-5`) ou o arquivo inteiro quando ele é binário, só renomeado ou removido (`arquivo#arquivo`).

Tela com `afetada_por` ou `acoplamentos` e sem trecho próprio **é tela alterada**: o efeito vem do componente, do texto, do mock ou da rota que passou a renderizar outro componente (o arquivo de rotas fica em `afetada_por`). Leia a tela inteira junto com o arquivo que a atinge.

## Presets de rotas

O código tem três estratégias de leitura e o preset diz o que muda de uma convenção para outra da mesma família. A detecção é automática: o `mapear` aplica as `marcas` de cada preset da skill a cada revisão (vigente e candidata) e usa os que casarem, na ordem de `prioridade` (Umi 10, React Router 20, TanStack 30). Para um protótipo com outra convenção, escreva um preset e passe `--rotas`: o mapa usa só ele e pula a detecção.

```bash
python3 <skill>/scripts/cobertura.py mapear --repo <prototipo> --vigente <vigente> --candidata <candidata> --rotas <preset>.json --saida <tmp>/mapa.json
```

O `cruzar` relê o preset pelo caminho que o mapa gravou, e o caminho relativo é gravado como foi passado: mantenha o arquivo acessível até o `cruzar` e rode-o do mesmo diretório (ou passe `--rotas` com caminho absoluto).

Preset inválido (estratégia desconhecida, campo obrigatório ausente, tipo errado, campo que não existe, regex inválida, `--rotas` vazio) sai 2 com o campo na mensagem (`campo «segmento.separador» deve ser um único caractere`). O preset é lido do disco e nada é gravado no protótipo. Caminhos usam `/` (a barra invertida é normalizada) e são normalizados na carga (`./app//routes/` vira `app/routes`); `*` casa qualquer sequência, inclusive `/`.

**`marcas.conteudo` vai para o `git grep -E`**: o subconjunto portável é o ERE do POSIX (`(...)`, `|`, `?`, `*`, `+`, `{n,m}`, `^`, `$`, classes `[[:alpha:]]`). `\b`, `\w` e `\s` são extensões do GNU: o git do macOS pode usar o regex BSD, que não as lê como o GNU; troque `\b` por `(^|[^A-Za-z0-9_])` antes da palavra e por `([^A-Za-z0-9_]|$)` depois dela (como o preset do TanStack). Não valem os construtos de Python que o git leria como outra coisa: grupo `(?:...)` e lookahead/lookbehind `(?=...)`, `\d` (use `[0-9]`) e quantificador não ávido (`+?`, `*?`); o preset que os usa é rejeitado na carga, citando `marcas.conteudo`. Se o `git grep` falhar mesmo assim (código 128, por exemplo classe `[[:foo:]]` desconhecida), o mapa sai 2 com a mensagem do git. O `criador` é buscado como texto literal (metacaracteres são escapados).

**Campos comuns** (todos os presets): `nome`, `rotulo` (nome do formato nos avisos), `estrategia` (`objeto-config`, `jsx` ou `arquivos`), `marcas` (`arquivos`: padrões de caminho; `conteudo`: expressão regular ERE buscada nos arquivos de código; ao menos um dos dois, e basta um casar), `prioridade` (opcional, padrão 100; menor vale primeiro), `aliases` (opcional, padrão `{"@/": "src/"}`), `descricao` (opcional).

| Estratégia | Lê | Campos próprios |
|---|---|---|
| `objeto-config` | lista de objetos `{ path, component, routes }` num arquivo de configuração (Umi) | `arquivos`; `chaves` (`caminho`, `componente`, `filhas`); `pasta_componentes` (base do `component` relativo) |
| `jsx` | tags `<Route path element>` e listas de objetos (`createBrowserRouter`, `useRoutes`) | `arquivos`; `tag`; `atributos` (`caminho`, `elemento`, `componente`, `indice`, `lazy`, `filhas`); `listas` (regex do início de cada lista de objetos, que precisa terminar em `\[`, o abre-colchete da lista; a carga rejeita a que não termina); `nao_tela` (tags que não são tela) |
| `arquivos` | um arquivo por rota numa pasta, mais rotas por código | `pasta`; `extensoes`; `config` (`arquivo` e `chave_pasta`, opcional: a pasta do roteador mora nessa chave do JSON); `gerado` (nome-base do arquivo gerado, fora do mapa); `marca_da_pasta` (sem `config`, a pasta só vale se algum arquivo casar); `segmento`; `chaves` (`componente`; `servidor`, `caminho`, `id`, `pai` opcionais); `lazy_funcao`, `outlet`, `criador` (opcionais) |

`segmento` (estratégia `arquivos`; entre parênteses, o valor do TanStack):

- `separador` (`.`): um caractere que separa segmentos no nome do arquivo, além de `/` (`posts.$id.tsx` é `posts/$id`);
- `sem_caminho` (`_`): prefixo de segmento que não gera caminho (`_authenticated`, layout sem URL);
- `sem_aninhamento` (`_`): sufixo que tira o aninhamento (`posts_` vira `posts`);
- `ignorado` (`-`): prefixo de arquivo ou pasta fora do mapa (`-helper.tsx`);
- `grupo` (`["(", ")"]`): par abre/fecha de segmento de agrupamento, que não gera caminho (`(grupo)`);
- `layout` (`route`): nome final que torna o arquivo layout da pasta (`users/route.tsx` não é tela); `raiz` (`__root`): arquivo raiz, dependência de toda tela;
- `indice` (`index`): segmento final que vira a raiz da pasta (`users/index.tsx` é `/users`);
- `sufixo_lazy` (`.lazy`): sufixo da metade preguiçosa da mesma rota;
- `parametro` (`$`): prefixo de segmento dinâmico; a rota do mapa o escreve sempre com `$` (`:id` vira `$id`);
- `nao_rota` (`.d`, `.gen`, `.test`, `.spec`, opcional): sufixos do nome (antes da extensão) de arquivo que não é rota.

`criador` liga a leitura de rotas por código (`createRoute({ getParentRoute, path, component })`) e exige `chaves.caminho`, `chaves.id` e `chaves.pai`; sem ele só as rotas por arquivo valem.

**`.umirc.ts` não é lido.** O `umi.json` só lê `config/routes.ts`: o `objeto-config` começa no primeiro `[` do arquivo e lê os objetos depois dele, então, num `.umirc.ts` com `plugins: [...]` antes de `routes: [...]`, pegaria o lugar errado. Para um Umi que declara as rotas ali, confira o arquivo e escreva um preset com `arquivos: [".umirc.ts"]`.

Exemplo: convenção `app/routes/pedidos+:id.tsx` (separador `+`, parâmetro `:`), sem código novo:

```json
{
  "nome": "remix-flat", "rotulo": "Remix flat routes", "estrategia": "arquivos",
  "marcas": {"arquivos": ["app/routes/*"]},
  "aliases": {"~/": "app/"},
  "pasta": "app/routes", "extensoes": [".tsx", ".ts"],
  "segmento": {"separador": "+", "sem_caminho": "__", "sem_aninhamento": "_", "ignorado": "-", "grupo": ["(", ")"],
               "layout": "_layout", "raiz": "root", "indice": "_index", "sufixo_lazy": ".lazy", "parametro": ":"},
  "chaves": {"componente": "component"}
}
```

Os presets da skill (`rotas/*.json`) são os melhores modelos: copie o da família mais próxima e troque os valores. **Limite:** convenção que não cabe numa das três estratégias (rota declarada em outro formato de arquivo, por exemplo) exige código novo no `cobertura_mapa.py`; até lá o mapa avisa «Nenhuma rota reconhecida» e o peso vem do tamanho dos arquivos.

## Tabela de rastreio

Um JSON com uma entrada por trecho do mapa:

```json
{"trechos": {
  "src/pages/Pedidos.tsx#L10-24": {"destino": "DF-12"},
  "src/locales/pt-BR.ts#menu.ajuda": {"destino": "SEM_IMPACTO", "motivo": "chave sem consumidor em rota"},
  "mock/pedidos.ts#L3-9": {"destino": "NAO_INVESTIGADO", "local": "RG-PEDIDOS-LISTA"}
}}
```

- `DF-…`: a diferença do catálogo em que o trecho entrou. Vários trechos podem ir para a mesma diferença.
- `SEM_IMPACTO`: exige `motivo` que outra pessoa consiga conferir (formatação, comentário, chave sem uso, arquivo de build).
- `NAO_INVESTIGADO`: exige `local`, a região ou o estado do catálogo marcado `NAO_INVESTIGADO` com `owner`, `risk` e `resume_trigger`.

Preencha a tabela enquanto lê, não no fim: é ela que mostra o que falta ler.

## Conferências

```bash
python3 <skill>/scripts/cobertura.py rastreio --mapa <tmp>/mapa.json --rastreio <tmp>/rastreio.json --catalogo <produto-wt>/.squad/contracts/parity/catalog.json --repo <prototipo> [--cruzamentos <tmp>/cruzamentos.json]
python3 <skill>/scripts/cobertura.py omissoes --antes <tmp>/catalogo-antes.json --depois <produto-wt>/.squad/contracts/parity/catalog.json
```

`rastreio` sai 0 quando tudo tem destino válido e 11 com achados: `faltantes` (trecho sem destino), `desconhecidos` (trecho que não é do mapa, sinal de mapa de outra versão), `ids_inexistentes` (DF que não está no catálogo), `sem_motivo`, `local_invalido`. `com_destino` conta só os destinos válidos, então `com_destino` menor que `total` sempre tem um desses cinco códigos por trás. Também reprova a identidade do mapa (`identidade`, lista de achados com `codigo`): com `--repo`, `MAPA_DESATUALIZADO` quando `vigente` ou `candidata` apontam hoje para outro commit que o gravado em `vigente_sha`/`candidata_sha` (a branch andou depois do mapa: refaça o mapa e a leitura); sem `--repo`, `MAPA_OUTRA_VERSAO` quando a `reference.version` do catálogo não é a `candidata_sha` do mapa. Mapa gerado antes dos SHAs, ou catálogo sem `reference.version`, não tem o que comparar e passa. Passe `--repo` sempre que tiver o repositório do protótipo. Com `--cruzamentos`, também reprovam `suspeitas_sem_destino` (suspeita forte sem diferença `INCONSISTENCIA-PROTO` com a assinatura em `cruzamento`) e o achado de identidade `CRUZAMENTO_OUTRA_VERSAO` (o `cruzamentos.json` é de outra candidata que a do mapa). Saída 2 é erro de uso; corrija o comando.

`omissoes` lista as diferenças que existem no catálogo depois da leitura cega e não existiam antes dela. Guarde a cópia de antes (`cp` do catálogo para `<tmp>/catalogo-antes.json`) imediatamente antes de integrar a leitura cega. A leitura cega é a [passada de fatos](../../descoberta-em-ondas/references/passada-de-fatos.md), mesmo quando o mapa cabe num agente: ela grava fatos por cenário, não diferenças, então o `omissoes` pode dar 0 e a medida fica nos itens de `--itens-omitidos`.

## Cruzamento entre telas (em avaliação)

A leitura por tela, de um agente ou por unidade, não compara telas entre si. O cruzamento procura, por script, em todas as telas da candidata, inclusive as que estão fora do mapa:

- **D1, guarda assimétrica:** a mesma coluna ou campo com guarda de permissão numa tela e sem guarda em outra, com a assimetria nova na versão. Guarda é `access.X`, nome do `useAccess()`, `<Access accessible>`, `hideInTable`, papel do `useAuth()` ou guarda de rota.
- **D2, texto antigo intacto:** um texto trocado (valor de chave do locale, ou literal trocado no diff) com um literal antigo no mesmo elemento: mensagem, placeholder ou dica.

Na primeira sincronização `preexistentes` é 0: todo D1 é novo e o D2 não se aplica (não há texto da versão anterior).

Rode só **depois do `omissoes`**, para a leitura cega continuar medindo a leitura:

```bash
python3 <skill>/scripts/cobertura.py cruzar --mapa <tmp>/mapa.json --repo <prototipo> --catalogo <produto-wt>/.squad/contracts/parity/catalog.json [--unidades <tmp>/unidades.json] [--idioma pt-BR] --saida <tmp>/cruzamentos.json
```

`--idioma` escolhe os arquivos de locale lidos pelo texto antigo; sem ele, vale `pt-BR`.

Saída 11 é suspeita forte, ou mapa desatualizado: nesse caso, refaça o mapa. Cada suspeita forte vai ao Diego como está: nenhuma é descartada, nem por você nem por outro agente.

- **Diferença:** cada suspeita forte vira uma diferença aberta, com:
  - `classe: "INCONSISTENCIA-PROTO"` e `cruzamento: "<assinatura>"`;
  - todas as telas da suspeita em `surface_ids`, criando a superfície (`id`, `rota`, `arquivo_prototipo`) de tela que não tem;
  - `agora` com a `pergunta` e as linhas do protótipo;
  - `produto_precisa: "Depende da decisão do Diego"`;
  - nenhum requisito até a decisão.
  - Se a suspeita é a mesma de uma diferença já registrada, acrescente a assinatura ao `cruzamento` dela, que vira uma lista.
- **Afetadas:** em cada diferença de `afeta_df`, grave `depende_de` com o ID da diferença nova e uma `nota`. O `produto_precisa` do agente fica como está; não o reescreva com o texto da suspeita.
- **Resumo:** nas decisões do Diego, uma linha por suspeita forte, com:
  - o ID da diferença e a `pergunta`;
  - as telas, e `fora_do_mapa` se houver;
  - as `afeta_df`, marcando as com `cita_texto`.
  - Depois, uma linha com a contagem de fracas e preexistentes, com as chaves do D1.
- **Fechamento:** o `rastreio` final leva `--cruzamentos <tmp>/cruzamentos.json`. `suspeitas_sem_destino` é suspeita que não chegou ao catálogo.

**Estrutura perdida.** O cruzamento lê a estrutura do arquivo (chaves, colchetes, parênteses e strings) sem rodar o protótipo. Se um arquivo termina com string ou template aberto (uma crase em regex ou no texto JSX) ou com delimitadores que não casam, o `cruzamentos.json` traz o aviso `ESTRUTURA_PERDIDA: <arquivo> (<candidata|vigente>): <motivo>`. Nenhuma suspeita que dependa desse arquivo é forte: no D1 ela vai às fracas com o motivo `estrutura_perdida`; no D2 ela conta em `fracas.D2_estrutura_perdida` (a chave só aparece quando há). Leia o arquivo à mão. Resíduo aceito: crases em número par podem fechar por engano, sem que nada seja detectado.

O cruzamento lê as telas e as rotas pelos mesmos presets do mapa (e pelo `--rotas` com que o mapa foi gerado). Só lê o protótipo por git: nada é gravado fora de `--saida`.

**Escopo da leitura.** Com rotas reconhecidas, o cruzamento lê os arquivos que as rotas ligam (a tela e os layouts), em qualquer pasta, e o que eles importam em `src/`, exceto `node_modules`, `components/ui`, `locales`, `i18n`, `services`, `integrations`, `mocks`, `tests`, `typings`, `types`, `*.d.ts` e afins. `src/` e essa lista de exclusões valem só para o que não veio de uma rota. Sem rota reconhecida, lê todos os arquivos de `src/` (menos os excluídos) e avisa. Cabe a você conferir `formato.arquivos_lidos` e `formato.telas`: o `cruzamentos.json` traz o aviso `NENHUM_ARQUIVO_LIDO` quando há telas e nenhum arquivo lido, e `TELA_SEM_LEITURA: <arquivo> (<tela>, candidata)` para a tela cujo arquivo de rota o cruzamento não lê (extensão fora de `.ts`, `.tsx`, `.js`, `.jsx`). Aviso desses quer dizer que o resultado «0 suspeitas» não prova nada: leia à mão.

Em avaliação: os detectores foram medidos na fixture sintética e numa sonda descartável sem LLM nos dois formatos reais (Umi Max com Ant Design e export Lovable em TanStack com shadcn), com 0 suspeitas fortes; a medição do export Lovable é da sonda, não do `cruzar` entregue (que, no par real `3492268c..c7a6bfde`, leu 118 arquivos de 27 telas e também deu 0 fortes). A adoção depende do piloto real: na primeira atualização real do protótipo oficial com o passo ligado, o Diego classifica cada suspeita forte como «procede» ou «ruído». O passo é adotado se houver no máximo 10 fortes e ao menos metade proceder. Com mais de 10 fortes, ou maioria de ruído, as regras são revistas antes de seguir. Com 0 fortes, o piloto é inconclusivo e se repete na versão seguinte.

## Inventário por tela

O catálogo diz o que muda em cada tela; o inventário diz do que ela é feita, para o plano reproduzi-la com os mesmos componentes do protótipo. O integrador copia `arquivos` e `componentes` de cada tela para `surfaces[].arquivos` e `surfaces[].componentes` do catálogo (campos extras: o motor de paridade não os lê).

```bash
python3 <skill>/scripts/cobertura.py inventario --mapa <tmp>/mapa.json --repo <prototipo> [--moldura <arquivo>]... --saida <tmp>/inventario.json
```

Lê só do git, na `candidata_sha` do mapa (nunca do disco: `src/.umi` existe no disco e não no git). Sai 0, ou 2 com a mensagem no stderr (JSON ilegível, mapa sem `candidata` ou `telas`, commit inexistente, `--moldura` fora da candidata); o que não se resolve vai em `avisos` e em `nao_resolvidos`, nunca em erro. `--moldura` (repetível) é um arquivo de entrada que não é tela, como `src/app.tsx`, o layout comum e o tema: sai em `molduras[]`, calculado como uma tela. Telas `removida` ficam de fora.

Por tela (e por moldura), listas ordenadas e sem repetição:

- `arquivos`: o fechamento de imports a partir do arquivo da tela, ele incluído. Segue `import`, `export ... from` e `import('literal')` em `.ts/.tsx/.js/.jsx/.mjs`; estilo e dado locais (`.css`, `.less`, `.json`, `.md`) entram sem ser seguidos; arquivo de tipos (`.d.ts`) é código e é seguido; `import('./x')` e `` import(`./x`) `` (crase sem interpolação) são literais. Barril (arquivo que só reexporta, inclusive `import X from './X'` mais `export { X }`) segue só o arquivo do símbolo pedido, e o barril entra na lista. Quando não dá para filtrar (`export *`, `import * as`, import padrão do barril, símbolo que o barril não declara), segue tudo e põe o barril em `barris`.
- `componentes`: por pacote externo (subcaminho conta no pacote: `antd/es/table` é `antd`), `valores` e `tipos` (`import type`, `{ type X }`). `{ Table as T }` grava `Table`, import padrão grava `default`, `import * as X` grava `*`, import só por efeito grava o pacote com listas vazias. `react` e `react-dom` ficam de fora; não há outra lista de bibliotecas.
- `elementos`: tags de Web Component (`<dom-table`, minúscula com hífen) nos arquivos do fechamento, sem comentários e sem o que está entre aspas; o Dom DS pode aparecer só como tag, sem import. É heurística: uma aspa solta no texto JSX esconde o resto da linha.
- `nao_resolvidos`: import relativo ou de alias que não existe na candidata, e `@@/...` (o Umi gera em `src/.umi`, fora do git; `@@/*` e `@@test/*` do `paths` caem aqui sozinhos). Import dinâmico não literal (`import(x)`) vai em `avisos` com o arquivo.

`global.<pacote>` conta, em todo o inventário (telas e molduras), os nomes distintos em `valores` e `tipos` (`default` e `*` contam como nome) e as `telas` que usam o pacote. Aliases: o inventário (só ele; `mapear` e `cruzar` não mudam) lê `compilerOptions.paths` e `baseUrl` do `tsconfig.json` (ou, sem ele, do `jsconfig.json`) da raiz da candidata, aceitando comentários e vírgula final e seguindo `extends` relativo (pacote de configuração base fica de fora); os aliases dos presets de rotas do mapa valem sobre os do tsconfig. `"@root/*": ["./*"]` vira o alias `@root/` para a raiz. Com `baseUrl`, `src/util` só é local se o arquivo existir na candidata; senão segue como pacote. `~/` e `#/` só valem se estiverem em `paths`; fora dele contam como pacote e geram aviso. `from '.'` e `from '..'` são relativos e `node:fs` e afins ficam fora de `componentes`. tsconfig ilegível ou `extends` ausente vira aviso, nunca erro.

**O que `--moldura` precisa cobrir.** O fechamento só anda por import. Layout-pai e convenções do framework são carregados sem que a tela os importe e não aparecem em `arquivos`: informe-os com `--moldura`. No Umi, por exemplo: `src/app.tsx`, `src/access.ts`, `src/global.tsx`, `src/loading.tsx`, o layout pai da rota (como `src/pages/list/search/index.tsx` para `/list/search/articles`) e o arquivo de locale do idioma principal. `--moldura` aceita arquivo, não pasta: passar uma pasta (por exemplo `src/locales`) sai com 2 («o arquivo não existe na candidata»), então passe arquivo por arquivo, e para locale, no mínimo o do idioma principal. Um barril filtrado também segue os `import './x'` dele (efeito), que rodam com qualquer símbolo.

**Limites conhecidos, mantidos.** Import dentro de string conta (a busca de import não distingue string de código); `require()` não é seguido; `.html` de template (o `document.ejs` do Umi, por exemplo) não é lido; `{a <b-c}` (comparação sem espaço depois do `<`) pode dar falso positivo em `elementos`; uma aspa solta em texto JSX esconde o resto da linha da busca de tags.

## Linha de cobertura do resumo

Gere a linha pelo script, depois da última integração, e copie o campo `linha` como está. Números escritos à mão já saíram errados (no piloto de 02/11, 350 trechos no lugar de 602).

```bash
python3 <skill>/scripts/cobertura.py resumo --mapa <tmp>/mapa.json --rastreio <tmp>/rastreio.json --catalogo <produto-wt>/.squad/contracts/parity/catalog.json --antes <tmp>/catalogo-antes.json --cega <tmp>/cega/1.json [--cega <tmp>/cega/2.json]... --itens-omitidos <tmp>/itens-omitidos.json --cruzamentos <tmp>/cruzamentos.json --caminho "<um agente | ondas (motivo)>"
```

Os arquivos de `--cega` e `--itens-omitidos` vêm de `relidas` e `omitidos`, na última etapa da passada de fatos.

Sai 0, ou 11 com trecho pendente ou tela nova sem releitura. Saída 11 por tela sem releitura só se aceita com a decisão do Diego, citada no resumo. A linha traz: trechos com destino, em diferenças, `SEM_IMPACTO` e `NAO_INVESTIGADO`, com as regiões; pendentes; diferenças no catálogo; telas relidas e novas sem releitura; omissões por item, por tela e por diferença; caminho; e cruzamento, com os avisos. O que não foi informado aparece como «não informado».
 Com `NENHUM_ARQUIVO_LIDO` ou `TELA_SEM_LEITURA`, «0 fortes» não prova nada: repita o aviso nas decisões do Diego.
