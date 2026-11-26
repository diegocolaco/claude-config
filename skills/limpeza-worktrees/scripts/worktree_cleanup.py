#!/usr/bin/env python3
"""Triagem e limpeza de git worktrees do workspace (~/projetos).

    plan   só lê: classifica cada worktree e imprime JSON, markdown (tabela completa) ou resumo
           (totais e só o que pede atenção: quarentena, em uso no checkout principal, erros).
    apply  executa o plano: remove SAFE, faz prune de PRUNABLE e move DOUBT/STRAY
           para a quarentena; IN_USE, QUARANTINED e OUT_OF_SCOPE ficam intactos.

Veredictos:
    SAFE          limpo, sem operação em andamento, HEAD já em algum remoto -> git worktree remove
    DOUBT         qualquer outra coisa (alteração, commit local, lock manual...) -> quarentena
    IN_USE        processo com cwd dentro ou lock com pid vivo -> não toca
    PRUNABLE      pasta já apagada, só metadado -> git worktree prune
    STRAY         pasta órfã com conteúdo (registro quebrado, ou solta em <workspace>/worktrees/,
                  .worktrees/ ou .claude/worktrees/ de um checkout principal) -> prune + quarentena
    JUNK          pasta órfã vazia ou só com regeneráveis (node_modules, .cache...) -> prune + apaga
    QUARANTINED   já está na quarentena -> não toca
    OUT_OF_SCOPE  fora do workspace -> não toca

Dúvida é motivo de quarentena, nunca de remoção. Lock de pid morto é lock velho (ignorado); se o
git worktree remove recusar um SAFE, o item vai para a quarentena.

Quarentena: <quarentena>/worktrees/<repo>/<nome>-<AAAAMMDD-HHMMSS>, com uma linha por item em
<quarentena>/worktrees/manifest.jsonl (origem, destino, branch, HEAD, motivos). Para devolver:
git -C <checkout-principal> worktree move <destino> <origem>; pasta STRAY volta com mv, e o HEAD
solto dela fica na ref refs/quarentena/<nome>-<data>. Para conferir um DOUBT:
git -C <worktree> status e git log <branch> --not --remotes.

Branches nunca são apagadas. @platform: linux-only (detecção de processos via /proc; WSL incluso).
Sem /proc, todo worktree com lock vira IN_USE por precaução.
"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

STRAY_PARENTS = ('.worktrees', '.claude/worktrees')
# Só caches e dependências que o próprio projeto reinstala; dist/build/coverage podem ser a única cópia.
REGENERABLE = {'node_modules', '__pycache__', '.pytest_cache', '.cache', '.turbo', '.next', '.angular', '.venv',
               '.DS_Store'}
OPERATION_MARKERS = ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'REBASE_HEAD', 'BISECT_LOG',
                     'rebase-merge', 'rebase-apply')
LOCK_PID = re.compile(r'\(pid (\d+)')


def git(cwd, *args, check=True):
    result = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f'git {" ".join(args)} em {cwd}: {result.stderr.strip()}')
    return result


def inside(path, root):
    try:
        return Path(path).resolve().is_relative_to(Path(root).resolve())
    except OSError:
        return False


def default_repos(workspace):
    """Checkouts principais (pasta .git real) em <workspace>/* e <workspace>/repo/*."""
    found = []
    for parent in (workspace, workspace / 'repo'):
        if parent.is_dir():
            found += sorted(p for p in parent.iterdir() if (p / '.git').is_dir())
    return found


def process_cwds():
    """cwd de todos os processos visíveis; None quando não há /proc."""
    proc = Path('/proc')
    if not proc.is_dir():
        return None
    cwds = []
    for entry in proc.iterdir():
        if entry.name.isdigit():
            try:
                cwds.append(Path(os.readlink(entry / 'cwd')))
            except OSError:
                pass
    return cwds


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def parse_worktrees(repo):
    entries, current = [], None
    # -z: campos separados por NUL e sem aspas/escapes (motivo de lock com acento chega intacto).
    for line in git(repo, 'worktree', 'list', '--porcelain', '-z').stdout.split('\0'):
        if line.startswith('worktree '):
            current = {'path': line[len('worktree '):], 'locked': None, 'prunable': False, 'branch': None}
            entries.append(current)
        elif current is None:
            continue
        elif line.startswith('HEAD '):
            current['head'] = line[5:]
        elif line.startswith('branch '):
            current['branch'] = line[len('branch refs/heads/'):]
        elif line == 'detached':
            current['branch'] = None
        elif line.startswith('locked'):
            current['locked'] = line[len('locked '):] if line != 'locked' else ''
        elif line.startswith('prunable'):
            current['prunable'] = True
    return entries[0]['path'] if entries else None, entries[1:]


def classify(repo, entry, cwds, workspace, quarantine, main_checkouts):
    path = Path(entry['path'])
    item = {'repo': str(repo), 'path': str(path), 'branch': entry['branch'], 'head': entry.get('head'),
            'locked': entry['locked'], 'stale_lock': False, 'prune_first': False, 'reasons': [],
            'inside_main_checkout': any(inside(path, m) for m in main_checkouts)}

    def verdict(value, *reasons):
        item['verdict'] = value
        item['reasons'] += list(reasons)
        return item

    if inside(path, quarantine):
        return verdict('QUARANTINED', 'já está na quarentena')
    if not inside(path, workspace):
        return verdict('OUT_OF_SCOPE', 'fora do workspace')
    if not path.exists():
        return verdict('PRUNABLE', 'pasta não existe mais')
    if entry['prunable'] or not (path / '.git').exists():
        orphan = orphan_item(repo, path, cwds)
        orphan['prune_first'] = True
        orphan['reasons'].insert(0, 'registro quebrado (sem .git válido)')
        return orphan
    if cwds is not None and any(inside(c, path) for c in cwds):
        return verdict('IN_USE', 'há processo com diretório de trabalho dentro')
    if entry['locked'] is not None:
        match = LOCK_PID.search(entry['locked'])
        if cwds is None:
            return verdict('IN_USE', 'lock e sem /proc para conferir processos')
        if match and pid_alive(int(match.group(1))):
            return verdict('IN_USE', f'lock de processo vivo: {entry["locked"]}')
        if match:
            item['stale_lock'] = True
        else:
            item['reasons'].append(f'lock manual: {entry["locked"] or "(sem motivo)"}')

    try:
        item['reasons'] += inspect(path)
    except RuntimeError as error:  # HEAD não nascido, git-dir quebrado...: um item estranho não derruba o plano
        item['reasons'].append(f'falha ao inspecionar: {error}')
    return verdict('DOUBT') if item['reasons'] else verdict('SAFE', 'limpo e publicado')


def inspect(path):
    """Motivos para não remover um worktree sem lock e sem processo dentro; lista vazia = seguro."""
    reasons = []
    if git(path, 'status', '--porcelain', '--ignore-submodules=none').stdout.strip():
        reasons.append('alterações não commitadas ou arquivos não rastreados')
    ignored = valuable_ignored(path)
    if ignored:  # git worktree remove apaga ignorados sem avisar (.env, banco local...)
        reasons.append('arquivos ignorados que não são cache: ' + ', '.join(ignored[:5]))
    admin = Path(git(path, 'rev-parse', '--absolute-git-dir').stdout.strip())
    markers = [m for m in OPERATION_MARKERS if (admin / m).exists()]
    if markers:
        reasons.append('operação em andamento: ' + ', '.join(markers))
    remotes = git(path, 'for-each-ref', '--contains', 'HEAD', '--format=%(refname)', 'refs/remotes').stdout.split()
    if not remotes:
        reasons.append('HEAD não está em nenhum remoto (commits só locais)')
    return reasons


def valuable_ignored(path):
    """Arquivos ignorados pelo .gitignore fora das pastas regeneráveis."""
    out = git(path, 'status', '--porcelain', '--ignored=matching', '-z').stdout.split('\0')
    names = [line[3:] for line in out if line.startswith('!! ')]
    return [n for n in names if n.rstrip('/').split('/')[0] not in REGENERABLE
            and n.rstrip('/').split('/')[-1] not in REGENERABLE]


def only_regenerable(path):
    return all(child.name in REGENERABLE for child in path.iterdir())


def orphan_item(repo, path, cwds, inside_main=False):
    item = {'repo': str(repo), 'path': str(path), 'branch': None, 'head': None, 'locked': None,
            'stale_lock': False, 'prune_first': False, 'inside_main_checkout': inside_main, 'reasons': []}
    if cwds is not None and any(inside(c, path) for c in cwds):
        item['verdict'] = 'IN_USE'
        item['reasons'].append('há processo com diretório de trabalho dentro')
    elif only_regenerable(path):
        item['verdict'] = 'JUNK'
        item['reasons'].append('vazia ou só com arquivos regeneráveis')
    else:
        item['verdict'] = 'STRAY'
        item['reasons'].append('pasta órfã com conteúdo')
    return item


def strays(folders, linked, mains, cwds, quarantine):
    """Filhos de `folders` ((pasta, repo, dentro_do_checkout)) sem registro: não estão dentro de um worktree
    registrado nem contêm worktree ou checkout principal."""
    items = []
    for folder, repo, inside_main in folders:
        if not folder.is_dir():
            continue
        for child in sorted(folder.iterdir()):
            if not child.is_dir() or inside(child, quarantine):
                continue
            if any(inside(r, child) for r in linked + mains) or any(inside(child, r) for r in linked):
                continue
            if live_foreign_worktree(child):
                items.append({'repo': str(repo), 'path': str(child), 'branch': None, 'head': None, 'locked': None,
                              'stale_lock': False, 'prune_first': False, 'inside_main_checkout': inside_main,
                              'verdict': 'OUT_OF_SCOPE', 'reasons': ['worktree de um repositório não varrido']})
                continue
            item = orphan_item(repo, child, cwds, inside_main)
            item['reasons'].insert(0, 'sem registro em nenhum repositório')
            items.append(item)
    return items


def live_foreign_worktree(path):
    """Pasta com arquivo .git apontando para um gitdir que existe: worktree de outro repositório."""
    marker = path / '.git'
    if not marker.is_file():
        return False
    text = marker.read_text(encoding='utf-8', errors='replace').strip()
    return text.startswith('gitdir:') and Path(text[len('gitdir:'):].strip()).is_dir()


def plan(workspace, repos=None, quarantine=None, only=None):
    # Absolutos: o git resolve caminho relativo a partir do repositório, não do cwd do script.
    workspace = Path(workspace).expanduser().resolve()
    quarantine = Path(quarantine).expanduser().resolve() if quarantine else workspace / '.tmp'
    repos = [Path(r).expanduser().resolve() for r in repos] if repos else default_repos(workspace)
    cwds = process_cwds()
    parsed = {repo: parse_worktrees(repo) for repo in repos}
    main_checkouts = [Path(main) for main, _ in parsed.values() if main]
    items = []
    for repo, (main, entries) in parsed.items():
        items += [classify(repo, e, cwds, workspace, quarantine, main_checkouts) for e in entries]
    linked = [Path(e['path']) for _, entries in parsed.values() for e in entries]
    folders = [(m / parent, m, True) for m in main_checkouts for parent in STRAY_PARENTS]
    folders.append((workspace / 'worktrees', workspace / 'worktrees', False))
    items += strays(folders, linked, main_checkouts, cwds, quarantine)
    if only:
        wanted = [Path(o).expanduser().resolve() for o in only]
        items = [i for i in items if Path(i['path']).resolve() in wanted]
    return {'workspace': str(workspace), 'quarantine': str(quarantine), 'process_detection': cwds is not None,
            'main_checkouts': [str(m) for m in main_checkouts], 'items': items}


def quarantine_destination(quarantine, item):
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    base = quarantine / 'worktrees' / Path(item['repo']).name
    dest = base / f'{Path(item["path"]).name}-{stamp}'
    n = 2
    while dest.exists():
        dest = base / f'{Path(item["path"]).name}-{stamp}-{n}'
        n += 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def record(quarantine, item, dest):
    manifest = quarantine / 'worktrees' / 'manifest.jsonl'
    line = {'data': datetime.now().isoformat(timespec='seconds'), 'repo': item['repo'], 'origem': item['path'],
            'destino': str(dest), 'branch': item['branch'], 'head': item['head'], 'motivos': item['reasons']}
    with manifest.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(line, ensure_ascii=False) + '\n')


def move_to_quarantine(item, quarantine):
    dest = quarantine_destination(quarantine, item)
    if item['verdict'] == 'STRAY':
        prune_registration(item)
        shutil.move(item['path'], dest)
    else:
        if item['locked'] is not None:
            git(item['repo'], 'worktree', 'unlock', item['path'])
        git(item['repo'], 'worktree', 'move', item['path'], str(dest))
        if item['locked'] is not None and not item['stale_lock']:
            git(item['repo'], 'worktree', 'lock', '--reason', item['locked'], str(dest))
    record(quarantine, item, dest)
    return dest


def prune_registration(item):
    """Registro quebrado: some com o metadado antes de mexer na pasta (o prune ignora pastas vivas)."""
    if not item.get('prune_first'):
        return
    admin = git(item['repo'], 'rev-parse', '--absolute-git-dir').stdout.strip()
    for entry in (Path(admin) / 'worktrees').iterdir():
        gitdir = entry / 'gitdir'
        if gitdir.is_file() and Path(gitdir.read_text().strip()).parent.resolve() == Path(item['path']).resolve():
            keep_head(item, entry)
            shutil.rmtree(entry)


def keep_head(item, admin_entry):
    """Antes de apagar o metadado: anota HEAD/branch e, se o HEAD estava solto, prende o commit numa ref
    refs/quarentena/... para o gc não levá-lo."""
    head_file = admin_entry / 'HEAD'
    head = head_file.read_text().strip() if head_file.is_file() else ''
    if head.startswith('ref: refs/heads/'):
        item['branch'] = head[len('ref: refs/heads/'):]
        item['head'] = git(item['repo'], 'rev-parse', '--verify', '-q', item['branch'], check=False).stdout.strip() or None
    elif head and git(item['repo'], 'cat-file', '-e', f'{head}^{{commit}}', check=False).returncode == 0:
        item['head'] = head
        ref = f'refs/quarentena/{Path(item["path"]).name}-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
        git(item['repo'], 'update-ref', ref, head)
        item['reasons'] = item['reasons'] + [f'HEAD solto preservado em {ref}']


def apply(result, quarantine=None):
    quarantine = Path(quarantine or result['quarantine']).expanduser()
    actions, pruned = [], set()
    for item in result['items']:
        action = {'path': item['path'], 'verdict': item['verdict'], 'reasons': item['reasons']}
        try:
            if item['verdict'] == 'SAFE':
                if item['locked'] is not None:
                    git(item['repo'], 'worktree', 'unlock', item['path'])
                removed = git(item['repo'], 'worktree', 'remove', item['path'], check=False)
                if removed.returncode == 0:
                    action['action'] = 'removed'
                else:  # o git recusou (arquivo surgiu, submódulo...): na dúvida, quarentena
                    action['reasons'] = item['reasons'] + [f'git worktree remove recusou: {removed.stderr.strip()}']
                    action['action'] = 'moved'
                    action['destination'] = str(move_to_quarantine({**item, 'reasons': action['reasons'],
                                                                    'locked': None}, quarantine))
            elif item['verdict'] in ('DOUBT', 'STRAY'):
                action['action'] = 'moved'
                action['destination'] = str(move_to_quarantine(item, quarantine))
            elif item['verdict'] == 'JUNK':
                prune_registration(item)
                shutil.rmtree(item['path'])
                action['action'] = 'deleted'
            elif item['verdict'] == 'PRUNABLE':
                if item['repo'] not in pruned:
                    git(item['repo'], 'worktree', 'prune')
                    pruned.add(item['repo'])
                action['action'] = 'pruned'
            else:
                action['action'] = 'skipped'
        except (RuntimeError, OSError) as error:
            action['action'] = 'error'
            action['error'] = str(error)
        actions.append(action)
    remove_empty_parents(result.get('main_checkouts', []))
    return {**result, 'actions': actions}


def remove_empty_parents(main_checkouts):
    """Pastas .worktrees/ e .claude/worktrees/ que ficaram vazias no checkout principal também saem."""
    for main in main_checkouts:
        for parent in STRAY_PARENTS:
            folder = Path(main) / parent
            if folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()


def markdown(result):
    rows = result.get('actions') or result['items']
    lines = ['| worktree | branch | veredicto | ação | motivos |', '|---|---|---|---|---|']
    branches = {i['path']: i['branch'] for i in result['items']}
    for row in rows:
        target = row.get('destination') or row.get('error') or ''
        action = row.get('action', 'plano') + (f' → {target}' if target else '')
        lines.append(f'| {row["path"]} | {branches.get(row["path"]) or "-"} | {row["verdict"]} | {action} '
                     f'| {"; ".join(row["reasons"])} |')
    violations = [i['path'] for i in result['items'] if i['inside_main_checkout'] and i['verdict'] == 'IN_USE']
    if violations:
        lines.append('\nAinda dentro de checkout principal (em uso, tratar depois): ' + ', '.join(violations))
    if not result['process_detection']:
        lines.append('\nSem /proc: detecção de processos indisponível.')
    return '\n'.join(lines)


ACTION_LABELS = {'removed': 'removidos', 'moved': 'quarentena', 'pruned': 'prune', 'deleted': 'lixo apagado',
                 'skipped': 'intocados', 'error': 'erros'}


def summary(result):
    """Totais e uma linha por item que pede atenção; os removidos com segurança viram só um número."""
    items, actions = result['items'], result.get('actions')
    root = result['workspace'].rstrip('/') + '/'

    def short(path):  # caminhos relativos ao workspace: metade do texto some
        return path[len(root):] if path.startswith(root) else path

    if actions:
        counts = {}
        for a in actions:
            counts[a['action']] = counts.get(a['action'], 0) + 1
        lines = [f'workspace: {root}']
        lines += [' · '.join(f'{ACTION_LABELS[k]}: {v}' for k, v in counts.items())]
        lines += [f'- quarentena: {short(a["path"])} → {short(a["destination"])} ({"; ".join(a["reasons"])})'
                  for a in actions if a['action'] == 'moved']
        lines += [f'- erro: {short(a["path"])}: {a["error"]}' for a in actions if a['action'] == 'error']
    else:
        counts = {}
        for i in items:
            counts[i['verdict']] = counts.get(i['verdict'], 0) + 1
        lines = [f'workspace: {root}', ' · '.join(f'{k}: {v}' for k, v in counts.items())]
        lines += [f'- {i["verdict"]}: {short(i["path"])} ({"; ".join(i["reasons"])})'
                  for i in items if i['verdict'] in ('DOUBT', 'STRAY')]
    lines += [f'- em uso dentro de checkout principal: {short(i["path"])} ({"; ".join(i["reasons"])})'
              for i in items if i['inside_main_checkout'] and i['verdict'] == 'IN_USE']
    if not result['process_detection']:
        lines.append('- sem /proc: detecção de processos indisponível')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('plan', 'apply'))
    parser.add_argument('--workspace', default='~/projetos', help='raiz do workspace (padrão ~/projetos)')
    parser.add_argument('--repo', action='append', help='checkout principal; repetível (padrão: autodetecção)')
    parser.add_argument('--quarantine', help='pasta de quarentena (padrão <workspace>/.tmp)')
    parser.add_argument('--only', action='append', help='limita a este worktree; repetível')
    parser.add_argument('--format', choices=('json', 'markdown', 'resumo'), default='json')
    args = parser.parse_args(argv)
    result = plan(args.workspace, args.repo, args.quarantine, args.only)
    if args.command == 'apply':
        result = apply(result)
    render = {'markdown': markdown, 'resumo': summary}.get(args.format)
    print(render(result) if render else json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if any(a.get('action') == 'error' for a in result.get('actions', [])) else 0


if __name__ == '__main__':
    sys.exit(main())
