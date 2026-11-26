# Adoção e baseline

## Adoção (merge da branch da versão)

É decisão do Diego. Antes de pedir:

1. Integre o ramo principal do produto na branch da versão. Na reconciliação do catálogo, mantenha deste ciclo a `disposition`, a classe e a revalidação; do ramo principal, o estado de execução (tarefas, testes, evidências, diferenças e requisitos novos). Liste cada campo reconciliado. Exceção, o refazer do zero: do ramo principal só se traz o que não é do catálogo antigo; o catálogo novo não reimporta tarefas, testes, evidências, diferenças nem requisitos dele.
2. Rode de novo `node ecosystem/automation/proto_env/parity.mjs catalog <manifest.json> <catalog.json>` e `… linkage <catalog.json>`, com o manifesto e os códigos tolerados de [catalogo.md](catalogo.md#validação), e confira que `baseline` é `{trusted: false}`.
3. Peça o merge ao Diego, junto com o da branch do descritor do protótipo.

Versão recusada: a branch é descartada. O plano dos ITENS começa depois do merge; como planejar a partir do catálogo está em [prototype-parity-verification/references/decisoes-e-planos.md](../../prototype-parity-verification/references/decisoes-e-planos.md).

## Baseline

A baseline diz «até aqui está comprovado» e é o que deixa a versão seguinte rodar INCREMENTAL. Marcada cedo, a próxima versão confia em algo nunca testado.

- `trusted` fica `false` até o marco ser decidido pelo Diego e atingido. Decisão ainda pendente: integrado na release, build servido e validado no DEV, ou versão liberada. Enquanto pendente, pergunte; testes verdes ou integração numa branch não bastam.
- No encerramento da onda, com o marco confirmado pelo Diego:
  - o commit do produto testado vai para `target.commit` **e** `baseline.target_commit`;
  - `reference.digest` vai para `baseline.reference_digest`, e `reference.version` para `baseline.reference_version`;
  - registre o marco, as evidências, `confirmed_by` e `decision_ref`;
  - só então `trusted: true`.
- Nunca por efeito do diff, do registro, do plano ou do merge.
- **Aceite parcial:** cenário fora do escopo comprovado perde `definition` (vai para campo adicional) e recebe `unknowns`; na versão seguinte, sai `uncertain`.
- Evidência da referência antiga não é prova fresca (`validateEvidence` acusa `STALE_REFERENCE`). `SUPERSEDED_REANCHOR_REQUIRED` só aparece quando o fingerprint muda; `NOT_EVALUATED` não valida nada. Nada é reancorado sozinho.
