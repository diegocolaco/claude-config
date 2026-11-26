---
tags: [skill-creator]
max_turns: 12
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Escreva o corpo da descrição deste PR em português do Brasil, pronto para colar. Preciso entender as mudanças sem ler o código. Seja objetivo, preciso aprovar ainda hoje. Use somente os fatos sintéticos fornecidos; não inspecione repositório, não execute testes e não publique nada.

O diff completo já foi conferido para este exercício:
- A exportação CSV de pedidos usava só a página atual, até 50 pedidos. Agora consulta todas as páginas, preserva filtros de status/período e aceita até 5.000 pedidos. Acima disso exibe aviso e não gera arquivo parcial.
- As datas exportadas eram UTC; agora seguem o fuso configurado da loja. O armazenamento das datas não muda.
- Um formatador CSV foi extraído para compartilhamento; é refatoração interna.
- O log fornecido registra 12 testes unitários aprovados, cobrindo paginação, filtros, limite e fuso. O comando não foi registrado. O E2E de download não foi executado porque o navegador estava indisponível.
- Nenhum pacote nem migração de banco mudou. O motivo de negócio não foi documentado.

Responda somente com o corpo Markdown da descrição.
