---
name: documentar-seguranca-gate
description: Use antes de gravar em user-doc quando o conteúdo puder trazer PII, credencial ou segredo.
---
CTX-ID: documentar-seguranca-gate@2

# Gate de segurança — documentar e exportar

**Projeto:** TR Jarbas Ai Multi-agents squad

## Quando usar (obrigatório)

Correr **antes** de gravar em `user-doc/`, commitar documentação, colar relatórios longos na resposta, Canvas, anexos ou qualquer **exportação** fora do ambiente de trabalho, quando o Diego pedir **explicitamente** para documentar:

- "documente", "apenas documente", "documente isso", "registre na documentação", "deixe documentado".
- Pausa de tarefa com "apenas documente agora".
- Exportação para revisão: pedidos cobertos por `exportar-chat` ou `exportar-conversa-e-arquivos-para-revisao` (pacote ZIP, agente externo, revisor).

**Ordem:** esta skill → (após aprovação humana) skill `documentar-user-doc` **ou** skills de export (`exportar-chat` / `exportar-conversa-e-arquivos-para-revisao`).

Não substitui global.mdc (referência Jarbas não importada; PII na leitura/escrita). Este gate acrescenta **confirmação humana** sobre âmbito e exportação.

## Princípio (não negociável)

- **Proibido** persistir ou exportar conteúdo que possa comprometer a segurança, a confidencialidade comercial ou a privacidade da **Thomson Reuters** (e clientes/dados tratados no âmbito do trabalho).
- Em **dúvida**, **não incluir** — usar placeholder genérico ou pedir orientação ao Diego.
- O agente **não** decide sozinho que "é seguro o suficiente" para exportar detalhes sensíveis.

## O que conta como "exportar"

| Canal | Exemplos |
|-------|----------|
| Persistência no repo | `user-doc/`, `docs/`, comentários em PR, auxílio de testes |
| Resposta ao Diego | Blocos longos copiáveis, dumps de config, trechos de código com segredos |
| Fora do chat | Canvas, gist, e-mail, ticket público, screenshot com dados reais |

## Gate — parar e perguntar (uma rodada)

Antes de escrever o documento, enviar ao Diego um bloco curto com:

1. **Resumo do que se pretende documentar** (3–6 linhas, sem dados sensíveis).
2. **Checklist de risco** — marcar o que o rascunho **poderia** incluir (só títulos; sem exemplos reais na pergunta):

   - **Segurança:** vulnerabilidades, falhas não corrigidas, bypass de controles, detalhes de autenticação/autorização, chaves, tokens, certificados, segredos de aplicação, configuração de firewall/WAF/ALB, hardening interno, resultados de pentest, CVEs não mitigados.
   - **Negócio confidencial:** estratégia, roadmap não público, pricing, margens, contratos, SLAs internos, métricas comerciais sensíveis, planos de fusão/aquisição, comunicação interna restrita.
   - **Dados e PII:** CPF/CNPJ, e-mails pessoais, nomes ligados a dados fiscais, dumps de BD, queries com dados reais, logs com identificadores (mascarar sempre; ver global.mdc, referência Jarbas não importada).
   - **Infra e operações:** hosts internos, URLs não públicas, credenciais de ambiente, connection strings, IPs de produção, runbooks com comandos que expõem segredos.
   - **Terceiros / compliance:** dados de parceiros, auditorias restritas, achados que não podem sair do perímetro TR.

3. **Perguntas fechadas** (o Diego responde por item ou "nenhum"):

   - «Este documento vai para **git versionado** (ex.: `user-doc/`)?»
   - «Algum destes tópicos de risco deve entrar **integralmente**, **só resumo sem detalhe**, **mascarado** ou **omitido**?»
   - «Há intenção de **partilhar fora** deste repositório ou desta conversa (PR público, cliente, suporte externo)?»

4. **Estado:** `[jarbas DOC-SECURITY-GATE] aguardando confirmação do Diego antes de gravar`.

**Não gravar ficheiros** nem fechar commit de documentação até resposta explícita do Diego (ou instrução clara no mesmo pedido: ex. «documente só decisões técnicas, sem nomes nem URLs»).

## Depois da resposta do Diego

| Decisão | Acção |
|---------|--------|
| Omitir tópico | Não mencionar ou usar «[OMITIDO — confidencial TR]» com motivo de uma linha |
| Mascarar | Aplicar tabelas de global.mdc (referência Jarbas não importada); generalizar (ex. «ambiente DEV» em vez de URL) |
| Resumo apenas | Conclusão e próximo passo, sem reproduzir evidência sensível |
| Aprovar com cuidado | Incluir só o mínimo necessário; evidência sensível fica em sistema interno, não no doc |

Seguir então a skill `documentar-user-doc` (destino, formato, índice, commit).

## Red flags — nunca documentar/exportar

- Segredos em claro (password, API key, private key, `Authorization:` completo).
- Instruções que facilitem acesso não autorizado a sistemas TR ou de clientes.
- Dados pessoais identificáveis sem máscara e sem necessidade operacional documentada.
- Conteúdo que o Diego classificar como restrito ou «não pode sair da TR».

Se o Diego pedir explicitamente para incluir algo da lista acima, **repetir o risco** em uma frase e só prosseguir após confirmação inequívoca; na dúvida, manter omitido.

## Integração

| Artefato | Papel |
|----------|--------|
| Rule `documentar-user-doc` | Dispara documentação; passo 1 = esta skill |
| Skill `documentar-user-doc` | Destino e formato após gate |
| Skill `analises-documentadas` | Grava análises sem palavra «documente»; **recomendado** aplicar o mesmo gate se o rascunho tocar categorias de risco acima |
| Skill `exportar-conversa-e-arquivos-para-revisao` | Pacote formal de revisão (00/01/02, inventário, ZIP); gate **antes** de gravar o pacote |

## Fecho

Após gravar com gate aprovado, na resposta ao Diego indicar em uma linha: «Gate DOC-SECURITY: aplicado; tópicos omitidos/mascarados: …».
