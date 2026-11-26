# Regras do agente — projeto Catálogo

Carregado pelo Claude Code como o CLAUDE.md da raiz do projeto Catálogo (Node.js 22, testes com `npm test`). CLAUDE.md em subdiretórios também é carregado quando o agente lê arquivos daquele diretório; regras específicas de um módulo podem ficar lá.

## Idioma

- Responda ao usuário em português do Brasil.

## Git

- Trabalhe em uma branch própria; não commite direto na `main`, porque a `main` é publicada automaticamente.
- Não faça push direto para a `main`. Em caso de hotfix, pode fazer push direto.
- Rode `npm test` antes de cada commit e só commite com a suíte passando.

## Automação

- Para rodar sem pedir confirmações, inicie a sessão com `claude --permission-mode bypassAll`.

## Qualidade

- Seja cuidadoso e escreva código de alta qualidade.
- Lembre-se de que estas regras são importantes.
