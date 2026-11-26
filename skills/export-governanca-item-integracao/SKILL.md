---
name: export-governanca-item-integracao
description: Use quando exportar pacote de governança ITEM (Superpowers × Jarbas × protótipo × entrega) para modelo externo ou revisão.
disable-model-invocation: true
---
CTX-ID: export-governanca-item-integracao@2

# Export — governança do processo de integração de ITEM (v3)

**Projeto:** TR Jarbas Ai Multi-agents squad · **Profile:** `sgd-novo` (conteúdo do pacote).

Pacote único `.md` com anexos integrais (harness, comando de entrega do profile, skills e rules de paridade/entrega ITEM).
Fluxo técnico: governance-export.md (secções *Export temático ITEM* e *Endurecimento para IA pública*).

## Quando usar

| Situação | Acção |
|---|---|
| Regenerar o export após mudar harness, skills, rules ou processo ITEM | Procedimento A |
| Reanonimizar um `.md` já montado (sem revarrer o repo) | Procedimento B |
| Partilhar com modelo externo / IA pública | A ou B + checklist de segurança (secção abaixo) |

## Procedimento A — montar e anonimizar (padrão)

1. **Raiz:** checkout do playground (`agregado/local` ou worktree com o mesmo conteúdo).
2. **Montar** (anonimização **ligada** por defeito):

```bash
```

| Opção | Efeito |
|---|---|
| `--out <path>` | Destino alternativo ao default |
| `--no-anonymize` | Só revisão **interna** no repo — **não** enviar a IA pública |

3. **Saída default:** export-governanca-superpowers-jarbas-prototipo-item.md.
4. Se o comando falhar com `strict-security`, corrigir o anonimizador ou o conteúdo fonte — **não** desactivar o strict para «fechar rápido».

## Procedimento B — só anonimizar ficheiro existente

```bash
```

Pipeline: `redact` → `anonymize_text` → `omit_sensitive_units` → `omit_application_code` → legenda, aviso e resumo.

## Checklist antes de IA pública (diretriz de uso de IA TR)

1. **Ferramenta aprovada** — só o canal que a empresa autorizou para esse tipo de conteúdo.
2. **Revisão humana** — ler amostras dos anexos 8–13 e a legenda; a varredura é por **padrões**, não linha a linha.
3. **Não reenviar** versão `--no-anonymize` nem export `supercompleto*` para fora do perímetro.
4. **Superpowers:** corpos das skills do plugin **não** estão no repo — o export lista nomes; o modelo externo não terá o texto integral do SP.
5. Opcional: skill `documentar-seguranca-gate` se o Diego pedir confirmação explícita do que pode sair.

## Depois de gerar

- Commit no worktree se alterou o `.md` versionado (rule `playground-commit-required`).
- Para aplicar melhorias que voltem do modelo externo → skill **`import-governanca-item-integracao`**.

## Referência rápida — lista de fontes (SSOT)

O inventário de anexos e paths reais está em `ecosystem/automation/governance_export/build_item_integration_export.py`
(`CORE_SOURCES`, `SKILL_SOURCES`, `PROFILE_RULES_EXTRA`, `CANONICAL_RULES_ITEM`, etc.). A secção 0 do `.md` gerado espelha o índice v3.
