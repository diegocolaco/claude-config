# Glossário, composição com outros fluxos e erros comuns

Ler em dúvida de termo, ao ligar esta skill ao `/sgd-entrega` ou ao `/diagnostico-causa-raiz`, ou para revisar a lista de erros comuns.

## Glossário

| Termo | Significado |
|-------|-------------|
| **EVIDÊNCIA-ERRO** | Pacote de provas de que o bug existe: matriz de **reprodução no DEV** + relatório **Datadog**, em `items/<codigo>/evidence/EVIDENCIA-ERRO.md` (gate **1c** da skill `validar-comportamento-dev-prototipo`) |
| **Reprodução no DEV (manual)** | Browser em `dev.sgd.dominiosistemas.com.br`; repetir a ação do relato — **não** é Playwright local |
| **Usuários de QA (lista ITEM-161)** | Personas do doc de smoke, acessadas por personificação no Keycloak; percorrer **todos os disponíveis** — **não** chamar de «smoke informal» nem «teste informal» |
| **E2E automatizado** | Pode produzir RED antes da correção, GREEN quando a fatia fica exercitável e prova final no TEST. Cada finalidade e snapshot ficam identificados; E2E complementa a reprodução inicial em DEV e não a substitui. |
| **Pedido informal** | Texto do chat/planilha — só **pista**; critério de aceite vem do protótipo Lovable (paridade), não do relato |
| **Veredito** | Resultado fechado da rodada Datadog: `CONFIRMADO`, `SEM_EVIDENCIA`, `DIVERGENTE`, `INCONCLUSIVO` (tabela no passo 5) |
| **Localizador de cenário** | Skill **`localizador-cenarios-teste`**: par registro + usuário no DEV sem ação mutável — **não** substitui matriz nem Datadog |

**Ordem fixa:** relato → (opcional **`localizador-cenarios-teste`** se faltar registro/usuário) → reprodução multi-usuário no DEV (gravar matriz) → ficha ITEM passo 2.7 → Datadog → só então correção de código.

Comando (`JCMD-INVESTIGAR-ERRO-001`) é a referência normativa; anexo SGD do localizador:
`ecosystem/canonical/skills/localizador-cenarios-teste/references/anexo-sgd-novo-dev.md`.

## Composição com outros fluxos

| Fluxo | Relação |
|-------|---------|
| `/diagnostico-causa-raiz` | Ciclo de 6 fases; a fase 1 segue este procedimento no SGD novo (reprodução → investigador) |
| `/sgd-entrega` (gates 1c e 11c) | Passo **1c** executa este procedimento integralmente em ITEM de erro, antes de PARIDADE-PRE/EXEC; **11c** reutiliza a política autónoma no DEV |
| `/status-entrega` | Pilares + evidências (fotos/vídeo/relatórios); checklist completo só com filtro `apêndice` (`JCMD-STATUS-ENTREGA-001`) |
| `validar-comportamento-dev-prototipo` | Gate obrigatório quando o retorno inclui falha no DEV remoto; depois paridade proto × SGD local (skill § Gate — erro no DEV remoto) |

## Relacionado

- investigar-erro.md (gates invioláveis) · rule/skill **`analysis-completeness-audit`** (passo 5b após `CONFIRMADO`) · validar-comportamento-dev-prototipo.md
- Subagente `error-evidence-investigator` (`ecosystem/canonical/agents/library/`, fonte `ecosystem/canonical/agents/subagents/`)

## Erros comuns

- Ler o passo 2.7 como «consultar a ficha» → escrever a subsecção «Reprodução DEV — contexto QA» em `item-<codigo>.md` e commitar a governança antes do passo 3 (Datadog).
- Reproduzir com «mais de um perfil» e parar → percorrer todos os usuários de QA disponíveis e registrar os indisponíveis na matriz.
- Despachar o investigador sem janela UTC e sem validar → incluir Janela BRT e UTC no pedido e rodar `evidencia-erro-check` no relatório.

