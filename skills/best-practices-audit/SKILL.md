---
name: best-practices-audit
description: Use quando pedirem auditar o workspace contra o Manual de Boas Práticas jarbas.
---


# Auditoria de Boas Práticas — TR Jarbas Ai Multi-agents squad

## Quando usar
Use esta skill quando o usuário, o Diego ou um portão de qualidade (Quality Gate) solicitar uma auditoria do workspace, verificação de conformidade de segurança e boas práticas, ou quando quiser certificar se um clone de produto, regra, skill ou código foi adicionado seguindo estritamente os padrões canônicos.

## Procedimento de Auditoria (Passo a Passo)

### 1. Auditoria de Governança de Instruções e Regras
Verifique se novas regras de robôs ou habilidades estão sendo introduzidas de forma descentralizada ou incorreta.
* **O que procurar:** Arquivos `.mdc`, `ecosystem/canonical/rule/`, `ecosystem/canonical/skills/`, `ecosystem/canonical/agents/library/` ou criados diretamente dentro de `repo/` ou na raiz `.cursor/` sem fonte equivalente em `ecosystem/canonical/` ou `ecosystem/profiles/`.
*   **Como auditar:** 
    *   Examine a árvore de diretórios de clones: `repo/**/.cursor/rules/**`.
    *   Verifique se o materializador de regras foi executado após edições das fontes canônicas.

### 2. Auditoria de Git e Worktrees
Verifique se alterações na torre de controle (o playground) estão poluindo a branch agregada principal.
*   **O que procurar:** Arquivos da pasta `ecosystem/`, `docs/` ou regras canônicas modificados diretamente no checkout raiz `agregado/local` sem o uso de worktrees temporários (`.worktrees/wt-*`).
*   **Como auditar:** Execute `git status` na raiz e verifique se há arquivos staged ou modificados que fazem parte de caminhos versionados de governança.

### 3. Auditoria de Isolamento de Repositórios (Clones)
Verifique se repositórios de produtos foram clonados fora das diretrizes de isolamento.
*   **O que procurar:** Pastas clonadas (ex: contendo arquivos `.git` ou arquivos de código de produtos) localizadas na raiz do workspace ou em qualquer diretório fora de `repo/`.
*   **Como auditar:** Busque arquivos `package.json`, `.git` ou arquivos TypeScript/Java de código de produto na raiz do workspace.

### 4. Auditoria de Deleções de Arquivos e Lixeira
Verifique se houve uso de comandos destrutivos diretos.
*   **O que procurar:** Presença de remoções em massa sem rastro na lixeira ou logs de purga com `delete-paths.py` ou `io-delete`.
*   **Como auditar:** Verifique se as pastas temporárias e a lixeira local em `.tmp/.trash/` contêm registros de deleções recentes correspondentes às atividades do dia.

### 5. Auditoria de Segurança de Dados e Mascaramento de PII
Garante que informações confidenciais não estejam sendo vazadas em logs de sessão, planos de execução ou mensagens.
*   **O que procurar:** Presença de CPFs, CNPJs reais, e-mails pessoais de clientes, ou chaves privadas/Bearer tokens não mascarados nos relatórios da pasta `docs/execucao/sessoes/` ou logs em `.tmp/`.
*   **Como auditar:** Faça buscas usando expressões regulares (regex) para padrões conhecidos de PII (conforme a tabela obrigatória do manual de boas práticas).

---

## Estrutura do Relatório de Desvio

Gere o resultado da auditoria no formato abaixo e grave em AAAA-MM-DD-auditoria-boas-praticas.md:

```markdown
# Relatório de Auditoria de Boas Práticas — Ecossistema Jarbas (<DD/MM/AAAA>)

Projeto: TR Jarbas Ai Multi-agents squad · trace: `<trace_id>`

## Resumo Executivo
<Veredito final de conformidade: PASSOU (Aprovado sem desvios) ou FALHOU (Bloqueado por violações)>

## 1. Verificação de Governança (Rules/Skills/Agentes)
- **Status:** <Em Conformidade | Desvio Encontrado>
- **Análise:** <Detalhamento técnico dos arquivos de regras encontrados e suas fontes>

## 2. Verificação de Git & Worktrees (Controle de Alterações)
- **Status:** <Em Conformidade | Desvio Encontrado>
- **Análise:** <Presença de arquivos modificados diretamente na raiz Aggregate sem worktree isolado>

## 3. Verificação de Isolamento de Repositórios
- **Status:** <Em Conformidade | Desvio Encontrado>
- **Análise:** <Verificação de clones de produtos fora de repo/>

## 4. Verificação de Segurança e Mascaramento de PII
- **Status:** <Em Conformidade | Desvio Encontrado>
- **Análise:** <Resultado da varredura de dados sensíveis e segredos em logs e relatórios de sessões>

## Próximos Passos (Ações Corretivas)
1. <Ação 1: Ex: Mover regra x para canonical e rodar materialize>
2. <Ação 2: Ex: Mascarar CPF na sessão y>

```
