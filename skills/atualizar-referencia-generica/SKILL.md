---
name: atualizar-referencia-generica
description: Use ao concluir alterações no controlador de origem da referência genérica, ao sincronizar sua versão derivada ou quando houver arquivos novos, renomes ou candidato pendente.
---

# Manter a referência genérica atualizada

Mantenha a versão derivada quase tão completa quanto o controlador compartilhável, com a mesma estrutura e os mesmos processos. Troque nomes por equivalentes genéricos somente na saída. Preserve o laboratório de origem e registre limitações concretas; não reduza o resultado a poucos documentos e agentes.

## Composição Superpowers

**REQUIRED BACKGROUND:** `superpowers:verification-before-completion`. Use o isolamento, a revisão e a integração exigidos pelo projeto ao corrigir seleção, adaptações ou gerador. Esta skill reaproveita o publicador existente; não cria outro exportador, serviço ou mecanismo de aprovação.

## Conferir origem e autorização

Resolva controlador, aplicações e worktrees por `ecosystem/ecosystem-config.yaml`. O estado privado é `.local/public-reference/`; leia a política `ecosystem/shared/public-reference-policy.yaml` e o procedimento `ecosystem/docs/public-reference.md` conforme a operação.

Confirme que está no controlador de origem. Um clone do destino, uma aplicação ou uma consulta somente em leitura não concede autorização para publicar. Não criar commits nem iniciar manutenção em resposta a uma consulta que só pede análise e chat.

A manutenção recorrente do destino conhecido foi solicitada pelo usuário. Não peça novamente uma autorização genérica de atualização quando ela já existe. Confira a conta autenticada e a visibilidade real do destino; preserve a decisão registrada em `visibility-decision.json`. Se a decisão é manter privado e o remoto está público, pare o envio e relate a divergência. Esta skill nunca muda a visibilidade, troca conta ou usa credenciais recebidas em fotos.

## Manter cobertura e fidelidade

1. Confira estado Git e o commit integrado em `agregado/local`. Não exporte alterações pendentes nem trabalho de outra branch como se estivesse integrado.
2. Execute `python3 ecosystem/automation/jarbas.py public-reference inventory` e compare todos os paths do commit com a seleção e a última correspondência privada. Examine adições, renomes, remoções e dependências. Arquivo novo não herda aprovação de uma pasta, mas também não pode ser esquecido por estar fora da lista antiga.
3. Preserve fontes genéricas de regras, skills, agentes, configurações, scripts, hooks, perfis e testes. Um nome de produto no arquivo não o torna inteiramente privado. Separe ou adapte somente a unidade específica quando o restante do processo é reaproveitável.
4. Mantenha os renomes consistentes em paths, identificadores, imports e referências. Preserve modos executáveis, licenças e atribuições. Regere hashes/manifestos dos bytes derivados; não copie prova, aprovação, commit ou proveniência privados para fingir validação pública.
5. Registre conteúdo privado e pendências por arquivo no controle privado, com causa. Conteúdo de negócio específico, credenciais, dados reais, histórico e particularidades identificáveis ficam fora. Renomear palavras não autoriza divulgar esse conteúdo. Adaptação presa ao hash de origem perde validade quando a fonte muda.

Se for preciso corrigir política ou código, faça-o em worktree exclusivo e integre pelo fluxo vigente antes de gerar a captura definitiva. Não altere o original privado só para facilitar a divulgação nem edite cópias materializadas como fonte. Não use reset, clean, force push ou descarte de trabalho para resolver divergência.

## Gerar, revisar e enviar

Use o observador e a reconciliação existentes:

```bash
python3 ecosystem/automation/jarbas.py public-reference reconcile
python3 ecosystem/automation/jarbas.py public-reference status
```

A geração automática produz um candidato, não uma aprovação. Confira a origem integrada, política, cobertura, bytes finais e o diff contra a edição anterior. Revise conteúdo e metadados além dos detectores: nada específico pode ser enviado por ter passado numa busca de palavras. Previews de tarefa não são publicáveis.

```bash
python3 ecosystem/automation/jarbas.py public-reference review --candidate CAMINHO_DO_CANDIDATO
python3 ecosystem/automation/jarbas.py public-reference review --candidate CAMINHO_DO_CANDIDATO --approve --expected-digest DIGEST_EXATO --reviewer IDENTIFICADOR_DA_REVISAO
python3 ecosystem/automation/jarbas.py public-reference publish --candidate CAMINHO_DO_CANDIDATO --destination DIRETORIO_DO_DESTINO --dry-run
python3 ecosystem/automation/jarbas.py public-reference publish --candidate CAMINHO_DO_CANDIDATO --destination DIRETORIO_DO_DESTINO
```

Obtenha candidato, digest e destino do estado/política real; os nomes acima são parâmetros, não novos paths a inventar. Identifique o agente ou a pessoa que efetivamente revisou, sem atribuir uma aprovação humana inexistente. Só registre aprovação depois da revisão e com o digest correspondente.

Use o Git separado do publicador. Preserve arquivos manuais; remoto, branch ou conteúdo divergentes exigem conciliação, não sobrescrita. Rede indisponível deixa a fila/journal para retomada. Uma atualização aprovada já enviada deve ser idempotente; não faça um commit vazio apenas para dizer que sincronizou.

## Concluir com estado real

Confira no destino os paths/hashes/modos da captura, identidade e histórico independentes e visibilidade autorizada. Informe versão enviada, commit de origem integrado, cobertura/omissões, resultado da publicação e pendências. Guarde correspondência e recibos apenas no estado privado.

Candidato pendente, adaptação inválida, fonte nova sem decisão ou falha de envio significa **pendente**, não sincronizado. Diga exatamente o que falta e continue o que for independente. Quando não há diferença de conteúdo e a conferência passou, informe que o destino já corresponde à referência.
