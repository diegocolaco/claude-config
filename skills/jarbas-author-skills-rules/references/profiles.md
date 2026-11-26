# Skills e rules de profile

Leia quando o artefato pertencer a um produto (`ecosystem/profiles/<profile_id>/`).

## Formato — Skill no profile

```
ecosystem/profiles/<profile_id>/skills/<nome-dir>/
├── SKILL.md           # frontmatter + corpo (ficheiro final, não materializado)
└── reference.md       # opcional — permitido aqui
```

- `name` no frontmatter pode ser prefixado com o profile quando a skill for **só** desse produto.
- `description` deve citar o **profile_id** e gatilhos do produto.
- Ler `profile.yaml` e rules em `profiles/<id>/rules/` para não duplicar.
- Fluxo **ITEM numerado** é global: `ecosystem/canonical/skills/governed-numbered-item-delivery/`; overlay de paths em `profiles/<id>/rules/entregas.md` (ex.: SGD).

**Não** correr `materialize` para publicar skills de profile — o jarbas carrega sob demanda quando o profile está ativo (`playground-profiles`).

---

## Formato — Rule no profile

```
ecosystem/profiles/<profile_id>/rules/
├── README.md          # opcional — índice
├── entregas.md        # exemplo SGD
└── <tema>.md          # markdown; NÃO .mdc na fonte
```

- Regras de produto são **`.md`**, aditivas às rules globais materializadas.
- Documentar no topo: para quem vale, repo fonte da verdade, conflito código vs doc.
- Exemplo: README.md.
