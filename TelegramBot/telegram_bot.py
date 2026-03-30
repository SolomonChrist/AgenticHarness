#!/usr/bin/env python3
"""
🦂 Agentic Harness — Personal Executive Assistant Bot
By Solomon Christ | AgenticHarness.io

Your 24/7 AI Executive Assistant via Telegram.
Runs on YOUR machine. Watches ALL your Harness projects.
Routes tasks to the right agents. Keeps you informed anywhere.

SETUP (5 minutes):
  1. pip install requests python-dotenv
  2. Copy .env.telegram.template → .env.telegram
  3. Fill in your BOT_TOKEN and TELEGRAM_USER_ID
  4. python telegram_bot.py

WHAT IT DOES:
  - Polls LAYER files every 60s, forwards 📨 notifications to your phone
  - Accepts natural language: "add task to SecondBrain: fix the login bug"
  - Shows project status, task queues, agent roster on demand
  - Lets you add tasks, wake agents, check progress — from anywhere
  - Routes requests to right project when you have multiple
"""

import os
import re
import sys
import json
import time
import signal
import logging
import threading
from pathlib import Path
from datetime import datetime

try:
    import requests
    from dotenv import load_dotenv
except ImportError:
    print('❌ Missing dependencies. Run:  pip install requests python-dotenv')
    sys.exit(1)

# ── LOAD CONFIG ───────────────────────────────────────────────────────────────
HERE = Path(__file__).parent
load_dotenv(HERE / '.env.telegram')

BOT_TOKEN        = os.getenv('TELEGRAM_BOT_TOKEN', '')
ALLOWED_USER_IDS = [int(x.strip()) for x in os.getenv('TELEGRAM_ALLOWED_USER_IDS', '').split(',')
                    if x.strip().isdigit()]
PROJECTS_PATH    = Path(os.getenv('HARNESS_PROJECTS_PATH', str(HERE.parent)))
POLL_INTERVAL    = int(os.getenv('POLL_INTERVAL_SECONDS', '60'))
BOT_NAME         = os.getenv('BOT_NAME', 'Harness Assistant')
OWNER_NAME       = os.getenv('OWNER_NAME', 'there')

if not BOT_TOKEN:
    print('❌  TELEGRAM_BOT_TOKEN not set.')
    print('    Copy .env.telegram.template → .env.telegram and fill it in.')
    sys.exit(1)
if not ALLOWED_USER_IDS:
    print('❌  TELEGRAM_ALLOWED_USER_IDS not set. See .env.telegram.template.')
    sys.exit(1)

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger('harness-bot')

# ── PERSISTENT STATE ──────────────────────────────────────────────────────────
DATA_DIR       = HERE / 'data'
DATA_DIR.mkdir(exist_ok=True)
NOTIFIED_FILE  = DATA_DIR / 'notified_entries.json'
last_update_id = 0
running        = True
notified_ids: set = set()

def load_state():
    global notified_ids
    try:
        if NOTIFIED_FILE.exists():
            notified_ids = set(json.loads(NOTIFIED_FILE.read_text()))
    except: notified_ids = set()

def save_state():
    try:
        NOTIFIED_FILE.write_text(json.dumps(list(notified_ids)[-500:]))
    except: pass

# ── TELEGRAM API ──────────────────────────────────────────────────────────────
API = f'https://api.telegram.org/bot{BOT_TOKEN}'

def tg(method: str, **kwargs) -> dict:
    try:
        r = requests.post(f'{API}/{method}', json=kwargs, timeout=15)
        return r.json()
    except Exception as e:
        log.error(f'API error ({method}): {e}')
        return {'ok': False}

def send(chat_id: int, text: str):
    """Send message, splitting at 4000 chars if needed."""
    for chunk in [text[i:i+4000] for i in range(0, max(len(text),1), 4000)]:
        tg('sendMessage', chat_id=chat_id, text=chunk, parse_mode='HTML')

def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USER_IDS

# ── PROJECT HELPERS ───────────────────────────────────────────────────────────
def discover_projects() -> list:
    return sorted([p.parent for p in PROJECTS_PATH.rglob('LAYER_HEARTBEAT.MD')])

def rf(path: Path, filename: str) -> str:
    f = path / filename
    try: return f.read_text(encoding='utf-8', errors='ignore') if f.exists() else ''
    except: return ''

ARCH_EMOJI = {'Builder':'🏗','Scout':'🔍','Guardian':'🛡','Sage':'🧠',
              'Hustler':'⚡','Creator':'🎨','Fixer':'🔧','Diplomat':'🤝'}

def read_soul(agent_id: str, project_path: Path = None) -> dict:
    soul = ''
    for sp in [project_path, Path.home() / '.harness' / 'souls'] if project_path else [Path.home() / '.harness' / 'souls']:
        if sp is None: continue
        sf = sp / f'SOUL_{agent_id}.md'
        if sf.exists(): soul = sf.read_text(encoding='utf-8', errors='ignore'); break
    arch  = re.search(r'Archetype:\s*([^\n|,]+)', soul)
    disp  = re.search(r'Display Name:\s*([^\n|,]+)', soul)
    score = re.search(r'(?:Score|Reputation)[^:]*:\s*(\d+)', soul)
    catch = re.search(r'Catchphrase:\s*"?([^\n"]+)"?', soul)
    return {
        'archetype': arch.group(1).strip().split()[0] if arch else 'Builder',
        'display':   disp.group(1).strip() if disp else agent_id.split('-')[0],
        'score':     score.group(1) if score else '0',
        'catchphrase': catch.group(1).strip()[:50] if catch else '',
    }

def get_project_agents(proj: Path) -> list:
    agents = []
    cfg = rf(proj, 'LAYER_CONFIG.MD')
    for line in cfg.splitlines():
        m = re.search(r'\|\s*([A-Za-z][A-Za-z0-9_\-]+-\d+[A-Za-z0-9_\-]*)\s*\|', line)
        if m:
            aid = m.group(1).strip()
            if aid and '---' not in aid and aid.upper() != 'AGENT_ID':
                agents.append(aid)
    # Also scan soul files
    for sp in [proj, Path.home() / '.harness' / 'souls']:
        if sp.exists():
            for sf in sp.glob('SOUL_*.md'):
                aid = sf.stem.replace('SOUL_', '')
                if '_archived' not in aid and aid not in agents:
                    agents.append(aid)
    return agents

def get_project_status(proj: Path) -> dict:
    hb  = rf(proj, 'LAYER_HEARTBEAT.MD')
    tl  = rf(proj, 'LAYER_TASK_LIST.MD')
    log_txt = rf(proj, 'LAYER_LAST_ITEMS_DONE.MD')

    status = 'OFFLINE'
    for line in hb.splitlines():
        if any(k in line for k in ('SESSION_OPEN','ACTIVE')): status = 'ACTIVE'
        if 'STANDBY' in line: status = 'STANDBY'
        if any(k in line for k in ('SESSION_CLOSE','HEARTBEAT CLOSE')): status = 'OFFLINE'
        if 'BLOCKED' in line: status = 'BLOCKED'

    counts = {'todo':0,'inprog':0,'done':0,'blocked':0,'human':0}
    for line in tl.splitlines():
        l = line.strip()
        if l.startswith('[→]'): counts['inprog'] += 1
        elif l.startswith('[✓]'): counts['done'] += 1
        elif l.startswith('[✗]'): counts['blocked'] += 1
        elif l.startswith('[⏸ HUMAN]'): counts['human'] += 1
        elif l.startswith('[ ]'): counts['todo'] += 1

    last = ''
    for line in log_txt.splitlines():
        if line.strip() and not line.startswith('#'):
            m = re.search(r'\[[^\]]+\] \[[^\]]+\] (.+)', line)
            if m: last = re.sub(r'^[^\w]+\s*','',m.group(1))[:70]
            break

    return {'name': proj.name, 'status': status, 'tasks': counts,
            'agents': get_project_agents(proj), 'last': last}

# ── NOTIFICATION POLLER ───────────────────────────────────────────────────────
def poll_and_notify():
    log.info(f'📡 Notification poller started — every {POLL_INTERVAL}s')
    while running:
        try:
            new = []
            for proj in discover_projects():
                log_txt = rf(proj, 'LAYER_LAST_ITEMS_DONE.MD')
                for line in log_txt.splitlines():
                    if '📨' not in line or line.startswith('#'): continue
                    entry_id = f'{proj.name}::{line[:100]}'
                    if entry_id in notified_ids: continue
                    m = re.search(r'\[(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?)\] \[([^\]]+)\] 📨 (.+)', line)
                    if m:
                        new.append({'id': entry_id, 'ts': m.group(1),
                                    'agent': m.group(2), 'msg': m.group(3)[:200],
                                    'project': proj.name})
            for n in new:
                msg = (f'📨 <b>{n["agent"]}</b> · {n["project"]}\n'
                       f'{n["msg"]}\n<code>{n["ts"]}</code>')
                for uid in ALLOWED_USER_IDS: send(uid, msg)
                notified_ids.add(n['id'])
                log.info(f'📨 Forwarded: {n["agent"]} — {n["msg"][:50]}')
            if new: save_state()
        except Exception as e:
            log.error(f'Poller error: {e}')
        time.sleep(POLL_INTERVAL)

# ── COMMAND HANDLERS ──────────────────────────────────────────────────────────
def cmd_start(chat_id: int) -> str:
    projects = discover_projects()
    agents_total = sum(len(get_project_agents(p)) for p in projects)
    return (f'👋 Hello {OWNER_NAME}! I\'m <b>{BOT_NAME}</b>, your Personal Executive Assistant.\n\n'
            f'Watching <b>{len(projects)} project(s)</b> · <b>{agents_total} agent(s)</b>\n\n'
            f'<b>Commands:</b>\n'
            f'/projects — All project status\n'
            f'/agents — Agent roster + summon commands\n'
            f'/tasks — Task queue overview\n'
            f'/tasks [project] — Tasks for one project\n'
            f'/add [project] | [task] | [PRIORITY] — Queue a task\n'
            f'/wake [project] — Get wake commands for offline agents\n'
            f'/status — Full system overview\n\n'
            f'Or just talk to me naturally:\n'
            f'<i>"Add a HIGH priority task to SecondBrain to fix the auth bug"</i>\n'
            f'<i>"What\'s the status on the CPA project?"</i>\n'
            f'<i>"Who are my agents?"</i>')

def cmd_projects(chat_id: int) -> str:
    projects = discover_projects()
    if not projects:
        return ('❌ No Harness projects found.\n'
                f'Check HARNESS_PROJECTS_PATH in .env.telegram\n'
                f'Currently looking in: <code>{PROJECTS_PATH}</code>')
    icons = {'ACTIVE':'🟢','WORKING':'🟢','STANDBY':'🟡','OFFLINE':'⚫','BLOCKED':'🔴','COMPLETE':'✅'}
    lines = [f'<b>📁 Projects ({len(projects)})</b>\n']
    for proj in projects:
        s = get_project_status(proj)
        icon = icons.get(s['status'], '⚫')
        t = s['tasks']
        tstr = f"{t['todo']} TODO"
        if t['inprog']: tstr += f" · {t['inprog']} ▶"
        if t['done']: tstr += f" · {t['done']} ✓"
        if t['blocked']: tstr += f" · {t['blocked']} ✗"
        if t['human']: tstr += f" · {t['human']} ⏸HUMAN"
        a_names = ', '.join(s['agents'][:2]) or 'none'
        if len(s['agents']) > 2: a_names += f'+{len(s["agents"])-2}'
        lines.append(f'{icon} <b>{s["name"]}</b> · {s["status"]}')
        lines.append(f'   {tstr} · {a_names}')
        if s['last']: lines.append(f'   <i>{s["last"][:65]}</i>')
        lines.append('')
    return '\n'.join(lines)

def cmd_agents(chat_id: int) -> str:
    all_agents = []
    for proj in discover_projects():
        s = get_project_status(proj)
        for aid in s['agents']:
            soul = read_soul(aid, proj)
            all_agents.append({**soul, 'id': aid, 'project': s['name'], 'proj_status': s['status']})
    if not all_agents:
        return ('👻 No agents found yet.\n\n'
                'Open Claude Code in any project folder and paste:\n'
                '<code>Read HARNESS_PROMPT.md and run it.</code>\n\n'
                'The agent will register itself and appear here.')
    lines = [f'<b>🤖 Agents ({len(all_agents)})</b>\n']
    for a in all_agents:
        emoji = ARCH_EMOJI.get(a['archetype'], '🤖')
        online = a['proj_status'] in ('ACTIVE','WORKING')
        dot = '🟢' if online else '⚫'
        lines.append(f'{dot} <b>{a["display"]}</b> ({a["id"]})')
        lines.append(f'   {emoji} {a["archetype"]} · {a["project"]} · {a["score"]}pts')
        if a['catchphrase']: lines.append(f'   <i>"{a["catchphrase"]}"</i>')
        lines.append(f'   Summon: <code>You are {a["id"]}. Scenario B.</code>')
        lines.append('')
    return '\n'.join(lines)

def cmd_tasks(chat_id: int, proj_filter: str = '') -> str:
    projects = discover_projects()
    if proj_filter:
        projects = [p for p in projects if proj_filter.lower() in p.name.lower()]
    if not projects:
        return f'❌ No project matching "{proj_filter}"'
    lines = ['<b>📋 Task Queues</b>\n']
    for proj in projects:
        tl = rf(proj, 'LAYER_TASK_LIST.MD')
        active, human, blocked, todos = [], [], [], []
        for line in tl.splitlines():
            l = line.strip()
            if not l or l.startswith('#'): continue
            clean = re.sub(r'^\[.*?\]\s*','',l).strip()
            clean = re.sub(r'\s*[⟵(].*$','',clean).strip()[:70]
            if l.startswith('[→]'): active.append(clean)
            elif l.startswith('[⏸ HUMAN]'): human.append(clean)
            elif l.startswith('[✗]'): blocked.append(clean)
            elif l.startswith('[ ]'): todos.append(clean)
        lines.append(f'<b>{proj.name}</b>')
        for t in active[:3]: lines.append(f'  ▶ {t}')
        for t in human[:2]:  lines.append(f'  ⏸ HUMAN: {t}')
        for t in blocked[:2]:lines.append(f'  ✗ {t}')
        for t in todos[:5]:  lines.append(f'  □ {t}')
        if len(todos) > 5: lines.append(f'  ... +{len(todos)-5} more')
        if not any([active,human,blocked,todos]): lines.append('  (empty)')
        lines.append('')
    return '\n'.join(lines)

def cmd_add(chat_id: int, args: str) -> str:
    parts = [p.strip() for p in args.split('|')]
    if len(parts) < 2:
        return ('❌ Format: <code>/add Project | Task description | PRIORITY</code>\n\n'
                'Example:\n<code>/add ai-SecondBrain | Fix auth bug | HIGH</code>')
    proj_hint = parts[0]
    task_text = parts[1]
    priority  = (parts[2].upper() if len(parts) > 2 else 'MED')
    if priority not in ('CRITICAL','HIGH','MED','LOW'): priority = 'MED'

    projects = discover_projects()
    matches  = [p for p in projects if proj_hint.lower() in p.name.lower()]
    if not matches:
        return f'❌ No project matching "{proj_hint}"\n\nProjects: ' + ', '.join(p.name for p in projects)

    proj = matches[0]
    ts   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'\n[ ] {priority} — {task_text}  ⟵ added via Telegram {ts}'

    # Write task
    tf = proj / 'LAYER_TASK_LIST.MD'
    try:
        existing = tf.read_text(encoding='utf-8', errors='ignore') if tf.exists() else '# LAYER_TASK_LIST.MD\n'
        tf.write_text(existing + line, encoding='utf-8')
    except Exception as e:
        return f'❌ Write failed: {e}'

    # Write 📨 notify to log
    lf = proj / 'LAYER_LAST_ITEMS_DONE.MD'
    notify = f'\n[{ts}] [TELEGRAM-EA] 📨 NOTIFY — New {priority} task: {task_text[:80]} | TYPE:ALERT'
    try:
        existing_log = lf.read_text(encoding='utf-8', errors='ignore') if lf.exists() else ''
        lines = existing_log.split('\n')
        idx = next((i for i,l in enumerate(lines) if l.strip() and not l.startswith('#')), len(lines))
        lines.insert(idx, notify.strip())
        lf.write_text('\n'.join(lines), encoding='utf-8')
    except: pass

    # Write wake file
    try:
        (proj / '.harness_wake').write_text(
            f'WAKE_REQUEST\nts: {ts}\nfrom: Telegram EA\n'
            f'reason: New {priority} task — {task_text[:100]}\n'
            f'instruction: Read HARNESS_PROMPT.md and run it. Scenario B.\n',
            encoding='utf-8')
    except: pass

    agents = get_project_agents(proj)
    agent_str = agents[0] if agents else '[AGENT_ID]'
    return (f'✅ <b>{priority} task queued in {proj.name}</b>\n\n'
            f'📋 {task_text}\n\n'
            f'To wake agent now — open Claude Code and paste:\n'
            f'<code>You are {agent_str}. Scenario B.</code>')

def cmd_wake(chat_id: int, proj_filter: str = '') -> str:
    projects = discover_projects()
    if proj_filter:
        projects = [p for p in projects if proj_filter.lower() in p.name.lower()]
    if not projects: return f'❌ No project matching "{proj_filter}"'
    lines = ['<b>🔔 How to Wake Agents</b>\n',
             'Open Claude Code in the project folder and paste:\n']
    for proj in projects[:6]:
        agents = get_project_agents(proj)
        agent_str = agents[0] if agents else '[AGENT_ID]'
        lines.append(f'<b>{proj.name}</b>')
        lines.append(f'<code>You are {agent_str}. Scenario B.</code>\n')
    return '\n'.join(lines)

def cmd_status(chat_id: int) -> str:
    projects = discover_projects()
    active = sum(1 for p in projects if get_project_status(p)['status'] in ('ACTIVE','WORKING'))
    total_todo = total_done = total_agents = 0
    for p in projects:
        s = get_project_status(p)
        total_todo += s['tasks']['todo']
        total_done += s['tasks']['done']
        total_agents += len(s['agents'])
    return (f'<b>🦂 Agentic Harness — Status</b>\n'
            f'<code>{datetime.now().strftime("%Y-%m-%d %H:%M")}</code>\n\n'
            f'Projects: {len(projects)} · {active} active\n'
            f'Agents:   {total_agents} registered\n'
            f'Tasks:    {total_todo} pending · {total_done} done\n\n'
            f'Watching: <code>{PROJECTS_PATH}</code>\n'
            f'Polling:  every {POLL_INTERVAL}s\n\n'
            f'/projects · /agents · /tasks · /add · /wake')

def route_natural(chat_id: int, text: str) -> str:
    t = text.lower()
    # Add task pattern
    for pat in [
        r'add (?:a |an )?(?:task|todo) (?:to |in |for )?([a-z0-9\-_]+)[\s:]+(.+)',
        r'(?:tell|ask) ([a-z0-9\-_]+) to (.+)',
    ]:
        m = re.search(pat, t)
        if m:
            projects = discover_projects()
            matches = [p for p in projects if m.group(1) in p.name.lower()]
            if matches:
                return cmd_add(chat_id, f'{matches[0].name} | {m.group(2)}')

    if any(w in t for w in ['status','update','progress','how are','happening']):
        return cmd_projects(chat_id)
    if any(w in t for w in ['agent','who is','who are','bots','roster']):
        return cmd_agents(chat_id)
    if any(w in t for w in ['task','todo','queue','backlog','pending','blocked']):
        return cmd_tasks(chat_id)
    if any(w in t for w in ['wake','start agent','activate']):
        return cmd_wake(chat_id)

    return (f'🤖 <b>{BOT_NAME}</b> here.\n\n'
            f'I got: <i>"{text[:100]}"</i>\n\n'
            f'I\'m not sure how to route that. Try:\n'
            f'/projects · /agents · /tasks\n'
            f'/add SecondBrain | fix the login bug | HIGH\n\n'
            f'Or be more specific about what you need.')

# ── UPDATE HANDLER ────────────────────────────────────────────────────────────
def handle_update(update: dict):
    global last_update_id
    uid = update.get('update_id', 0)
    if uid <= last_update_id: return
    last_update_id = uid

    msg = update.get('message') or update.get('edited_message')
    if not msg: return

    chat_id = msg['chat']['id']
    user_id = msg['from']['id']
    text    = (msg.get('text') or '').strip()

    if not is_allowed(user_id):
        send(chat_id, '⛔ Access denied.')
        return
    if not text: return

    log.info(f'[{user_id}] {text[:60]}')

    if text.startswith('/start') or text.startswith('/help'):
        reply = cmd_start(chat_id)
    elif text.startswith('/projects'):
        reply = cmd_projects(chat_id)
    elif text.startswith('/agents'):
        reply = cmd_agents(chat_id)
    elif text.startswith('/tasks'):
        reply = cmd_tasks(chat_id, text.replace('/tasks','').strip())
    elif text.startswith('/add'):
        reply = cmd_add(chat_id, text.replace('/add','').strip())
    elif text.startswith('/wake'):
        reply = cmd_wake(chat_id, text.replace('/wake','').strip())
    elif text.startswith('/status'):
        reply = cmd_status(chat_id)
    elif text.startswith('/'):
        reply = f'Unknown command. /help for commands.'
    else:
        reply = route_natural(chat_id, text)

    send(chat_id, reply)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    global running, last_update_id
    load_state()

    me = tg('getMe')
    if not me.get('ok'):
        log.error(f'Bot token invalid: {me}')
        sys.exit(1)

    username = me['result'].get('username', BOT_NAME)
    log.info(f'✅ @{username} connected')
    log.info(f'👤 Allowed: {ALLOWED_USER_IDS}')
    log.info(f'📁 Projects: {PROJECTS_PATH}')

    projects = discover_projects()
    log.info(f'🗂  {len(projects)} project(s): {[p.name for p in projects]}')

    # Background notification poller
    threading.Thread(target=poll_and_notify, daemon=True).start()

    # Startup message
    for uid in ALLOWED_USER_IDS:
        send(uid, f'🦂 <b>{BOT_NAME}</b> online.\n'
                  f'Watching {len(projects)} project(s). /status for overview.')

    # Graceful shutdown
    def shutdown(sig, frame):
        global running
        running = False
        log.info('Shutting down...')
        for uid in ALLOWED_USER_IDS:
            send(uid, f'🔴 <b>{BOT_NAME}</b> going offline.')
        sys.exit(0)
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Skip old messages
    r = tg('getUpdates', timeout=1)
    if r.get('ok') and r.get('result'):
        last_update_id = r['result'][-1]['update_id']
        log.info(f'Skipping {len(r["result"])} old messages')

    log.info('🔄 Ready — polling for messages...')
    while running:
        try:
            r = tg('getUpdates', offset=last_update_id + 1, timeout=30)
            if r.get('ok'):
                for upd in r.get('result', []):
                    handle_update(upd)
        except Exception as e:
            log.error(f'Loop error: {e}')
            time.sleep(5)

if __name__ == '__main__':
    main()
