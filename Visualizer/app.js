const stateUrl = "/api/state";

function statusClass(status) {
  if (status === "active") return "active";
  if (status === "stale") return "stale";
  if (status === "working") return "working";
  return "unclaimed";
}

function daemonStatusClass(status) {
  if (status === "active") return "active";
  if (status === "degraded") return "stale";
  if (status === "stopped" || status === "inactive") return "unclaimed";
  return "unclaimed";
}

function formatLease(row) {
  if (!row.lease_expires_at) return "No lease";
  return `Expires ${row.lease_expires_at}`;
}

function roleDisplayState(row) {
  if (row.status === "active" && row.task) return "working";
  return row.status;
}

function daemonLabel(status) {
  if (status === "active") return "ACTIVE";
  if (status === "degraded") return "DEGRADED";
  if (status === "stopped") return "STOPPED";
  return "INACTIVE";
}

function renderNav(state) {
  document.getElementById("generated-at").textContent = state.generated_at || "unknown";
  document.getElementById("role-count").textContent = state.roles.length;
  document.getElementById("project-count").textContent = state.projects.length;
  document.getElementById("todo-count").textContent = state.tasks.todo;
}

function renderStats(state) {
  const map = {
    active: state.roles.filter(r => r.status === "active").length,
    stale: state.roles.filter(r => r.status === "stale").length,
    todo: state.tasks.todo,
    progress: state.tasks.in_progress,
    done: state.tasks.done
  };
  Object.entries(map).forEach(([key, value]) => {
    const node = document.getElementById(`stat-${key}`);
    if (node) node.textContent = value;
  });
}

function roleCardHtml(row, index) {
  const mode = row.automation_mode || "unregistered";
  const harness = row.actual_harness || row.registered_harness_type || "Unknown harness";
  const ready = (row.automation_ready || "NO").toUpperCase();
  const displayState = roleDisplayState(row);
  const x = 18 + (index % 3) * 30;
  const y = 28 + ((index * 17) % 46);
  return `
    <div class="status ${statusClass(displayState)}">${displayState.toUpperCase()}</div>
    <div class="agent-body">
      <div class="role-meta">${row.claimed_by || "No current holder"}</div>
      <h3>${row.role}</h3>
      <div class="task">${row.task || "idle / no current task"}</div>
      <div class="meta-row"><span>Harness</span><b>${harness}</b></div>
      <div class="meta-row"><span>Mode</span><b>${mode}</b></div>
      <div class="meta-row"><span>Automation Ready</span><b>${ready}</b></div>
      <div class="lease">${formatLease(row)}</div>
      <div class="scene">
        <div class="dot ${statusClass(displayState)}" style="left:${x}%; top:${y}%"></div>
      </div>
    </div>
  `;
}

function renderWorld(state) {
  const host = document.getElementById("roles-grid");
  if (!host) return;
  host.innerHTML = "";
  state.roles.forEach((row, index) => {
    const card = document.createElement("article");
    card.className = "card agent";
    card.innerHTML = roleCardHtml(row, index);
    host.appendChild(card);
  });
}

function renderEvents(state) {
  const host = document.getElementById("events");
  if (!host) return;
  host.innerHTML = "";
  state.recent_events.slice().reverse().slice(0, 12).forEach(line => {
    const item = document.createElement("div");
    item.className = "line";
    item.textContent = line;
    host.appendChild(item);
  });
}

function renderProjects(state) {
  const host = document.getElementById("projects");
  if (!host) return;
  host.innerHTML = "";
  state.projects.forEach(project => {
    const t = project.task_summary || {};
    const item = document.createElement("div");
    item.className = "line";
    item.innerHTML = `
      <strong>${project.title || project.slug}</strong><br>
      <span class="muted">${project.slug}</span><br>
      <span class="micro">todo ${t.todo || 0} / active ${t.in_progress || 0} / done ${t.done || 0} / blocked ${t.blocked || 0}</span>
    `;
    host.appendChild(item);
  });
}

function renderDaemons(state) {
  const host = document.getElementById("daemon-grid");
  if (!host) return;
  const daemons = state.daemons || {};
  const cards = [
    { key: "runner", title: "Runner", meta: `${daemons.runner?.mode || "unknown"} / enabled ${daemons.runner?.enabled || "NO"}` },
    { key: "telegram", title: "Telegram", meta: daemons.telegram?.bot_name || "bridge" },
    { key: "visualizer", title: "Visualizer", meta: "local server" },
    { key: "wake_queue", title: "Wake Queue", meta: `pending ${daemons.wake_queue?.pending || 0}` },
    { key: "reminder_queue", title: "Reminders", meta: `pending ${daemons.reminder_queue?.pending || 0}` },
  ];
  host.innerHTML = "";
  cards.forEach(cardInfo => {
    const data = daemons[cardInfo.key] || {};
    const status = cardInfo.key === "wake_queue"
      ? ((data.pending || 0) > 0 ? "degraded" : "active")
      : (data.status || "inactive");
    const card = document.createElement("article");
    card.className = "card daemon-card";
    card.innerHTML = `
      <div class="status ${daemonStatusClass(status)}">${daemonLabel(status)}</div>
      <div class="agent-body">
        <div class="role-meta">${cardInfo.meta}</div>
        <h3>${cardInfo.title}</h3>
        <div class="task">${data.last_error || data.last_request || data.next_text || "healthy"}</div>
        <div class="lease">updated ${data.updated_at || "-"}</div>
      </div>
    `;
    host.appendChild(card);
  });
}

function renderWorkzone(state) {
  const host = document.getElementById("workzone");
  if (!host) return;
  const roleModes = state.roles.reduce((acc, role) => {
    const mode = role.automation_mode || "unregistered";
    acc[mode] = (acc[mode] || 0) + 1;
    return acc;
  }, {});
  const readyCount = state.roles.filter(role => (role.automation_ready || "").toUpperCase() === "YES").length;
  host.innerHTML = `
    <div class="line">
      <strong>Current ecosystem</strong><br>
      <span class="micro">roles ${state.roles.length} / projects ${state.projects.length}</span>
    </div>
    <div class="line">
      <strong>Automation mix</strong><br>
      <span class="micro">interval ${roleModes.interval || 0} / manual ${roleModes.manual || 0} / persistent ${roleModes.persistent || 0} / unregistered ${roleModes.unregistered || 0}</span>
    </div>
    <div class="line">
      <strong>Runner ownership</strong><br>
      <span class="micro">automation ready ${readyCount} / waiting for first manual proof ${Math.max(state.roles.length - readyCount, 0)}</span>
    </div>
    <div class="line">
      <strong>Task board</strong><br>
      <span class="micro">todo ${state.tasks.todo} / in progress ${state.tasks.in_progress} / done ${state.tasks.done} / blocked ${state.tasks.blocked}</span>
    </div>
  `;
}

async function refresh() {
  try {
    const res = await fetch(stateUrl, { cache: "no-store" });
    const state = await res.json();
    renderNav(state);
    renderStats(state);
    renderWorld(state);
    renderEvents(state);
    renderProjects(state);
    renderDaemons(state);
    renderWorkzone(state);
  } catch (err) {
    console.error(err);
  }
}

refresh();
setInterval(refresh, 5000);
