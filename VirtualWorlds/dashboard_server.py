#!/usr/bin/env python3
"""
🦂 Agentic Harness — Dashboard Server v11.0
By Solomon Christ | AgenticHarness.io

Reads v11 LAYER files from all Harness project folders.
Serves JSON API consumed by dashboard.html.

SETUP:
  pip install flask flask-cors python-dotenv
  python dashboard_server.py

Then open: http://localhost:8765/dashboard.html
Or from any device on LAN: http://YOUR_IP:8765/dashboard.html
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

PROJECT_BASE = Path('.')

# ── ENV LOADING ───────────────────────────────────────────────────────────────
def load_env():
    global PROJECT_BASE
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        for line in env_file.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())
    path = os.environ.get('HARNESS_PROJECTS_PATH', str(Path(__file__).parent.parent))
    # Fix Windows backslashes
    path = path.replace('\\', '/').strip('"').strip("'")
    PROJECT_BASE = Path(path)

load_env()

# ── PROJECT DISCOVERY ─────────────────────────────────────────────────────────
def discover_projects():
    found = []
    for hb in PROJECT_BASE.rglob('LAYER_HEARTBEAT.MD'):
        found.append(hb.parent)
    return sorted(found)

def rf(project, filename):
    f = project / filename
    try:
        return f.read_text(encoding='utf-8', errors='ignore') if f.exists() else ''
    except:
        return ''

# ── SOUL FILE READING ─────────────────────────────────────────────────────────
def read_soul(agent_id, project_path=None):
    soul = ''
    paths = []
    if project_path:
        paths.append(project_path / f'SOUL_{agent_id}.md')
    paths.append(Path.home() / '.harness' / 'souls' / f'SOUL_{agent_id}.md')
    for sp in paths:
        if sp.exists():
            try:
                soul = sp.read_text(encoding='utf-8', errors='ignore')
                break
            except:
                pass
    arch  = re.search(r'Archetype:\s*([^\n|,]+)', soul)
    disp  = re.search(r'Display Name:\s*([^\n|,]+)', soul)
    score = re.search(r'(?:Score|Reputation)[^:]*:\s*(\d+)', soul)
    catch = re.search(r'Catchphrase:\s*"?([^\n"]+)"?', soul)
    tasks = re.search(r'Tasks completed:\s*(\d+)', soul)
    sess  = re.search(r'Sessions:\s*(\d+)', soul)
    return {
        'archetype':   arch.group(1).strip().split()[0] if arch else 'Builder',
        'display':     disp.group(1).strip() if disp else agent_id.split('-')[0],
        'score':       int(score.group(1)) if score else 0,
        'catchphrase': catch.group(1).strip()[:60] if catch else '',
        'tasks_done':  int(tasks.group(1)) if tasks else 0,
        'sessions':    int(sess.group(1)) if sess else 0,
    }

# ── PROJECT PARSER ────────────────────────────────────────────────────────────
def parse_project(path):
    hb   = rf(path, 'LAYER_HEARTBEAT.MD')
    tl   = rf(path, 'LAYER_TASK_LIST.MD')
    log  = rf(path, 'LAYER_LAST_ITEMS_DONE.MD')
    cfg  = rf(path, 'LAYER_CONFIG.MD')
    mem  = rf(path, 'LAYER_MEMORY.MD')
    ctx  = rf(path, 'LAYER_SHARED_TEAM_CONTEXT.MD')
    proj = rf(path, 'PROJECT.md')
    card = rf(path, 'AGENT_CARD.md')

    # Status from heartbeat
    status = 'OFFLINE'
    last_pulse = None
    for line in hb.splitlines():
        if any(k in line for k in ('SESSION_OPEN','🟢')): status = 'ACTIVE'
        if 'STANDBY' in line: status = 'STANDBY'
        if any(k in line for k in ('SESSION_CLOSE','HEARTBEAT CLOSE','🔒')): status = 'OFFLINE'
        if 'BLOCKED' in line: status = 'BLOCKED'
        ts = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', line)
        if ts: last_pulse = ts.group(1)

    # Stale check
    if last_pulse and status == 'ACTIVE':
        try:
            lp = datetime.strptime(last_pulse, '%Y-%m-%d %H:%M')
            if datetime.now() - lp > timedelta(minutes=15):
                status = 'STALE'
        except: pass

    # Task counts
    counts = {'todo':0,'inprog':0,'done':0,'blocked':0,'human':0}
    human_items = []
    for line in tl.splitlines():
        l = line.strip()
        if l.startswith('[→]'): counts['inprog'] += 1
        elif l.startswith('[✓]'): counts['done'] += 1
        elif l.startswith('[✗]'): counts['blocked'] += 1
        elif l.startswith('[⏸ HUMAN]'):
            counts['human'] += 1
            clean = re.sub(r'^\[⏸ HUMAN\]\s*','',l)
            clean = re.sub(r'\s*⟵.*$','',clean).strip()[:100]
            human_items.append({'text': clean, 'project': path.name})
        elif l.startswith('[ ]'): counts['todo'] += 1

    # Agent discovery from SOUL files + LAYER_CONFIG + logs
    agents = {}

    # Scan soul files in project + global
    soul_paths = [path]
    global_souls = Path.home() / '.harness' / 'souls'
    if global_souls.exists():
        soul_paths.append(global_souls)
    for sp in soul_paths:
        for sf in sp.glob('SOUL_*.md'):
            aid = sf.stem.replace('SOUL_','')
            if '_archived' in aid or aid in agents: continue
            try: soul_txt = sf.read_text(encoding='utf-8', errors='ignore')
            except: continue
            arch  = re.search(r'Archetype:\s*([^\n|,]+)', soul_txt)
            disp  = re.search(r'Display Name:\s*([^\n|,]+)', soul_txt)
            score = re.search(r'(?:Score|Reputation)[^:]*:\s*(\d+)', soul_txt)
            catch = re.search(r'Catchphrase:\s*"?([^\n"]+)"?', soul_txt)
            tdone = re.search(r'Tasks completed:\s*(\d+)', soul_txt)
            agents[aid] = {
                'id': aid,
                'display': disp.group(1).strip() if disp else aid.split('-')[0],
                'archetype': arch.group(1).strip().split()[0] if arch else 'Builder',
                'score': int(score.group(1)) if score else 0,
                'catchphrase': catch.group(1).strip()[:60] if catch else '',
                'tasks_done': int(tdone.group(1)) if tdone else 0,
                'status': 'OFFLINE',
                'last_action': '',
                'current_task': '',
            }

    # Enrich from log
    for line in log.splitlines():
        if not line.strip() or line.startswith('#'): continue
        m = re.search(r'\[(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?)\] \[([^\]]+)\] (.+)', line)
        if not m: continue
        ts_s, aid, action = m.group(1), m.group(2).strip(), m.group(3).strip()
        if aid in ('BOOTSTRAP','SYSTEM','WORLD-UI','TELEGRAM-EA'): continue
        if aid not in agents:
            agents[aid] = {'id':aid,'display':aid.split('-')[0],'archetype':'Builder',
                           'score':0,'catchphrase':'','tasks_done':0,'current_task':''}
        if agents[aid].get('status') != 'ACTIVE':
            st = 'ACTIVE' if 'SESSION_OPEN' in action else \
                 'OFFLINE' if 'SESSION_CLOSE' in action or 'HEARTBEAT CLOSE' in action else \
                 'STANDBY' if 'STANDBY' in action else \
                 'BLOCKED' if 'BLOCKED' in action else 'WORKING'
            agents[aid]['status'] = st
        if not agents[aid].get('last_action'):
            clean = re.sub(r'^[🟢🔒⬆️✅🔨📋💓🚨❌⚠️🔄⏸🎓📸📨🌍🔁✓✗►]+\s*','',action)
            clean = re.sub(r'^(SESSION_OPEN|SESSION_CLOSE|PULSE|RETRO|CONTEXT_SAVE)\s*[-—]?\s*','',clean).strip()
            agents[aid]['last_action'] = (clean or action)[:80]

    # Current tasks from task list
    for line in tl.splitlines():
        m = re.match(r'\[→\]\s+(.+?)(?:\s+\[([A-Za-z][^\]]+)\])?\s*$', line.strip())
        if m:
            task_desc = re.sub(r'\s*⟵.*$','',m.group(1).strip()).strip()[:60]
            task_agent = m.group(2).strip() if m.group(2) else None
            if task_agent and task_agent in agents:
                agents[task_agent]['current_task'] = task_desc

    # Recent notifications
    notifications = []
    for line in log.splitlines():
        if '📨' not in line or line.startswith('#'): continue
        m = re.search(r'\[(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?)\] \[([^\]]+)\] 📨 (.+)', line)
        if m:
            notifications.append({'ts':m.group(1),'agent':m.group(2),'msg':m.group(3)[:120]})
    notifications = notifications[:10]

    # Recent log lines
    recent_log = []
    for line in log.splitlines():
        if line.strip() and not line.startswith('#'):
            recent_log.append(line.strip())
            if len(recent_log) >= 15: break

    # Milestone from PROJECT.md
    milestone = 'M1'
    for line in proj.splitlines():
        m2 = re.search(r'[Mm]ilestone[^:]*:\s*(M\d+)', line)
        if m2: milestone = m2.group(1)

    # Version from LAYER_CONFIG
    version = '11.0'
    for line in cfg.splitlines():
        m3 = re.search(r'Version:\s*([\d.]+)', line)
        if m3: version = m3.group(1); break

    # Wake file present?
    has_wake = (path / '.harness_wake').exists()

    return {
        'id':            path.name,
        'name':          path.name,
        'path':          str(path),
        'status':        status,
        'version':       version,
        'milestone':     milestone,
        'last_pulse':    last_pulse,
        'tasks':         counts,
        'human_items':   human_items,
        'agents':        list(agents.values()),
        'notifications': notifications,
        'recent_log':    recent_log,
        'has_wake':      has_wake,
    }

# ── API ROUTES ────────────────────────────────────────────────────────────────
@app.route('/api/status')
def api_status():
    projects = [parse_project(p) for p in discover_projects()]
    all_agents = []
    for p in projects:
        for a in p['agents']:
            if not any(x['id']==a['id'] for x in all_agents):
                all_agents.append({**a, 'project': p['name']})
    all_agents.sort(key=lambda x: x['score'], reverse=True)

    human_queue = []
    for p in projects:
        human_queue.extend(p['human_items'])

    return jsonify({
        'projects':    projects,
        'agents':      all_agents,
        'human_queue': human_queue,
        'stats': {
            'total_projects': len(projects),
            'active_projects': sum(1 for p in projects if p['status'] in ('ACTIVE','WORKING')),
            'total_agents': len(all_agents),
            'tasks_todo':  sum(p['tasks']['todo']  for p in projects),
            'tasks_done':  sum(p['tasks']['done']  for p in projects),
            'tasks_human': sum(p['tasks']['human'] for p in projects),
            'wake_files':  sum(1 for p in projects if p['has_wake']),
        },
        'ts': datetime.now().isoformat(),
    })

@app.route('/api/project/<name>')
def api_project(name):
    projects = discover_projects()
    matches = [p for p in projects if p.name.lower() == name.lower()]
    if not matches:
        return jsonify({'error': 'Project not found'}), 404
    return jsonify(parse_project(matches[0]))

@app.route('/api/task', methods=['POST'])
def api_add_task():
    body = request.json or {}
    proj_name = body.get('project', '')
    task_text = body.get('task', '')
    priority  = body.get('priority', 'MED')
    milestone = body.get('milestone', '')
    if not proj_name or not task_text:
        return jsonify({'ok': False, 'error': 'Missing project or task'}), 400

    projects = discover_projects()
    matches = [p for p in projects if p.name.lower() == proj_name.lower()]
    if not matches:
        return jsonify({'ok': False, 'error': f'Project not found: {proj_name}'}), 404

    proj = matches[0]
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    prefix = f'{priority}/{milestone} — ' if milestone else f'{priority} — '
    task_line = f'\n[ ] {prefix}{task_text}  ⟵ added via Dashboard {ts}'

    # Write task
    tf = proj / 'LAYER_TASK_LIST.MD'
    try:
        existing = tf.read_text(encoding='utf-8', errors='ignore') if tf.exists() else '# LAYER_TASK_LIST.MD\n'
        tf.write_text(existing + task_line, encoding='utf-8')
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

    # Write 📨 notification
    lf = proj / 'LAYER_LAST_ITEMS_DONE.MD'
    notify = f'\n[{ts}] [DASHBOARD] 📨 NOTIFY — New {priority} task: {task_text[:80]} | TYPE:ALERT'
    try:
        existing_log = lf.read_text(encoding='utf-8', errors='ignore') if lf.exists() else ''
        lines = existing_log.split('\n')
        idx = next((i for i,l in enumerate(lines) if l.strip() and not l.startswith('#')), len(lines))
        lines.insert(idx, notify.strip())
        lf.write_text('\n'.join(lines), encoding='utf-8')
    except: pass

    # Write .harness_wake
    try:
        (proj / '.harness_wake').write_text(
            f'WAKE_REQUEST\nts: {ts}\nfrom: Dashboard\n'
            f'reason: New {priority} task — {task_text[:100]}\n'
            f'instruction: Read HARNESS_PROMPT.md and run it. Scenario B.\n',
            encoding='utf-8')
    except: pass

    # Find agent to wake
    agents = []
    cfg = rf(proj, 'LAYER_CONFIG.MD')
    for line in cfg.splitlines():
        m = re.search(r'\|\s*([A-Za-z][A-Za-z0-9_\-]+-\d+)\s*\|', line)
        if m:
            aid = m.group(1).strip()
            if aid and '---' not in aid and aid.upper() != 'AGENT_ID':
                agents.append(aid)
    agent_str = agents[0] if agents else '[AGENT_ID]'

    return jsonify({
        'ok': True,
        'summon': f'You are {agent_str}. Scenario B.',
        'message': f'Task queued in {proj_name}. Wake agent with summon command.'
    })

@app.route('/dashboard.html')
def serve_dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/')
def index():
    return '''<html><body style="font-family:monospace;background:#080a0c;color:#e8a422;padding:2rem">
    <h2>🦂 Agentic Harness Dashboard Server v11.0</h2>
    <p>API running. <a href="/dashboard.html" style="color:#5dba7a">Open Dashboard →</a></p>
    <p style="color:#7a8a9e">Watching: ''' + str(PROJECT_BASE.resolve()) + '''</p>
    </body></html>'''

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Agentic Harness Dashboard Server v11.0')
    parser.add_argument('--projects', help='Path to projects folder (overrides .env)')
    parser.add_argument('--port', type=int, default=None)
    args = parser.parse_args()

    if args.projects:
        PROJECT_BASE = Path(args.projects)
    port = args.port or int(os.environ.get('DASHBOARD_PORT', '8765'))

    ip = '127.0.0.1'
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except: pass

    print(f'\n🦂 Agentic Harness Dashboard Server v11.0')
    print(f'   http://localhost:{port}/dashboard.html')
    print(f'   http://{ip}:{port}/dashboard.html  (LAN)')
    print(f'   Watching: {PROJECT_BASE.resolve()}')
    print(f'   Press Ctrl+C to stop\n')
    app.run(host='0.0.0.0', port=port, debug=False)
