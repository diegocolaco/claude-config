# Passada de fatos

Esta é a leitura cega da descoberta. Agentes novos leem as telas sem ver o catálogo nem os achados das unidades, e só depois um passo separado diz o que o catálogo ainda não traz. Ela substitui a leitura em Sonnet e o ataque às unidades, decisão do Diego em 03/11/2026.

## Por que é assim

Foi medido em 03/11/2026, e o registro completo está em `user-doc/ecossistema-jarbas/temas/ciclo-versao-prototipo/2026-11-03-processo-paridade-testes.md`.

- **Modelo maior não acha o que falta.** Numa tela de 11 fatos, com o mesmo brief: Haiku medium 7 inteiros (US$ 0,06), Sonnet high 8 (0,31), Opus high 8 (1,03). Todos perderam «a falha da consulta não é tratada», porque quem lê o que existe não enxerga o que não existe. A passada de ausências fechou esses casos em Haiku.
- **Cada tipo de fato tem um caminho.** O que está escrito sai bloco a bloco; o que falta sai perguntando; o que nasce na biblioteca se lê no pacote da versão travada; o que é mecânico sai de script, sem variar entre rodadas.
- **Mais raciocínio não pagou.** Haiku low perdeu fatos e afirmou um erro; Haiku high custou 64% a mais, sem ganho.

Resultado nos testes: 92% a 94% dos fatos por inteiro, e 98% a 99% contando os achados em parte. Esses números são contaminados: parte dos briefs e dos scripts foi ajustada depois de ver fatos destes testes, e o gabarito é limitado e já mostrou erro. Não existe como provar 100%. O que fica sem resposta aparece como NÃO VERIFICADO, em vez de virar afirmação.

## Antes de começar

`<fatos>` é `python3 <ondas>/scripts/fatos/processo.py`, com `<ondas>` sendo o diretório desta skill. Só a etapa 6 escreve no produto.

Telas: as novas, as 20% de maior `peso` (no mínimo 2) e a amostra em ordem fixa da skill da versão, ou toda tela numa sincronização do zero. **Não corte telas por custo sem perguntar ao Diego:** o `resumo` reprova tela nova sem releitura.

Copie o catálogo para `<tmp>/catalogo-antes.json`. Todo despacho vem pronto: cada entrada dos arquivos `despachos*.json` traz `modelo`, `esforco` e `prompt`. Até 6 agentes `task-researcher` ao mesmo tempo; o resto na onda seguinte. O agente grava em arquivo e devolve 1 linha, e o que vale é o arquivo.

## Etapas

Cada comando abaixo sai 0 se pode seguir. Saída 2 é erro de uso ou de identidade (commit, repositório ou tela que não existe, mapa de outra versão, `--moldura` fora do commit): corrija o comando, porque nada foi gerado.

**1. Preparar, sem modelo.**

```bash
<fatos> iniciar <tmp>/fatos --repo <prototipo> --commit <candidata> --mapa <tmp>/mapa.json [--moldura <arquivo>]... [--superficie-moldura SF-LAYOUT]
<fatos> prepara <tmp>/fatos <TL-id>...
<fatos> projeto <tmp>/fatos
<fatos> biblioteca-baixa <tmp>/fatos
```

`prepara` corta o código de cada tela em blocos numerados, o livro, e já gera os fatos que não dependem de leitura. `projeto` faz o mesmo uma vez só para a moldura e os arquivos globais, porque aparecem em toda tela, e gera as perguntas de biblioteca, uma passada por pacote. `biblioteca-baixa` baixa cada pacote da versão do `package-lock.json`, sem instalar nem executar nada; sem pergunta de biblioteca, diz `nada a baixar`. Repetir `prepara` ou `projeto` não apaga as dúvidas resolvidas nem os padrões já integrados. `--moldura` só é preciso em protótipo que não seja Umi, com os mesmos arquivos do `cobertura.py inventario`. Fora do Umi, os fatos de sessão e de build voltam como NÃO VERIFICADO: leia esses arquivos à mão e diga no resumo.

**2. Inventário, ausências, moldura e biblioteca: `haiku`, `medium`.** Despache `despachos.json` e `despachos-projeto.json`. Depois:

```bash
<fatos> confere <tmp>/fatos <TL-id>... TL-moldura TL-global
<fatos> biblioteca-confere <tmp>/fatos <tmp>/fatos/biblioteca/respostas-*.json
<fatos> junta <tmp>/fatos <TL-id>... TL-moldura TL-global
```

- `confere` sai 1 com a linha `REFAZER`: bloco sem resposta é trecho que ninguém leu. Despache um agente novo para aquela parte, uma vez. Na segunda falha, a tela entra `NAO_INVESTIGADO`, como em [Integrar](../SKILL.md#integrar-fim-de-cada-onda).
- `biblioteca-confere` só aceita resposta com citação que exista naquela linha da versão travada. Recusada ou `NAO_ACHEI` não vira fato e segue NÃO VERIFICADO. Não complete de memória. Sai 1 se há perguntas e nenhuma resposta.
- `junta` sai 1 se a saída de um agente faltar ou estiver quebrada: refaça aquela. Ela também roda o conferidor, que marca `VALOR_AUSENTE` quando um valor citado não aparece no código.

**3. Dúvidas: `haiku`, `medium`.**

```bash
<fatos> duvidas <tmp>/fatos <TL-id>... TL-moldura
```

Despache `despachos-duvidas.json`, em lotes de 8, porque 21 dúvidas num agente só estouraram o limite de turnos sem gravar nada. Depois, `<fatos> duvidas-grava <tmp>/fatos <lote.json> <resp.json> ...`, com cada par, e `junta` de novo, para as resolvidas virarem fatos. Só vira fato o que tem citação batendo; o resto segue NÃO VERIFICADO e vai ao resumo.

**4. Revisão: `sonnet`, `medium`.** O Diego não aceita Haiku sem a revisão de um modelo melhor, e esta etapa é essa revisão.

```bash
<fatos> amostra <tmp>/fatos <TL-id>... TL-moldura TL-global
<fatos> biblioteca-amostra <tmp>/fatos
```

A amostra leva todo item com alarme do conferidor, toda dúvida resolvida e 6 itens sorteados por tela, em semente fixa. Despache `despachos-revisao.json` e `despachos-biblioteca-revisao.json`, e rode `<fatos> revisao-aplica <tmp>/fatos`:

- **Saída 1:** sem lote, ou sem a saída de um lote, do reenvio ou da biblioteca: despache o que a mensagem nomeia, porque nada foi aplicado. `amostra` nova apaga as saídas e o reenvio da anterior; o que já foi decidido fica.
- FALSO sai dos fatos e vai para `revisao/removidos.json`; IMPRECISO fica, com o motivo, que vai até o arquivo ao lado. Motivo sem `arquivo:linha` não vale: o comando sai 1 e gera `despachos-reenvio.json`; despache uma vez e rode `revisao-aplica` de novo. O que seguir sem citação fica como fato não revisado, sai 0 e vai ao resumo.
- **Saída 11:** mais de 2% de falsos entre os sorteados. A amostra não basta: rode `amostra --tudo`, despache e aplique de novo. Motivo: com 2% de falsos, a amostra de 27 telas tem 96% de chance de mostrar ao menos um. Nos testes a taxa foi de 1 falso em 269.
- Diga no resumo a taxa e os removidos.

**5. Diferença e destino: `haiku`, `medium`.**

```bash
<fatos> dif <tmp>/fatos <catalogo> <TL-id>... TL-moldura TL-global
```

Despache `despachos-dif.json`. Na dúvida, o item é NOVO. Depois, `<fatos> dest <tmp>/fatos <catalogo> <TL-id>... TL-moldura TL-global` e `despachos-dest.json`. `dest` sai 1 se algum item ficou sem decisão: refaça a diferença daquela tela.

**6. Gravar, só você.**

```bash
<fatos> grava <tmp>/fatos <catalogo> <catalogo> --ao-lado <produto-wt>/.squad/contracts/parity/fatos <TL-id>... TL-moldura TL-global
node ecosystem/automation/proto_env/parity.mjs catalog <manifest.json> <catalogo>
node ecosystem/automation/proto_env/parity.mjs linkage <catalogo>
```

Os fatos ficam ao lado do catálogo, em `.squad/contracts/parity/fatos/<TL-id>.json`, por cenário, com fonte e sem resumo: quem escreve o plano e quem implementa leem esse arquivo. O catálogo só ganha as regiões novas. Rodar de novo não muda um byte, e fato sem fonte é recusado. Fato de `mock/` ou `cloudflare-worker/`, padrão de biblioteca ou marcado NÃO USADO não cria região: no piloto, cerca de 80% dos novos eram desse tipo e virariam cenário de algo que a tela não alcança. Ele fica na chave `sem_cenario` do mesmo arquivo; a contagem sai na linha `sem cenário N` e vai ao resumo. Se o agente de destino o pôs num cenário existente, fica naquele cenário. Esse corte só vale com `--ao-lado`: sem essa opção, tudo entra no catálogo. A mesma gravação guarda duas coisas para quem planeja: na chave `biblioteca` de cada tela, o padrão dos componentes que ela usa; e em `fatos/ausencias/<TL-id>.json`, a passada de ausências, que a matriz de variações lê quando `<tmp>` já não existe.

**Toda linha `CENARIO_LIGADO <cenário> -> <requisito>` é uma ligação automática,** feita ao primeiro requisito aberto da superfície, sem olhar o assunto. O validador aceita, mas o requisito pode não ter relação com o cenário: no piloto, um requisito recebeu 12 regiões sem relação. Leve a lista ao resumo e a quem escreve o plano do grupo. **Saída 11, `CENARIO_SEM_DONO`:** a superfície não tem requisito aberto; crie diferença e requisito à mão, como manda a skill da versão, porque um cenário sem requisito nunca entra num plano. Em `linkage`, nenhum código novo pode aparecer além de `MISSING_TEST` do cenário novo.

**7. Fechar a medição.**

```bash
<fatos> relidas <tmp>/fatos <tmp>/cega/1.json <TL-id>... TL-moldura TL-global
<fatos> omitidos <tmp>/fatos <tmp>/itens-omitidos.json <TL-id>... TL-moldura TL-global
```

Passe os dois ao `cobertura.py resumo`, em `--cega` e `--itens-omitidos`. O `omissoes` segue contando diferenças; aqui, as omissões vêm por item. `relidas` sai 1 se a tela não tem fato de leitura, porque ela contaria como relida sem ninguém ter lido.

## O que falta

Falta uma etapa que confronte o que a tela afirma com o que a moldura afirma: uma tela pode dizer «pública» enquanto a moldura exige sessão. O script de sessão por rota dá a regra certa, mas nada aponta a contradição. Ao ler a revisão, confira as afirmações de acesso de cada tela. O script de sessão, o de build e a poda de arquivos só leem o Umi.
