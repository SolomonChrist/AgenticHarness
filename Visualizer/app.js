const stateUrl = "/api/state";

function statusClass(status) {
  if (status === "active") return "active";
  if (status === "stale") return "stale";
  return "unclaimed";
}

function formatLease(row) {
  if (!row.lease_expires_at) return "No lease";
  return `Expires ${row.lease_expires_at}`;
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

function renderWorld(state) {
  const host = document.getElementById("roles-grid");
  host.innerHTML = "";
  state.roles.forEach((row, index) => {
    const card = document.createElement("article");
    card.className = "card agent";
    const x = 18 + (index % 3) * 30;
    const y = 28 + ((index * 17) % 46);
    card.innerHTML = `
      <div class="status ${statusClass(row.status)}">${row.status.toUpperCase()}</div>
      <div class="agent-body">
        <div class="role-meta">${row.claimed_by || "No current holder"}</div>
        <h3>${row.role}</h3>
        <div class="task">${row.task || "No current task"}</div>
        <div class="lease">${formatLease(row)}</div>
        <div class="scene">
          <div class="dot ${statusClass(row.status)}" style="left:${x}%; top:${y}%; color:${row.status === "active" ? "var(--good)" : row.status === "stale" ? "var(--warn)" : "var(--muted)"}"></div>
        </div>
      </div>
    `;
    host.appendChild(card);
  });
}

function renderEvents(state) {
  const host = document.getElementById("events");
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
  host.innerHTML = "";
  state.projects.forEach(project => {
    const item = document.createElement("div");
    item.className = "line";
    item.innerHTML = `<strong>${project.slug}</strong><br><span class="muted">project:${project.has_project} tasks:${project.has_tasks} context:${project.has_context}</span>`;
    host.appendChild(item);
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
  } catch (err) {
    console.error(err);
  }
}

refresh();
setInterval(refresh, 5000);
