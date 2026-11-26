# Auxílio de testes — PR #<numero> (ITEM-<codigo>)

**Repositório:** tr/ebs-dominio_sgd  
**Branch:** `<headRefName>` → **Base:** `<baseRefName>`  
**PR:** https://github.com/tr/ebs-dominio_sgd/pull/<numero>  
**ITEM / ficha:** `repo/sgd-cursor-governance/items/<codigo>/item-<codigo>.md`  
**Gerado:** <YYYY-MM-DD> · trace_id: `<trace_id>`

---

## Objetivo do teste manual

Uma frase: o que o revisor/testador deve confirmar após o merge/deploy desta PR.

## Ambiente recomendado

| Opção | Quando usar |
|-------|-------------|
| DEV remoto (`env:dev`) | Padrão para testadores; Keycloak e dados partilhados |
| Slot local (`sgd-env start` + worktree) | Reproduzir bug ou validar antes do deploy |

**URL base:** (preencher conforme ambiente)  
**Perfil de utilizador:** (ex. vendedor comercial, master, …)  
**Pré-requisitos de dados:** (empresa, unidade, negociação de exemplo, …)

---

## Roteiro por menu (passo a passo)

Repetir o padrão da descrição da PR — quem testa não abre o código.

### Menu <Área> > <Módulo> > <Tela ou fluxo>

1. Navegar: …
2. Acção: …
3. **Resultado esperado:** …
4. **Não deve ocorrer:** …

(Copiar uma subsecção por área tocada pela PR.)

---

## Mapa critérios de aceite → prova manual

| CA / ID | O que validar manualmente | Passo no roteiro acima |
|---------|---------------------------|-------------------------|
| CA-… | … | § Menu … |

Se existir `items/<codigo>/evidence/MATRIZ-EVIDENCIAS.md`, alinhar linhas com a coluna «como analisar».

---

## Cobertura automatizada (referência)

| Tipo | Spec / ficheiro | O que já cobre |
|------|-----------------|----------------|
| E2E | `tests/e2e/...` | … |
| Unitário | `apps/.../__tests__/...` | … |
| Dual | `tests/e2e/paridade-dual/...` | … ou «não executado nesta entrega — ver ficha» |

O auxílio manual **complementa** E2E; não substitui gates do ITEM.

---

## Fora de escopo / não testar aqui

- …

---

## Regressões relacionadas

- ITEMs ou retornos (R###) que o testador deve revalidar rapidamente.
