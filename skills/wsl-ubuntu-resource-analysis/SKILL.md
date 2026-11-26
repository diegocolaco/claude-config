---
name: wsl-ubuntu-resource-analysis
description: Use quando pedirem análise geral de recursos do Ubuntu/WSL (CPU, memória, swap, disco, Docker).
---
CTX-ID: wsl-ubuntu-resource-analysis@2

# Analise de recursos — Ubuntu no WSL

## Composição Superpowers

Coleta jarbas de recursos do WSL; gargalo é problema de performance, logo segue o diagnóstico do Superpowers.

**REQUIRED BACKGROUND:** You MUST understand `superpowers:systematic-debugging` — evidência antes de apontar causa ou ação.

## Quando usar

- Pedido de **analise geral** ou **panorama** de recursos no WSL/Ubuntu
- Lentidao local (build, Docker, SGD, varios apps Node/Vite)
- Suspeita de falta de RAM, swap, disco cheio ou CPU saturada
- Antes/depois de subir stacks pesados (`sgd-env`, Docker compose)

## Principios

1. **Somente leitura** — nao matar processos, nao alterar limites WSL, nao `apt install` sem pedido explicito.
2. **Playground primeiro** — preferir export Glances do repo (metricas consistentes + PII redigida).
3. **WSL nao e bare metal** — rede e alguns contadores podem parecer estranhos; priorize **tendencia** e **limites** (RAM livre, % disco, load vs cores).
4. Responder no **idioma do usuario**; metricas e nomes de comando podem ficar em ingles.

## Fluxo (checklist)

```
- [ ] 1. Confirmar ambiente WSL/Linux
- [ ] 2. Coletar snapshot (Glances export OU comandos nativos)
- [ ] 3. Interpretar vs limiares
- [ ] 4. Entregar relatorio estruturado + acoes sugeridas (nao destrutivas)
```

### 1. Confirmar ambiente

Executar (raiz do playground ou qualquer cwd):

```bash
uname -a
grep -i microsoft /proc/version 2>/dev/null || true
nproc
```

Se nao for Linux/WSL, informar que a skill targeta Ubuntu no WSL e adaptar o que for possivel.

### 2. Coleta — caminho preferido (Glances)

Na **raiz do playground** `TaxProf_brtap-integration-playground`:

```bash
bash ecosystem/automation/glances/glances-env.sh status
bash ecosystem/automation/glances/glances-env.sh export --samples 1
```

`env-perf` entrega veredito **OK / Atencao / Critico** e label de rapidez (`rapido`, `moderado`, `lento`); use `--json` para integracao.

Para gargalos **intermitentes** (build, start de varios apps):

```bash
bash ecosystem/automation/glances/glances-env.sh export --samples 15 --interval 2
```

Ler e interpretar:

| Artefato | Caminho |
|----------|---------|
| Bundle JSON | `.tmp/glances-export/latest/metrics-bundle.json` |
| Brief | agent-brief.md |

Web UI (humano): http://127.0.0.1:61208/ — ver manual-glances-monitoramento-linux.md.

Se Glances falhar (Docker indisponivel), seguir **coleta nativa** abaixo e registrar pendencia.

### 2b. Coleta nativa (fallback ou complemento)

Executar em paralelo quando util:

```bash
uptime
free -h
swapon --show 2>/dev/null || true
df -hT
df -i
ss -s 2>/dev/null || true
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || true
docker stats --no-stream 2>/dev/null || true
ps aux --sort=-%mem | head -n 15
ps aux --sort=-%cpu | head -n 15
```

Opcional (I/O):

```bash
iostat -xz 1 3 2>/dev/null || true
```

Nao usar `rm`, `kill`, `docker system prune`, nem alterar `.wslconfig` automaticamente.

### 3. Limiares (dev local — alinhado ao manual Glances)

| Recurso | Alerta | Critico (escalar ao humano) |
|---------|--------|-----------------------------|
| Load (1/5/15 min) | load medio > **2x** `nproc` por varios minutos | load >> cores + apps irresponsivos |
| RAM | swap em uso **constante**; available muito baixo | OOM / processos morrendo |
| Disco `/` ou `/mnt` | **> 85%** | **> 92%** |
| Inodes | **> 85%** | **> 92%** |
| Docker | container `Restarting` | varios containers em loop |
| Processos dev | Node/Java/Vite no topo de CPU/RAM sem carga explicada | — |

No WSL2, `%`/rede pode oscilar; cruzar **free**, **df**, **top processos** e **docker stats**.

### 4. Relatorio — template obrigatorio

Entregar ao usuario:

```markdown
# Analise de recursos — Ubuntu/WSL

## Resumo executivo
[1–3 frases: saude geral + principal risco]

## Ambiente
- Kernel / WSL: …
- CPUs (`nproc`): …
- Fonte dos dados: Glances export | comandos nativos | ambos

## CPU e carga
- Load: …
- Interpretacao: …

## Memoria e swap
- RAM / available / swap: …
- Interpretacao: …

## Disco e inodes
- Particoes relevantes (`/`, `/mnt`, bind do Windows): …
- Interpretacao: …

## Rede (WSL)
- Nota WSL se aplicavel: …

## Processos (top consumidores)
- CPU: …
- RAM: …

## Docker (se aplicavel)
- Containers / stats: …

## Veredito
| Area | Status (OK / Atencao / Critico) | Evidencia |
|------|----------------------------------|-----------|
| CPU  | … | … |
| RAM  | … | … |
| Disco| … | … |
| Docker | … | … |

## Acoes sugeridas (nao destrutivas)
1. …
2. …

## Pendencias
- O que nao foi possivel medir e por que

## Referencias
- manual-glances-monitoramento-linux.md
- Export: `.tmp/glances-export/latest/` (se usado)
```

Marcar **Atencao/Critico** apenas com numeros citados; nao inventar metricas se a coleta falhou.

## Integracao com desenvolvimento SGD

Se o contexto for SGD local (`jarbas.py sgd-env`):

- Mencionar se Glances **DOCKER** / **PROCESS** mostram varios Node/Vite
- Sugerir amostragem `--samples 15` durante `start` ou build, nao so snapshot idle
- Nao parar apps do usuario sem pedido

## Nao fazer

- Expor tokens, e-mails ou paths com credenciais nos logs (export Glances ja redige padroes comuns)
- Recomendar `git` destrutivo, prune Docker agressivo ou editar `.wslconfig` sem confirmacao
- Declarar "ambiente saudavel" sem ter executado pelo menos uma coleta

## Referencias

- Manual: manual-glances-monitoramento-linux.md (raiz do playground)
- Scripts: `ecosystem/automation/glances/glances-env.sh`, `export-metrics.py`
- Run Tasks: `.vscode/tasks.json` (prefixo **Glances:**)
