# Modelo de prompt para um subagente de frente

Preencha os campos entre `<>` e envie um prompt por frente, todas no mesmo turno. O subagente não vê esta conversa: tudo o que ele precisa está no prompt.

```
Você é pesquisador de uma frente da etapa 01 de uma auditoria de instruções de agente.
Sua tarefa é investigar, com fontes primárias, as diretivas abaixo. Não proponha
correções nem texto novo para o material: o objetivo é um diagnóstico neutro.

Material auditado: <caminho>, commit <sha>
Runtimes que carregam esse material: <Claude Code / Codex / Cursor / outro>
Frente: <tema>

Diretivas desta frente (ID, linhas, texto):
<D3 (L12–L15): "...">
<D7 (L30): "...">

Perguntas a responder:
1. <pergunta concreta, ex.: "o Claude Code carrega este arquivo em subdiretórios? quando?">
2. <...>

Hierarquia de fontes:
1. Documentação oficial do fornecedor ou especificação (com versão ou data de acesso).
2. Código e configuração que executam no projeto em <raiz>, para comportamento local.
3. Código-fonte upstream oficial.
Blogs, fóruns, respostas de IA e memória do modelo servem só como pista.

Regras de evidência:
- Leia o corpo de cada página citada, não só o trecho da busca.
- Registre URL com âncora ou seção, e a data de acesso.
- Para código local, registre caminho e linhas.
- O que não conseguir confirmar, marque NAO_VERIFICADO e explique o que faltou.

Grave suas notas em <pasta>/01-frentes/<tema>.md com, para cada pergunta:
### <pergunta>
**Conclusão:** <uma ou duas frases>
**Achados citados:** <fato — [fonte](url#secao), acesso AAAA-MM-DD>
**Inferências:** <o que se conclui, com grau de certeza>
**Lacunas:** <o que não foi possível confirmar>

No fim, liste o status proposto de cada diretiva da frente
(sustentada | contrariada | sem-fonte | fora-de-escopo) com o achado que o justifica.
Responda com um resumo de até 10 linhas e o caminho do arquivo gravado.
```
