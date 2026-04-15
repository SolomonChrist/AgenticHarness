import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const canvas = document.getElementById('viz-canvas');
const statusLine = document.getElementById('viz-statusline');
const feedEl = document.getElementById('viz-feed');

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x07101b, 0.028);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;

const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 200);
camera.position.set(0, 12, 24);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.enablePan = false;
controls.minDistance = 6;
controls.maxDistance = 40;
controls.maxPolarAngle = Math.PI * 0.48;
controls.target.set(0, 2.6, 0);

const clock = new THREE.Clock();
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

const botNodes = new Map();
let botOrder = [];
let selectedBotId = null;
let motionEnabled = false;

const palette = {
    working: { core: 0x73c9ff, ring: 0x378fff, emissive: 0x0f5fb0 },
    queue: { core: 0xffd46b, ring: 0xe8a531, emissive: 0x7e5518 },
    done: { core: 0x67f5a2, ring: 0x2dbd74, emissive: 0x13593b },
    blocked: { core: 0xff6e81, ring: 0xd73652, emissive: 0x6b1324 },
    cancelled: { core: 0x969eb4, ring: 0x5d6679, emissive: 0x283043 },
    idle: { core: 0xaab8ff, ring: 0x6d7ae4, emissive: 0x23317a },
    unknown: { core: 0xb7c2d9, ring: 0x6f809d, emissive: 0x2f3f58 },
};

function colorSetFor(status) {
    return palette[status] || palette.unknown;
}

function visualStatusFor(bot) {
    const raw = String(bot?.status || 'idle').toLowerCase();
    if (raw === 'done' || raw === 'cancelled') return 'idle';
    return raw;
}

function focusTextFor(bot) {
    const visualStatus = visualStatusFor(bot);
    if (visualStatus === 'idle') return 'idle';
    return bot.focus || bot.activity || visualStatus;
}

function resize() {
    const rect = canvas.getBoundingClientRect();
    camera.aspect = rect.width / Math.max(rect.height, 1);
    camera.updateProjectionMatrix();
    renderer.setSize(rect.width, rect.height, false);
}

window.addEventListener('resize', resize);

function addEnvironment() {
    const hemi = new THREE.HemisphereLight(0xbad7ff, 0x08101a, 1.15);
    scene.add(hemi);

    const spot = new THREE.SpotLight(0x7eb8ff, 2.2, 140, Math.PI / 7, 0.45, 1.5);
    spot.position.set(12, 18, 8);
    spot.target.position.set(0, 0, 0);
    scene.add(spot, spot.target);

    const floor = new THREE.Mesh(
        new THREE.CylinderGeometry(10.8, 13.8, 0.8, 72, 1, false),
        new THREE.MeshStandardMaterial({
            color: 0x0b1424,
            metalness: 0.55,
            roughness: 0.46,
            emissive: 0x09162a,
            emissiveIntensity: 0.8,
        })
    );
    floor.position.y = -0.4;
    scene.add(floor);

    const floorRing = new THREE.Mesh(
        new THREE.TorusGeometry(10.7, 0.08, 24, 140),
        new THREE.MeshBasicMaterial({ color: 0x2d5aa7, transparent: true, opacity: 0.35 })
    );
    floorRing.rotation.x = Math.PI / 2;
    floorRing.position.y = 0.02;
    scene.add(floorRing);

    for (let i = 0; i < 120; i += 1) {
        const star = new THREE.Mesh(
            new THREE.SphereGeometry(Math.random() * 0.06 + 0.02, 8, 8),
            new THREE.MeshBasicMaterial({ color: i % 3 === 0 ? 0x9bc2ff : 0x5d7bc9 })
        );
        star.position.set(
            (Math.random() - 0.5) * 70,
            Math.random() * 24 + 8,
            (Math.random() - 0.5) * 70
        );
        scene.add(star);
    }
}

function trimLabelText(text, max = 44) {
    const clean = String(text || '').replace(/\s+/g, ' ').trim();
    if (!clean) return 'idle';
    return clean.length > max ? `${clean.slice(0, max - 1)}…` : clean;
}

function makeLabelSprite(titleText, subtitleText, accentColor = '#ffffff') {
    const width = 512;
    const height = 160;
    const canvasEl = document.createElement('canvas');
    canvasEl.width = width;
    canvasEl.height = height;
    const ctx = canvasEl.getContext('2d');
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = 'rgba(7, 14, 25, 0.82)';
    roundRect(ctx, 14, 18, width - 28, height - 36, 28);
    ctx.fill();
    ctx.strokeStyle = 'rgba(154, 190, 255, 0.22)';
    ctx.lineWidth = 3;
    roundRect(ctx, 14, 18, width - 28, height - 36, 28);
    ctx.stroke();
    ctx.font = 'bold 42px "Segoe UI"';
    ctx.fillStyle = accentColor;
    ctx.fillText(trimLabelText(titleText, 20), 34, 78);
    ctx.font = '23px "Segoe UI"';
    ctx.fillStyle = 'rgba(225, 235, 255, 0.85)';
    ctx.fillText(trimLabelText(subtitleText, 38), 36, 118);
    ctx.font = '18px "Segoe UI"';
    ctx.fillStyle = 'rgba(150, 172, 210, 0.82)';
    ctx.fillText('live specialist', 36, 143);

    const texture = new THREE.CanvasTexture(canvasEl);
    texture.needsUpdate = true;
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(4.2, 1.3, 1);
    sprite.userData.canvas = canvasEl;
    sprite.userData.ctx = ctx;
    sprite.userData.texture = texture;
    return sprite;
}

function refreshLabelSprite(sprite, titleText, subtitleText, accentColor = '#ffffff') {
    const { canvas, ctx, texture } = sprite.userData;
    if (!canvas || !ctx || !texture) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = 'rgba(7, 14, 25, 0.82)';
    roundRect(ctx, 14, 18, canvas.width - 28, canvas.height - 36, 28);
    ctx.fill();
    ctx.strokeStyle = 'rgba(154, 190, 255, 0.22)';
    ctx.lineWidth = 3;
    roundRect(ctx, 14, 18, canvas.width - 28, canvas.height - 36, 28);
    ctx.stroke();
    ctx.font = 'bold 42px "Segoe UI"';
    ctx.fillStyle = accentColor;
    ctx.fillText(trimLabelText(titleText, 20), 34, 78);
    ctx.font = '23px "Segoe UI"';
    ctx.fillStyle = 'rgba(225, 235, 255, 0.85)';
    ctx.fillText(trimLabelText(subtitleText, 38), 36, 118);
    ctx.font = '18px "Segoe UI"';
    ctx.fillStyle = 'rgba(150, 172, 210, 0.82)';
    ctx.fillText('live specialist', 36, 143);
    texture.needsUpdate = true;
}

function roundRect(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
}

function createBotNode(bot, index, total) {
    const group = new THREE.Group();
    group.userData.botId = bot.id;

    const isMaster = !!bot.is_master;
    const statusColors = colorSetFor(visualStatusFor(bot));

    const core = new THREE.Mesh(
        isMaster ? new THREE.IcosahedronGeometry(1.45, 1) : new THREE.SphereGeometry(0.9, 28, 28),
        new THREE.MeshStandardMaterial({
            color: statusColors.core,
            emissive: statusColors.emissive,
            emissiveIntensity: 1.15,
            metalness: 0.5,
            roughness: 0.22,
        })
    );

    const halo = new THREE.Mesh(
        isMaster ? new THREE.TorusGeometry(2.3, 0.12, 16, 48) : new THREE.TorusGeometry(1.45, 0.06, 12, 48),
        new THREE.MeshBasicMaterial({
            color: statusColors.ring,
            transparent: true,
            opacity: 0.72,
        })
    );
    halo.rotation.x = Math.PI / 2;

    const stem = new THREE.Mesh(
        new THREE.CylinderGeometry(0.08, 0.12, isMaster ? 2.7 : 1.9, 12),
        new THREE.MeshStandardMaterial({
            color: 0x15304f,
            emissive: 0x0b1a2c,
            emissiveIntensity: 0.7,
            metalness: 0.2,
            roughness: 0.8,
        })
    );
    stem.position.y = -1.6;

    const label = makeLabelSprite(
        bot.name,
        focusTextFor(bot),
        `#${new THREE.Color(statusColors.core).getHexString()}`
    );
    label.position.set(0, isMaster ? 2.9 : 2.1, 0);

    group.add(core, halo, stem, label);
    group.userData = {
        ...group.userData,
        core,
        halo,
        label,
        isMaster,
        phase: index * 1.371,
        orbitRadius: isMaster ? 0 : 6.5 + Math.floor(index / 5) * 3.4,
        orbitSpeed: isMaster ? 0 : 0.11 + (index % 5) * 0.017,
        verticalBase: isMaster ? 2.8 : 1.8 + (index % 2) * 0.25,
        bot,
        angleOffset: isMaster ? 0 : (index / Math.max(total, 1)) * Math.PI * 2,
    };

    scene.add(group);
    return group;
}

function updateBotNode(node, bot, index, total) {
    const displayStatus = visualStatusFor(bot);
    const colors = colorSetFor(displayStatus);
    node.userData.bot = bot;
    node.userData.orbitRadius = node.userData.isMaster ? 0 : 6.5 + Math.floor(index / 5) * 3.4;
    node.userData.orbitSpeed = node.userData.isMaster ? 0 : 0.11 + (index % 5) * 0.017;
    node.userData.verticalBase = node.userData.isMaster ? 2.8 : 1.8 + (index % 2) * 0.25;
    node.userData.angleOffset = node.userData.isMaster ? 0 : (index / Math.max(total, 1)) * Math.PI * 2;
    node.userData.phase = index * 1.371;
    node.userData.displayStatus = displayStatus;
    node.userData.core.material.color.setHex(colors.core);
    node.userData.core.material.emissive.setHex(colors.emissive);
    node.userData.halo.material.color.setHex(colors.ring);
    refreshLabelSprite(
        node.userData.label,
        bot.name,
        focusTextFor(bot),
        `#${new THREE.Color(colors.core).getHexString()}`
    );
}

function syncScene(state) {
    const bots = state.bots || [];
    const used = new Set();
    botOrder = bots.map(bot => bot.id);

    bots.forEach((bot, index) => {
        let node = botNodes.get(bot.id);
        if (!node) {
            node = createBotNode(bot, index, bots.length);
            botNodes.set(bot.id, node);
        }
        updateBotNode(node, bot, index, bots.length);
        used.add(bot.id);
    });

    for (const [botId, node] of botNodes.entries()) {
        if (!used.has(botId)) {
            scene.remove(node);
            botNodes.delete(botId);
        }
    }

    if (!selectedBotId && bots.length) {
        selectedBotId = bots[0].id;
    }
    renderSelectedBot(state);
    renderSummary(state.summary || {});
    renderFeed(state.feed || []);
    statusLine.textContent = `${state.summary?.ready_explanation || 'Awaiting live state.'} Last sync: ${state.generated_at || 'unknown'}`;
}

function renderSummary(summary) {
    document.getElementById('sum-ready').textContent = summary.ready_state || 'UNKNOWN';
    document.getElementById('sum-bots').textContent = `${summary.bot_count || 0}`;
    document.getElementById('sum-working').textContent = `${summary.working_count || 0}`;
    document.getElementById('sum-blocked').textContent = `${summary.blocked_count || 0}`;
}

function renderSelectedBot(state) {
    const bots = state.bots || [];
    const selected = bots.find(bot => bot.id === selectedBotId) || bots[0];
    const empty = document.getElementById('bot-detail-empty');
    const detail = document.getElementById('bot-detail');
    if (!selected) {
        empty.classList.remove('hidden');
        detail.classList.add('hidden');
        return;
    }
    selectedBotId = selected.id;
    empty.classList.add('hidden');
    detail.classList.remove('hidden');
    document.getElementById('bot-name').textContent = selected.name;
    document.getElementById('bot-role').textContent = selected.role;
    document.getElementById('bot-provider').textContent = selected.provider || '-';
    document.getElementById('bot-model').textContent = selected.model || '-';
    document.getElementById('bot-harness').textContent = selected.harness || '-';
    document.getElementById('bot-locality').textContent = selected.local_cloud || '-';
    document.getElementById('bot-status').textContent = visualStatusFor(selected) || '-';
    document.getElementById('bot-heartbeat').textContent = typeof selected.heartbeat_age === 'number' ? `${selected.heartbeat_age}s` : '-';
    document.getElementById('bot-focus').textContent = focusTextFor(selected);
    document.getElementById('bot-activity').textContent = visualStatusFor(selected) === 'idle' ? 'standing by' : (selected.activity || 'active');
    document.getElementById('bot-blockers').textContent = selected.blockers || 'none';
}

function renderFeed(feed) {
    if (!feed.length) {
        feedEl.innerHTML = `<div class="viz-empty">No activity yet.</div>`;
        return;
    }
    feedEl.innerHTML = feed.slice().reverse().map(item => `
        <div class="viz-feed-item">
            <div class="viz-feed-meta">
                <span>${escapeHtml(item.sender || 'Unknown')}</span>
                <span>${escapeHtml(item.timestamp || '')}</span>
            </div>
            <div class="viz-feed-body">${escapeHtml(item.body || '')}</div>
        </div>
    `).join('');
}

function escapeHtml(text) {
    return String(text || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;');
}

function animate() {
    const elapsed = clock.getElapsedTime();
    for (const botId of botOrder) {
        const node = botNodes.get(botId);
        if (!node) continue;
        const { isMaster, orbitRadius, orbitSpeed, verticalBase, phase, angleOffset, core, halo, displayStatus } = node.userData;
        const status = displayStatus || 'idle';
        const energy = status === 'working' ? 0.9 : status === 'blocked' ? 0.35 : status === 'queue' ? 0.55 : 0.18;
        const bob = Math.sin(elapsed * (1.45 + energy) + phase) * (isMaster ? 0.18 : 0.25 * energy);
        if (isMaster) {
            node.position.set(0, verticalBase + bob, 0);
            core.rotation.y += 0.008;
            core.rotation.x += 0.004;
        } else {
            const animatedOrbit = motionEnabled ? orbitSpeed : 0;
            const statusOrbit = status === 'working' ? animatedOrbit : status === 'queue' ? animatedOrbit * 0.45 : 0;
            const angle = elapsed * statusOrbit + angleOffset;
            node.position.set(Math.cos(angle) * orbitRadius, verticalBase + bob, Math.sin(angle) * orbitRadius);
            core.rotation.y += status === 'blocked' ? 0.018 : 0.01;
        }
        halo.rotation.z += motionEnabled ? 0.002 + energy * 0.004 : 0.0015;
        const pulse = 0.82 + Math.sin(elapsed * (2.5 + energy) + phase) * 0.16;
        halo.material.opacity = status === 'blocked' ? 0.9 : pulse;
    }

    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
}

async function refreshState() {
    try {
        const res = await fetch('/api/visualizer_state');
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || 'Visualizer state request failed');
        }
        syncScene(data);
    } catch (error) {
        statusLine.textContent = `Visualizer sync failed: ${error.message}`;
    }
}

canvas.addEventListener('pointerdown', event => {
    const rect = canvas.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects([...botNodes.values()], true);
    if (!hits.length) return;
    const hit = hits[0].object;
    const carrier = hit.parent?.userData?.botId ? hit.parent : hit.parent?.parent;
    if (carrier?.userData?.botId) {
        selectedBotId = carrier.userData.botId;
        refreshState();
    }
});

addEnvironment();
resize();
refreshState();
setInterval(refreshState, 3000);
animate();

document.getElementById('viz-motion-toggle')?.addEventListener('click', () => {
    motionEnabled = !motionEnabled;
    document.getElementById('viz-motion-toggle').textContent = motionEnabled ? 'Motion: Active' : 'Motion: Calm';
});

document.getElementById('viz-focus-toggle')?.addEventListener('click', () => {
    camera.position.set(0, 12, 24);
    controls.target.set(0, 2.6, 0);
    controls.update();
});
