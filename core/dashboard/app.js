// Helpers
function escHtml(str) {
    if (!str) return "";
    const p = document.createElement('p');
    p.textContent = str;
    return p.innerHTML;
}

// Views
const V_WORKSPACE = 'workspace-select';
const V_ONBOARDING = 'onboarding';
const V_DASHBOARD = 'dashboard';

let currentStep = 1;
let onboardingData = {};
let refreshInterval = null;
let latestReadinessData = null;
let currentTourStep = -1;
window.CURRENT_WORKSPACE_PATH = window.CURRENT_WORKSPACE_PATH || "";
window.LAST_SWARM_ROSTER = window.LAST_SWARM_ROSTER || [];

// ── GLOBAL STATE (V12.1.2) ──────────────────────────────────────────
let LAST_TASK_STATES = {};

function showNotification(title, message, type = "working") {
    const container = document.getElementById('notification-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `notification-toast ${type}`;
    
    toast.innerHTML = `
        <div class="notification-title">${title}</div>
        <div class="notification-body">${message}</div>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove
    setTimeout(() => {
        toast.classList.add('toast-fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 5000);
}
const TOUR_STEPS = [
    {
        target: 'ready-indicator',
        content: "Wait! I can see your MasterBot is offline. You MUST run 'py core/master_daemon.py' in your terminal before the swarm can hear you.",
        pos: 'bottom'
    },
    {
        target: 'nav-bots',
        content: "First, go here to 'Bot Management' and ensure at least one Specialist is enabled (Provider config must be valid).",
        pos: 'right'
    },
    {
        target: 'tour-restart-btn',
        content: "This is the most important button! Click here to 'Restart Swarm' whenever you change settings or if a bot goes stale. It brings the whole fleet online.",
        pos: 'bottom'
    },
    {
        target: 'nav-terminal',
        content: "This is where you talk to the swarm. Use the composer at the bottom to send instructions.",
        pos: 'right'
    },
    {
        target: 'nav-board',
        content: "Check here to see your requests being decomposed into specific tasks and assigned to workers.",
        pos: 'right'
    }
];

function getTourDoneKey() {
    return `harness_tour_done::${window.CURRENT_WORKSPACE_PATH || 'default'}`;
}

function clearTourForWorkspace(path) {
    window.CURRENT_WORKSPACE_PATH = path || "";
    localStorage.removeItem(getTourDoneKey());
    sessionStorage.removeItem('harness_tour_offered');
}

// Routing logic
async function checkStatus() {
    try {
        const wsRes = await fetch('/api/workspace');
        const wsData = await wsRes.json();
        
        if (!wsData.workspace) {
            showView(V_WORKSPACE);
            return;
        }

        const statRes = await fetch('/api/status');
        const statData = await statRes.json();

        if (statData.is_onboarded) {
            if (window.CURRENT_WORKSPACE_PATH !== (wsData.workspace || "")) {
                clearTourForWorkspace(wsData.workspace || "");
            }
            showView(V_DASHBOARD);
            startAutoRefresh();
            refreshData();
            
            // V12.1 PROACTIVE TOUR: If system is offline on landing, offer help
            setTimeout(() => {
                const sysState = window.SYSTEM_STATE || "NOT_READY";
                if (!sessionStorage.getItem('harness_tour_offered')) {
                    sessionStorage.setItem('harness_tour_offered', 'true');
                    startTour();
                }
            }, 1000);
        } else {
            showView(V_ONBOARDING);
            currentStep = statData.onboarding_state.step || 1;
            onboardingData = statData.onboarding_state.data || {};
            renderFtueStep();
        }
    } catch (e) {
        console.error("Status check failed", e);
    }
}

function showView(viewId) {
    document.getElementById(V_WORKSPACE).classList.add('hidden');
    document.getElementById(V_ONBOARDING).classList.add('hidden');
    document.getElementById(V_DASHBOARD).classList.add('hidden');
    document.getElementById(viewId).classList.remove('hidden');
}

// Workspace Selection
async function setWorkspace(create = false) {
    const path = document.getElementById('ws-path').value.trim();
    if (!path) return;
    
    document.getElementById('ws-error').innerText = "Connecting...";
    document.getElementById('ws-create-btn').classList.add('hidden');
    
    try {
        const res = await fetch('/api/workspace', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({workspace: path, create: create})
        });
        const data = await res.json();
        
        if (data.success) {
            checkStatus();
        } else {
            if (data.error_type === "missing") {
                document.getElementById('ws-error').innerText = "That folder does not exist yet. Please select an existing workspace created by setup.py or INSTALL_HARNESS.bat.";
                document.getElementById('ws-create-btn').classList.remove('hidden');
            } else if (data.error_type === "not_dir") {
                document.getElementById('ws-error').innerText = "The path provided is a file, not a directory.";
            } else if (data.error_type === "uninitialized") {
                document.getElementById('ws-error').innerText = "Folder exists but is not an initialized workspace. Create one here?";
                document.getElementById('ws-create-btn').classList.remove('hidden');
            } else {
                document.getElementById('ws-error').innerText = data.error || "Invalid directory path.";
            }
        }
    } catch (e) {
        document.getElementById('ws-error').innerText = "Connection error.";
    }
}

// FTUE (Onboarding)
function renderFtueStep() {
    const content = document.getElementById('ftue-content');
    const title = document.getElementById('ftue-title');
    
    if (currentStep === 1) {
        title.innerText = "Welcome to Agentic Harness";
        content.innerHTML = `
            <p>This system will guide you through setting up your MasterBot.</p>
            <p>- Your bot is defined by the files you own.</p>
            <p>- Providers (OpenAI, LM Studio) are replaceable engines.</p>
            <p>- You will define your MasterBot's identity now.</p>
        `;
    } else if (currentStep === 2) {
        title.innerText = "Step 2: MasterBot Identity";
        content.innerHTML = `
            <input type="text" id="ftue-name" placeholder="MasterBot Name [MasterBot]">
            <input type="text" id="ftue-role" placeholder="Role Label [Chief of Staff]">
            <input type="text" id="ftue-style" placeholder="Movement Style [calm]">
            <input type="text" id="ftue-purpose" placeholder="Short Purpose [Coordinate work and protect operator time]">
        `;
    } else if (currentStep === 3) {
        title.innerText = "Step 3: Provider Setup";
        content.innerHTML = `
            <select id="ftue-provider">
                <option value="1">OpenAI (Cloud)</option>
                <option value="2">LM Studio (Local)</option>
                <option value="3">Configure Later</option>
            </select>
            <input type="password" id="ftue-apikey" class="mt-1" placeholder="OpenAI API Key (sk-...)">
            <input type="text" id="ftue-baseurl" class="mt-1 hidden" placeholder="LM Studio Base URL [http://localhost:1234/v1]">
        `;
        document.getElementById('ftue-provider').addEventListener('change', (e) => {
            const urlInput = document.getElementById('ftue-baseurl');
            const keyInput = document.getElementById('ftue-apikey');
            if(e.target.value === "1") {
                keyInput.classList.remove('hidden');
                urlInput.classList.add('hidden');
            } else if(e.target.value === "2") {
                keyInput.classList.add('hidden');
                urlInput.classList.remove('hidden');
            } else {
                keyInput.classList.add('hidden');
                urlInput.classList.add('hidden');
            }
        });
    } else if (currentStep === 4) {
        title.innerText = "Step 4: First Project";
        content.innerHTML = `
            <select id="ftue-mkproj">
                <option value="yes">Yes, create a project</option>
                <option value="no">No, skip for now</option>
            </select>
            <div id="proj-inputs" class="mt-1">
                <input type="text" id="ftue-pname" placeholder="Project Name [Research]">
                <input type="text" id="ftue-ppurpose" placeholder="Project Purpose">
                <input type="text" id="ftue-ppath" placeholder="Real Absolute Workspace Path (optional)">
            </div>
        `;
        document.getElementById('ftue-mkproj').addEventListener('change', (e) => {
            const wrap = document.getElementById('proj-inputs');
            if(e.target.value === "yes") wrap.classList.remove('hidden');
            else wrap.classList.add('hidden');
        });
    } else if (currentStep === 5) {
        title.innerText = "Final Step: Ready State";
        content.innerHTML = `<p>MasterBot configured successfully. Ready to generate canonical workspace files.</p>`;
    }
}

async function nextFtueStep() {
    if (currentStep === 2) {
        onboardingData.name = document.getElementById('ftue-name').value || "MasterBot";
        onboardingData.role = document.getElementById('ftue-role').value || "Chief of Staff";
        onboardingData.style = document.getElementById('ftue-style').value || "calm";
        onboardingData.purpose = document.getElementById('ftue-purpose').value || "Coordinate work and protect operator time.";
    } else if (currentStep === 3) {
        onboardingData.provider_choice = document.getElementById('ftue-provider').value;
        if(onboardingData.provider_choice === "1") {
            onboardingData.api_key = document.getElementById('ftue-apikey').value || "";
        } else if(onboardingData.provider_choice === "2") {
            onboardingData.api_base = document.getElementById('ftue-baseurl').value || "http://localhost:1234/v1";
        }
    } else if (currentStep === 4) {
        const mkProj = document.getElementById('ftue-mkproj').value;
        if (mkProj === "yes") {
            onboardingData.create_project = true;
            onboardingData.project_name = document.getElementById('ftue-pname').value || "Research";
            onboardingData.project_purpose = document.getElementById('ftue-ppurpose').value || "Initial research";
            onboardingData.project_path = document.getElementById('ftue-ppath').value || "";
        } else {
            onboardingData.create_project = false;
        }
    }

    try {
        const res = await fetch('/api/onboard/step', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({step: currentStep, data: onboardingData})
        });
        const data = await res.json();
        
        if (data.complete) {
            checkStatus(); // Should move to dashboard
        } else if (data.next_step) {
            currentStep = data.next_step;
            renderFtueStep();
        }
    } catch (e) {
        console.error("FTUE step failed", e);
    }
}

// Dashboard Tabs
function switchTab(tabId) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    
    const navItem = document.querySelector(`.nav-item[onclick="switchTab('${tabId}')"]`);
    if (navItem) {
        navItem.classList.add('active');
        const titleElem = document.getElementById('current-tab-title');
        if (titleElem) titleElem.innerText = navItem.innerText.split('<')[0].trim();
    }
    
    const targetTab = document.getElementById(`tab-${tabId}`);
    if (targetTab) targetTab.classList.add('active');

    if (tabId === 'tasks') {
        refreshTasksOnly();
    }
    if (tabId === 'bots') {
        refreshBots(); // refreshBots now handles restoring selection
    }
    
    // Tutorial Helper Auto-Display (if not dismissed)
    const tutId = `${tabId}-tutorial`;
    const tutElem = document.getElementById(tutId);
    if (tutElem) {
        if (localStorage.getItem(`dismissed-${tutId}`)) {
            tutElem.style.display = 'none';
        } else {
            tutElem.style.display = 'block';
        }
    }
}

function dismissTutorial(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
    localStorage.setItem(`dismissed-${id}`, 'true');
}

function toggleTutorial() {
    const p = document.getElementById('quick-start-panel');
    p.classList.toggle('hidden');
}

// Data fetching
let taskPollInterval = null;

function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    if (taskPollInterval) clearInterval(taskPollInterval);
    // Full data refresh every 10s
    refreshInterval = setInterval(refreshData, 10000);
    // Fast task-only poll every 5s — keeps the task board feeling live
    taskPollInterval = setInterval(refreshTasksOnly, 5000);
}

async function refreshTasksOnly() {
    try {
        const isArchive = document.getElementById('archive-toggle')?.checked;
        if (isArchive) return; // Don't auto-refresh live tasks while looking at archive

        const res = await fetch('/api/tasks');
        if (!res.ok) return;
        const data = await res.json();
        renderTasks(data.tasks || [], data.summary || {});
        
        // Update diagnostics
        const d = data.diagnostics || {};
        const dTasks = document.getElementById('diag-tasks');
        if (dTasks) dTasks.innerText = `L-TASKS: ${d.tasks_total ?? '?'}`;

        const s = data.summary || {};
        // Update task-live-badge (inside the board summary bar)
        const badge = document.getElementById('task-live-badge');
        if (badge) {
            badge.innerText = `${s.active || 0} active · ${s.blocked || 0} blocked · ${s.done || 0} done`;
        }
        // Update sidebar nav badge
        const navCount = document.getElementById('task-nav-count');
        if (navCount) {
            const activeN = s.active || 0;
            navCount.innerText = activeN > 0 ? activeN : '';
            navCount.style.display = activeN > 0 ? 'inline' : 'none';
        }
    } catch(e) { /* silent */ }
}


async function refreshData() {
    try {
        const res = await fetch('/api/data');
        const data = await res.json();
        
        if (data.error) return; 
        
        document.getElementById('ws-current-path').innerText = data.workspace_path || "none";
        if (data.workspace_path && window.CURRENT_WORKSPACE_PATH !== data.workspace_path) {
            clearTourForWorkspace(data.workspace_path);
        }
        document.getElementById('content-status').innerText = data.status || "No Status";
        
        // ── Health Computation ─────────────────────────────────────────────
        let systemHealth = "HEALTHY";
        let healthClass = "health-healthy";
        let nextAction = "System normal. Awaiting instructions.";
        
        const tasks = data.parsed_tasks || [];
        const roster = data.swarm_roster || [];
        window.LAST_SWARM_ROSTER = roster;
        
        // ── Status Transition Detection (V12.1.2 Hardening) ──────────────
        tasks.forEach(t => {
            const prevState = LAST_TASK_STATES[t.id];
            const currentStatus = (t.status || "").toLowerCase();
            
            if (prevState !== undefined && prevState !== currentStatus) {
                const botName = t.owner !== 'none' ? t.owner : t.pref_bot;
                if (currentStatus === "claimed" || currentStatus === "in_progress") {
                    if (prevState === "new") {
                        showNotification("🤖 Task Claimed", `${botName} is now processing: <b>${t.title}</b>`, "working");
                    }
                } else if (currentStatus === "done") {
                    showNotification("✅ Task Complete", `<b>${t.title}</b> finished by ${botName}`, "success");
                }
            }
            LAST_TASK_STATES[t.id] = currentStatus;
        });

        const activeTasks = tasks.filter(t => ['new','claimed','in_progress'].includes(t.status.toLowerCase()));
        const blockedTasks = tasks.filter(t => t.status.toLowerCase() === 'blocked');
        
        let staleCount = 0;
        roster.forEach(bot => {
            if (bot.heartbeat !== "none") {
                const lastHb = new Date(bot.heartbeat);
                if ((new Date() - lastHb) > 60000) staleCount++;
            }
        });

        if (blockedTasks.length > 0) {
            systemHealth = "ATTENTION NEEDED";
            healthClass = "health-blocked";
            nextAction = `Next Action: ${blockedTasks.length} task(s) are blocked. Check Master Tasks.`;
        } else if (staleCount > 0) {
            systemHealth = "STALE BOTS";
            healthClass = "health-stale";
            nextAction = `Next Action: ${staleCount} specialist(s) are stale. Restart recommended.`;
        } else if (activeTasks.length > 0) {
            systemHealth = "WORKING";
            healthClass = "health-working";
            nextAction = "Next Action: Swarm is executing tasks. Monitor Command Center.";
        }

        const healthTag = document.getElementById('health-tag-container');
        if (healthTag) {
            healthTag.innerText = systemHealth;
            healthTag.className = `health-tag ${healthClass}`;
        }
        const tipElem = document.getElementById('next-action-tip');
        if (tipElem) tipElem.innerText = nextAction;

        // ── Render Board v3 ────────────────────────────────────────────────
        const svBots = document.getElementById('sv-bots');
        if (svBots) svBots.innerText = roster.length;
        const svActive = document.getElementById('sv-active');
        if (svActive) svActive.innerText = activeTasks.length;
        const svBlocked = document.getElementById('sv-blocked');
        if (svBlocked) svBlocked.innerText = blockedTasks.length;
        const svStale = document.getElementById('sv-stale');
        if (svStale) svStale.innerText = staleCount;

        const boardActive = document.getElementById('board-active-work');
        if (boardActive) {
            if (activeTasks.length === 0) {
                boardActive.innerHTML = '<div class="subtle small p-1">No active tasks being executed by specialists.</div>';
            } else {
                boardActive.innerHTML = activeTasks.map(t => `
                    <div style="background:var(--bg-panel); border:1px solid var(--border); border-radius:6px; padding:10px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                        <div style="flex:1;">
                            <div style="font-weight:600; font-size:0.9rem; color:var(--accent);">${escHtml(t.title)}</div>
                            <div class="subtle small">🤖 ${t.owner !== 'none' ? t.owner : t.pref_bot} | ${t.id}</div>
                        </div>
                        <div class="health-tag health-working" style="font-size:0.65rem;">${t.status.toUpperCase()}</div>
                    </div>
                `).join("");
            }
        }

        const boardHistory = document.getElementById('board-history');
        if (boardHistory) {
            const history = tasks.filter(t => ['done','cancelled'].includes(t.status.toLowerCase())).slice(0, 5);
            if (history.length === 0) {
                boardHistory.innerHTML = '<div class="subtle small p-1">Recent history is empty.</div>';
            } else {
                boardHistory.innerHTML = history.map(t => `
                    <div class="subtle small" style="padding:6px; border-bottom:1px solid var(--border);">
                        <b>${t.status.toUpperCase()}:</b> ${escHtml(t.title)}
                    </div>
                `).join("");
            }
        }

        // ── Original Syncs ─────────────────────────────────────────────────
        const modeElem = document.getElementById('swarm-bot-mode');
        if (modeElem) {
            modeElem.innerText = (data.bot_mode || "fast").toUpperCase();
            modeElem.style.borderColor = data.bot_mode === "deep" ? "var(--success)" : "var(--border)";
            modeElem.style.color = data.bot_mode === "deep" ? "var(--success)" : "var(--accent)";
        }
        
        const policySelect = document.getElementById('routing-policy-select');
        if (policySelect && data.routing_policy) {
            policySelect.value = data.routing_policy;
        }

        renderTasks(data.parsed_tasks || [], {});
        
        // V12.1 Pending Instruction Banner logic
        const boardActiveParent = document.getElementById('board-active');
        if (data.pending_instruction && (data.parsed_tasks || []).length === 0) {
            const pendingBanner = document.createElement('div');
            pendingBanner.className = "readiness-banner";
            pendingBanner.style.position = "relative";
            pendingBanner.style.left = "0";
            pendingBanner.style.marginBottom = "15px";
            pendingBanner.style.background = "rgba(245, 158, 11, 0.15)";
            pendingBanner.style.border = "1px solid var(--warning)";
            pendingBanner.style.color = "var(--warning)";
            pendingBanner.style.animation = "pulse 2s infinite";
            pendingBanner.innerHTML = `
                <div style="display:flex; align-items:center; gap:10px;">
                    <span>⏳</span>
                    <div>
                        <b>Instruction Pending:</b> Your instruction is in the queue, but the MasterBot is currently offline and cannot process it into tasks.
                    </div>
                </div>
            `;
            if (boardActiveParent) boardActiveParent.prepend(pendingBanner);
        }
        renderSpecialists(data.swarm_roster || []);
        renderChat(data.parsed_comms || [], data.team_communication || "");
        renderLogs(data.parsed_comms || []);
        
        const diag = data.diagnostics || {};
        const dTasks = document.getElementById('diag-tasks');
        const dComms = document.getElementById('diag-comms');
        if (dTasks) dTasks.innerText = `TASKS: ${diag.tasks_total ?? '?'}`;
        if (dComms) dComms.innerText = `COMMS: ${diag.comms_total ?? '?'}`;

        // ── Readiness & Health (Blocker 2 & 3) ───────────────────────────────
        const rd = data.readiness || {};
        const readyInd = document.getElementById('ready-indicator');
        const readyBanner = document.getElementById('readiness-banner');
        
        if (readyInd) {
            window.SYSTEM_STATE = rd.state || "NOT_READY";
            readyInd.innerText = (rd.state || "UNKNOWN").replace("_", " ");
            readyInd.className = `ready-badge ready-${rd.state || "NOT_READY"}`;
            
            // V12.1 Visual Pointer Logic: Help them find the 'Next Step'
            if (rd.state === "NOT_READY" && !document.getElementById('tour-help-pointer')) {
                const pointer = document.createElement('div');
                pointer.id = 'tour-help-pointer';
                pointer.className = 'help-pointer';
                // Position above the 'Quick Start' button tentatively
                const qsBtn = document.querySelector('button[onclick="toggleTutorial()"]');
                if (qsBtn) {
                    const rect = qsBtn.getBoundingClientRect();
                    pointer.style.top = (rect.top - 20) + 'px';
                    pointer.style.left = (rect.left + (rect.width/2) - 10) + 'px';
                    document.body.appendChild(pointer);
                    qsBtn.classList.add('pulse-hint');
                }
            } else if (rd.state !== "NOT_READY") {
                const pointer = document.getElementById('tour-help-pointer');
                if (pointer) pointer.remove();
                const qsBtn = document.querySelector('button[onclick="toggleTutorial()"]');
                if (qsBtn) qsBtn.classList.remove('pulse-hint');
            }
        }

        if (readyBanner) {
            latestReadinessData = rd;
            if (rd.state === "NOT_READY") {
                readyBanner.style.display = "block";
                readyBanner.className = "readiness-banner error";
                document.getElementById('readiness-message').innerHTML = `⚠️ <b>SYSTEM HALTED</b>: ${rd.explanation || "System unconfigured."}`;
                
                // Loud Alert if Master is specifically offline
                if (rd.explanation.includes("OFFLINE")) {
                    document.getElementById('readiness-message').innerHTML = `
                        🚨 <b>DAEMON OFFLINE</b>: ${rd.explanation}
                        <div style="margin-top:10px; font-size:0.8rem; opacity:0.9; background:rgba(0,0,0,0.2); padding:10px; border-radius:4px;">
                            <b>System Health Checklist:</b><br>
                            • [${rd.master_ok ? '✅' : '❌'}] MasterBot Process<br>
                            • [${rd.runnable_workers > 0 ? '✅' : '❌'}] Specialized Workers (${rd.runnable_workers} online)<br>
                            • [${rd.unconfigured === 0 ? '✅' : '❌'}] Provider Configs
                        </div>
                        <div style="margin-top:10px; font-weight:bold; color:var(--accent);">
                            👉 Click the "Quick Start" button in the top right for a guided walkthrough.
                        </div>
                    `;
                }
            } else if (rd.state === "PARTIAL") {
                readyBanner.style.display = "block";
                readyBanner.className = "readiness-banner";
                document.getElementById('readiness-message').innerHTML = `ℹ️ <b>PARTIAL READINESS</b>: ${rd.explanation}`;
                const forceButtons = [document.getElementById('force-submit-btn'), document.getElementById('floating-force-submit-btn')].filter(Boolean);
                forceButtons.forEach((btn) => btn.style.display = 'none');
            } else {
                readyBanner.style.display = "none";
            }
        }
        
        const timestr = new Date().toLocaleTimeString();
        const refreshElem = document.getElementById('last-sync-time');
        if (refreshElem) refreshElem.innerText = timestr;

        // V12.1 FTUE: Auto-start tour if uninitialized or manually requested
        if (currentTourStep === -1 && rd.state === "NOT_READY" && !localStorage.getItem(getTourDoneKey())) {
            startTour();
        }
    } catch (e) {
        console.error("Data refresh failed", e);
    }
}

function renderSpecialists(roster) {
    const container = document.getElementById('content-bots');
    if (!container) return;
    container.innerHTML = "";
    if (roster.length === 0) {
        container.innerHTML = '<div class="subtle">No specialists detected. Start Swarm to discover.</div>';
    } else {
        roster.forEach(bot => {
            const card = document.createElement('div');
            card.className = "bot-card";
            let stale = false;
            if (bot.heartbeat_age !== undefined && bot.heartbeat_age !== -1) {
                stale = bot.heartbeat_age > 60; // 60s threshold
            } else if (bot.heartbeat !== "none") {
                stale = (new Date() - new Date(bot.heartbeat)) > 60000;
            }
            let dotClass = "dot-unknown";
            if (bot.mode === "active") dotClass = stale ? "dot-stale" : "dot-live";
            if (bot.status === "blocked") dotClass = "dot-blocked";
            if (bot.status === "in_progress") dotClass = "dot-working";
            if (bot.heartbeat === "none") dotClass = "dot-inactive";

            card.innerHTML = `
                <div class="bot-card-header">
                    <span class="status-dot ${dotClass}"></span>
                    <span class="bot-name">${bot.name}</span>
                </div>
                <div class="bot-role">${bot.role}</div>
                <div class="bot-details">
                    <span>Status: ${bot.status || 'idle'}</span>
                    <span>${stale ? '<span style="color:var(--error); font-weight:bold;">OFFLINE</span>' : '<span style="color:var(--success);">ONLINE</span>'}</span>
                </div>
                <div class="bot-pill-row">
                    <span class="bot-pill">${escHtml(bot.provider || 'unassigned')}</span>
                    <span class="bot-pill">${escHtml(bot.model || 'no-model')}</span>
                </div>
            `;
            container.appendChild(card);
        });
    }
}

async function renderChat(comms, rawSource = "") {
    const container = document.getElementById('content-comms');
    if (!container) return;
    
    const currentScroll = container.scrollTop;
    const scrollMax = container.scrollHeight - container.clientHeight;
    const isAtBottom = scrollMax <= 0 || (currentScroll >= scrollMax - 80);
    
    const relevantTypes = [
        'instruction', 'response', 'completion', 'blocked', 'reroute', 
        'error', 'report', 'operator_response', 'system_update', 
        'task_complete', 'task_blocked', 'task_reroute', 'announcement'
    ];
    const filtered = comms.filter(c => relevantTypes.includes(c.type?.toLowerCase()) || c.sender?.toLowerCase() === 'operator');
    
    if (filtered.length === 0) {
        if (comms.length > 0 || (rawSource && rawSource.length > 50)) {
            renderFallback('Chat', container, rawSource);
        } else {
            container.innerHTML = '<div class="subtle p-2">Wait for instructions or responses...</div>';
        }
    } else {
        container.innerHTML = filtered.map((c, i) => {
            let bubbleClass = "bubble-bot";
            if (c.sender === "Operator") bubbleClass = "bubble-operator";
            else if (c.sender === "MasterBot") bubbleClass = "bubble-master";
            
            // Noise reduction: check for orchestration syntax
            let body = c.body;
            let orchestrationDetails = "";
            if (body.includes("STEP_KEY:") && body.includes("DELEGATE:")) {
                // Extract human summary if possible or just show a label
                orchestrationDetails = body;
                body = "⚡ Internal Workflow Decomposition Generated.";
            }

            return `
                <div class="chat-bubble ${bubbleClass}">
                    <div class="bubble-meta">
                        <span class="sender-name">${c.sender}</span>
                        <span class="ts">${c.ts?.split('T')[1]?.split('-')[0] || ''}</span>
                    </div>
                    <div class="bubble-body">${escHtml(body)}</div>
                    ${orchestrationDetails ? `
                        <div class="bubble-details-toggle" onclick="const d = this.nextElementSibling; d.style.display = (d.style.display==='block'?'none':'block')">
                            <span>▶ Orchestration Details</span>
                        </div>
                        <div class="bubble-details-content">${escHtml(orchestrationDetails)}</div>
                    ` : `
                        <div class="bubble-details-content" style="display:none; border-top:1px solid rgba(255,255,255,0.05); padding-top:5px; margin-top:8px;">
                            ID: ${c.task_id} | Type: ${c.type}
                        </div>
                    `}
                </div>
            `;
        }).join("");
    }

    if (isAtBottom) container.scrollTop = container.scrollHeight;
    else container.scrollTop = currentScroll;
}

function renderLogs(comms) {
    const logElem = document.getElementById('content-logs');
    if (!logElem) return;

    // Filter for operational noise vs systems events
    const filtered = comms.filter(c => c.sender !== 'Operator').slice(-50); // Last 50 entries

    if (filtered.length === 0) {
        logElem.innerHTML = '<div class="subtle p-2">No operational noise yet.</div>';
        return;
    }

    logElem.innerHTML = filtered.map(c => {
        let typeClass = "color:var(--text-subtle)";
        if (['error','blocked','task_blocked'].includes(c.type?.toLowerCase())) typeClass = "color:var(--error); font-weight:bold;";
        if (['instruction','response'].includes(c.type?.toLowerCase())) typeClass = "color:var(--accent);";
        if (['report','system_update'].includes(c.type?.toLowerCase())) typeClass = "color:var(--success);";

        return `
            <div class="log-entry" style="font-size:0.75rem; border-bottom:1px solid rgba(255,255,255,0.02); padding:4px 0;">
                <span class="ts" style="opacity:0.4;">[${c.ts?.split('T')[1]?.split('.')[0] || ''}]</span>
                <span style="${typeClass}">${c.type?.toUpperCase() || 'EVENT'}</span>
                <span style="color:var(--text-main); opacity:0.8;"> - ${c.sender}: ${escHtml(c.body.substring(0, 120))}${c.body.length > 120 ? '...' : ''}</span>
            </div>
        `;
    }).join("");
    
    logElem.scrollTop = logElem.scrollHeight;
}

function renderFallback(label, container, raw) {
    container.innerHTML = `
        <div class="fallback-view">
            <div class="fallback-header">
                <span>⚠ PARSER FALLBACK [${label.toUpperCase()}]</span>
                <span>DATA DETECTED BUT ZERO MATCHES</span>
            </div>
            <div class="fallback-raw">${escHtml(raw)}</div>
        </div>
    `;
}

async function toggleArchive() {
    const isChecked = document.getElementById('archive-toggle').checked;
    if (isChecked) {
        try {
            const res = await fetch('/api/tasks/archive');
            const data = await res.json();
            renderTasks(data.tasks || [], {total: data.total, active: 0, blocked: 0, done: data.total, cancelled: 0});
        } catch(e) { console.error("Archive fetch failed", e); }
    } else {
        refreshTasksOnly();
    }
}

async function toggleRoutingPolicy() {
    const policy = document.getElementById('routing-policy-select').value;
    const feedback = document.getElementById('policy-feedback');
    feedback.innerText = "Updating policy...";
    try {
        const res = await fetch('/api/system/policy', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({policy: policy})
        });
        const data = await res.json();
        if (data.success) {
            feedback.innerText = `Switched to ${policy} mode.`;
            refreshData();
        } else {
            feedback.innerText = "Error updating policy.";
        }
    } catch(e) { feedback.innerText = "Connection error."; }
}

function renderTasks(tasks, summary) {
    const board = document.getElementById('task-board');
    if (!board) return;

    const currentScroll = board.scrollTop;
    const scrollMax = board.scrollHeight - board.clientHeight;
    const isAtBottom = scrollMax <= 0 || (currentScroll >= scrollMax - 80);

    const s = summary || {};
    const summaryHtml = `
        <div class="task-summary-bar" id="task-summary-bar">
            <span class="tsb-pill tsb-active">⬤ ${s.active ?? 0} Active</span>
            <span class="tsb-pill tsb-waiting">⧗ ${s.waiting ?? 0} Queue</span>
            <span class="tsb-pill tsb-blocked">⚠ ${s.blocked ?? 0} Blocked</span>
            <span class="tsb-pill tsb-done">✔ ${s.done ?? 0} Done</span>
            <span class="tsb-pill tsb-cancelled">✕ ${s.cancelled ?? 0} Cancelled</span>
            <span class="tsb-count">Total: ${s.total ?? 0}</span>
        </div>
    `;

    if (tasks.length === 0) {
        board.innerHTML = summaryHtml + `
            <div class="empty-state" style="text-align:center; padding:40px 20px; opacity:0.8;">
                <div style="font-size:3rem; margin-bottom:15px;">📂</div>
                <h3>Your Task Board is Empty</h3>
                <p class="subtle">Submit your first instruction to the swarm in the <b>Operator Station</b>.</p>
                <div class="empty-prompts" style="display:flex; flex-direction:column; gap:8px; align-items:center; margin-top:20px;">
                    <div class="prompt-suggestion" onclick="suggestion('Create a test.txt file in the workspace.')" style="cursor:pointer; padding:8px 15px; background:var(--bg-panel); border:1px solid var(--border); border-radius:99px; font-size:0.85rem;">📄 "Create a test.txt file"</div>
                    <div class="prompt-suggestion" onclick="suggestion('Research the latest local AI models.')" style="cursor:pointer; padding:8px 15px; background:var(--bg-panel); border:1px solid var(--border); border-radius:99px; font-size:0.85rem;">🔍 "Research local AI models"</div>
                    <div class="prompt-suggestion" onclick="suggestion('Summarize the workspace activity from today.')" style="cursor:pointer; padding:8px 15px; background:var(--bg-panel); border:1px solid var(--border); border-radius:99px; font-size:0.85rem;">📊 "Analyze today's activity"</div>
                </div>
            </div>
        `;
        return;
    }

    const LANE_ORDER = ['new', 'active', 'claimed', 'in_progress', 'blocked', 'waiting', 'done', 'cancelled'];
    const LANE_META = {
        new:         { label: 'New',         color: '#4a9eff', icon: '○' },
        active:      { label: 'Active',       color: '#4a9eff', icon: '○' },
        claimed:     { label: 'Claimed',      color: '#f59e0b', icon: '⧗' },
        in_progress: { label: 'In Progress',  color: '#10b981', icon: '▶' },
        blocked:     { label: 'Blocked',      color: '#ef4444', icon: '⚠' },
        waiting:     { label: 'Queue (Waiting)',color: '#14b8a6', icon: '⧗' },
        done:        { label: 'Done',         color: '#6b7280', icon: '✔' },
        cancelled:   { label: 'Cancelled',    color: '#374151', icon: '✕' },
    };

    const lanes = {};
    tasks.forEach(t => {
        const key = t.status.toLowerCase().replace(' ', '_');
        if (!lanes[key]) lanes[key] = [];
        lanes[key].push(t);
    });

    let html = summaryHtml + '<div class="task-lanes">';

    LANE_ORDER.forEach(laneKey => {
        const items = lanes[laneKey];
        if (!items || items.length === 0) return;
        const meta = LANE_META[laneKey] || { label: laneKey, color: '#888', icon: '?' };

        html += `<div class="task-lane">
            <div class="task-lane-header" style="border-left: 3px solid ${meta.color};">
                <span style="color:${meta.color};">${meta.icon} ${meta.label}</span>
                <span class="lane-count">${items.length}</span>
            </div>`;

        items.forEach(t => {
            const isTerminal = ['done','cancelled'].includes(laneKey);
            const canCancel = !isTerminal;
            const ownerBot = t.owner !== 'none' ? t.owner : (t.pref_bot !== 'none' ? t.pref_bot : 'MasterBot');
            
            let acctHtml = '';
            if (t.rerouted_from) acctHtml += `<span class="task-acct reroute">🔄 From ${t.rerouted_from}</span>`;
            if (t.retry_count && t.retry_count !== '0') acctHtml += `<span class="task-acct retry">📦 Retry #${t.retry_count}</span>`;
            if (t.blocked_reason) acctHtml += `<span class="task-acct blocked-reason">⚠ ${escHtml(t.blocked_reason.substring(0,80))}</span>`;

            let outputActionHtml = '';
            if (laneKey === 'done') {
                const out = (t.outputs || 'none').trim();
                const items = out !== 'none' && out !== '' ? out.split(',').map(i => i.trim()).filter(i => i.length > 0) : [];
                
                if (items.length === 1) {
                    outputActionHtml = `<button onclick="openItem('${ownerBot}', '${escHtml(items[0])}')" class="btn-task" style="border-color:var(--success); color:var(--success);">📄 View Result</button>`;
                } else if (items.length > 1) {
                    outputActionHtml = `<button onclick="showArtifactChooser('${ownerBot}', '${escHtml(out)}')" class="btn-task" style="border-color:var(--accent); color:var(--accent);">📚 View Results (${items.length})</button>`;
                } else {
                    outputActionHtml = `<button onclick="openItem('${ownerBot}', '')" class="btn-task">📂 Open Folder</button>`;
                }
            }

            html += `
            <div class="task-card2" id="tc-${t.id}">
                <div class="tc2-top">
                    <span class="tc2-bot">🤖 ${ownerBot}</span>
                    <span class="tc2-id">${t.id}</span>
                </div>
                <div class="tc2-title">${escHtml(t.title)}</div>
                ${acctHtml ? `<div class="tc2-acct">${acctHtml}</div>` : ''}
                <div class="tc2-footer">
                    <div class="tc2-actions">
                        ${outputActionHtml}
                        ${canCancel ? `<button id="cancel-${t.id}" onclick="cancelTask('${t.id}')" class="btn-cancel">✕ Cancel</button>` : ''}
                        ${isTerminal ? `<button onclick="taskAction('${t.id}', 'archive')" class="btn-archive">Archive</button>` : ''}
                    </div>
                </div>
            </div>`;
        });
        html += `</div>`;
    });

    html += '</div>';
    board.innerHTML = html;

    if (isAtBottom) board.scrollTop = board.scrollHeight;
    else board.scrollTop = currentScroll;
}

function suggestion(text) {
    const input = document.getElementById('operator-input');
    if (input) {
        input.value = text;
        input.focus();
        switchTab('terminal');
    }
}

async function submitEntry(force = false) {
    const inputField = document.getElementById('operator-input');
    const feedback = document.getElementById('operator-feedback');
    const btn = inputField?.closest('.composer-actions')?.querySelector('button') || document.getElementById('submit-btn');
    const msg = inputField.value.trim();
    if(!msg) return;

    // Submit Safety Check (Phase 4)
    if (!force && latestReadinessData && latestReadinessData.state === "NOT_READY") {
        // Only block execution-style requests
        const actionVerbs = ["create", "make", "write", "generate", "research", "analyze", "fix", "update", "audit", "setup", "install", "test", "deploy", "sync"];
        const isExecution = actionVerbs.some(v => msg.toLowerCase().includes(v));
        
        if (isExecution) {
            feedback.innerHTML = `<span style="color:var(--error)">⚠️ <b>System NOT READY</b>. Execution requested. Please configure providers first or use 'Submit Anyway'.</span>`;
            feedback.className = "error small";
            return;
        }
    }

    btn.disabled = true;
    feedback.innerHTML = `<span>⏳ Verifying swarm health...</span>`;
    feedback.className = "success small";

    try {
        const healthRes = await fetch('/api/health');
        const health = await healthRes.json();
        
        let subState = "accepted";
        if (health.status !== "online") {
            subState = "stale";
            feedback.innerHTML = `<span>⚠️ <b>Offline Warning</b>: MasterBot is stale (${Math.round(health.master_age)}s age). Command sent, but may not process immediately.</span>`;
            feedback.className = "warning small";
        } else {
            feedback.innerText = "🚀 Sending to swarm...";
        }

        const res = await fetch('/api/entry', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: msg})
        });
        const data = await res.json();
        
        if (data.success) {
            inputField.value = "";
            if (subState === "accepted") {
                feedback.innerText = "✅ Command accepted and queued.";
            }
            setTimeout(() => { if(feedback.innerText.includes("Command")) feedback.innerText = ""; }, 5000);
            refreshData();
        } else {
            feedback.innerText = "❌ Submission failed: " + data.error;
            feedback.className = "error small";
        }
    } catch (e) {
        feedback.innerText = "❌ Connection error.";
        feedback.className = "error small";
    } finally {
        btn.disabled = false;
    }
}

// Project Registration
async function registerProject() {
    const name = document.getElementById('proj-name').value.trim();
    const path = document.getElementById('proj-path').value.trim();
    if(!name) return;

    try {
        const res = await fetch('/api/projects/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name: name, path: path})
        });
        if (res.ok) {
            document.getElementById('proj-name').value = "";
            document.getElementById('proj-path').value = "";
            refreshData();
        }
    } catch (e) {
        console.error("Failed to register project", e);
    }
}

// System Actions
async function triggerAction(action, target, subtarget, backupPath, overwrite=false) {
    const log = document.getElementById('action-log');
    log.className = "mt-1 small subtle";
    log.innerText = `Executing ${action}...`;

    try {
        const res = await fetch('/api/action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                action: action,
                target: target,
                subtarget: subtarget,
                backup_path: backupPath,
                overwrite: overwrite
            })
        });
        const data = await res.json();
        
        if (data.success) {
            log.className = "mt-1 small success";
            log.innerText = data.message;
        } else {
            log.className = "mt-1 small error";
            log.innerText = "Error: " + data.error;
        }
    } catch (e) {
        log.className = "mt-1 small error";
        log.innerText = "Execution failed.";
    }
}

function triggerBackup() {
    const type = document.getElementById('backup-type').value;
    triggerAction("backup", type, "");
}

function triggerRestore() {
    const path = document.getElementById('restore-path').value.trim();
    const overwrite = document.getElementById('restore-overwrite').checked;
    if(!path) {
        alert("Enter a backup path first.");
        return;
    }
    triggerAction("restore", "full", "", path, overwrite);
}

async function killAllServices() {
    if (!confirm("Are you sure you want to hard-terminate all background Master and Worker bots? You will need to start them manually again.")) return;
    triggerAction("kill_all");
}

function confirmRestartSwarm() {
    // V12.1 UX CLIP: Close tour if a modal is opened to avoid overlay collision
    finishTour();
    document.getElementById('restart-modal').style.display = 'flex';
}

function closeRestartModal() {
    document.getElementById('restart-modal').style.display = 'none';
}

async function restartSwarmDaemons() {
    closeRestartModal();
    const feedback = document.getElementById('operator-feedback');
    feedback.innerHTML = `<span>🔄 <b>Warm Boot: Restarting Swarm...</b> Keeping dashboard alive.</span>`;
    feedback.className = "warning small";
    
    try {
        const res = await fetch('/api/action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action: "restart_daemons"})
        });
        const data = await res.json();
        
        if (data.success) {
            feedback.innerHTML = `<span>⏳ <b>Stabilizing Swarm</b>: New consoles spawned. Verified in 10s...</span>`;
            setTimeout(async () => {
                const hRes = await fetch('/api/health');
                const h = await hRes.json();
                if (h.status === "online") {
                    feedback.innerText = "✅ Warm Boot Successful. Swarm online.";
                    feedback.className = "success small";
                } else {
                    feedback.innerText = "⚠️ Warm Boot complete, but MasterBot is still initializing.";
                    feedback.className = "warning small";
                }
            }, 10000);
        } else {
            feedback.innerText = "❌ Warm Boot failed: " + data.error;
            feedback.className = "error small";
        }
    } catch (e) {
        feedback.innerText = "❌ Connection error during restart.";
    }
}

async function openItem(botName, item) {
    try {
        const res = await fetch('/api/open-item', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({bot_name: botName, item: item})
        });
    } catch (e) { console.error("Open item failed", e); }
}

function showArtifactChooser(bot, outString) {
    const container = document.getElementById('artifact-list');
    const modal = document.getElementById('artifact-modal');
    container.innerHTML = "";
    
    const items = outString.split(',').map(i => i.trim()).filter(i => i.length > 0);
    items.forEach(item => {
        const d = document.createElement('div');
        d.className = "list-item";
        d.innerHTML = `📄 ${item}`;
        d.onclick = () => {
            openItem(bot, item);
            hideArtifactModal();
        };
        container.appendChild(d);
    });
    
    modal.style.display = 'flex';
}

function hideArtifactModal() {
    document.getElementById('artifact-modal').style.display = 'none';
}

async function toggleBotMode() {
    const mode = document.getElementById('bot-mode-select').value;
    const feedback = document.getElementById('mode-feedback');
    feedback.innerText = "Switching mode...";
    try {
        const res = await fetch('/api/bot/mode', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mode: mode})
        });
        const data = await res.json();
        if (data.success) {
            feedback.innerText = `Switched to ${mode.toUpperCase()} mode.`;
            refreshData();
        }
    } catch(e) { feedback.innerText = "Error toggling mode."; }
}

// Bot Management
let activeBotName = null;
let activeBotFile = null;

async function refreshBots() {
    try {
        const res = await fetch('/api/bots');
        const data = await res.json();
        const container = document.getElementById('bot-list');
        container.innerHTML = "";
        const rosterMap = new Map((window.LAST_SWARM_ROSTER || []).map(bot => [String(bot.name || '').toLowerCase(), bot]));
        
        // Restore persistence
        if (!activeBotName) activeBotName = localStorage.getItem('activeBotName');
        if (!activeBotFile) activeBotFile = localStorage.getItem('activeBotFile');

        data.bots.forEach(bot => {
            const live = rosterMap.get(String(bot).toLowerCase()) || {};
            const stale = typeof live.heartbeat_age === 'number' ? live.heartbeat_age > 60 : false;
            let dotClass = "dot-unknown";
            if (live.status === "blocked") dotClass = "dot-blocked";
            else if (live.status === "in_progress") dotClass = "dot-working";
            else if (live.heartbeat === "none") dotClass = "dot-inactive";
            else if (live.name) dotClass = stale ? "dot-stale" : "dot-live";
            const d = document.createElement('div');
            d.className = "list-item";
            if (activeBotName === bot) {
                d.classList.add('selected');
                // Auto-load files for the persistsed bot
                setTimeout(() => selectBot(bot, d, true), 50); 
            }
            d.innerHTML = `
                <div class="bot-card-header">
                    <span class="status-dot ${dotClass}"></span>
                    <span class="bot-list-card-name">${escHtml(bot)}</span>
                </div>
                <div class="bot-list-card-meta">
                    <span>${escHtml(live.role || 'specialist')}</span>
                    <span>${escHtml(live.provider || 'provider?')}</span>
                    <span>${escHtml(live.model || 'model?')}</span>
                </div>
                <div class="bot-list-card-focus">${escHtml(live.focus || live.activity || live.status || 'Standing by')}</div>
            `;
            d.onclick = () => selectBot(bot, d);
            container.appendChild(d);
        });
    } catch(e) { console.error("Failed to load bots"); }
}

function selectBot(botName, elem, isRestoring = false) {
    document.querySelectorAll('#bot-list .list-item').forEach(e => e.classList.remove('selected'));
    if(elem) elem.classList.add('selected');
    activeBotName = botName;
    localStorage.setItem('activeBotName', botName);
    
    // Group files for better UX
    const groups = [
        { label: "Core Identity", files: ["Identity.md", "Soul.md", "Skills.md", "RolePolicies.md"] },
        { label: "Runtime State", files: ["Status.md", "Heartbeat.md", "Lease.json"] },
        { label: "Configuration", files: ["HarnessProfile.json", "ProviderProfile.json", "RuntimeProfile.json"] },
        { label: "Long-term Memory", files: ["Memory.md", "Learnings.md"] }
    ];
    
    const container = document.getElementById('bot-file-list');
    container.innerHTML = "";
    
    groups.forEach(group => {
        const shell = document.createElement('div');
        shell.className = "bot-file-group";
        const header = document.createElement('div');
        header.className = "section-label";
        header.style.fontSize = "0.65rem";
        header.innerText = group.label;
        shell.appendChild(header);

        group.files.forEach(file => {
            const d = document.createElement('div');
            d.className = "list-item";
            if (activeBotFile === file) {
                d.classList.add('selected');
                if (isRestoring) selectBotFile(file, d);
            }
            d.innerText = file;
            d.onclick = () => selectBotFile(file, d);
            shell.appendChild(d);
        });
        container.appendChild(shell);
    });
    
    if (!isRestoring) resetEditor();
}

function selectBotFile(fileName, elem) {
    document.querySelectorAll('#bot-file-list .list-item').forEach(e => e.classList.remove('selected'));
    if(elem) elem.classList.add('selected');
    activeBotFile = fileName;
    localStorage.setItem('activeBotFile', fileName);
    
    loadBotFileContent();
}

async function selectBotFile(filename, elem) {
    document.querySelectorAll('#bot-file-list .list-item').forEach(e => e.classList.remove('selected'));
    if(elem) elem.classList.add('selected');
    activeBotFile = filename;
    
    document.getElementById('bot-editor-title').innerText = `${activeBotName} / ${filename}`;
    document.getElementById('bot-save-btn').style.display = 'block';
    
    try {
        const res = await fetch(`/api/bot/${activeBotName}/file/${filename}`);
        const data = await res.json();
        
        if (filename === "ProviderProfile.json") {
            document.getElementById('bot-file-editor').style.display = 'none';
            document.getElementById('bot-provider-form').style.display = 'flex';
            populateProviderForm(data.content);
        } else {
            document.getElementById('bot-provider-form').style.display = 'none';
            document.getElementById('bot-file-editor').style.display = 'block';
            document.getElementById('bot-file-editor').value = data.content || "";
        }
    } catch (e) { console.error("Failed to load file"); }
}

function resetEditor() {
    activeBotFile = null;
    document.getElementById('bot-editor-title').innerText = "Editor";
    document.getElementById('bot-save-btn').style.display = 'none';
    document.getElementById('bot-file-editor').style.display = 'none';
    document.getElementById('bot-provider-form').style.display = 'none';
}

function populateProviderForm(content) {
    let data = {};
    try { data = JSON.parse(content); } catch(e){}
    
    // Auto-migrate raw keys incorrectly saved in api_key_env
    let keyVal = data.api_key || "";
    let legacyEnv = data.api_key_env || "";
    if (!keyVal && legacyEnv && (legacyEnv.startsWith("sk-") || legacyEnv.length > 30)) {
        keyVal = legacyEnv;
        legacyEnv = "";
    }
    
    document.getElementById('prov-enabled').checked = !!data.enabled;
    document.getElementById('prov-provider').value = data.provider || "PLACEHOLDER";
    document.getElementById('prov-model').value = data.model || "";
    document.getElementById('prov-base').value = data.api_base || "";
    document.getElementById('prov-key').value = keyVal;
    
    const statusText = document.getElementById('prov-status-text');
    
    if (keyVal) {
        statusText.innerText = "Loaded: Plaintext API Key";
        statusText.style.color = "var(--success)";
    } else if (legacyEnv) {
        statusText.innerText = `Loaded: Legacy Environment Variable [${legacyEnv}]`;
        statusText.style.color = "var(--error)";
    } else if (!data.enabled) {
        statusText.innerText = "Configured (Disabled)";
        statusText.style.color = "inherit";
    } else {
        statusText.innerText = "Unconfigured / Empty";
        statusText.style.color = "var(--error)";
    }
}

function dumpProviderForm() {
    return JSON.stringify({
        enabled: document.getElementById('prov-enabled').checked,
        provider: document.getElementById('prov-provider').value,
        model: document.getElementById('prov-model').value,
        api_base: document.getElementById('prov-base').value,
        api_key: document.getElementById('prov-key').value
    }, null, 2);
}

async function saveBotFile() {
    if(!activeBotName || !activeBotFile) return;
    
    const feedback = document.getElementById('bot-save-feedback');
    const saveBtn = document.getElementById('bot-save-btn');
    const originalText = saveBtn.innerText;
    
    let content = "";
    if (activeBotFile === "ProviderProfile.json") {
        const isEnabled = document.getElementById('prov-enabled').checked;
        const provider = document.getElementById('prov-provider').value;
        const key = document.getElementById('prov-key').value.trim();
        
        if (isEnabled && (provider === "openai" || provider === "anthropic") && !key) {
            feedback.innerText = "Error: API Key is required for cloud providers.";
            feedback.style.color = "#ff6b6b";
            return;
        }
        content = dumpProviderForm();
    } else {
        content = document.getElementById('bot-file-editor').value;
    }

    // UI Feedback: Disable and show saving
    saveBtn.disabled = true;
    saveBtn.innerText = "Saving...";
    feedback.innerText = "Synchronizing with file system...";
    feedback.style.color = "var(--text-main)";
    
    try {
        const res = await fetch(`/api/bot/${activeBotName}/file/${activeBotFile}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({content: content})
        });
        const data = await res.json();
        
        if(data.success) {
            saveBtn.innerText = "✅ Saved!";
            saveBtn.classList.add('btn-success-flash');
            feedback.innerText = "File saved successfully.";
            feedback.style.color = "var(--success)";
            
            setTimeout(() => {
                saveBtn.disabled = false;
                saveBtn.innerText = originalText;
                saveBtn.classList.remove('btn-success-flash');
                feedback.innerText = "";
            }, 1500);
        } else {
            saveBtn.disabled = false;
            saveBtn.innerText = originalText;
            feedback.innerText = "Error saving file.";
            feedback.style.color = "#ff6b6b";
        }
    } catch(e) {
        saveBtn.disabled = false;
        saveBtn.innerText = originalText;
        feedback.innerText = "Connection error.";
        feedback.style.color = "#ff6b6b";
    }
}

// Bot Creation
function showCreateBotModal() {
    document.getElementById('create-bot-modal').style.display = 'flex';
}

function hideCreateBotModal() {
    document.getElementById('create-bot-modal').style.display = 'none';
}

async function createNewBot() {
    const name = document.getElementById('new-bot-name').value.trim();
    if (!name) { alert("Name is required"); return; }

    const payload = {
        name: name,
        role: document.getElementById('new-bot-role').value || "specialist",
        harness: document.getElementById('new-bot-harness').value,
        style: document.getElementById('new-bot-style').value,
        provider: document.getElementById('new-bot-provider').value,
        model: document.getElementById('new-bot-model').value || "gpt-4-turbo",
        purpose: document.getElementById('new-bot-purpose').value,
        skills: document.getElementById('new-bot-skills').value,
        tools: document.getElementById('new-bot-tools').value,
        work_types: document.getElementById('new-bot-work-types').value
    };

    try {
        const res = await fetch('/api/bots/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            hideCreateBotModal();
            refreshBots();
        } else {
            alert("Error: " + data.error);
        }
    } catch (e) {
        alert("Failed to connect to server.");
    }
}

// Init
window.onload = () => {
    checkStatus();
    
    const opInput = document.getElementById('operator-input');
    if (opInput) {
        opInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                submitEntry();
            }
        });
    }

    const floatingInput = document.getElementById('floating-operator-input');
    if (floatingInput) {
        floatingInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitEntry(false, 'floating-operator-input');
            }
        });
    }
};

async function quickStart() {
    const feedback = document.getElementById('operator-feedback');
    if (feedback) {
        feedback.innerText = "⚡ Initializing high-performance providers...";
        feedback.className = "success small";
    }
    
    try {
        // 1. Force MasterBot to DEEP mode (Persisted via SystemProfile.json)
        await fetch('/api/bot/mode', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mode: 'deep'})
        });
        
        // 2. Enable MasterBot provider
        await fetch('/api/bot/MasterBot/file/ProviderProfile.json', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({content: JSON.stringify({
                enabled: true,
                provider: "lmstudio",
                api_base: "http://localhost:1234/v1",
                api_key: "lm-studio",
                model: "model-identifier"
            }, null, 2)})
        });
        
        if (feedback) feedback.innerText = "✅ Swarm ready for DEEP orchestration.";
        setTimeout(() => { if (feedback) feedback.innerText = ""; }, 3000);
        refreshData();
    } catch (e) {
        if (feedback) {
            feedback.innerText = "❌ Quick start failed.";
            feedback.className = "error small";
        }
    }
}

// ── Guided Tour Logic ───────────────────────────────────────────────
function startTour() {
    currentTourStep = 0;
    document.getElementById('tour-overlay').classList.remove('hidden');
    renderTourStep();
}

function nextTourStep() {
    currentTourStep++;
    if (currentTourStep >= TOUR_STEPS.length) {
        finishTour();
    } else {
        renderTourStep();
    }
}

function skipTour() {
    finishTour();
}

function finishTour() {
    currentTourStep = -1;
    document.getElementById('tour-overlay').classList.add('hidden');
    localStorage.setItem(getTourDoneKey(), 'true');
    // Remove any leftover highlights
    document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight', 'tour-highlight-active'));
    
    // V12.1 FINAL FTUE HARDENING: Automated Restart Prompt
    const sysState = window.SYSTEM_STATE || "NOT_READY";
    if (sysState === "NOT_READY") {
        if (confirm("Onboarding Complete! Would you like to bring your Agentic Swarm online now? (This will spawn the MasterBot and Specialist terminal windows)")) {
            confirmRestartSwarm();
        }
    }
}

function renderTourStep() {
    const step = TOUR_STEPS[currentTourStep];
    const target = document.getElementById(step.target);
    const tooltip = document.getElementById('tour-tooltip');
    const content = document.getElementById('tour-content');
    
    // Cleanup previous
    document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight', 'tour-highlight-active'));
    
    if (!target) {
        nextTourStep();
        return;
    }

    target.classList.add('tour-highlight', 'tour-highlight-active');
    
    // V12.1 Dynamic Tour Content
    let stepContent = step.content;
    const sysState = window.SYSTEM_STATE || "NOT_READY";
    
    if (currentTourStep === 0) {
        if (sysState !== "NOT_READY") {
            stepContent = "Success! Your MasterBot is online and ready for instructions.";
        }
    } else if (currentTourStep === 4) {
        if (sysState === "NOT_READY") {
            stepContent = "The system is currently OFFLINE. Click the 'Quick Start' button to bring your Swarm online now!";
        }
    }
    
    content.innerText = stepContent;
    
    // Switch tab if needed
    if (step.target.startsWith('nav-')) {
        const tab = step.target.replace('nav-', '');
        if (tab !== 'terminal') switchTab(tab); 
    }

    const rect = target.getBoundingClientRect();
    const pad = 15;
    const ttW = 320; 
    const winW = window.innerWidth;
    const winH = window.innerHeight;

    let left = rect.left;
    let top = rect.bottom + pad;
    
    if (step.pos === 'right') {
        left = rect.right + pad;
        top = rect.top;
        document.querySelector('.tour-arrow').className = 'tour-arrow tour-arrow-left';
    } else if (step.pos === 'bottom') {
        left = rect.left + (rect.width/2) - (ttW/2);
        top = rect.bottom + pad;
        document.querySelector('.tour-arrow').className = 'tour-arrow tour-arrow-top';
    }

    // Viewport Boundary Guard (V12.1.2 Hardening)
    if (left + ttW > winW - 20) left = winW - ttW - 20;
    if (left < 20) left = 20;
    if (top + 250 > winH - 20) top = rect.top - 250 - pad; // Flip up if no room

    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    
    document.getElementById('tour-next-btn').innerText = (currentTourStep === TOUR_STEPS.length - 1) ? "Finish" : "Next";
}

window.toggleTutorial = function() {
    localStorage.removeItem(getTourDoneKey());
    startTour();
};

// Launch polish overrides: compact console + cleaner bot management
const BOT_FILE_GROUPS = [
    { label: "Core Identity", files: ["Identity.md", "Soul.md", "Skills.md", "RolePolicies.md"] },
    { label: "Runtime State", files: ["Status.md", "Heartbeat.md", "Lease.json"] },
    { label: "Configuration", files: ["HarnessProfile.json", "ProviderProfile.json", "RuntimeProfile.json"] },
    { label: "Long-term Memory", files: ["Memory.md", "Learnings.md"] }
];

function buildChatMarkup(comms, rawSource = "") {
    const relevantTypes = [
        'instruction', 'response', 'completion', 'blocked', 'reroute',
        'error', 'report', 'operator_response', 'system_update',
        'task_complete', 'task_blocked', 'task_reroute', 'announcement'
    ];
    const filtered = comms.filter(c => relevantTypes.includes(c.type?.toLowerCase()) || c.sender?.toLowerCase() === 'operator');
    if (filtered.length === 0) {
        if (comms.length > 0 || (rawSource && rawSource.length > 50)) {
            return `
                <div class="fallback-view">
                    <div class="fallback-header">
                        <span>⚠ PARSER FALLBACK [CHAT]</span>
                        <span>DATA DETECTED BUT ZERO MATCHES</span>
                    </div>
                    <div class="fallback-raw">${escHtml(rawSource)}</div>
                </div>
            `;
        }
        return '<div class="subtle p-2">Wait for instructions or responses...</div>';
    }

    return filtered.map((c) => {
        let bubbleClass = "bubble-bot";
        if (c.sender === "Operator") bubbleClass = "bubble-operator";
        else if (c.sender === "MasterBot") bubbleClass = "bubble-master";

        let body = c.body || "";
        let orchestrationDetails = "";
        if (body.includes("STEP_KEY:") && body.includes("DELEGATE:")) {
            orchestrationDetails = body;
            body = "⚡ Internal Workflow Decomposition Generated.";
        }

        return `
            <div class="chat-bubble ${bubbleClass}">
                <div class="bubble-meta">
                    <span class="sender-name">${c.sender}</span>
                    <span class="ts">${c.ts?.split('T')[1]?.split('-')[0] || ''}</span>
                </div>
                <div class="bubble-body">${escHtml(body)}</div>
                ${orchestrationDetails ? `
                    <div class="bubble-details-toggle" onclick="const d = this.nextElementSibling; d.style.display = (d.style.display==='block'?'none':'block')">
                        <span>▶ Orchestration Details</span>
                    </div>
                    <div class="bubble-details-content">${escHtml(orchestrationDetails)}</div>
                ` : `
                    <div class="bubble-details-content" style="display:none; border-top:1px solid rgba(255,255,255,0.05); padding-top:5px; margin-top:8px;">
                        ID: ${c.task_id} | Type: ${c.type}
                    </div>
                `}
            </div>
        `;
    }).join("");
}

async function renderChat(comms, rawSource = "") {
    const targets = [
        document.getElementById('content-comms'),
        document.getElementById('floating-console-chat')
    ].filter(Boolean);
    if (!targets.length) return;

    const markup = buildChatMarkup(comms, rawSource);
    targets.forEach((target) => {
        const currentScroll = target.scrollTop;
        const scrollMax = target.scrollHeight - target.clientHeight;
        const isAtBottom = scrollMax <= 0 || (currentScroll >= scrollMax - 80);
        target.innerHTML = markup;
        if (isAtBottom) target.scrollTop = target.scrollHeight;
        else target.scrollTop = currentScroll;
    });
}

function toggleOperatorConsole(forceOpen) {
    const shell = document.getElementById('operator-console-shell');
    if (!shell) return;
    const shouldOpen = typeof forceOpen === 'boolean' ? forceOpen : !shell.classList.contains('open');
    shell.classList.toggle('open', shouldOpen);
    if (shouldOpen) {
        const main = document.getElementById('operator-input');
        const floating = document.getElementById('floating-operator-input');
        if (main && floating && !floating.value) floating.value = main.value;
        setTimeout(() => floating?.focus(), 40);
    }
}

function normalizeDashboardChrome() {
    const footer = document.querySelector('.global-footer');
    if (footer) {
        footer.querySelectorAll('#composer-mode-label, .composer-actions, #readiness-banner, #operator-input, #submit-btn').forEach((node) => node.remove());
        footer.querySelectorAll(':scope > div').forEach((node) => {
            const keep = node.id === 'operator-feedback' || node.id === 'diagnostics-footer' || node.classList?.contains('footer-marketing');
            if (!keep) node.remove();
        });
    }

    const editorTitle = document.getElementById('bot-editor-title');
    if (editorTitle && !editorTitle.dataset.defaultTitle) editorTitle.dataset.defaultTitle = editorTitle.textContent;
    const editor = document.getElementById('bot-file-editor');
    if (editor && !editor.placeholder) editor.placeholder = 'Select a bot, then choose a file from the dropdown to begin editing.';
}

function copyOperatorDraftToMain() {
    const main = document.getElementById('operator-input');
    const floating = document.getElementById('floating-operator-input');
    if (!main || !floating) return;
    main.value = floating.value;
    main.focus();
}

async function submitEntry(force = false, inputId = 'operator-input') {
    const inputField = document.getElementById(inputId);
    const feedback = document.getElementById('operator-feedback');
    const btn = inputField?.closest('.composer-actions')?.querySelector('button') || document.getElementById('submit-btn');
    const msg = inputField?.value.trim();
    if (!msg) return;

    if (!force && latestReadinessData && latestReadinessData.state === "NOT_READY") {
        const actionVerbs = ["create", "make", "write", "generate", "research", "analyze", "fix", "update", "audit", "setup", "install", "test", "deploy", "sync"];
        const isExecution = actionVerbs.some(v => msg.toLowerCase().includes(v));
        if (isExecution) {
            feedback.innerHTML = `<span style="color:var(--error)">⚠️ <b>System NOT READY</b>. Execution requested. Please configure providers first or use 'Submit Anyway'.</span>`;
            feedback.className = "error small";
            return;
        }
    }

    btn.disabled = true;
    feedback.innerHTML = `<span>⏳ Verifying swarm health...</span>`;
    feedback.className = "success small";

    try {
        const healthRes = await fetch('/api/health');
        const health = await healthRes.json();

        let subState = "accepted";
        if (health.status !== "online") {
            subState = "stale";
            feedback.innerHTML = `<span>⚠️ <b>Offline Warning</b>: MasterBot is stale (${Math.round(health.master_age)}s age). Command sent, but may not process immediately.</span>`;
            feedback.className = "warning small";
        } else {
            feedback.innerText = "🚀 Sending to swarm...";
        }

        const res = await fetch('/api/entry', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: msg})
        });
        const data = await res.json();

        if (data.success) {
            inputField.value = "";
            if (inputId === 'floating-operator-input') {
                const mainInput = document.getElementById('operator-input');
                if (mainInput) mainInput.value = "";
            }
            if (subState === "accepted") feedback.innerText = "✅ Command accepted and queued.";
            setTimeout(() => { if(feedback.innerText.includes("Command")) feedback.innerText = ""; }, 5000);
            refreshData();
        } else {
            feedback.innerText = "❌ Submission failed: " + data.error;
            feedback.className = "error small";
        }
    } catch (e) {
        feedback.innerText = "❌ Connection error.";
        feedback.className = "error small";
    } finally {
        btn.disabled = false;
    }
}

function getLiveBot(botName) {
    const rosterMap = new Map((window.LAST_SWARM_ROSTER || []).map(bot => [String(bot.name || '').toLowerCase(), bot]));
    return rosterMap.get(String(botName || '').toLowerCase()) || {};
}

function renderBotOverview(botName) {
    const card = document.getElementById('bot-overview-card');
    if (!card) return;
    if (!botName) {
        card.innerHTML = `<div class="subtle small">Choose a bot to see its role, provider, model, and live focus.</div>`;
        return;
    }
    const live = getLiveBot(botName);
    const status = live.status || live.activity || 'idle';
    const focus = live.focus || live.activity || 'Standing by';
    card.innerHTML = `
        <div class="bot-overview-title">${escHtml(botName)}</div>
        <div class="subtle small">${escHtml(live.role || 'specialist')}</div>
        <div class="bot-overview-grid">
            <div class="bot-overview-stat">
                <div class="bot-overview-stat-label">Provider</div>
                <div class="bot-overview-stat-value">${escHtml(live.provider || 'unconfigured')}</div>
            </div>
            <div class="bot-overview-stat">
                <div class="bot-overview-stat-label">Model</div>
                <div class="bot-overview-stat-value">${escHtml(live.model || 'not set')}</div>
            </div>
            <div class="bot-overview-stat">
                <div class="bot-overview-stat-label">Status</div>
                <div class="bot-overview-stat-value">${escHtml(status)}</div>
            </div>
            <div class="bot-overview-stat">
                <div class="bot-overview-stat-label">Focus</div>
                <div class="bot-overview-stat-value">${escHtml(focus)}</div>
            </div>
        </div>
    `;
}

function renderBotFileGroups() {
    const container = document.getElementById('bot-file-list');
    if (!container) return;
    if (!activeBotName) {
        container.innerHTML = '<div class="subtle small p-1">Pick a bot to load a file. The dropdown above is the main control.</div>';
        return;
    }
    container.innerHTML = `
        <div class="subtle small p-1">
            <strong>${escHtml(activeBotName)}</strong> has ${BOT_FILE_GROUPS.reduce((count, group) => count + group.files.length, 0)} managed files across
            ${BOT_FILE_GROUPS.length} categories. Use the dropdown above to open the exact file you want to edit.
        </div>
    `;
}

function populateBotFileDropdown() {
    const dropdown = document.getElementById('bot-file-dropdown');
    if (!dropdown) return;
    dropdown.innerHTML = '<option value="">Select a file...</option>';
    if (!activeBotName) return;

    BOT_FILE_GROUPS.forEach(group => {
        const optgroup = document.createElement('optgroup');
        optgroup.label = group.label;
        group.files.forEach((file) => {
            const opt = document.createElement('option');
            opt.value = file;
            opt.textContent = file;
            if (activeBotFile === file) opt.selected = true;
            optgroup.appendChild(opt);
        });
        dropdown.appendChild(optgroup);
    });
}

async function refreshBots() {
    try {
        const res = await fetch('/api/bots');
        const data = await res.json();
        const dropdown = document.getElementById('bot-select-dropdown');
        if (!dropdown) return;

        if (!activeBotName) activeBotName = localStorage.getItem('activeBotName');
        if (!activeBotFile) activeBotFile = localStorage.getItem('activeBotFile');

        dropdown.innerHTML = '<option value="">Select a bot...</option>';
        data.bots.forEach((bot) => {
            const live = getLiveBot(bot);
            const opt = document.createElement('option');
            opt.value = bot;
            opt.textContent = live.provider ? `${bot} · ${live.provider}` : bot;
            if (activeBotName === bot) opt.selected = true;
            dropdown.appendChild(opt);
        });

        if (activeBotName && data.bots.includes(activeBotName)) {
            renderBotOverview(activeBotName);
            renderBotFileGroups();
            populateBotFileDropdown();
            if (activeBotFile) setTimeout(() => openBotFile(activeBotFile), 40);
        } else {
            activeBotName = null;
            activeBotFile = null;
            renderBotOverview(null);
            renderBotFileGroups();
            populateBotFileDropdown();
            resetEditor();
        }
    } catch (e) {
        console.error("Failed to load bots", e);
    }
}

function onBotDropdownChange() {
    const dropdown = document.getElementById('bot-select-dropdown');
    activeBotName = dropdown?.value || null;
    localStorage.setItem('activeBotName', activeBotName || '');
    activeBotFile = null;
    localStorage.removeItem('activeBotFile');
    renderBotOverview(activeBotName);
    renderBotFileGroups();
    populateBotFileDropdown();
    resetEditor();
}

function onBotFileDropdownChange() {
    const dropdown = document.getElementById('bot-file-dropdown');
    const file = dropdown?.value || null;
    if (!file) return;
    openBotFile(file);
}

async function openBotFile(filename) {
    if (!activeBotName || !filename) return;
    activeBotFile = filename;
    localStorage.setItem('activeBotFile', filename);
    document.getElementById('bot-editor-title').innerText = `${activeBotName} / ${filename}`;
    document.getElementById('bot-save-btn').style.display = 'block';

    try {
        const res = await fetch(`/api/bot/${activeBotName}/file/${filename}`);
        const data = await res.json();
        if (filename === "ProviderProfile.json") {
            document.getElementById('bot-file-editor').style.display = 'none';
            document.getElementById('bot-provider-form').style.display = 'flex';
            populateProviderForm(data.content);
        } else {
            document.getElementById('bot-provider-form').style.display = 'none';
            document.getElementById('bot-file-editor').style.display = 'block';
            document.getElementById('bot-file-editor').value = data.content || "";
        }
        populateBotFileDropdown();
    } catch (e) {
        console.error("Failed to load file", e);
    }
}

function normalizeDashboardChrome() {
    const footer = document.querySelector('.global-footer');
    if (footer) {
        footer.querySelectorAll('#composer-mode-label, .composer-actions, #readiness-banner, #operator-input, #submit-btn').forEach((node) => node.remove());
        footer.querySelectorAll(':scope > div').forEach((node) => {
            const keep = node.id === 'operator-feedback' || node.id === 'diagnostics-footer' || node.classList?.contains('footer-marketing');
            if (!keep) node.remove();
        });
    }

    const title = document.getElementById('bot-editor-title');
    if (title && !title.dataset.defaultTitle) title.dataset.defaultTitle = title.textContent;
    const editor = document.getElementById('bot-file-editor');
    if (editor) editor.placeholder = 'Select a bot and choose a file from the dropdown to begin editing.';
}

function renderBotFileGroups() {
    const container = document.getElementById('bot-file-list');
    if (!container) return;
    container.innerHTML = activeBotName
        ? `<div class="subtle small p-1"><strong>${escHtml(activeBotName)}</strong> is selected. Use the dropdown above to jump straight to a file.</div>`
        : '<div class="subtle small p-1">Pick a bot to load a file. The dropdown above is the main control.</div>';
}

async function refreshBots() {
    try {
        const res = await fetch('/api/bots');
        const data = await res.json();
        const dropdown = document.getElementById('bot-select-dropdown');
        if (!dropdown) return;

        if (!activeBotName) activeBotName = localStorage.getItem('activeBotName');
        if (!activeBotFile) activeBotFile = localStorage.getItem('activeBotFile');

        dropdown.innerHTML = '<option value="">Select a bot...</option>';
        data.bots.forEach((bot) => {
            const live = getLiveBot(bot);
            const opt = document.createElement('option');
            opt.value = bot;
            opt.textContent = live.provider ? `${bot} · ${live.provider}` : bot;
            if (activeBotName === bot) opt.selected = true;
            dropdown.appendChild(opt);
        });

        if (activeBotName && data.bots.includes(activeBotName)) {
            renderBotOverview(activeBotName);
            renderBotFileGroups();
            populateBotFileDropdown();
            if (activeBotFile) setTimeout(() => openBotFile(activeBotFile), 40);
        } else {
            activeBotName = null;
            activeBotFile = null;
            renderBotOverview(null);
            renderBotFileGroups();
            populateBotFileDropdown();
            resetEditor();
        }

        normalizeDashboardChrome();
    } catch (e) {
        console.error("Failed to load bots", e);
    }
}

async function submitEntry(force = false, inputId = 'operator-input') {
    const inputField = document.getElementById(inputId);
    const feedback = document.getElementById('operator-feedback');
    const btn = inputField?.closest('.composer-actions')?.querySelector('button') || document.getElementById('submit-btn');
    const msg = inputField?.value.trim();
    if (!msg) return;

    if (!force && latestReadinessData && latestReadinessData.state === "NOT_READY") {
        const actionVerbs = ["create", "make", "write", "generate", "research", "analyze", "fix", "update", "audit", "setup", "install", "test", "deploy", "sync"];
        if (actionVerbs.some(v => msg.toLowerCase().includes(v))) {
            if (feedback) {
                feedback.innerHTML = `<span style="color:var(--error)">⚠️ <b>System NOT READY</b>. Execution requested. Please configure providers first or use 'Submit Anyway'.</span>`;
                feedback.className = "error small";
            }
            return;
        }
    }

    if (btn) btn.disabled = true;
    if (feedback) {
        feedback.innerHTML = `<span>⏳ Verifying swarm health...</span>`;
        feedback.className = "success small";
    }

    try {
        const healthRes = await fetch('/api/health');
        const health = await healthRes.json();

        let subState = "accepted";
        if (health.status !== "online") {
            subState = "stale";
            if (feedback) {
                feedback.innerHTML = `<span>⚠️ <b>Offline Warning</b>: MasterBot is stale (${Math.round(health.master_age)}s age). Command sent, but may not process immediately.</span>`;
                feedback.className = "warning small";
            }
        } else if (feedback) {
            feedback.innerText = "🚀 Sending to swarm...";
        }

        const res = await fetch('/api/entry', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: msg})
        });
        const data = await res.json();

        if (data.success) {
            inputField.value = "";
            const mainInput = document.getElementById('operator-input');
            if (inputId === 'floating-operator-input' && mainInput) mainInput.value = "";
            if (feedback && subState === "accepted") feedback.innerText = "✅ Command accepted and queued.";
            setTimeout(() => {
                if (feedback && feedback.innerText.includes("Command")) feedback.innerText = "";
            }, 5000);
            refreshData();
        } else if (feedback) {
            feedback.innerText = `❌ Submission failed: ${data.error}`;
            feedback.className = "error small";
        }
    } catch (e) {
        if (feedback) {
            feedback.innerText = "❌ Connection error.";
            feedback.className = "error small";
        }
    } finally {
        if (btn) btn.disabled = false;
    }
}

normalizeDashboardChrome();
