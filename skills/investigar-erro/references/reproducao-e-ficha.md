# Relato, universo afetado, reprodução e registro na ficha (passos 1, 2 e 2.7)

Ler ao montar a matriz de reprodução, ao registrar na ficha do ITEM ou quando o relato tiver quantificador.

### 1. Relato
Extrair sintoma (texto do aviso, tela, ação, severidade), horário BRT, traceId, ITEM. Faltando horário ou ação: perguntar
**uma vez**, tudo junto. Gerar `trace_id` (`jarbas-YYYYMMDD-HHMMSS-xxxx`). Se souber a rota, indicar o serviço dono pela
tabela «Caminho de um pedido» do mapa do DEV.

**Relato de defeito com quantificador → universo afetado.** «Alguns», «vários», «todos», «às vezes» ou um **exemplo** («ex.: CT-…») descrevem uma **classe**, não um registro; o exemplo é só o caso de partida. Antes da reprodução, consultar o DEV (somente leitura) e contar a população que cai na mesma condição do exemplo, **por tipo e estado** (raiz × filho, PF × PJ, modo/canal nulo × preenchido, com × sem o recurso). Gravar sob `## Universo afetado`, logo depois da matriz de reprodução (só contagens, sem PII): `grupo · quantidade · reproduz? · destino`. **Destino** de cada grupo no 1c: `corrigir neste ITEM` · `fora de escopo (decisão do Diego, data)` · `decidir com o Diego` (bloqueia PRE/EXEC e vai a «Com você»); no 11c vira `corrigido (PR)` · `fora de escopo` · `aberto`. Grupo sem destino bloqueia o `CONFIRMADO` (`[jarbas CA-CLASSE BLOCKED] … motivo=universo sem destino`). O `CA-*` da ficha nasce sobre a classe (skill `governed-numbered-item-delivery` § 3) e o 11c reconfere esta tabela. Rule: `sgd-novo-investigar-erro` gate 11.

### 2. Reprodução multi-usuário no DEV (obrigatório, antes do Datadog)

**Cenário (opcional):** sem ID de registro na etapa ou persona com escopo → skill **`localizador-cenarios-teste`** antes deste passo; citar par `VALIDADO` na matriz.

Seguir **Execução autónoma no DEV**.

1. Browser em `https://dev.sgd.dominiosistemas.com.br`.
2. Para **cada usuário disponível**: personificar no Keycloak → conferir `/api/auth/me` → repetir a **ação** do relato (roteiro da ficha ITEM ou passos do sintoma).
3. Ação que grava → liberada sem aprovação, **exceto** usuário/registro da empresa Dominio (`sgd-dev-nao-criar-na-dominio`); dados `ZZ-TESTE-<trace_id>`; listar para limpeza.
4. Por usuário, registrar na **matriz de reprodução** (máscara de CPF ou persona): reproduziu? (sim/não/não aplicável) ·
   traceId UI/rede · screenshot ou nota curta · bloqueio (401, inativo, personificação falhou).
5. Se **nenhum** usuário reproduzir e todos estiverem bloqueados por infra/login →
   `[jarbas EVIDENCIA-ERRO BLOCKED] trace_id=<id> | motivo=<...> | acao=...`; caso contrário seguir mesmo com repro parcial.
6. Persistir a matriz **no início** de `repo/sgd-cursor-governance/items/<codigo>/evidence/EVIDENCIA-ERRO.md` (ITEM) ou
   `.tmp/<trace_id>/evidencia-erro.md` (sem ITEM) sob o título `## Reprodução DEV (multi-usuário)` **antes** de despachar o
   investigador. O `evidencia-erro-check` aceita este bloco antes do primeiro `[evidencia-erro]`, só com esse título na
   primeira linha; **CPF completo em qualquer parte do ficheiro falha o check**.
7. **Registro na ficha do ITEM (passo 2.7 — obrigatório quando houver `ITEM-<codigo>`):** seguir
   investigar-erro-registro-ficha-item.md.
   1. Na matriz, identificar o usuário/persona que **reproduziu** (ou o prioritário da ficha) e os dados de negócio vistos na UI (cliente, contrato, prospect, URLs).
   2. Acrescentar em `repo/sgd-cursor-governance/items/<codigo>/item-<codigo>.md` a subsecção **«Reprodução DEV — contexto QA»** (tabela: URL base, URL tela com query, rota UI, entidade, **cliente**, **usuário** com CPF mascarado, ação, `trace_id`, `traceId` rede/UI, ponte para EVIDENCIA-ERRO.md). **Não** copiar senha — só planilha #N do doc de credenciais.
   3. Espelhar rodada datada em `items/<codigo>/evidence/README.md` (ou parágrafo ligado à matriz em EVIDENCIA-ERRO.md).
   4. **Commit** no repo `sgd-cursor-governance` **antes do passo 3** (Datadog): `docs(ITEM-<codigo>): registro reprodução DEV investigar-erro`.
   5. Sem ITEM no relato → só `.tmp/<trace_id>/reproducao-dev-contexto.md` com a mesma tabela (não saltar a matriz).
