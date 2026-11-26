# Workflow após criar ou editar

Leia ao fechar a mudança: checklists por tipo, modificação de artefato existente e cobertura do governance-export.

### Playground (canonical)

Copiar checklist e marcar:

```
- [ ] Artefato em ecosystem/canonical/ (não em .cursor/)
- [ ] meta.yaml com id, type, description, targets.cursor
- [ ] content.md completo e UTF-8 OK
- [ ] `python3 ecosystem/automation/jarbas.py materialize --target all` (Cursor **e** Claude Code — rule `dual-ide-materialize`)
- [ ] Paridade: skill → `ecosystem/canonical/skills/` + `.claude/skills/`; rule always-on → `.claude/rules/`; rule on-demand → `.claude/skills/`; subagent → `ecosystem/canonical/agents/library/` + `.claude/agents.md` (índice)
- [ ] Diff em `.cursor/` e `.claude/` revisto (só output esperado)
- [ ] **Testes/validação só no `.cursor/`** (platform-check, catalogo, Task/subagent, contratos); não duplicar gate no Claude Code
- [ ] Docs vivos se mudou política/ecossistema (jarbas.md, docs/01, 99.x) — ver automation-governance
- [ ] Referências a artefatos renomeados ou removidos atualizadas no mesmo commit
- [ ] Opcional: python ecosystem/automation/jarbas.py lint --docs
```

### Profile

```
- [ ] Ficheiro em ecosystem/profiles/<profile_id>/...
- [ ] profile.yaml existe; activation_triggers coerentes
- [ ] Sem duplicar rule global (traceId, TEST gate, etc.)
- [ ] README ou índice do profile atualizado se pasta nova
- [ ] Referências a artefatos renomeados ou removidos atualizadas no mesmo commit
```

### Modificar skill/rule existente

1. Localizar fonte: `rg` em `ecosystem/canonical` e `ecosystem/profiles`.
2. Se só existir em `.cursor/`, **migrar** para canonical/profile antes de editar.
3. Editar fonte → `materialize --target all` (canonical) → validar **só no `.cursor/`** (rule `dual-ide-materialize`).
4. Renomeou, moveu ou apagou: atualizar as referências a ele no mesmo commit (`rg` pelo nome antigo).
   Vale também para comandos e agentes `ecosystem/canonical/agents/library/`.

### Tipo ou local novo de objeto

Se o artefato for um tipo novo (ex.: outro ficheiro de instruções de agente) ou ficar num local fora das categorias de `ecosystem/shared/governance-export.yaml`, acrescentar o glob a uma categoria desse YAML, ou o caminho a `cobertura.ignorar` com o motivo. Caso contrário, o teste de cobertura do export de governança falha (`jarbas.py governance-export --dry-run --strict`, flow governance-export.md).
