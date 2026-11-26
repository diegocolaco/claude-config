# Detalhes do SGD

- **Repositórios:** pelo contrato `ecosystem/ecosystem-config.yaml`.
  - Produto: alias `ebs-dominio_sgd`.
  - Protótipo: alias `sgd-novo-lovable`. Hoje é o Ant Design Pro em repositório Git público (`reference-version.json` kind `public-repository`); o nome da pasta é histórico.
- **Rotas do produto:** `apps/web/src/app.tsx` (navegação plana «Módulos»; não há `menuKey`).
- **Rotas do protótipo:** `config/routes.ts`.
- **Gaps conhecidos:** seção «Fora do relato» das fichas de ITEM, que não têm caminho fixo. Procure; se não achar, registre «não encontrado» como `NAO_INVESTIGADO`, com a busca usada.
- **`def-audit-gate`:** o relatório, se existir, fica em `.tmp/<session-id>/def-audit-report.md`. Leia como pista. Este ciclo não abre DEF-AUDIT nem PRE.
- **Rules Lovable** (`sgd-novo-lovable-proto`, `sgd-novo-proto-diff-revisao`): valem só para importar export Lovable (zip, `rsync`, `feature/v00N`). Se estiverem carregadas e contradisserem esta skill, pergunte ao Diego. Caminho citado nelas que não existe (`VERSION.yaml`, `newsgd-1/`) é registrado, não recriado.
- **Biblioteca de componentes:** Ant Design agora, Dom DS depois, se vier. O Dom DS é privado e fica fora do alcance até o pacote aparecer no `package.json` do produto; antes disso, as rules e skills do Dom DS não se aplicam. Componente que a biblioteca não tem: o agente pode sugerir, e quem decide é o Diego (detalhes em [prototype-parity-verification/references/decisoes-e-planos.md](../../prototype-parity-verification/references/decisoes-e-planos.md)).
- **Regra geral:** «O máximo possivel igual dentro do possível», inclusive os textos, que ficam como no protótipo.
- **Sem subir para comparar aparência, sem prints:** o protótipo nunca sobe, e nada sobe só para comparar aparência, que se confere pelo código (componente, props e tema, a partir do `inventario` e do catálogo). Os testes E2E da aplicação nova seguem normais, como `prototype-parity-verification` manda.
