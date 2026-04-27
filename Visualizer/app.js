const stateUrl = "/api/state";
let fastRefreshUntil = 0;
let lastChatStatus = "";

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function statusClass(status) {
  if (status === "active") return "active";
  if (status === "stale") return "stale";
  if (status === "working") return "working";
  if (status === "run") return "working";
  if (status === "pause") return "stale";
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
  const preflight = row.preflight || {};
  const displayState = roleDisplayState(row);
  const scheduleEnabled = !!row.schedule_enabled;
  const pendingCount = row.pending_work?.length || 0;
  const command = row.command_preview || "";
  const x = 18 + (index % 3) * 30;
  const y = 28 + ((index * 17) % 46);
  return `
    <div class="status ${statusClass(preflight.decision || displayState)}">${escapeHtml(preflight.status || displayState).toUpperCase()}</div>
    <div class="agent-body">
      <div class="role-meta">${escapeHtml(row.claimed_by || "No current holder")}</div>
      <h3>${escapeHtml(row.role)}</h3>
      <div class="task">${escapeHtml(row.task || preflight.summary || "idle / no current task")}</div>
      <div class="meta-row"><span>Harness</span><b>${escapeHtml(harness)}</b></div>
      <div class="meta-row"><span>Mode</span><b>${escapeHtml(mode)}</b></div>
      <div class="meta-row"><span>Schedule</span><b>${scheduleEnabled ? "ON" : "OFF"}</b></div>
      <div class="meta-row"><span>Pending</span><b>${pendingCount}</b></div>
      <div class="meta-row"><span>Automation Ready</span><b>${escapeHtml(ready)}</b></div>
      <div class="lease">${escapeHtml(formatLease(row))}</div>
      <div class="command-preview">${escapeHtml(command)}</div>
      <button class="mini-btn" type="button" data-role-toggle="${escapeHtml(row.role)}" data-enabled="${scheduleEnabled ? "true" : "false"}">
        ${scheduleEnabled ? "Disable" : "Enable"}
      </button>
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
    const toggle = card.querySelector("[data-role-toggle]");
    if (toggle) {
      toggle.addEventListener("click", () => toggleRole(row.role, !(row.schedule_enabled)));
    }
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
  const serviceCards = ((state.production_health || {}).services || []).map(service => ({
    key: service.key,
    title: service.label,
    status: service.ok ? "active" : "degraded",
    meta: `${service.priority || "service"} / ${service.required ? "required" : "optional"}`,
    detail: service.last_error || `updated ${service.updated_at || "-"}`
  }));
  const cards = serviceCards.concat([
    { key: "wake_queue", title: "Wake Queue", status: ((daemons.wake_queue?.pending || 0) > 0 ? "degraded" : "active"), meta: `pending ${daemons.wake_queue?.pending || 0}`, detail: daemons.wake_queue?.last_request || "queue clear" },
    { key: "reminder_queue", title: "Reminders", status: ((daemons.reminder_queue?.pending || 0) > 0 ? "degraded" : "active"), meta: `pending ${daemons.reminder_queue?.pending || 0}`, detail: daemons.reminder_queue?.next_text || "none pending" },
  ]);
  host.innerHTML = "";
  cards.forEach(cardInfo => {
    const data = daemons[cardInfo.key] || {};
    const status = cardInfo.status || data.status || "inactive";
    const card = document.createElement("article");
    card.className = "card daemon-card";
    card.innerHTML = `
      <div class="status ${daemonStatusClass(status)}">${daemonLabel(status)}</div>
      <div class="agent-body">
        <div class="role-meta">${cardInfo.meta}</div>
        <h3>${cardInfo.title}</h3>
        <div class="task">${cardInfo.detail || data.last_error || data.last_request || data.next_text || "healthy"}</div>
        <div class="lease">${cardInfo.key === "telegram" ? "optional unless configured" : "production check surface"}</div>
        ${["runner", "telegram", "visualizer"].includes(cardInfo.key) ? `
          <div class="button-row">
            <button class="mini-btn" type="button" data-service="${cardInfo.key}" data-action="start">Start</button>
            <button class="mini-btn ghost" type="button" data-service="${cardInfo.key}" data-action="stop">Stop</button>
          </div>
        ` : ""}
      </div>
    `;
    card.querySelectorAll("[data-service]").forEach(button => {
      button.addEventListener("click", () => serviceControl(button.dataset.service, button.dataset.action));
    });
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
  const production = state.production_health || {};
  const prodSummary = production.summary || {};
  host.innerHTML = `
    <div class="line">
      <strong>Production health</strong><br>
      <span class="micro">${production.ok ? "PASS" : "NEEDS ATTENTION"} / services needing attention ${prodSummary.service_failures || 0}</span>
    </div>
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

function renderChat(state) {
  const host = document.getElementById("chat-log");
  if (!host) return;
  const items = state.operator_chat || [];
  host.innerHTML = "";
  items.slice(-24).forEach(item => {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${item.from === "operator" ? "operator" : "chief"}`;
    bubble.textContent = item.text || "";
    host.appendChild(bubble);
  });
  host.scrollTop = host.scrollHeight;
}

function renderChatStatus(state) {
  const host = document.getElementById("chat-status");
  if (!host) return;
  const phase = state.production_phase || {};
  const commands = state.corrective_commands || [];
  const health = state.production_health || {};
  const text = lastChatStatus || phase.message || "Visualizer is ready.";
  host.className = `chat-status ${health.ok && phase.ready ? "ready" : commands.length ? "failed" : "waiting"}`;
  host.textContent = commands.length ? `${text} Fix: ${commands[0]}` : text;
}

function addLocalChatBubble(text, from = "operator") {
  const host = document.getElementById("chat-log");
  if (!host) return;
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${from}`;
  bubble.textContent = text;
  host.appendChild(bubble);
  host.scrollTop = host.scrollHeight;
}

async function postJson(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`${url} failed: ${res.status}`);
  return res.json();
}

async function toggleRole(role, enabled) {
  lastChatStatus = `${enabled ? "Enabling" : "Disabling"} ${role}...`;
  try {
    await postJson("/api/role-toggle", { role, enabled });
    lastChatStatus = `${role} schedule ${enabled ? "enabled" : "disabled"}.`;
    await refresh();
  } catch (err) {
    console.error(err);
    lastChatStatus = `Could not update ${role}.`;
  }
}

async function serviceControl(service, action) {
  lastChatStatus = `${action} ${service} requested...`;
  try {
    await postJson("/api/service-control", { service, action });
    lastChatStatus = `${service} ${action} request finished.`;
    await refresh();
  } catch (err) {
    console.error(err);
    lastChatStatus = `Could not ${action} ${service}.`;
  }
}

async function sendChatMessage(message) {
  addLocalChatBubble(message, "operator");
  lastChatStatus = "Sent. Runner wake queued; waiting for Chief_of_Staff...";
  fastRefreshUntil = Date.now() + 45000;
  const payload = await postJson("/api/chat", { message });
  if (payload.delivery === "answered") {
    lastChatStatus = "Answered by local control action.";
  } else if ((payload.corrective_commands || []).length) {
    lastChatStatus = payload.production_phase?.message || "Message queued, but the system needs attention.";
  } else {
    lastChatStatus = "Queued. Waiting for the daemonized Chief reply...";
  }
  await refresh();
}

function setupChat() {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  if (!form || !input) return;
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    input.placeholder = "Sending...";
    try {
      await sendChatMessage(message);
    } catch (err) {
      console.error(err);
      input.placeholder = "Could not send. Check Visualizer server.";
      return;
    }
    input.placeholder = "Message Chief_of_Staff from the browser...";
  });
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
    renderChat(state);
    renderChatStatus(state);
  } catch (err) {
    console.error(err);
  }
}

setupChat();
refresh();
setInterval(refresh, 5000);
setInterval(() => {
  if (Date.now() < fastRefreshUntil) refresh();
}, 1200);
