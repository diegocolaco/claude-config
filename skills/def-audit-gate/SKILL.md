---
name: def-audit-gate
description: Use quando houver DEF-AUDIT ou divergência de definição entre SGD novo e Lovable/SDD, antes de PO ou developer.
---
CTX-ID: def-audit-gate@4

# DEF-AUDIT Gate — Paridade definicao vs prototipo (SGD novo)

## Composição Superpowers

Gate jarbas antes de PO/DEV; alinhamento de definição segue descoberta/desenho do Superpowers.

**REQUIRED BACKGROUND:** You MUST understand `superpowers:brainstorming` — confronto definição × proto é etapa de desenho, não implementação.

## Quando usar

- Profile **`sgd-novo`** ativo **e** o pedido envolve definicao externa, nova onda Lovable, SDD de tela ou implementacao que possa alterar regra de negocio.
- **Antes** de `product-owner` ou `developer` quando a fonte nao e apenas SDD ja alinhado ao proto.
- Jarbas classificou ou vai classificar fluxo com risco de **linha alternativa de RB**.

Nao substitui o **SDD gate** (`sdd-gate`); corre **depois** de definition.md existir ou em paralelo ao Clarify quando a definicao recebida e o foco.

## Ordem e paralelismo

Reincidência no ITEM-15000: o DEF-AUDIT foi tratado como tarefa de execução, ficou depois do plano e correu com **um auditor só**. Passa a valer:

1. **Antes do plano.** Corre **antes de o desenho ser apresentado ao Diego** e, portanto, antes do plano e do PRE. O plano só cita o def-audit-report.md; **não** inclui o DEF-AUDIT como tarefa.
2. **Em paralelo, um auditor por domínio** (`AGENTS.md`, «Despacho de subagents»): produto/regra de negócio · estrutura/telas · SDD aprovado, todos na mesma mensagem. Medir a capacidade antes de despachar (auditor só lê, `capacity.py:52`); `media` serializa sem motivo. Um auditor para tudo = achado de processo.
3. **Fecho:** confirmação limitada (auditor retomado) para o que achou + **uma** revisão ampla (`task-reviewer`) nas costuras e pendências; consolidar num único `.tmp/<session-id>/def-audit-report.md` com a linha `Verdict:` e `ACHADOS_RELEVANTES`.
4. **Trava no gate:** o gate do PRE recusa o PRE sem def-audit-report.md com `Verdict: ALINHADO`. `N/A` ou veredito ≠ `ALINHADO` só passam com `aprovado: Diego, <data>, «<trecho>»` no relatório. A trava só vale no 1.º PASS do PRE (não é retroativa a PRE já trancado).

## Principio

Pedir correcao ao produto quando necessario; **paridade funcional com o export Lovable vigente**; nao implementar RB que contradiz o proto em item ainda em aberto no SDD de paridade.

## Procedimento

1. **researcher** (opcional, mesmo turno jarbas): localizar export `SGD Novo (N)`, ficheiros de tela no export, `SDD-PARIDADE-PROTO*.md`, SDDs de tela e codigo afetado.
2. **auditor de definição (DPA)**: preencher relatorio a partir do template:
   - def-audit-report.md
   - Destino: `.tmp/<session-id>/def-audit-report.md`
3. Emitir **verdict**.
4. Jarbas:
   - `ALINHADO` → continuar pipeline (PO / DEV).
   - `ATUALIZAR_SDD` → `product-owner` (sem inventar RB fora do proto).
   - `PEDIR_CORRECAO_PRODUTO` ou `BLOQUEADO_PROTO_AUSENTE` → **nao codar**; escalar humano/produto.

## Bloqueio

```
[jarbas DEF-AUDIT BLOCKED] trace_id=<id> | motivo=<verdict> | acao=ver def-audit-report.md
```

## Referencias

- doc-sgd-novo-melhorias-processo.md (MP-001)
- doc-sgd-novo-definicao.md secao 4.1
- Agente: `ecosystem/canonical/agents/library/dpa/content.md`
