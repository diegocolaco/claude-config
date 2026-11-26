# Anti-padrões, promoção e templates

Leia para conferir erros comuns, escolher o flow de promoção ou partir de um template.

## Anti-padrões

| Errado | Certo |
|--------|--------|
| Editar SKILL.md direto | Editar content.md + `materialize --target all` |
| Materializar só `--target cursor` e esquecer `.claude/` | `materialize --target all`; testar só no Cursor (rule `dual-ide-materialize`) |
| Skill de produto em canonical | `ecosystem/profiles/<id>/skills/` |
| Rule `activation: always` para contexto de um repo | Profile rules ou rule `activation: files` com `globs` do repo |
| content.md de rule com frontmatter `---` | Só corpo; frontmatter vem do `meta.yaml` |
| Shell (`echo`, `sed`) para criar `.md` | Ferramentas Write/edição de arquivo da IDE |
| Promover skill com cópia manual para preset | Flow `promote-skill` / `jarbas.py` (automação) quando for promoção formal |

---

## Promoção e branch (referência)

| Objetivo | Flow / script |
|----------|----------------|
| Materializar IDE | `jarbas.py materialize` |
| Promover skill/conhecimento | `promote-skill.py`, `promote-knowledge` |
| Promover comportamento `.cursor` | `promote-behavior` (via PR) |

Agents **não** reimplementam estes scripts; só editam fonte canonical/profile e acionam CLI quando o usuário pedir promoção.

---

## Template rápido — nova skill (playground)

**meta.yaml:**

```yaml
id: my-workflow
type: skill
scope: agent-requestable
description: "Descrição em terceira pessoa com gatilhos."
targets:
  cursor:
    directory: my-workflow
```

**content.md:** (copiar estrutura da secção "Formato — Skill no playground")

---

## Template rápido — nova rule (playground, agent-requestable)

**meta.yaml:**

```yaml
id: my-agent
type: rule
description: "my-agent — papel em uma linha."
activation: files
globs: ["apps/**/*.ts"]
```

**content.md:** título `# my-agent`, secções Papel, Limites, Quando invocar.

---

## Integração com skills Cursor genéricas

Se o usuário pedir "skill no Cursor" sem contexto jarbas:

1. Aplicar **este** skill (ecossistema TR Jarbas).
2. Para formato Cursor puro (pessoal vs projeto), alinhar com boas práticas: diretório + SKILL.md, `name` + `description`, &lt; 500 linhas.
3. No **playground**, destino final continua sendo **canonical**, não `.cursor/` nem `~/.cursor/skills-cursor/`.
