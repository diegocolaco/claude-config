# Evidência e triagem

`[src]` é fonte da referência alcançável; `[obs]` é captura/observação com condições; `[doc]` exige decisão aprovada pertinente à versão; `[net]` da aplicação não define expected da referência; `[inf]` não autoriza conformidade.

Separar `discovery_status` (`INVESTIGADO`, `NAO_INVESTIGADO`, `BLOQUEADO`, `FORA_ESCOPO_JUSTIFICADO`) de `parity_status` (`CONFORME`, `DIVERGENTE`, `NAO_VERIFICADO`, `BLOQUEADO`, `EXCECAO_APROVADA`, `SEM_COMPARACAO`). `aggregateParity` exige provas declaradas por dimensão; ele não autentica seu conteúdo. Exceção exige autoridade, razão, escopo e revisão. Evidência antiga/estado diferente não é prova fresca.

Falha de teste: distinguir app, teste, ambiente, flaky sem causa, expected desatualizado e bloqueio. Usar systematic-debugging oficial; não esconder falha com skip/retry. Jornada ainda não executável aponta dependências e proprietário, sem RED artificial por infraestrutura ausente.

Relatar paridade dos cenários conhecidos por padrão. Totalidade depende de escopo independente fechado e sem lacunas, não do número de IDs. Auditoria de utilidade/custo só sob pedido, usando fatos registrados pelo core quando disponíveis; dado ausente é `NAO_MEDIDO`.
