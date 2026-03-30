#!/usr/bin/env python3
"""
🦂 Agentic Harness — Migration & Cleanup Tool
By Solomon Christ | AgenticHarness.io

What this does:
  1. Creates ~/.harness/ global directory structure
  2. Moves SOUL_*.md files from project folders → ~/.harness/souls/
  3. Creates .claude/CLAUDE.md in every Harness project (auto-boot)
  4. Creates AGENTS.md platform boot files
  5. Removes legacy files (LAYER_AGENT_REGISTRY, LAYER_TASK_METADATA, etc.)
  6. Moves loose project files into organized subfolders
  7. Reports what's clean vs what needs manual review

Usage:
  python harness_migrate.py --projects C:\\Users\\info\\OneDrive\\Desktop\\claude-code-projects
  python harness_migrate.py --projects ~/projects --dry-run
"""

import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# ── COLORS ──
def green(s): return f'\033[92m{s}\033[0m'
def amber(s): return f'\033[93m{s}\033[0m'
def red(s):   return f'\033[91m{s}\033[0m'
def dim(s):   return f'\033[2m{s}\033[0m'
def bold(s):  return f'\033[1m{s}\033[0m'

def log_ok(msg):   print(f'  ✅ {green(msg)}')
def log_skip(msg): print(f'  ⏭  {dim(msg)}')
def log_warn(msg): print(f'  ⚠️  {amber(msg)}')
def log_info(msg): print(f'  ℹ️  {msg}')

# ── CONFIG ──
HARNESS_DIR     = Path.home() / '.harness'
SOULS_DIR       = HARNESS_DIR / 'souls'
AGENTS_DIR      = HARNESS_DIR / 'agents'
SKILLS_DIR      = HARNESS_DIR / 'skills'

CLAUDE_MD_CONTENT = """\
# Agentic Harness v11.0
# This project uses Agentic Harness by Solomon Christ — AgenticHarness.io
# Claude Code reads this file automatically on every session start.

Read HARNESS_PROMPT.md and run it before doing anything else.
Detect scenario (A/B/C/D) and execute immediately. No chat first.
"""

AGENTS_MD_CONTENT = """\
# Agentic Harness v11.0 — AgenticHarness.io
Read HARNESS_PROMPT.md and run it before doing anything else.
Detect scenario (A/B/C/D) and execute immediately. No chat first.
"""

GLOBAL_ROSTER_CONTENT = """\
# Agentic Harness — Global Agent Roster
# Updated by each agent on session close.
# One row per active agent — archived agents removed.
| AGENT_ID | Display | Archetype | Project | Score | Tier | Last Active |
|----------|---------|-----------|---------|-------|------|-------------|
"""

# Legacy files to remove (after verifying they're consolidated)
LEGACY_FILES = [
    'LAYER_AGENT_REGISTRY.MD',
    'LAYER_AGENT_REGISTRY.md',
    'LAYER_TASK_METADATA.MD',
    'LAYER_TASK_METADATA.md',
    'REPUTATION.md',
    'MASTER_STATUS.md',
    'TELEGRAM_QUEUE.md',
    'LAYER_HUMAN_QUEUE.MD',
]

# Platform boot files — all get the same content pointing to HARNESS_PROMPT.md
PLATFORM_BOOT_FILES = {
    'AGENTS.md':                          AGENTS_MD_CONTENT,
    'CLAUDE.md':                          AGENTS_MD_CONTENT,
    'GEMINI.md':                          AGENTS_MD_CONTENT,
    'AGENT.md':                           AGENTS_MD_CONTENT,
    '.cursorrules':                       AGENTS_MD_CONTENT,
    '.windsurfrules':                     AGENTS_MD_CONTENT,
    'JULES.md':                           AGENTS_MD_CONTENT,
    'CONVENTIONS.md':                     AGENTS_MD_CONTENT,
}


def step(n, title):
    print(f'\n{bold(f"── STEP {n}: {title}")}')


def setup_global_harness(dry_run=False):
    """Create ~/.harness/ directory structure."""
    step(1, 'Setting up ~/.harness/ global directory')
    for d in [HARNESS_DIR, SOULS_DIR, AGENTS_DIR, SKILLS_DIR]:
        if not d.exists():
            if not dry_run:
                d.mkdir(parents=True, exist_ok=True)
            log_ok(f'Created {d}')
        else:
            log_skip(f'Already exists: {d}')

    # Create global agents roster if missing
    roster = AGENTS_DIR / 'AGENTS.md'
    if not roster.exists():
        if not dry_run:
            roster.write_text(GLOBAL_ROSTER_CONTENT, encoding='utf-8')
        log_ok(f'Created global roster: {roster}')
    else:
        log_skip(f'Roster exists: {roster}')


def discover_harness_projects(projects_root: Path):
    """Find all Harness projects under the given root."""
    found = []
    for hb in projects_root.rglob('LAYER_HEARTBEAT.MD'):
        found.append(hb.parent)
    return sorted(found)


def migrate_soul_files(project_path: Path, dry_run=False):
    """Move SOUL_*.md files from project → ~/.harness/souls/"""
    moved = []
    for soul in project_path.glob('SOUL_*.md'):
        if '_archived' in soul.name:
            log_skip(f'Skipping archived: {soul.name}')
            continue
        dest = SOULS_DIR / soul.name
        if dest.exists():
            log_skip(f'Soul already in global: {soul.name}')
            # Still remove local copy to avoid duplication
            if not dry_run:
                soul.unlink()
            log_ok(f'Removed local duplicate: {soul.name}')
        else:
            if not dry_run:
                shutil.copy2(soul, dest)
                soul.unlink()
            log_ok(f'Moved to global: {soul.name} → {dest}')
            moved.append(soul.name)
    return moved


def create_claude_md(project_path: Path, dry_run=False):
    """Create .claude/CLAUDE.md for auto-boot."""
    claude_dir = project_path / '.claude'
    claude_md  = claude_dir / 'CLAUDE.md'
    if not claude_md.exists():
        if not dry_run:
            claude_dir.mkdir(exist_ok=True)
            claude_md.write_text(CLAUDE_MD_CONTENT, encoding='utf-8')
        log_ok(f'Created .claude/CLAUDE.md')
    else:
        log_skip(f'.claude/CLAUDE.md exists')


def create_platform_boot_files(project_path: Path, dry_run=False):
    """Create all platform boot files if missing."""
    created = []
    for fname, content in PLATFORM_BOOT_FILES.items():
        f = project_path / fname
        if not f.exists():
            if not dry_run:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(content, encoding='utf-8')
            created.append(fname)
    if created:
        log_ok(f'Created platform boot files: {", ".join(created)}')
    else:
        log_skip('All platform boot files exist')

    # Cursor mdc file (special case — needs frontmatter)
    cursor_rules = project_path / '.cursor' / 'rules'
    cursor_mdc   = cursor_rules / 'harness.mdc'
    if not cursor_mdc.exists():
        if not dry_run:
            cursor_rules.mkdir(parents=True, exist_ok=True)
            cursor_mdc.write_text(
                '---\ndescription: Agentic Harness boot\nalwaysApply: true\n---\n'
                'Read HARNESS_PROMPT.md and run it before doing anything else.\n',
                encoding='utf-8'
            )
        log_ok('Created .cursor/rules/harness.mdc')


def remove_legacy_files(project_path: Path, dry_run=False):
    """Remove legacy v10 files that have been consolidated."""
    removed = []
    for fname in LEGACY_FILES:
        f = project_path / fname
        if f.exists():
            if not dry_run:
                # Archive first, then remove
                archive = project_path / 'BACKUP' / f'{fname}.legacy_backup'
                archive.parent.mkdir(exist_ok=True)
                shutil.copy2(f, archive)
                f.unlink()
            removed.append(fname)
            log_ok(f'Removed legacy file: {fname} (backed up to BACKUP/)')
    if not removed:
        log_skip('No legacy files found')


def check_core_files(project_path: Path):
    """Check which of the 10 core files are present."""
    core_files = [
        'AGENT_CARD.md',
        'PROJECT.md',
        'LAYER_ACCESS.MD',
        'LAYER_CONFIG.MD',
        'LAYER_MEMORY.MD',
        'LAYER_TASK_LIST.MD',
        'LAYER_SHARED_TEAM_CONTEXT.MD',
        'LAYER_HEARTBEAT.MD',
        'LAYER_LAST_ITEMS_DONE.MD',
        'HARNESS_PROMPT.md',
    ]
    missing = [f for f in core_files if not (project_path / f).exists()]
    present = [f for f in core_files if (project_path / f).exists()]
    return present, missing


def report_loose_files(project_path: Path):
    """Report files in root that should probably be in subfolders."""
    harness_files = {
        'AGENT_CARD.md', 'PROJECT.md', 'LAYER_ACCESS.MD', 'LAYER_CONFIG.MD',
        'LAYER_MEMORY.MD', 'LAYER_TASK_LIST.MD', 'LAYER_SHARED_TEAM_CONTEXT.MD',
        'LAYER_HEARTBEAT.MD', 'LAYER_LAST_ITEMS_DONE.MD', 'HARNESS_PROMPT.md',
        '.gitattributes', '.gitignore', 'AGENTS.md', 'CLAUDE.md',
        'GEMINI.md', 'AGENT.md', '.cursorrules', '.windsurfrules',
        'JULES.md', 'CONVENTIONS.md', 'package.json', 'package-lock.json',
        'tsconfig.json', 'README.md', 'DEPLOYMENT-COMPLETE.md',
        'DEPLOYMENT-SETUP-SUMMARY.md', 'TOKEN_OPTIMIZATION_SUMMARY.md',
        'TASK_ENGINE_DELIVERY.md', 'URGENT_SOLOMON_YEUNG_DELIVERABLES.md',
    }
    loose = []
    for f in project_path.iterdir():
        if f.is_file() and f.suffix in ('.js', '.ts', '.py', '.sh', '.html', '.css'):
            if f.name not in harness_files:
                loose.append(f.name)
    if loose:
        log_warn(f'{len(loose)} loose project files in root (consider moving to src/ or scripts/):')
        for fname in loose[:8]:
            print(f'       {dim(fname)}')
        if len(loose) > 8:
            print(f'       {dim(f"... and {len(loose)-8} more")}')


def migrate_project(project_path: Path, dry_run=False):
    print(f'\n{"═"*55}')
    print(f'  {bold(project_path.name)}')
    print(f'  {dim(str(project_path))}')
    print(f'{"═"*55}')

    # Check core files
    present, missing = check_core_files(project_path)
    log_info(f'Core files: {len(present)}/10 present')
    if missing:
        log_warn(f'Missing: {", ".join(missing)}')

    # Step A: .claude/CLAUDE.md (most critical)
    create_claude_md(project_path, dry_run)

    # Step B: Platform boot files
    create_platform_boot_files(project_path, dry_run)

    # Step C: Move soul files to global
    moved = migrate_soul_files(project_path, dry_run)

    # Step D: Remove legacy files
    remove_legacy_files(project_path, dry_run)

    # Step E: Report loose files for manual review
    report_loose_files(project_path)


def main():
    parser = argparse.ArgumentParser(
        description='🦂 Agentic Harness Migration Tool v11.0'
    )
    parser.add_argument(
        '--projects',
        default='.',
        help='Path to your projects root folder (default: current directory)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing anything'
    )
    parser.add_argument(
        '--project',
        help='Migrate a single specific project folder (full path)'
    )
    args = parser.parse_args()

    print(bold('\n🦂 AGENTIC HARNESS MIGRATION TOOL v11.0'))
    print(dim('By Solomon Christ | AgenticHarness.io'))
    if args.dry_run:
        print(amber('  DRY RUN — no files will be modified'))

    # Step 1: Global directory setup
    setup_global_harness(args.dry_run)

    # Step 2: Find projects
    if args.project:
        projects = [Path(args.project)]
    else:
        root = Path(args.projects)
        if not root.exists():
            print(red(f'\n❌ Projects path not found: {root}'))
            sys.exit(1)
        projects = discover_harness_projects(root)

    print(f'\n{bold(f"Found {len(projects)} Harness project(s):")}')
    for p in projects:
        print(f'  • {p.name}  {dim(str(p))}')

    # Step 3: Migrate each project
    for proj in projects:
        migrate_project(proj, args.dry_run)

    # Summary
    print(f'\n{"═"*55}')
    print(bold('✅ MIGRATION COMPLETE'))
    print(f'  Soul files → {SOULS_DIR}')
    print(f'  Agent roster → {AGENTS_DIR / "AGENTS.md"}')
    print(f'  .claude/CLAUDE.md created in all projects')
    print()
    print(amber('  NEXT STEPS:'))
    print('  1. Open each project in Claude Code')
    print('  2. It will auto-boot Harness via .claude/CLAUDE.md')
    print('  3. Agent will run Scenario B and print WHO_AM_I card')
    print('  4. If structure looks messy, paste:')
    print(dim('     "Read HARNESS_PROMPT.md. Run Scenario D to clean up."'))
    print()

    if args.dry_run:
        print(amber('  This was a DRY RUN. Run without --dry-run to apply.'))


if __name__ == '__main__':
    main()
