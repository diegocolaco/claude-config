# Etapa: conferência final

Use a skill `prototype-parity-verification` e siga a seção 10 de `../../prototype-parity-verification/references/decisoes-e-planos.md`. Trabalhe num worktree próprio do produto, a partir do `develop`.

Rode nesta ordem, e traga a saída de cada um:
1. `../../prototype-parity-verification/scripts/verificacao.py` `stubs --raiz <produto> --desde <commit do develop antes do primeiro plano>`. Tela com dados vazios é oca, não aprovada.
2. `../../prototype-parity-verification/scripts/verificacao.py` `sem-teste --catalogo <catalogo> --todos`. A saída 11 só é esperada pelos cenários visuais: cenário funcional sem teste é divergência.
3. `node ecosystem/automation/proto_env/parity.mjs linkage <catalogo>`. Na descoberta, `MISSING_TASK_OWNER` é tolerado; aqui não. Toda diferença sem `disposition` e todo requisito precisam de dono.
4. Os testes E2E da aplicação nova, nunca no protótipo. Se não der para rodá-los, diga por quê.
5. A aparência pelo código, tela a tela: componente, props e tema do código novo contra o que o `inventario`, o `definition.agora` do catálogo e os fatos em `.squad/contracts/parity/fatos/<TL-id>.json` apontam. Nada sobe só para comparar. Com o pacote `@onviobr/dom-components` no `package.json` do alvo, compare com o alvo da tabela da seção 4 do guia, não com o componente do protótipo, e confira a tela pelo `dom-ds-gate`. O que só der para ver na tela fica `NAO_VERIFICADO`.

Regras:
- Procure sucesso vazio: teste verde numa tela sem dados, filtro que não filtra nada, comando que sai 0 sem ter lido nada.
- `SEM_COMPARACAO` e `NAO_VERIFICADO` ficam visíveis no relatório e nunca viram aprovado.
- Não marque baseline e não corrija código neste chat.
- Liste as divergências para o Diego decidir o que vira plano novo. Registre cada uma escolhida como diferença nova no catálogo, com requisito e cenário, em commit próprio, como manda a seção 10, e em «Divergências abertas».

Na medição, acrescente os cenários com veredito e as divergências encontradas, com o grupo em que cada uma nasceu.
