# Decisões e planos sobre o catálogo

Para quem vai escrever o documento de decisões ou um plano a partir do catálogo de paridade, ou executar um plano que traga o bloco `**Catálogo:**`. O catálogo (`.squad/contracts/parity/catalog.json`) já existe e foi adotado: a descoberta e a adoção são da skill `atualizacao-versao-prototipo`. Aqui começa o que vem depois. O catálogo diz **o quê** a aplicação nova tem de ter; o que este arquivo cobre é **como** decidir, planejar e executar.

## 1. Fluxo em chats

1. **Chat de decisões e primeiro teste.** Escreve o documento de decisões (seção 2), recebe as respostas do Diego (seção 3) e executa um primeiro plano: a base comum e uma tela difícil. A base comum é o que toda tela usa (layout, tema, cabeçalho, componentes compartilhados).
2. **Um chat por grupo de telas, em sequência.** Cada um escreve o seu plano, o Diego o revisa, e o chat o executa. Nenhum chat de grupo começa antes de o Diego aprovar o resultado do primeiro teste. Se o resultado pedir replanejar, a correção segue a seção 10: vira diferença nova, com dono novo.
3. **Último chat, de conferência** (seção 10).

Em sequência e não em paralelo porque os planos disputam os mesmos arquivos compartilhados: o arquivo de rotas e o próprio catálogo. Chats simultâneos reescreveriam a mesma linha e produziriam conflito de merge.

## 2. Documento de decisões

Segue o formato do `superpowers:brainstorming`: `docs/superpowers/specs/YYYY-MM-DD-<topico>-design.md`, com o builder check e a aprovação do Diego **antes de qualquer código**. Precedência: o catálogo diz o quê, o documento diz como; o plano argumenta a partir do documento, e o campo `Spec` do plano aponta para ele. O documento traz também a **divisão das telas em grupos**, um grupo por chat da seção 1. Mantenha no mesmo grupo as diferenças que compartilham requisito ou cenário: `verificacao.py ligar` bloqueia com `DUPLA_POSSE` o plano que tente ligar um requisito ou cenário que já pertence a outro plano.

## 3. Perguntas que só o Diego responde

O agente não decide estas. Leve em blocos, cada pergunta com o número medido, e registre a resposta no documento: primeiro os riscos, até 6 por mensagem e por tema, esperando a resposta pelo nome antes do próximo bloco; depois as demais perguntas, juntas. Motivo: dezenas de perguntas numa mensagem levam a uma resposta geral. Os números abaixo têm duas origens. **Do protótipo,** medidos em `c7a6bfd`: os caminhos `/api`, os trechos em chinês, as chaves de locale, as telas e os pontos de quebra. **Do produto,** medidos em `f005d19`: a ausência de `/api`, o login que exige e-mail válido, o `scripts/journeys.mjs` e os atributos `implementation-tag` e `data-record-id`. **Meça de novo** nas versões em uso (o `cobertura.py inventario` e `git grep` no commit do mapa, para o protótipo; `git grep` no commit do produto) e cite os números novos.

- **Dados.** O protótipo chama cerca de 27 caminhos `/api/...` (`git grep` por `/api/` literal em `src` no commit `c7a6bfde24479dd6c1efa08667c1b8f66fe15d63`, contando os caminhos distintos entre aspas; o número exato depende de como se contam variantes com parâmetro, como `/api/geographic/city/` e `/api/geographic/city/33`, e inclui os dos arquivos `_mock.ts` e de teste); o produto não tem nenhum (`/api/` não aparece em `apps` nem em `packages`). As opções são mock no navegador, mock no backend ou tabelas reais. «Dados iguais» significa a mesma forma ou os mesmos valores? Parte dos mocks usa valores aleatórios e a hora atual, então valores idênticos não existem.
- **Comportamento de mock é regra?** Em alguns lugares o mock faz menos do que a tela promete: os filtros refazem a consulta e o mock ignora os parâmetros; «carregar mais» troca a lista em vez de acumular; botões de período só mudam o destaque. Copia-se o que o protótipo faz hoje ou o que ele parece querer fazer?
- **Login real × mock, e a exceção que tira o login do produto da paridade (DF-30 no catálogo antigo).** O protótipo entra com um usuário e senha fixos, tem abas de conta e celular, captcha e cadastro; o produto exige e-mail válido e, no perfil Keycloak, o formulário é só um link. Só o visual muda, com a autenticação real por trás? O que fazem celular, captcha e cadastro, que não têm backend?
- **Telas atuais, `/` e `journeys`.** O protótipo leva `/` para a análise e o produto mostra Cadastros. `scripts/journeys.mjs` espera `/cadastros` depois do login, e os testes atuais dependem de `implementation-tag` no cabeçalho e de `data-record-id`. As telas atuais (Cadastros, Comercial, Gestão) entram no menu lateral? Para onde vai `/`? O cabeçalho igual ao do protótipo mantém a marca de teste?
- **Marca e conteúdo do template.** O cabeçalho e o rodapé dizem «Ant Design Pro», e há etiquetas «Ant Design» e «蚂蚁集团». Valem no produto, que tem outro nome?
- **Peças de ferramenta.** Engrenagem de tema com modo escuro, link de documentação OpenAPI (só em desenvolvimento), seletor de versão, link de documentação, aviso de offline, service worker. Quais fazem parte do SGD?
- **Idiomas e seletor.** O protótipo tem cerca de 652 trechos fixos em chinês em 20 telas, sem tradução; 230 chaves de locale pt-BR (menu, login, listagem, erros); e textos que a biblioteca renderiza sozinha. O menu sai em português e em inglês, e o conteúdo em chinês. Confirma que a mistura fica assim? O seletor de 8 idiomas só muda parte da tela e o produto não tem biblioteca de tradução: mantém? O que fazer com os textos em chinês ou em inglês do protótipo, e as frases da biblioteca entram como texto fixo em português?
- **Recursos externos.** Avatares e capas, fonte do template, atlas do mapa e API do chat vêm de hospedagens de terceiros. O SGD busca de lá, copia para dentro ou troca? A licença de cada recurso não foi verificada, e o produto usa outra fonte.
- **Telas cortadas.** Das 27 telas de página do protótipo, o catálogo antigo cobria 20, por decisão registrada. As demais entram agora, depois ou nunca? Tela fora do escopo só com decisão nomeada do Diego.
- **Responsivo.** O protótipo tem pontos de quebra em quase toda tela (480, 576, 768, 992, 1200 e 1600 no tema da biblioteca). O celular faz parte de «igual»?

**Resposta geral não decide risco.** Uma regra única do Diego, como «escolha o que mantém a paridade», decide aparência e comportamento. Não decide o que expõe dados ou acesso: texto do usuário enviado a terceiro, senha pública ou entrada sem senha. Cada item desses vira pergunta própria, pelo nome e com a consequência. Até ele responder nomeando o item, a tela fica igual e o efeito fica atrás de uma trava desligada por padrão, ligada só por configuração explícita. Motivo: a paridade é da tela; o dado que sai do SGD não volta.

## 4. Regra da biblioteca

Ant Design agora; Dom DS quando o pacote `@onviobr/dom-components` estiver no `package.json` do alvo (antes disso é privado e fora do alcance, e as rules e skills do Dom DS não se aplicam). A regra geral do Diego é «O máximo possivel igual dentro do possível»: mesmos componentes, mesmas regras, mesmas cores e mesmos textos.

**Com o pacote no `package.json` do alvo:** leia `ecosystem/canonical/rule/sgd-novo-dom-ds-mapeamento-proto/content.md` pelo caminho, porque essa regra não fica carregada. Para cada componente do protótipo, use o alvo da tabela, preferindo o wrapper de `apps/web/src/components/ui/`. Use a skill `dom-ds-gate`, lendo o componente real no pacote instalado antes do primeiro uso. Pare e leve as opções ao Diego quando a tabela não trouxer um componente do Dom DS, inclusive em linha que aponta elemento nativo ou diz «Não levantado», quando a interação for diferente da do protótipo ou quando a tabela não bater com o que o alvo tem. Só vale sem perguntar o que a tabela registra como exceção aprovada.

Componente que a biblioteca não tem: o agente pode **sugerir**, e quem decide é o Diego: «Eu que tenho que definir se deve ser criado um ou usar componentes nativos mesmo». O agente não cria componente nem adota biblioteca por conta.

**Componentes difíceis.** Vão numa lista única, levada ao Diego para decidir de uma vez. Meça-a a partir do `inventario`: os totais por pacote em `global` e os `componentes` por tela, e some, por componente, as telas em que o nome aparece (`global.<pacote>` traz os nomes distintos e as telas que usam o pacote, mas não a contagem por componente; `componentes` de cada tela traz os nomes). Confira cada item pelo uso real (um `Upload` sem ação, sem lista e sem arrastar é um botão que abre arquivo, não um upload completo). Parta desta lista, que cobre o que deu trabalho antes:

- **Gráficos:** área, colunas, linha, rosca, radar, medidor, líquido, nuvem de palavras, anel pequeno.
- **Tabela editável.**
- **Seletor de datas:** data, faixa, data e hora, hora (calendário, locale).
- **Upload.**
- **Chat:** bolhas, conversas, campo de envio, streaming, API externa.
- **Ícones:** os importados e os que a configuração de rotas nomeia; a segunda lista não aparece nos imports.
- **Layout comum:** cabeçalho de página, trilha de navegação, menu aninhado e recolhível, permissão. Toda tela depende dele e nenhum import o revela.
- **Tabela com busca gerada** (barra, seleção, paginação).
- **Formulários** (validação, dependência entre campos, rolagem até o erro) e **formulário em etapas** dentro de modal.
- **Select** com múltipla escolha e etiquetas removíveis.
- **Flutuantes:** dropdown, tooltip, popover (uma decisão só: à mão ou biblioteca).
- **Mapa** (dependências próprias e dados de rede).
- **Markdown** com realce de código, fora do chat também.
- **Tema:** gaveta de configuração, modo escuro e o conjunto de tokens.

## 5. Decisão que muda escopo

Toda decisão do Diego que tire ou altere algo do catálogo vira `disposition` na diferença, com `kind` (`duplicate`, que exige também `duplicate_of`; `out-of-scope`; `approved-exception`; ou `blocked`), `reason`, `decision_ref` (registro verificável: mensagem com data e IDs, ou commit do documento de decisões) e `approved_by`. Sem isso o catálogo continua exigindo a coisa e a conferência final a cobra.

**Quem grava e quando.** O controlador do chat de decisões, na diferença do catálogo novo, em commit próprio, **antes do primeiro plano**; nenhuma tarefa de plano faz isso. Ao gravar, ele retira o requisito que ficou sem nenhuma diferença aberta, com as referências a ele (o ID em `requirement_ids` da diferença). Requisito compartilhado com outra diferença aberta fica, ligado por ela. Motivo: `parity.mjs linkage` e `verificacao.py ligar` exigem tarefa em todo requisito, e exceção aprovada não recebe tarefa; o requisito esquecido ficaria cobrado para sempre (`REQ_SEM_TAREFA`). O cenário do requisito retirado continua no catálogo, e `linkage` o acusa com `MISSING_TEST`, que é tolerado. Depois de gravar, rode `parity.mjs catalog` e `parity.mjs linkage` e confira que nenhum código novo apareceu.

**Diferença aberta sem requisito.** A diferença do inventário inverso que o Diego manda substituir fica sem `disposition` e sem `requirement_ids`. O controlador cria requisito e cenário para ela, com o que o documento decidiu, no mesmo commit e antes do primeiro plano. Motivo: sem eles, nenhum plano consegue ligá-la, e nada prova a entrega. Depois de gravar, `MISSING_REQUIREMENT` tem de dar 0 no `linkage`; `MISSING_TASK_OWNER` e `MISSING_TEST` continuam tolerados até os planos.

## 6. Restrição global para copiar no plano

Todo plano traz, nas restrições globais, esta frase:

> Biblioteca nova ou componente fora da lista: parar e perguntar.

Ela vence a execução contínua do `subagent-driven-development`, conforme a precedência de `AGENTS.md`: o subagent devolve `BLOCKED` em vez de decidir, e o controlador pergunta ao Diego, sem ruling. Componente difícil encontrado durante a tarefa também para: se não estava na lista decidida, é pergunta, não improviso.

## 7. Bloco `**Catálogo:**`

Toda tarefa do plano (`Task N: …`) traz uma linha:

    **Catálogo:** DF-13, REQ-13, SC-013

ou, quando não entrega nada do catálogo:

    **Catálogo:** nenhum

Regras (as confere `verificacao.py ligar`, e o plano que as viola é bloqueado):

- O fechamento só desce (DF → REQ → SC): listar a DF já cobre o REQ e o SC dela.
- DF com `disposition` não entra no bloco: exceção aprovada não recebe tarefa.
- REQ que restar sem dono (nenhuma DF dele entra no plano): liste o REQ direto. Sai só o aviso `REQ_SEM_DF`.
- Tarefa com cenário funcional precisa de `` - Test: `caminho/do/teste` ``. O caminho tem `/` ou extensão; «verificar manualmente» não é caminho, não vale e bloqueia.
- O cenário `visual` não recebe teste: fica como pendência de conferência por código (seção 10).
- Plano de correção (divergência da conferência, ou replanejamento depois do primeiro teste): liste a **diferença nova** da seção 10, nunca a diferença que já pertence a outro plano; essa daria `DUPLA_POSSE`. `**Catálogo:** nenhum` continua só para tarefa que não entrega nada do catálogo.

**Fatos, raio de alcance e variações.** Três entradas do plano que o `ligar` não confere, mas a revisão final cobra:

- **Fatos da tela.** O que o cenário exige em detalhe está em `.squad/contracts/parity/fatos/<TL-id>.json`, por cenário, quando esse arquivo existe. Copie para a tarefa os fatos dos cenários dela, porque o implementador não lê o catálogo. A chave `biblioteca` traz o padrão dos componentes que a tela usa, como o valor de uma prop que o código não define: copie os dos componentes da tarefa. A chave `sem_cenario` traz o que ficou sem cenário, como mock e código que nada alcança: leia, e leve à tarefa só o que mudar o que se constrói. Fato com `imprecisao` foi corrigido na revisão: vale o motivo, não o texto.
- **Ligações automáticas.** O resumo da descoberta lista as linhas `CENARIO_LIGADO`: o cenário foi ligado ao primeiro requisito aberto da superfície, sem olhar o assunto. Ao planejar, confira as dos cenários do grupo e mude a ligação que não fizer sentido, antes do `ligar`.
- **Raio de alcance.** Antes de planejar, para cada arquivo compartilhado que o plano vai mudar, rode `python3 <skill>/scripts/raio_alcance.py <produto> <commit> <arquivo>... --src <pasta do código> [--alias @=<pasta>] [--rotas <arquivo de rotas>]`. Cole a saída no plano, e toda tela listada entra nos testes da tarefa. `telas` só sai preenchido com rotas no formato do Umi; com o aviso `rotas_ausentes`, liste as telas a partir de `todos_afetados`. Motivo: um ajuste num componente comum já quebrou outras telas sem ninguém ver. A saída é piso, não teto: ela não enxerga import dinâmico por variável nem CSS global, então diga isso no plano quando houver.
- **Matriz de variações.** Com a saída da passada de ausências, guardada ao lado do catálogo em `.squad/contracts/parity/fatos/ausencias/<TL-id>.json`, rode `python3 <skill>/scripts/matriz_variacoes.py <arquivo>...` e leve ao plano as linhas de cada alvo: carregamento, falha, vazio, sucesso, entrada e navegação. Cada linha pede teste. **Linha com `NAO` pede teste da ausência:** nunca invente mensagem ou estado que o protótipo não tem. Sem esses arquivos, diga no plano que não há e por quê.

## 8. Ordem em chat que executa plano

Vale para o controlador, **fora das tarefas**, e também no chat de decisões e primeiro teste. Depois da última tarefa completa:

1. `python3 <skill>/scripts/verificacao.py ligar --catalogo <catalogo> --planos <plano.md> --ledger <plano.md>=<workspace>/progress.md --raiz <produto> --gravar`, em que `<workspace>` é a pasta que o `sdd-workspace` imprime para este plano e o ledger é o `<workspace>/progress.md`. Sem `--gravar` é dry-run (`--formato md` para ler). O `ligar` vem antes de tudo porque a revisão final apaga o ledger, e o ledger é o que diz quais tarefas foram entregues.
2. `verificacao.py sem-teste --catalogo <catalogo>`.
3. Commit.
4. Revisão final.
5. Apagar o workspace.
6. `superpowers:finishing-a-development-branch`.

Saída 11 só com pendências (`DF_SEM_TAREFA`, `REQ_SEM_TAREFA`: o que outro plano ainda vai ligar) é esperada até o último chat; o comando grava. Com bloqueantes, não grava, e se resolve antes de seguir. Confira os nomes das flags com `verificacao.py ligar --help` se a versão do script for outra. Rodar o `ligar` de novo no **mesmo** plano não dá `DUPLA_POSSE`.

`sem-teste` sai 11 quando há cenário `visual` entregue, mesmo com tudo ligado. Isso é esperado: não se cria teste falso para zerar. Confira com `parity.mjs linkage` (o `MISSING_TEST` do cenário visual é tolerado) e pelo código (seção 10).

**Nenhuma tarefa de plano edita o catálogo.** Quem o altera é o controlador, um chat por vez, e só assim: `tasks[]` e `tests[]` saem apenas do `ligar`; `disposition` (seção 5), diferença nova com requisito e cenário (seção 10) e correção de `definition.agora` confirmada no código do protótipo o controlador grava à mão, em commit próprio e antes do plano que depende deles.

## 9. Abertura de chat

Abra o chat no playground (o repositório das skills e da automação, onde o chat abre). Crie o worktree do produto com `git -C <produto> worktree add <layout.worktrees_root>/<nome> -b <branch> develop`, a partir do `develop` integrado (caminhos e raiz de worktrees vêm de `ecosystem/ecosystem-config.yaml`). Faça `cd` para o worktree **antes** de rodar o `sdd-workspace` do `subagent-driven-development`: o workspace fica na árvore de trabalho em que o comando roda, e rodado do playground ele cairia fora do worktree do produto.

## 10. Aparência em cada chat

O protótipo nunca sobe. Nada sobe só para comparar aparência, e não há print (a etapa de subir as aplicações e tirar prints não é necessária): a aparência se confere **pelo código**: compare componente, props e tema do código novo com o que o `inventario` e o `definition.agora` do catálogo apontam para a tela. O que não dá para concluir assim fica `NAO_VERIFICADO`, dito no relato.

O chat final, de conferência, usa o vocabulário que já existe (`SEM_COMPARACAO`, `NAO_VERIFICADO`) e **não marca baseline**. O que divergir abre um chat de plano novo, na mesma sequência da seção 1. A divergência, ou a correção que caiba a um plano novo (inclusive o replanejamento depois do primeiro teste), vira **diferença nova** no catálogo, com requisito e cenário. O controlador a registra em commit próprio, antes do plano, e o plano novo fica dono dela. Motivo: mantém um dono por item, e o teste da correção entra em `tests[]`; o plano novo que listasse a diferença antiga tomaria `DUPLA_POSSE`.

Os testes E2E da aplicação nova seguem normais, como a skill manda; o que não existe é subir qualquer aplicação para comparar aparência. Na reconstrução do SGD a partir do protótipo, a skill [qa-visual-agent](../../qa-visual-agent/SKILL.md) (QA visual pixel a pixel contra baseline de imagem) não é o caminho: só se aplica se o Diego pedir QA visual. A fronteira da skill continua: a automação de navegador roda só na aplicação nova, nunca no protótipo.
