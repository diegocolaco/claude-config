# Formatos e brief

## Unidades (`unidades.json`)

Saída do `unidades --propor`; você só edita `telas`, `regioes` e o agrupamento.

```json
{"orcamento": 100000, "unidades": [
  {"id": "U-01", "telas": ["TL-vendas-pedidos", "TL-relatorios-vendas"], "regioes": [], "trechos": ["mock/pedidos.ts#L3-9", "src/pages/vendas/Pedidos.tsx#L40-52"], "contexto": [], "peso": 41200.0},
  {"id": "U-02", "telas": ["TL-cadastros-fornecedores"], "dividir_por_regiao": true, "regioes": ["RG-FORN-LISTA", "RG-FORN-FORM"], "trechos": ["..."], "peso": 130000.0}
]}
```

- `trechos`: os que a unidade **possui** e precisa destinar. `contexto`: trechos de outra unidade que ajudam a ler esta (só leitura).
- Unidade `U-COMP-nn`: trechos sem tela (componente puro, arquivo solto).
- Unidade `U-IDIOMAS`: trechos de locale fora do idioma de referência, com `"sem_agente": true` e `"referencia": "pt-BR"`. Não se despacha agente: os achados vêm do comando `idiomas`.
- `dividir_por_regiao` vale só para unidade de uma tela e exige `len(regioes) >= ceil(peso / orcamento)` regiões distintas (o exemplo acima, de 130000 com orçamento de 100000, pede 2). Nomes de região sem espaço nem barra: entram no nome do arquivo.

## Unidade dividida por região

Cada região da unidade é lida por um agente, com o brief abaixo e o campo `regiao` preenchido.

- **Despacho:** o campo `regiao` é um item de `regioes` da unidade. O agente lê a tela inteira, mas destina só os trechos que caem na região dele.
- **Arquivo:** `achados/<U-xx>-<regiao>.json`, no mesmo formato de «Achados de uma unidade», com `"regiao": "<regiao>"` na raiz e `"unidade": "<U-xx>"`. Os arquivos das regiões ficam como estão: não se juntam num `<U-xx>.json`.
- **Junção (feita pela conferência `achados --regiao R --arquivo F …`):** a cobertura da unidade é a união dos arquivos. Todo trecho de `trechos` da unidade precisa de destino em **ao menos um** arquivo de região (`TRECHO_SEM_DESTINO`); um trecho que cruza regiões pode estar em mais de um, desde que o `destino` seja o mesmo. Destinos diferentes para o mesmo trecho (`DESTINO_DIVERGENTE`) são achado e voltam ao integrador. Cada arquivo é conferido sozinho pelo que traz, sem exigir que cubra a unidade, e o problema dele leva `@<regiao>`. Região da unidade sem arquivo é `REGIAO_SEM_ARQUIVO`, região que não é da unidade é `REGIAO_DESCONHECIDA` e `regiao` declarada em outro valor é `REGIAO_DIVERGENTE`.
- **Integração:** o integrador lê todos os arquivos de região. As referências de proposta (`P1`) valem dentro de cada arquivo; propostas de regiões diferentes sobre o mesmo componente ou chave viram uma diferença só.

## Achados de uma unidade (`achados/<U-xx>.json`)

```json
{"unidade": "U-01", "status": "OK",
 "trechos": {
   "src/pages/vendas/Pedidos.tsx#L40-52": {"destino": "DIFERENCA", "proposta": "P1"},
   "mock/pedidos.ts#L3-9": {"destino": "DIFERENCA", "proposta": "P1"},
   "src/pages/vendas/Pedidos.tsx#L90-90": {"destino": "SEM_IMPACTO", "motivo": "só reindentação"}
 },
 "propostas": [
   {"ref": "P1", "tela": "TL-vendas-pedidos", "regiao": "tabela de pedidos",
    "antes": "sem coluna de canal", "agora": "coluna «Canal de venda» com valores do mock",
    "fonte_prototipo": "src/pages/vendas/Pedidos.tsx:44", "fonte_produto": "apps/web/src/pages/Pedidos.tsx:120",
    "trechos": ["src/pages/vendas/Pedidos.tsx#L40-52", "mock/pedidos.ts#L3-9"]}
 ]}
```

- `destino`: `DIFERENCA` (com `proposta` que lista o trecho), `SEM_IMPACTO` (com `motivo` conferível) ou `NAO_INVESTIGADO` (com `motivo` e, se souber, `regiao`: o integrador cria a região do catálogo e grava o `local` no rastreio; o agente não escreve `local`).
- `status`: `OK` só com a unidade inteira lida; `PARCIAL` enquanto o agente ainda grava; `FALHA` quando ele não conseguiu ler a unidade. A conferência reprova `PARCIAL`.
- Sem IDs `DF-…`: quem numera é o integrador.
- `agora` é texto livre: a conferência só exige que o campo exista, e o conteúdo é pedido pelo brief abaixo.

## Brief do agente de unidade

Preencha os caminhos e despache como está. Ele não recebe o mapa inteiro nem os achados de outras unidades.

```text
Você lê uma unidade de uma versão nova do protótipo e registra o que mudou e o que o produto precisa mudar. Não escreve no catálogo nem em nenhum repositório.

- Protótipo (só leitura de arquivos e git; nada de npm, build, servidor ou navegador): <prototipo>, versão vigente <vigente> (na primeira sincronização é a árvore vazia: `git show` do arquivo nela falha, leia só a candidata), candidata <candidata>.
- Produto (só leitura): <produto-wt>. Catálogo atual (só leitura): <catalogo>.
- Sua unidade: <tmp>/unidades/<U-xx>.json (`unidade`: telas, regiões, trechos e contexto; `telas` e `status_trechos`: o que vem do mapa). Não abra <tmp>/unidades.json nem <tmp>/mapa.json: são grandes e tratam de outras unidades. Avisos «Arquivo volumoso …» do mapa que cabem à sua unidade (arquivo com trecho em posse ou no contexto), repasse aqui: dê destino a esse arquivo pelo cabeçalho e pelas chaves, sem ler inteiro. (Apague esta frase se não houver.)
- Sua região: <regiao> (linha só em unidade dividida por região; apague-a nas demais). Leia a tela inteira, mas destine só os trechos que caem nessa região; os de outras regiões são de outro agente. Um trecho que cruza regiões pode ser destinado por você também.

**Limite de 60 turnos. Grave cedo:** crie o arquivo de achados até o turno 15, com `"status": "PARCIAL"`, e acrescente a cada tela lida só o que for novo: o comando carrega o arquivo, junta os novos em `trechos` e `propostas` e grava (`d=json.load(open(p)); d["trechos"].update(novos); d["propostas"]+=novas; json.dump(d,open(p,"w"),ensure_ascii=False)`). Não redigite o que já gravou: isso enche o seu contexto. Só no fim passe para `"OK"`. Destine em lote, por script, trechos repetitivos de um mesmo arquivo (chaves do locale, mock, config). Se receber um arquivo parcial, complete só os trechos sem destino.

Para cada tela da unidade, leia a tela inteira e as dependências nos dois lados, nas duas versões (`git -C <prototipo> show <versao>:<arquivo>`). O diff localiza; o requisito vem do que a tela faz na candidata. O requisito não depende de texto literal trocado: se um rótulo mudou e uma mensagem, placeholder ou dica ao lado continua literal com o texto antigo, `produto_precisa` replica os dois como estão e cita a linha do literal. Não derive mensagem nem comportamento que a candidata não mostra. Tela sem trecho próprio muda pelo arquivo em `afetada_por` ou pelo acoplamento: descreva o efeito nela.

Em `agora`, escreva o que a tela mostra e faz na candidata, em frases separadas para o que é comportamento e o que é aparência (o integrador cria um cenário para cada): os textos literais visíveis (fixos no código, de locale com o texto resolvido da chave e, quando você os conhecer, os que a biblioteca renderiza), copiados como estão, sem paráfrase nem tradução; o endpoint e a forma dos dados; o que o mock faz ou ignora; em controle interativo, onde ele fica, como abre e fecha, quando habilita e qual valor confirma (o que vier da biblioteca e não aparecer no código, diga que não é conhecido); e o que define a aparência (componente, props, tema). Cite a linha de cada item. Leia inteiros os arquivos de estilo das telas (cores, tokens, classes): a busca por palavra não basta, porque a aparência precisa ficar igual.

Grave em <tmp>/achados/<U-xx>.json (em unidade dividida por região, <tmp>/achados/<U-xx>-<regiao>.json, com `"regiao": "<regiao>"` na raiz) com `python3 -c` e `json.dump` (um heredoc de shell quebra com aspas, «» e apóstrofos), no formato de <ondas>/references/formatos.md («Achados de uma unidade»): todo trecho da unidade (da sua região, se houver) com destino; cada diferença com tela, região, antes, agora, fonte nos dois lados (arquivo:linha) e trechos. Sem narrativa.

Devolva só 2-3 linhas: quantos trechos, quantas propostas, o que ficou NAO_INVESTIGADO.
```

## Briefs da passada de fatos

Ficam em [references/briefs/](briefs/), um arquivo por etapa, e o `prompt` de cada despacho aponta o caminho. A etapa que usa cada um está em [passada-de-fatos.md](passada-de-fatos.md).

## Itens omitidos

`<tmp>/itens-omitidos.json`, gravado por `processo.py omitidos`: `{"<id da tela>": [{"tipo": "...", "texto": "...", "fonte": "arquivo:linha", "origem": "cega"}]}`. Só os itens que o catálogo não tinha. Tela sem omissão fica com lista vazia.
