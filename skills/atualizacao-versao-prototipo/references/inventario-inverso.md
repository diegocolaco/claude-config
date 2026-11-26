# Inventário inverso (produto → protótipo novo)

Procura o que o produto tem e o protótipo novo não tem. Sem isso, botões e regras de versões velhas ficam no produto para sempre.

## Escopo

- INCREMENTAL: todas as rotas dos módulos tocados pelo diff e as áreas sem sobras registradas.
- FULL: todas as rotas do produto.
- Leia rotas pelo roteador e pela navegação dos dois lados, pelo que cada rota renderiza. Componente do protótipo que nenhuma rota importa é órfão e não é régua. Se o `delta` rodou, inclua `target_only` e `target_obsolete`.
- ITENS em andamento: confira no código do worktree do ITEM. O que ele já remove vira diferença ligada à tarefa dele (`task_ids`), não sobra nova.

## Classes (campo `classe` da diferença)

| Classe | Prova exigida | Registro |
|---|---|---|
| `SOBRA-PROTO-ANTIGO` | o mesmo controle (rota ou região + elemento) numa `reference.version` registrada antes, e ausência na nova | diferença aberta |
| `SGD-PROPRIO` | motivo (integração, canal, regra própria) | aberta até aprovação; depois `approved-exception` |
| `ADAPTACAO-APROVADA` | decisão anterior verificável | idem |
| `INCONSISTENCIA-PROTO` | as duas fontes contraditórias | aberta, vai às decisões do Diego |

- Rótulo genérico isolado («Editar», «Nome», «Ações») encontrado em qualquer commit antigo não prova sobra.
- Sem prova, a classe é `NAO_COMPROVADA` e vai às decisões do Diego.
- Mensagem de erro com código de rastreio é sempre `SGD-PROPRIO`.
- Classe nenhuma autoriza remover integração real: sai a UI, o canal fica.

## Pente fino por elemento

Campo, opção, botão, coluna, aba, mensagem. Faça quando algum texto do produto falta no protótipo novo, quando o par é só por comentário que cita arquivo do protótipo, ou quando o texto existe na versão anterior do protótipo. Liste os textos comparados; sem a lista, o pente fino não foi feito.

## Leitura independente

- **Descoberta cega de omissões:** um subagente recebe um pacote sem inventário nem conclusões, com as telas novas, as de maior `peso` no mapa de cobertura (as 20% maiores, no mínimo 2) e uma amostra em ordem fixa que o autor não escolhe. Copie o catálogo antes de integrar o que ela achar e rode `omissoes` depois ([cobertura.md](cobertura.md#conferências)). Sem contexto limpo comprovável no runtime, ela é «dirigida», e o resumo diz isso.
- **Prova da `SOBRA-PROTO-ANTIGO`:** é mecânica, sem segunda leitura. Registre na diferença o comando e a saída: `git -C <prototipo> grep -n '<texto>' <versão registrada> -- <arquivo>` com resultado, e o mesmo na candidata, sem resultado. Sem esse par de saídas, a classe é `NAO_COMPROVADA`.
