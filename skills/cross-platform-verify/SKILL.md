---
name: cross-platform-verify
description: Use antes de concluir mudança em tasks, scripts de automação ou shell, para checar CRLF, paths /home/ e @platform.
---
CTX-ID: cross-platform-verify@2

# Cross-platform verify

## Composição Superpowers

Jarbas-specific check on top of the official verification step.

**REQUIRED SUB-SKILL:** Use `superpowers:verification-before-completion` — run the manual checks below and report their real output before claiming the change is cross-platform safe.

## When to use

- After editing VS Code tasks, `tasks.deploy.json`, `.code-workspace`, `ecosystem/automation/`, or `package.json` scripts
- Before jarbas declares delivery complete on non-trivial changes
- When the user mentions Windows, WSL, PowerShell, or Rancher

## Workflow

1. **Identify the changed files** — `git diff --name-only <base>..HEAD` in the task worktree.
2. **Run the manual checks** on those files (Linux/WSL shell):
   ```bash
   grep -c $'\r' <changed-files>
   grep -n '/home/' <changed-files>
   ```
   - Carriage returns: the count must be 0 for every changed file (`.gitattributes` pins LF for the generated and canonical roots).
   - `/home/` paths: allowed only where the path is the point (for example the `--runtime-root` example); otherwise use a relative path or `pathlib`.
   - Tasks and scripts that are Linux-only carry the `@platform: linux-only | windows-only | wsl-bridge` marker.
3. **Interpret findings**
   - `&&` / `||` chain in a PowerShell task → move it to a `linux` block or call `jarbas.py`
   - `/home/...` in a default task → add a `linux` override or `@platform: linux-only`
   - U+FFFD in a file → re-save as UTF-8 (see automation-governance)
   - mixed line endings → report only; do not mass-convert
4. **Windows long paths** — after Write/file edit on deep paths, verify disk content (silent failure on Windows >260 chars).
5. **Windows-only behaviour** — a Linux pass says nothing about Windows. Mark what was not run there as «não verificado».

## Do not

- Suggest `git add --renormalize`, mass CRLF fixes, or global git config
- Treat Linux-only test pass as sufficient for Windows developers

## References

- 99.12-cross-platform.md
- cross-platform-development.md
- ADR-0012
