import "./styles.css";
import type { State, Raid, Draft, OverlayState } from "./types";

const root = document.querySelector<HTMLDivElement>("#app")!;
const overlay = location.pathname === "/overlay";
const logo = `<svg viewBox="0 0 40 40" fill="none" aria-hidden="true"><path d="M7 12h17l-5-5M33 28H16l5 5" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="m28 11 5 5-5 5M12 29l-5-5 5-5" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const esc = (value: unknown): string =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ]!,
  );
const el = <T extends HTMLElement = HTMLElement>(id: string): T =>
  document.getElementById(id) as T;
const time = (timestamp: number | null | undefined): string =>
  timestamp
    ? new Date(timestamp * 1000).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "—";
const number = (value: number | null | undefined): string =>
  value == null ? "—" : value.toLocaleString();
const seconds = (value: number): string => `${Math.max(0, Math.floor(value))}s`;
const link = (value: string): string => {
  try {
    const url = new URL(value);
    return url.protocol === "https:" &&
      (url.hostname === "twitch.tv" ||
        url.hostname.endsWith(".twitch.tv") ||
        url.hostname.endsWith(".jtvnw.net"))
      ? esc(url.href)
      : "#";
  } catch {
    return "#";
  }
};

function guestCard(raid: Raid, now: number): string {
  const elapsed = Math.max(0, now - raid.started_at);
  return `<div class="guest-top"><span class="pill purple">INCOMING RAID</span><span class="tiny muted">${esc(time(raid.started_at))} · real EventSub</span></div>
    <div class="guest-identity"><div class="avatar">${raid.guest.image ? `<img src="${link(raid.guest.image)}" alt=""/>` : esc(raid.source_name.slice(0, 2).toUpperCase())}</div><div class="identity-copy"><h2>${esc(raid.source_name)}</h2><a href="https://www.twitch.tv/${encodeURIComponent(raid.source_login)}" target="_blank" rel="noreferrer">twitch.tv/${esc(raid.source_login)} ↗</a></div><div class="raid-size"><strong>${number(raid.viewers)}</strong><span>raid participants</span></div></div>
    <div class="stream-context"><span class="eyebrow">THEY WERE STREAMING</span><span class="category">${esc(raid.guest.category)}</span><p>${esc(raid.guest.title)}</p></div>
    <div class="clip-section"><span class="eyebrow">RECENT CLIP TITLES <span class="dim">· LAST 7 DAYS</span></span>${raid.guest.clips.length ? `<ul class="clip-list">${raid.guest.clips.map((clip, i) => `<li><span class="clip-num">0${i + 1}</span><a href="${link(clip.url)}" target="_blank" rel="noreferrer">${esc(clip.title)} <span>↗</span></a></li>`).join("")}</ul>` : `<p class="muted small">${raid.guest.error ? esc(raid.guest.error) : "No clips available in the returned time window."}</p>`}</div>
    <div class="wave-section"><div class="section-line"><span class="eyebrow">LEARNING THE RAID WAVE</span><span class="tiny ${raid.learning.status === "learned" ? "lime-text" : "muted"}">${raid.learning.status === "learning" ? `${Math.ceil(Math.max(0, 60 - elapsed))}s remaining` : `${number(raid.learning.messages)} messages · ${number(raid.learning.authors)} people`}</span></div>
    ${raid.learning.status === "learning" ? `<div class="progress"><span style="width:${Math.min(100, (elapsed / 60) * 100)}%"></span></div><p class="muted small">Listening for source-owned emotes and repeated words in this channel.</p>` : ""}
    ${raid.learning.emotes?.length ? `<div class="learned-row"><span class="tiny muted">SOURCE EMOTES</span>${raid.learning.emotes.map((item) => `<span class="token">${esc(item.name)} <b>×${number(item.count)}</b></span>`).join("")}</div>` : ""}
    ${raid.learning.tokens?.length ? `<div class="learned-row"><span class="tiny muted">REPEATED TEXT</span>${raid.learning.tokens.map((item) => `<span class="token text-token">${esc(item.text)} <b>×${number(item.count)}</b></span>`).join("")}</div><p class="tiny muted">Text tokens may include third-party emotes; their identity is unverified.</p>` : ""}
    ${raid.learning.status === "insufficient" ? '<p class="insufficient">样本不足 <span>· Not enough repeated signals from multiple people.</span></p>' : ""}</div>`;
}

function metricsCard(raid: Raid, now: number): string {
  const elapsed = Math.max(0, now - raid.started_at);
  const latest = raid.samples.at(-1);
  return `<div class="section-line"><div><span class="eyebrow">CHAT CONNECTIONS</span><h3>The handoff, observed.</h3></div><span class="pill subtle">ESTIMATE</span></div>
    <div class="cohort-row"><div><strong>${number(raid.population)}</strong><span>estimated new connections</span></div><span class="small muted">${raid.cohort_finalized ? "90-second arrival window closed" : `${Math.ceil(Math.max(0, 90 - elapsed))}s left in arrival window`}</span></div>
    <div class="checkpoint-grid">${[5, 15, 30]
      .map((minute) => {
        const sample = raid.samples.find((item) => item.minute === minute);
        return `<div class="checkpoint ${sample ? "observed" : ""}"><div class="checkpoint-top"><span>${minute} MIN</span><span>${sample ? time(sample.observed_at) : elapsed < minute * 60 ? `in ${Math.ceil((minute * 60 - elapsed) / 60)}m` : "sampling…"}</span></div>
        <dl><div><dt>Connected</dt><dd>${sample ? number(sample.connected) : "—"}</dd></div><div><dt>Spoke in last 5m</dt><dd>${sample ? number(sample.spoken) : "—"}</dd></div><div><dt>Follow events*</dt><dd>${sample ? number(sample.follows) : "—"}</dd></div></dl>${sample?.error ? `<p class="tiny amber-text">${esc(sample.error)}</p>` : ""}</div>`;
      })
      .join("")}</div>
    <div class="method-note"><span class="status-dot amber"></span><p>聊天连接口径，存在更新延迟。<br/><span>New arrivals can include unrelated users and bots. *Follows count the whole channel since the raid.</span></p></div>
    ${raid.baseline_at == null ? '<p class="small amber-text">No fresh pre-raid baseline. Cohort estimates are unknown.</p>' : `<p class="tiny muted">Baseline ${Math.max(0, raid.started_at - raid.baseline_at).toFixed(1)}s before raid. ${latest?.observed_at ? `Last observation ${time(latest.observed_at)}.` : "Waiting for first checkpoint."}</p>`}
    ${!raid.cohort_complete ? '<p class="tiny amber-text">A polling interruption may have omitted arrivals.</p>' : ""}
    ${raid.overlap ? '<p class="tiny amber-text">Arrival windows overlap another raid; the estimated cohorts can overlap.</p>' : ""}`;
}

let csrf = "";
let obsUrl = "";
let state: State | null = null;
let configLoaded = false;
let settingsDirty = false;
let connection: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
const previewed = new Set<string>();

async function api<T = unknown>(
  path: string,
  body?: unknown,
  method = "POST",
): Promise<T> {
  const response = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Request failed. Check the control room.",
    );
  return data as T;
}
function toast(message: string, error = false): void {
  const region = el("toast");
  region.textContent = message;
  region.className = `toast visible ${error ? "error" : ""}`;
  setTimeout(() => region.classList.remove("visible"), 5500);
}
async function action(
  work: () => Promise<unknown>,
  success?: string,
): Promise<void> {
  try {
    await work();
    if (success) toast(success);
    await refreshState();
  } catch (error) {
    toast(error instanceof Error ? error.message : "Request failed.", true);
  }
}
async function refreshState(): Promise<void> {
  if (overlay) return;
  const response = await fetch("/api/state");
  if (response.ok) render((await response.json()) as State);
}
function pending(): Draft | null {
  const raid = state?.raids[0];
  return state?.drafts.find((d) => d.id === raid?.draft_id) ?? null;
}
async function markPreview(draft: Draft): Promise<void> {
  const revision = `${draft.id}:${draft.text_hash}`;
  if (
    document.visibilityState !== "visible" ||
    previewed.has(revision) ||
    !["pending", "previewed", "failed"].includes(draft.status)
  )
    return;
  previewed.add(revision);
  try {
    await api(`/api/drafts/${encodeURIComponent(draft.id)}/preview`, {
      text_hash: draft.text_hash,
    });
  } catch {
    previewed.delete(revision);
  }
}

function mount(): void {
  root.innerHTML = `<header class="app-header"><a class="brand" href="/"><span class="brand-mark">${logo}</span><span>raid<span class="brand-light">handshake</span><small>CONTEXT CONNECTS COMMUNITIES</small></span></a><div class="header-actions"><span class="local-badge"><span class="status-dot lime"></span>LOCAL CONTROL ROOM</span><a class="button ghost" href="/guide" target="_blank">中文准备指南 ↗</a><button class="button purple-button" id="copy-obs">Copy OBS URL <span>↗</span></button></div></header>
    <main class="shell"><section class="hero"><div><span class="eyebrow lime-text">THE FIRST 30 SECONDS MATTER</span><h1>A new crowd.<br/><span>A little shared context.</span></h1><p>Welcome the people behind the raid. Give them a way into your stream.</p></div><div class="hero-status"><span id="connection-badge" class="pill subtle">STANDING BY</span><div id="receiver-label">Connect your receiving channel to begin.</div><span class="tiny muted" id="transport-state">Waiting for local service…</span></div></section>
    <section class="health-grid" aria-label="Connection health"><div id="health-twitch" class="health-card"></div><div id="health-baseline" class="health-card"></div><div id="health-openai" class="health-card"></div><div id="health-audio" class="health-card"></div></section>
    <section class="panel setup-panel"><div class="section-line"><div><span class="eyebrow">FIRST THINGS FIRST</span><h3>Connect, listen, welcome.</h3></div><a href="/guide" target="_blank" class="text-link">从注册账号开始 →</a></div><div class="setup-grid"><div class="setup-block"><div class="step-heading"><span class="step-number">01</span><h4>Your receiving channel</h4></div><p class="small muted">Use the Public Client ID you registered on Twitch. Authorize as channel B.</p><label for="client-id">Twitch Client ID</label><div class="input-action"><input id="client-id" autocomplete="off" spellcheck="false" placeholder="Paste Public Client ID"/><button id="connect-twitch" class="button primary">Connect Twitch</button></div><div id="twitch-auth"></div><button class="text-button" id="disconnect-twitch" hidden>Disconnect Twitch</button></div>
    <div class="setup-block"><div class="step-heading"><span class="step-number">02</span><h4>Live context with OpenAI</h4></div><p class="small muted">Audio segments and chat context are processed through your OpenAI API project.</p><label for="openai-key">OpenAI API key <span id="key-status" class="tiny lime-text"></span></label><form id="key-form" class="input-action"><input id="openai-key" type="password" autocomplete="new-password" placeholder="Paste key · stored securely on this computer"/><button class="button secondary" type="submit">Save key</button></form><div class="audio-control"><label for="audio-device">Audio input</label><div class="input-action"><select id="audio-device"><option value="">System default microphone</option></select><button class="button secondary" id="refresh-devices" aria-label="Refresh audio inputs">↻</button><button class="button primary" id="audio-toggle">Start audio</button></div><div class="audio-meta"><div class="audio-meter"><span id="audio-meter-fill"></span></div><span class="tiny muted" id="audio-meta">Microphone capture is off.</span></div></div><p class="tiny amber-text" id="audio-error"></p></div></div></section>
    <section class="workspace"><article class="panel guest-panel" id="guest-panel"><div class="empty-state"><div class="empty-art">${logo}<span class="orbit orbit-one"></span><span class="orbit orbit-two"></span></div><span class="eyebrow">GUEST CHEAT SHEET</span><h2>Ready for a real hello.</h2><p>When a raid lands, its channel, clips and shared signals appear here.</p><span class="empty-footnote">Listening to Twitch EventSub · no simulated events</span></div></article>
    <aside class="panel landing-panel"><div class="section-line"><div><span class="eyebrow">FOR THE NEW ARRIVALS</span><h3>The landing card</h3></div><span class="pill subtle" id="send-mode">HOTKEY CONFIRM</span></div><p class="small muted">A short introduction to what's happening here, grounded in your recent audio.</p><div class="landing-preview"><span class="chat-label">CHAT PREVIEW</span><p id="draft-text">Your landing card will appear after a real raid and a fresh transcript.</p><div class="draft-meta"><span id="draft-status">Waiting for a raid</span><span id="draft-length">— / 500</span></div></div><p class="small amber-text" id="draft-error"></p><button class="button send-button" id="send-draft" disabled>Send to Twitch chat <kbd>Ctrl ⇧ Enter</kbd></button><button class="text-button" id="rebuild-draft" disabled>Generate from the latest transcript ↻</button><div class="quiet-note"><span class="status-dot purple-dot"></span><p id="hotkey-note">Preview the complete message, then confirm with the send button or global hotkey.</p></div></aside></section>
    <section class="panel context-panel"><div class="section-line"><div><span class="eyebrow">WHAT YOUR STREAM IS DOING</span><h3>Context stays warm.</h3></div><button class="button ghost small-button" id="refresh-summary">Refresh summary ↻</button></div><p class="summary-text" id="summary-text">Start your microphone to build a real, rolling stream summary.</p><div id="summary-evidence"></div><p class="tiny muted" id="summary-meta">A three-minute audio window. No title-only substitution.</p><p class="small amber-text" id="summary-error"></p><details class="transcript-details"><summary>Recent transcript <span>· local control room only</span></summary><div id="transcript-list" class="transcript-list"><p class="muted small">No transcribed speech yet.</p></div></details></section>
    <section class="panel metrics-panel" id="metrics-panel"><div class="section-line"><div><span class="eyebrow">AFTER THE HANDOFF</span><h3>Watch the conversation settle.</h3></div><span class="pill subtle">5 / 15 / 30 MIN</span></div><p class="muted small">After a real raid, new chat connections are estimated against your pre-raid baseline.</p><div class="empty-checkpoints"><span>05 MIN <b>—</b></span><span>15 MIN <b>—</b></span><span>30 MIN <b>—</b></span></div><p class="tiny muted">聊天连接口径，存在更新延迟。These metrics do not measure video viewing.</p></section>
    <section class="panel settings-panel"><div class="section-line"><div><span class="eyebrow">MAKE IT SOUND LIKE YOUR CHANNEL</span><h3>A few familiar words.</h3></div><span class="tiny amber-text" id="settings-dirty"></span></div><form id="settings-form"><div class="settings-grid"><div><label for="commands">Your actual commands / participation hint</label><input id="commands" maxlength="100" placeholder="e.g. !help — only list commands that really exist"/><label for="channel-rule">One rule</label><input id="channel-rule" maxlength="100"/><label for="language">Card language</label><input id="language" maxlength="40"/></div><div><label for="template">Landing card template</label><textarea id="template" rows="4" spellcheck="false"></textarea><p class="tiny muted">Placeholders: {summary}, {commands}, {rule}. Final messages must fit within 500 characters.</p><details class="advanced"><summary>OpenAI model settings</summary><label for="transcription-model">Transcription model</label><input id="transcription-model"/><label for="summary-model">Summary model</label><input id="summary-model"/></details></div></div><div class="settings-bottom"><button class="button secondary" type="submit">Save channel settings</button><span class="tiny muted" id="storage-note"></span></div></form><div class="auto-mode"><div><h4>Preapproved template mode <span class="pill subtle" id="auto-status">OFF</span></h4><p class="small muted">After you approve the structure and fixed wording, a raid fills in the current summary and sends automatically. The final text changes with the summary.</p></div><button class="button secondary" id="auto-toggle">Confirm template & enable</button></div></section>
    <section class="activity-section"><div class="section-line"><h4>Connection & handoff activity</h4><span class="tiny muted">Transcript and audio stay out of diagnostic logs.</span></div><div id="activity-list"><p class="small muted">Waiting for your first connection.</p></div></section><footer>RAID HANDSHAKE <span>Built with Codex for the Twitch community.</span><a href="/guide" target="_blank">First real raid checklist ↗</a></footer></main><div id="toast" class="toast" role="status" aria-live="polite"></div>`;
  bind();
}

function healthCard(
  id: string,
  label: string,
  title: string,
  detail: string,
  ok: boolean,
  warn = false,
): void {
  el(id).innerHTML =
    `<div class="health-label"><span class="status-dot ${ok ? "lime" : warn ? "amber" : "gray"}"></span>${esc(label)}</div><strong>${esc(title)}</strong><span class="tiny muted">${esc(detail)}</span>`;
}
function render(next: State): void {
  state = next;
  if (!configLoaded) {
    el<HTMLInputElement>("client-id").value = next.config.twitch_client_id;
    populateConfig(next);
    configLoaded = true;
  }
  const connected = next.health.eventsub === "connected";
  const freshBaseline =
    next.health.baseline_at != null &&
    next.now - next.health.baseline_at <= next.config.chatters_poll_seconds * 3;
  el("connection-badge").textContent = connected
    ? "LISTENING LIVE"
    : "STANDING BY";
  el("connection-badge").className =
    `pill ${connected ? "lime-pill" : "subtle"}`;
  el("receiver-label").textContent = next.user
    ? `Receiving raids at twitch.tv/${next.user.login}`
    : "Connect your receiving channel to begin.";
  el("transport-state").textContent =
    next.health.eventsub_error ?? "EventSub WebSocket · broadcaster identity";
  healthCard(
    "health-twitch",
    "TWITCH EVENTS",
    connected ? "Listening live" : next.user ? "Connecting…" : "Not connected",
    next.user ? next.user.display_name : "Authorize your receiving channel",
    connected,
  );
  healthCard(
    "health-baseline",
    "CHATTERS BASELINE",
    freshBaseline
      ? `${number(next.health.chatters_count)} connected`
      : "Waiting for baseline",
    next.health.chatters_error ??
      (next.health.baseline_at
        ? `Last sampled ${time(next.health.baseline_at)}`
        : "Start polling before the raid"),
    freshBaseline,
    !!next.health.chatters_error,
  );
  healthCard(
    "health-openai",
    "OPENAI CONTEXT",
    next.summary_ready
      ? "Summary ready"
      : next.health.openai_configured
        ? "Key configured"
        : "Key required",
    next.summary_running
      ? "Updating from real transcript…"
      : next.config.summary_model,
    next.summary_ready,
  );
  healthCard(
    "health-audio",
    "LIVE TRANSCRIPT",
    next.audio.active ? "Microphone live" : "Capture off",
    next.audio.error ??
      (next.transcript.at(-1)
        ? `Last speech ${time(next.transcript.at(-1)!.at)}`
        : "No audio sent until you start"),
    next.audio.active,
    !!next.audio.error,
  );
  el<HTMLButtonElement>("connect-twitch").disabled = !!next.user;
  el("disconnect-twitch").hidden = !next.user;
  el("key-status").textContent = next.health.openai_configured
    ? "· configured"
    : "";
  const device = next.device_login;
  el("twitch-auth").innerHTML = next.user
    ? `<div class="connected-channel"><span class="status-dot lime"></span>Connected as <b>${esc(next.user.display_name)}</b></div>`
    : device?.status === "pending"
      ? `<div class="device-login"><span class="tiny muted">TWITCH ACTIVATION CODE</span><strong>${esc(device.user_code)}</strong><a href="${link(device.verification_uri)}" target="_blank" rel="noreferrer">Activate on Twitch ↗</a><span class="tiny muted">Check that Twitch is logged into channel B · expires in ${Math.ceil(Math.max(0, device.expires_at - next.now) / 60)}m</span></div>`
      : next.login_error
        ? `<p class="small amber-text">${esc(next.login_error)}</p>`
        : "";
  el("audio-toggle").textContent = next.audio.active
    ? "Stop audio"
    : "Start audio";
  el("audio-toggle").classList.toggle("recording", next.audio.active);
  el("audio-meter-fill").style.width =
    `${Math.min(100, next.audio.level * 700)}%`;
  el("audio-meta").textContent = next.audio.active
    ? `Sending voiced 8-second segments to OpenAI · queue ${next.audio.queue}`
    : "Microphone capture is off.";
  el("audio-error").textContent = next.audio.error ?? "";
  el("send-mode").textContent = next.config.preapproved_enabled
    ? "PREAPPROVED AUTO"
    : "HOTKEY CONFIRM";
  el("auto-status").textContent = next.config.preapproved_enabled
    ? "ON"
    : "OFF";
  el("auto-status").className =
    `pill ${next.config.preapproved_enabled ? "lime-pill" : "subtle"}`;
  el("auto-toggle").textContent = next.config.preapproved_enabled
    ? "Turn off automatic sending"
    : "Confirm template & enable";
  el("storage-note").textContent =
    `Credentials: ${next.health.credential_storage}`;
  el("hotkey-note").textContent = next.health.global_hotkey
    ? "Preview this exact text, then press Ctrl+Shift+Enter from any app to send."
    : (next.health.hotkey_error ??
      "Use the send button after previewing the complete message.");
  const raid = next.raids[0];
  if (raid) {
    el("guest-panel").innerHTML = guestCard(raid, next.now);
    el("metrics-panel").innerHTML = metricsCard(raid, next.now);
  }
  const draft = pending();
  el("draft-text").textContent =
    draft?.text ??
    (raid
      ? "Waiting for a fresh transcript. Start audio, then generate this raid’s landing card."
      : "Your landing card will appear after a real raid and a fresh transcript.");
  el("draft-length").textContent = draft
    ? `${Array.from(draft.text).length} / 500`
    : "— / 500";
  el("draft-status").textContent = draft
    ? draft.status === "sent"
      ? `Sent at ${time(draft.sent_at)}`
      : draft.status.replace("_", " ")
    : "Waiting for a raid";
  el("draft-error").textContent = draft?.error ?? "";
  el<HTMLButtonElement>("send-draft").disabled =
    !draft || !["pending", "previewed", "failed"].includes(draft.status);
  el<HTMLButtonElement>("rebuild-draft").disabled =
    !raid ||
    (!!draft && ["sent", "sending", "uncertain"].includes(draft.status));
  if (draft) void markPreview(draft);
  el("summary-text").textContent =
    next.summary?.activity ??
    "Start your microphone to build a real, rolling stream summary.";
  el("summary-evidence").innerHTML = next.summary
    ? `<div class="evidence">${next.summary.evidence.map((quote) => `<blockquote>“${esc(quote)}”</blockquote>`).join("")}</div>`
    : "";
  el("summary-meta").textContent = next.summary
    ? `Spoken context ${time(next.summary.window_start)}–${time(next.summary.window_end)} · summary ${time(next.summary.created_at)}${next.summary_ready ? "" : " · STALE"}`
    : "A three-minute audio window. No title-only substitution.";
  el("summary-error").textContent = next.summary_error ?? "";
  el("transcript-list").innerHTML = next.transcript.length
    ? next.transcript
        .map((item) => `<p><time>${time(item.at)}</time>${esc(item.text)}</p>`)
        .join("")
    : '<p class="muted small">No transcribed speech yet.</p>';
  el("activity-list").innerHTML = next.activity.length
    ? next.activity
        .slice(0, 8)
        .map(
          (item) =>
            `<div class="activity-item"><time>${time(item.at)}</time><span class="activity-kind">${esc(item.kind.replaceAll("_", " "))}</span><span>${esc(item.message)}</span></div>`,
        )
        .join("")
    : '<p class="small muted">Waiting for your first connection.</p>';
}
function populateConfig(next: State): void {
  if (settingsDirty) return;
  for (const [id, key] of [
    ["commands", "commands"],
    ["channel-rule", "rule"],
    ["template", "template"],
    ["language", "language"],
    ["transcription-model", "transcription_model"],
    ["summary-model", "summary_model"],
  ] as const)
    el<HTMLInputElement>(id).value = next.config[key];
}
async function loadDevices(): Promise<void> {
  const response = await fetch("/api/audio/devices");
  const data = (await response.json()) as {
    devices: { id: string; name: string; loopback: boolean }[];
    error: string | null;
  };
  const selected = state?.config.audio_device_id ?? "";
  el("audio-device").innerHTML =
    '<option value="">System default microphone</option>' +
    data.devices
      .map(
        (device) =>
          `<option value="${esc(device.id)}"${device.id === selected ? " selected" : ""}>${esc(device.name)}${device.loopback ? " · system playback" : ""}</option>`,
      )
      .join("");
  if (data.error) toast(data.error, true);
}
function bind(): void {
  el("copy-obs").addEventListener(
    "click",
    () =>
      void action(async () => {
        await navigator.clipboard.writeText(obsUrl);
      }, "OBS URL copied. Add it as a Browser source at 1920×1080."),
  );
  el("connect-twitch").addEventListener(
    "click",
    () =>
      void action(async () => {
        await api("/api/config", {
          values: {
            twitch_client_id: el<HTMLInputElement>("client-id").value.trim(),
          },
        });
        await api("/api/twitch/connect");
      }),
  );
  el("disconnect-twitch").addEventListener(
    "click",
    () =>
      void action(() => api("/api/twitch/disconnect"), "Twitch disconnected."),
  );
  el("key-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void action(async () => {
      await api("/api/openai/key", {
        api_key: el<HTMLInputElement>("openai-key").value.trim(),
      });
      el<HTMLInputElement>("openai-key").value = "";
    }, "API key saved. Start audio to verify transcription.");
  });
  el("refresh-devices").addEventListener(
    "click",
    () => void action(loadDevices),
  );
  el("audio-toggle").addEventListener(
    "click",
    () =>
      void action(async () => {
        if (state?.audio.active) await api("/api/audio/stop");
        else {
          await api("/api/config", {
            values: {
              audio_device_id: el<HTMLSelectElement>("audio-device").value,
            },
          });
          await api("/api/audio/start");
        }
      }),
  );
  el("refresh-summary").addEventListener(
    "click",
    () => void action(() => api("/api/summary/refresh")),
  );
  el("send-draft").addEventListener(
    "click",
    () =>
      void action(async () => {
        const draft = pending();
        if (!draft) throw new Error("Wait for a real raid first.");
        await api(`/api/drafts/${encodeURIComponent(draft.id)}/preview`, {
          text_hash: draft.text_hash,
        });
        const sent = await api<Draft>(
          `/api/drafts/${encodeURIComponent(draft.id)}/send`,
        );
        if (sent.status !== "sent")
          throw new Error(sent.error ?? "Message not delivered.");
      }, "Landing card delivered to Twitch."),
  );
  el("rebuild-draft").addEventListener(
    "click",
    () =>
      void action(async () => {
        const raid = state?.raids[0];
        if (raid) await api(`/api/raids/${encodeURIComponent(raid.id)}/draft`);
      }),
  );
  el("settings-form").addEventListener("input", () => {
    settingsDirty = true;
    el("settings-dirty").textContent = "Unsaved changes";
  });
  el("settings-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void action(async () => {
      await api("/api/config", {
        values: {
          commands: el<HTMLInputElement>("commands").value,
          rule: el<HTMLInputElement>("channel-rule").value,
          template: el<HTMLTextAreaElement>("template").value,
          language: el<HTMLInputElement>("language").value,
          transcription_model: el<HTMLInputElement>("transcription-model")
            .value,
          summary_model: el<HTMLInputElement>("summary-model").value,
        },
      });
      settingsDirty = false;
      el("settings-dirty").textContent = "";
    }, "Channel settings saved. Template edits turn automatic mode off.");
  });
  el("auto-toggle").addEventListener(
    "click",
    () =>
      void action(async () => {
        if (settingsDirty)
          throw new Error(
            "Save and review your current template before enabling it.",
          );
        if (state)
          await api("/api/template/approval", {
            enabled: !state.config.preapproved_enabled,
            template_hash: state.template_hash,
          });
      }),
  );
  document.addEventListener("visibilitychange", () => {
    const draft = pending();
    if (draft) void markPreview(draft);
  });
  document.addEventListener("keydown", (event) => {
    if (
      event.ctrlKey &&
      event.shiftKey &&
      event.key === "Enter" &&
      !state?.health.global_hotkey
    ) {
      event.preventDefault();
      el<HTMLButtonElement>("send-draft").click();
    }
  });
}

function renderOverlay(next: OverlayState): void {
  const raid = next.raids[0];
  if (!raid || !next.channel) {
    root.innerHTML =
      '<div class="overlay-standby"><span class="brand-mark">' +
      logo +
      "</span><span>Raid Handshake · standing by</span></div>";
    return;
  }
  const elapsed = next.now - raid.started_at;
  const latest = raid.samples.at(-1);
  const showMetrics =
    latest && next.now - (latest.observed_at ?? latest.scheduled_at) < 45;
  root.innerHTML = `<div class="overlay-guest ${elapsed > 90 ? "collapsed" : ""}">${elapsed <= 90 ? guestCard(raid, next.now) : `<span class="pill purple">RAID HANDSHAKE</span><strong>${esc(raid.source_name)}</strong><span>${number(raid.viewers)} participants</span>`}</div>${next.landing && elapsed < 90 ? `<div class="overlay-landing"><span class="eyebrow lime-text">WELCOME TO ${esc(next.channel)}</span><p>${esc(next.landing)}</p></div>` : ""}${showMetrics ? `<div class="overlay-metrics">${metricsCard(raid, next.now)}</div>` : ""}`;
}
function socketConnect(token: string): void {
  const ws = new WebSocket(
    `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`,
  );
  connection = ws;
  ws.addEventListener("open", () =>
    ws.send(JSON.stringify({ token, view: overlay ? "overlay" : "admin" })),
  );
  ws.addEventListener("message", (event) => {
    if (overlay) renderOverlay(JSON.parse(event.data) as OverlayState);
    else render(JSON.parse(event.data) as State);
  });
  ws.addEventListener("close", () => {
    if (!overlay && el("transport-state"))
      el("transport-state").textContent =
        "Local connection interrupted. Reconnecting…";
    if (reconnectTimer) clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(() => {
      void bootSocket();
    }, 2500);
  });
}
async function bootSocket(): Promise<void> {
  try {
    if (overlay) {
      socketConnect(new URLSearchParams(location.search).get("key") ?? "");
      return;
    }
    const response = await fetch("/api/session");
    if (!response.ok) throw new Error("Local session unavailable.");
    const session = (await response.json()) as {
      csrf_token: string;
      overlay_url: string;
    };
    csrf = session.csrf_token;
    obsUrl = session.overlay_url;
    socketConnect(csrf);
  } catch {
    if (!overlay)
      el("transport-state").textContent =
        "Local service unavailable. Retrying…";
    reconnectTimer = setTimeout(() => {
      void bootSocket();
    }, 3000);
  }
}
if (overlay) {
  document.body.classList.add("overlay");
  root.innerHTML =
    '<div class="overlay-standby">Connecting to Raid Handshake…</div>';
} else {
  mount();
}
void bootSocket().then(() => {
  if (!overlay)
    void loadDevices().catch(() => toast("Could not load audio inputs.", true));
});
window.addEventListener("beforeunload", () => {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  connection?.close();
});
