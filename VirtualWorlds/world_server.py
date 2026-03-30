#!/usr/bin/env python3
"""
🦂 Agentic Harness — Virtual World Server
By Solomon Christ AI | www.SolomonChrist.com

Serves the 2D virtual world interface.
Reads LAYER files from all your Harness projects.
Accessible on LAN — later add Tailscale for remote access.

SETUP:
  pip install flask flask-cors python-dotenv
  python world_server.py --projects /path/to/projects/ --port 8888

ACCESS:
  Local:  http://localhost:8888
  LAN:    http://YOUR_LOCAL_IP:8888  (find with: ipconfig or ifconfig)
  Later:  http://YOUR_TAILSCALE_IP:8888
"""

import os
import re
import json
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app)

PROJECT_BASE = Path('.')

def get_local_ip():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'YOUR_LOCAL_IP'
WORLD_START_TIME = time.time()

# ── PROJECT DISCOVERY ──────────────────────────────────────────────────
def discover_projects():
    found = []
    for p in PROJECT_BASE.rglob('LAYER_HEARTBEAT.MD'):
        found.append(p.parent)
    return sorted(found)

def rf(project, filename):
    """Read file safely."""
    f = project / filename
    try:
        return f.read_text(encoding='utf-8', errors='ignore') if f.exists() else ''
    except:
        return ''

# ── PARSERS ────────────────────────────────────────────────────────────
def parse_project(path):
    """Parse all LAYER files into a world-ready project object."""
    name = path.name
    hb   = rf(path, 'LAYER_HEARTBEAT.MD')
    tl   = rf(path, 'LAYER_TASK_LIST.MD')
    log  = rf(path, 'LAYER_LAST_ITEMS_DONE.MD')
    ctx  = rf(path, 'LAYER_SHARED_TEAM_CONTEXT.MD')
    cfg  = rf(path, 'LAYER_CONFIG.MD')
    proj = rf(path, 'PROJECT.md')

    # Status from heartbeat
    status = 'UNKNOWN'
    last_pulse = None
    for line in hb.splitlines():
        if 'SESSION_OPEN' in line or 'ACTIVE' in line:
            status = 'ACTIVE'
        if 'STANDBY' in line:
            status = 'STANDBY'
        if 'SESSION_CLOSE' in line or 'HEARTBEAT CLOSE' in line:
            status = 'OFFLINE'
        if 'BLOCKED' in line:
            status = 'BLOCKED'
        if 'COMPLETE' in line:
            status = 'COMPLETE'
        ts = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', line)
        if ts:
            last_pulse = ts.group(1)

    # Stale check — if last pulse > 15min and not CLOSED, mark stale
    if last_pulse and status == 'ACTIVE':
        try:
            lp = datetime.strptime(last_pulse, '%Y-%m-%d %H:%M')
            if datetime.now() - lp > timedelta(minutes=15):
                status = 'STALE'
        except:
            pass

    # Tasks
    todo = blocked = done = inprog = human = 0
    for line in tl.splitlines():
        l = line.strip()
        if l.startswith('[✓]') or l.startswith('[✓]'):
            done += 1
        elif l.startswith('[→]'):
            inprog += 1
        elif l.startswith('[✗]'):
            blocked += 1
        elif l.startswith('[⏸ HUMAN]'):
            human += 1
        elif l.startswith('[ ]'):
            todo += 1

    # ── AGENT DISCOVERY ── (5-step, most robust first)
    agents = {}

    # Step 0: Scan for SOUL_*.md files — most reliable source
    # Check project folder + global ~/.harness/souls/
    soul_search_paths = [path]
    global_souls = Path.home() / '.harness' / 'souls'
    if global_souls.exists():
        soul_search_paths.append(global_souls)

    for search_path in soul_search_paths:
        for soul_file in search_path.glob('SOUL_*.md'):
            aid = soul_file.stem.replace('SOUL_', '')
            if not aid or aid in agents or '_archived' in aid:
                continue
            try:
                soul = soul_file.read_text(encoding='utf-8', errors='ignore')
            except:
                continue
            arch = re.search(r'Archetype:\s*([^\n|,]+)', soul)
            disp = re.search(r'Display Name:\s*([^\n|,]+)', soul)
            score = re.search(r'(?:Score|Reputation)[^:]*:\s*(\d+)', soul)
            catch = re.search(r'Catchphrase:\s*"?([^\n"]+)"?', soul)
            tasks_n = re.search(r'Tasks completed:\s*(\d+)', soul)
            sessions = re.search(r'Sessions:\s*(\d+)', soul)
            agents[aid] = {
                'id': aid,
                'display': disp.group(1).strip() if disp else aid.split('-')[0],
                'archetype': arch.group(1).strip().split()[0] if arch else 'Builder',
                'score': int(score.group(1)) if score else 0,
                'catchphrase': catch.group(1).strip()[:50] if catch else '',
                'tasks_done': int(tasks_n.group(1)) if tasks_n else 0,
                'sessions': int(sessions.group(1)) if sessions else 0,
                'last_action': 'Offline',
                'last_seen': '',
                'status': 'OFFLINE',
                'current_task': '',
            }

    # Step 1: Also check AGENT_CARD.md and LAYER_CONFIG for any agents not in SOUL files
    card_content = rf(path, 'AGENT_CARD.md')
    if card_content:
        card_id_m = re.search(r'Agent ID:\s*([^\s|,\n]+)', card_content)
        if card_id_m:
            aid = card_id_m.group(1).strip()
            if aid and aid not in agents:
                card_disp = re.search(r'Display Name:\s*([^\n|,]+)', card_content)
                card_arch = re.search(r'Personality[^:]*:\s*([^\n|,]+)', card_content)
                card_score = re.search(r'Score:\s*(\d+)', card_content)
                card_tasks = re.search(r'Tasks:\s*(\d+)', card_content)
                agents[aid] = {
                    'id': aid,
                    'display': card_disp.group(1).strip() if card_disp else aid.split('-')[0],
                    'archetype': card_arch.group(1).strip().split()[0] if card_arch else 'Builder',
                    'score': int(card_score.group(1)) if card_score else 0,
                    'tasks_done': int(card_tasks.group(1)) if card_tasks else 0,
                    'sessions': 0, 'catchphrase': '',
                    'last_action': 'Offline',
                    'last_seen': '', 'status': 'OFFLINE', 'current_task': '',
                }
            elif aid in agents:
                # Enrich existing agent from card
                card_disp = re.search(r'Display Name:\s*([^\n|,]+)', card_content)
                card_arch = re.search(r'Personality[^:]*:\s*([^\n|,]+)', card_content)
                card_score = re.search(r'Score:\s*(\d+)', card_content)
                if card_disp: agents[aid]['display'] = card_disp.group(1).strip()
                if card_arch and not agents[aid].get('archetype'): agents[aid]['archetype'] = card_arch.group(1).strip().split()[0]
                if card_score: agents[aid]['score'] = max(agents[aid].get('score',0), int(card_score.group(1)))

    # Also scan LAYER_CONFIG registry as fallback
    for line in cfg.splitlines():
        m = re.search(r'\|\s*([A-Za-z][A-Za-z0-9_\-]+-\d+[A-Za-z0-9_\-]*)\s*\|', line)
        if m:
            aid = m.group(1).strip()
            # Skip header rows and separator lines
            if aid in ('AGENT_ID','---|---') or '---' in aid:
                continue
            if aid and aid not in agents:
                agents[aid] = {
                    'id': aid, 'display': aid.split('-')[0],
                    'archetype': 'Builder', 'score': 0, 'tasks_done': 0,
                    'sessions': 0, 'catchphrase': '',
                    'last_action': 'Registered', 'last_seen': '',
                    'status': 'OFFLINE', 'current_task': '',
                }

    # Step 2: Parse LAYER_LAST_ITEMS_DONE — get latest action per agent
    log_lines = [l.strip() for l in log.splitlines() if l.strip() and not l.startswith('#')]
    seen_agents = {}
    for line in log_lines:
        m = re.search(r'\[(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?)\] \[([^\]]+)\] (.+)', line)
        if not m:
            continue
        ts, aid, action = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        if aid in ('BOOTSTRAP', 'SYSTEM') or not aid:
            continue
        if aid not in seen_agents:
            seen_agents[aid] = {'ts': ts, 'action': action}
            # Determine live status from most recent log entry
            if any(k in action for k in ('SESSION_OPEN', '🟢 SESSION_OPEN')):
                st = 'ACTIVE'
            elif any(k in action for k in ('SESSION_CLOSE', '🔒', 'HEARTBEAT CLOSE')):
                st = 'OFFLINE'
            elif 'STANDBY' in action:
                st = 'STANDBY'
            elif 'BLOCKED' in action:
                st = 'BLOCKED'
            else:
                st = 'WORKING'

            # Clean action text for display
            clean = re.sub(r'^[🟢🔒⬆️✅🔨📋💓🚨🌐❌⚠️❓🔄⏸🎓🧑📸📨🌍🔁✓✗►]+\s*', '', action)
            clean = re.sub(r'^(SESSION_OPEN|SESSION_CLOSE|UPGRADE|DONE|ACTION|READ|PULSE|RETRO'
                           r'|SKILL|HANDOFF|CONTEXT_SAVE|BOOTSTRAP|CONSOLIDATION_COMPLETE'
                           r'|UPGRADE|OPEN|CLOSE)\s*[—\-]?\s*', '', clean).strip()
            clean = clean[:72] if clean else action[:72]

            if aid not in agents:
                agents[aid] = {
                    'id': aid, 'display': aid.split('-')[0],
                    'archetype': 'Builder', 'score': 0, 'tasks_done': 0,
                    'sessions': 0, 'catchphrase': '',
                    'current_task': '',
                }
            agents[aid].update({
                'last_action': clean or action[:72],
                'last_seen': ts,
                'status': st,
            })

    # Step 3: Find IN PROGRESS tasks — match [→] ... [AGENT_ID] in task list
    for line in tl.splitlines():
        # Match: [→] anything [AGENT_ID]
        m = re.match(r'\[→\]\s+(.+?)(?:\s+\[([A-Za-z][^\]]+)\])?\s*$', line.strip())
        if m:
            task_desc = m.group(1).strip().rstrip('—- ')
            task_agent = m.group(2).strip() if m.group(2) else None
            # Clean priority prefix
            task_desc = re.sub(r'^(CRITICAL|HIGH|MED|LOW|URGENT)/M\d+\s*[—\-]?\s*', '', task_desc).strip()
            if task_agent and task_agent in agents:
                agents[task_agent]['current_task'] = task_desc[:60]
                if agents[task_agent].get('status') not in ('OFFLINE', 'STANDBY'):
                    agents[task_agent]['status'] = 'WORKING'
            elif not task_agent:
                # Assign to first ACTIVE agent
                for a_id, a_data in agents.items():
                    if a_data.get('status') in ('ACTIVE', 'WORKING'):
                        a_data['current_task'] = task_desc[:60]
                        break

    # Step 4: Stale check
    for aid in agents:
        a = agents[aid]
        if a.get('status') == 'ACTIVE' and a.get('last_seen'):
            try:
                ts_str = a['last_seen'].replace('T', ' ')[:16]
                lp = datetime.strptime(ts_str, '%Y-%m-%d %H:%M')
                if datetime.now() - lp > timedelta(minutes=10):
                    agents[aid]['status'] = 'STALE'
            except:
                pass

    # Recent notifications (📨 entries)
    notifications = []
    for line in log.splitlines():
        if '📨' in line and not line.startswith('#'):
            m = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[([^\]]+)\] 📨 (.+)', line)
            if m:
                notifications.append({
                    'ts': m.group(1),
                    'agent': m.group(2),
                    'msg': m.group(3)[:120]
                })
    notifications = notifications[:10]  # last 10

    # Recent log entries
    recent_log = []
    for line in log.splitlines():
        if line.strip() and not line.startswith('#'):
            recent_log.append(line.strip())
            if len(recent_log) >= 8:
                break

    # Milestone from project file
    milestone = 'M1'
    for line in proj.splitlines():
        if 'Current Milestone' in line or 'milestone' in line.lower():
            m = re.search(r'M(\d+)', line)
            if m:
                milestone = f'M{m.group(1)}'

    # Version
    version = '?'
    for line in cfg.splitlines():
        if 'Version:' in line:
            m = re.search(r'Version:\s*([\d.]+)', line)
            if m:
                version = m.group(1)
                break

    return {
        'id': name,
        'name': name,
        'path': str(path),
        'status': status,
        'version': version,
        'milestone': milestone,
        'last_pulse': last_pulse,
        'tasks': {'todo': todo, 'inprog': inprog, 'done': done, 'blocked': blocked, 'human': human},
        'agents': list(agents.values()),
        'notifications': notifications,
        'recent_log': recent_log,
    }

# ── API ROUTES ─────────────────────────────────────────────────────────
@app.route('/api/world')
def api_world():
    projects = [parse_project(p) for p in discover_projects()]
    total_agents = sum(len(p['agents']) for p in projects)
    total_tasks  = sum(p['tasks']['todo'] for p in projects)
    return jsonify({
        'projects': projects,
        'stats': {
            'projects': len(projects),
            'agents': total_agents,
            'tasks_todo': total_tasks,
            'uptime': int(time.time() - WORLD_START_TIME),
        },
        'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })

@app.route('/api/project/<name>')
def api_project(name):
    projects = discover_projects()
    matches = [p for p in projects if p.name.lower() == name.lower()]
    if not matches:
        return jsonify({'error': 'not found'}), 404
    p = matches[0]
    detail = parse_project(p)
    detail['task_list']  = rf(p, 'LAYER_TASK_LIST.MD')
    detail['team_ctx']   = rf(p, 'LAYER_SHARED_TEAM_CONTEXT.MD')
    detail['memory']     = rf(p, 'LAYER_MEMORY.MD')[-2000:]  # last 2000 chars
    detail['full_log']   = [l for l in rf(p, 'LAYER_LAST_ITEMS_DONE.MD').splitlines()
                            if l.strip() and not l.startswith('#')][:30]
    return jsonify(detail)

@app.route('/api/task', methods=['POST'])
def api_add_task():
    body = request.json or {}
    proj_name = body.get('project','')
    task_text = body.get('task','')
    priority  = body.get('priority','MED')
    milestone = body.get('milestone','')
    if not proj_name or not task_text:
        return jsonify({'ok': False, 'error': 'Missing project or task'}), 400

    projects = discover_projects()
    matches = [p for p in projects if p.name.lower() == proj_name.lower()]
    if not matches:
        return jsonify({'ok': False, 'error': f'Project not found: {proj_name}'}), 404

    proj_path = matches[0]
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    prefix = f'{priority}/{milestone} — ' if milestone else f'{priority} — '
    new_task = f'\n[ ] {prefix}{task_text}  ⟵ added via World UI {ts}'

    # 1. Write task to LAYER_TASK_LIST.MD
    task_file = proj_path / 'LAYER_TASK_LIST.MD'
    if task_file.exists():
        existing = task_file.read_text(encoding='utf-8', errors='ignore')
        task_file.write_text(existing + new_task, encoding='utf-8')
    else:
        task_file.write_text(
            '# LAYER_TASK_LIST.MD\n# [ ] TODO  [→] IN PROGRESS  [✓] DONE\n' + new_task,
            encoding='utf-8'
        )

    # 2. Write 📨 NOTIFY entry to LAYER_LAST_ITEMS_DONE so Telegram + dashboard pick it up
    log_file = proj_path / 'LAYER_LAST_ITEMS_DONE.MD'
    notify_line = (
        f'\n[{ts}] [WORLD-UI] 📨 NOTIFY — New task added: {task_text[:80]} '
        f'| Priority:{priority} | TYPE:ALERT'
    )
    if log_file.exists():
        existing_log = log_file.read_text(encoding='utf-8', errors='ignore')
        # Insert after header lines
        lines = existing_log.split('\n')
        header_end = next((i for i, l in enumerate(lines) if l.strip() and not l.startswith('#')), len(lines))
        lines.insert(header_end, notify_line.strip())
        log_file.write_text('\n'.join(lines), encoding='utf-8')

    # 3. Write .harness_wake file — agent startup scripts can watch for this
    wake_file = proj_path / '.harness_wake'
    wake_file.write_text(
        f'WAKE_REQUEST\n'
        f'ts: {ts}\n'
        f'from: World UI\n'
        f'reason: New task added — {task_text[:100]}\n'
        f'priority: {priority}\n'
        f'instruction: Read HARNESS_PROMPT.md and run it. Scenario B. Check LAYER_TASK_LIST for new task.\n',
        encoding='utf-8'
    )

    return jsonify({
        'ok': True,
        'message': f'Task added to {proj_name}. Agent will see it on next session open.',
        'wake_file': str(wake_file),
        'summon': f'You are [AGENT_ID]. Scenario B. Check LAYER_TASK_LIST — new {priority} task waiting.'
    })


@app.route('/api/world/export')
def api_world_export():
    """
    Unity/Unreal/game engine polling endpoint.
    Returns stable JSON schema with world coordinates.
    Poll this URL every 5 seconds from your game engine.
    """
    projects = [parse_project(p) for p in discover_projects()]
    ZONE_W, ZONE_H, PAD = 20.0, 12.0, 6.0
    cols = max(1, int(len(projects)**0.5 + 0.5))

    export = {
        'schema_version': '1.0',
        'harness_version': '11.0',
        'ts': datetime.now().isoformat(),
        'world': {
            'name': 'Agentic Harness World',
            'unit': 'meters',
            'zone_width': ZONE_W,
            'zone_depth': ZONE_H,
            'zone_padding': PAD,
        },
        'projects': [],
        'agents': [],
        'notifications': [],
        'stats': {
            'total_projects': len(projects),
            'total_agents': sum(len(p['agents']) for p in projects),
            'tasks_todo': sum(p['tasks']['todo'] for p in projects),
            'tasks_done': sum(p['tasks']['done'] for p in projects),
        }
    }

    for i, p in enumerate(projects):
        col = i % cols
        row = i // cols
        cx = col * (ZONE_W + PAD)
        cz = row * (ZONE_H + PAD)

        export['projects'].append({
            'id': p['id'],
            'name': p['name'],
            'status': p['status'],
            'version': p['version'],
            'milestone': p['milestone'],
            'position': {'x': cx, 'y': 0.0, 'z': cz},
            'dimensions': {'w': ZONE_W, 'h': 4.0, 'd': ZONE_H},
            'color_hex': {
                'ACTIVE':'#5dba7a','STANDBY':'#7a8a9e','OFFLINE':'#e85a34',
                'STALE':'#e8a422','BLOCKED':'#e85a34','COMPLETE':'#5d9eba'
            }.get(p['status'], '#3a4455'),
            'tasks': p['tasks'],
            'last_pulse': p['last_pulse'],
        })

        for ai, agent in enumerate(p['agents']):
            ax = cx + 3.0 + (ai % 4) * 4.0
            az = cz + ZONE_H * 0.6 + (ai // 4) * 3.0
            archetype = (agent.get('archetype') or 'Builder').split()[0]
            export['agents'].append({
                'id': agent['id'],
                'display': agent.get('display', agent['id']),
                'archetype': archetype,
                'project': p['name'],
                'status': agent.get('status', 'UNKNOWN'),
                'position': {'x': ax, 'y': 0.0, 'z': az},
                'color_hex': {
                    'Builder':'#e8a422','Scout':'#5dba7a','Guardian':'#5d9eba',
                    'Sage':'#9b7dea','Hustler':'#e8a422','Creator':'#e85a34',
                    'Fixer':'#5dba7a','Diplomat':'#9b7dea'
                }.get(archetype, '#7a8a9e'),
                'last_action': agent.get('last_action',''),
                'last_seen': agent.get('last_seen',''),
            })

        for n in p['notifications'][:5]:
            export['notifications'].append({
                'project': p['name'],
                'agent': n['agent'],
                'message': n['msg'],
                'ts': n['ts'],
            })

    return jsonify(export)

@app.route('/api/world/state.json')
def api_world_state_file():
    """Static file path alias — easier for Unity to poll."""
    return api_world_export()


@app.route('/')
def index():
    return send_from_directory('.', 'world.html')

@app.route('/world3d')
@app.route('/world3d.html')
def world3d():
    return send_from_directory('.', 'world3d.html')

@app.route('/worldvr')
@app.route('/worldvr.html')
def worldvr():
    return send_from_directory('.', 'worldvr.html')

@app.route('/api/world/unity')
def api_unity_blueprint():
    """
    Unity / Unreal / Game Engine blueprint.
    Poll GET /api/world/unity every 5 seconds from C# or Blueprints.
    Flat arrays of zones and agents with transform data.
    """
    projects = [parse_project(p) for p in discover_projects()]
    ZONE_W, ZONE_H, PAD = 20.0, 12.0, 6.0
    cols = max(1, int(len(projects)**0.5 + 0.5))
    color_map = {'Builder':'#e8a422','Scout':'#5dba7a','Guardian':'#5d9eba',
                 'Sage':'#9b7dea','Hustler':'#e8a422','Creator':'#e85a34',
                 'Fixer':'#5dba7a','Diplomat':'#9b7dea'}
    status_color = {'ACTIVE':'#5dba7a','STANDBY':'#7a8a9e','OFFLINE':'#e85a34',
                    'STALE':'#e8a422','BLOCKED':'#e85a34','COMPLETE':'#5d9eba'}

    out = {
        'meta': {
            'schema': 'agentic-harness-unity-v1',
            'generated': datetime.now().isoformat(),
            'poll_interval_seconds': 5,
            'coordinate_system': 'right-handed Y-up meters',
        },
        'zones': [], 'agents': [], 'events': [],
    }

    for i, p in enumerate(projects):
        col, row = i % cols, i // cols
        cx = float(col * (ZONE_W + PAD))
        cz = float(row * (ZONE_H + PAD))
        out['zones'].append({
            'id': p['id'], 'name': p['name'], 'status': p['status'],
            'milestone': p['milestone'], 'version': p['version'],
            'pos_x': cx + ZONE_W/2, 'pos_y': 0.0, 'pos_z': cz + ZONE_H/2,
            'width': ZONE_W, 'height': 4.0, 'depth': ZONE_H,
            'color_hex': status_color.get(p['status'], '#3a4455'),
            'tasks_todo': p['tasks']['todo'], 'tasks_done': p['tasks']['done'],
            'tasks_blocked': p['tasks']['blocked'], 'tasks_active': p['tasks']['inprog'],
            'agent_count': len(p['agents']), 'last_pulse': p['last_pulse'] or '',
        })
        for ai, agent in enumerate(p['agents']):
            arch = (agent.get('archetype') or 'Builder').split()[0]
            out['agents'].append({
                'id': agent['id'], 'display': agent.get('display', agent['id']),
                'archetype': arch, 'project_id': p['id'],
                'status': agent.get('status', 'UNKNOWN'),
                'is_active': int(agent.get('status','') not in ('OFFLINE','UNKNOWN')),
                'pos_x': cx + 3.0 + (ai % 4) * 4.0, 'pos_y': 0.0,
                'pos_z': cz + ZONE_H * 0.65 + (ai // 4) * 3.5,
                'color_hex': color_map.get(arch, '#7a8a9e'),
                'last_action': agent.get('last_action','')[:100],
                'last_seen': agent.get('last_seen',''),
            })
        for n in p['notifications'][:3]:
            out['events'].append({
                'project': p['name'], 'agent': n['agent'],
                'message': n['msg'][:100], 'ts': n['ts'],
            })
    return jsonify(out)

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

# ── MAIN ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Agentic Harness Virtual World Server')
    parser.add_argument('--projects', default=None, help='Root folder containing Harness projects')
    parser.add_argument('--port', type=int, default=None)
    parser.add_argument('--host', default='0.0.0.0')
    args = parser.parse_args()

    # Load .env from same directory as this script
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        for line in env_file.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

    # Use .env values as fallback if not passed on command line
    projects_path = args.projects or os.environ.get('HARNESS_PROJECTS_PATH', './projects')
    port = args.port or int(os.environ.get('WORLD_PORT', '8888'))

    PROJECT_BASE = Path(projects_path)

    if not PROJECT_BASE.exists():
        print(f'\n⚠️  Projects folder not found: {PROJECT_BASE}')
        print(f'   Edit .env → set HARNESS_PROJECTS_PATH to your projects folder')
        print(f'   Or run: py world_server.py --projects /your/path/\n')
    else:
        found = list(PROJECT_BASE.rglob('LAYER_HEARTBEAT.MD'))
        print(f'\n🦂 Agentic Harness Virtual World Server')
        print(f'   Projects: {PROJECT_BASE.resolve()}')
        print(f'   Found {len(found)} Harness project(s)')
        print(f'\n   2D World:    http://localhost:{port}/')
        print(f'   3D World:    http://localhost:{port}/world3d.html')
        print(f'   VR World:    http://localhost:{port}/worldvr.html')
        print(f'   Unity Data:  http://localhost:{port}/api/world/unity')
        print(f'   Export JSON: http://localhost:{port}/api/world/export')
        print(f'\n   LAN: http://{get_local_ip()}:{port}/')
        print(f'   (use LAN IP for phones, tablets, VR headsets)\n')

    app.run(host=args.host, port=port, debug=False)
