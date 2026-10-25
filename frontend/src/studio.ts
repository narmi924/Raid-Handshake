import type { State, Raid, Draft, OverlayState } from "./types";

const root = document.querySelector<HTMLDivElement>("#app")!;
const isOverlay = location.pathname === "/overlay";
const logo = `<svg viewBox="0 0 40 40" fill="none" aria-hidden="true"><path d="M7 12h17l-5-5M33 28H16l5 5M28 11l5 5-5 5M12 29l-5-5 5-5" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const icon = (name: string): string => {
  const paths: Record<string, string> = {
    settings:
      '<path d="m9 4 1-2h4l1 2 2 1 2-.2 2 3.4-1.2 1.6v2.4l1.2 1.6-2 3.4-2-.2-2 1-1 2h-4l-1-2-2-1-2 .2-2-3.4L4.2 12V9.6L3 8l2-3.4 2 .2Z"/><circle cx="12" cy="10.8" r="3"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
    close: '<path d="m6 6 12 12M6 18 18 6"/>',
    mic: '<rect x="9" y="3" width="6" height="12" rx="3"/><path d="M6 10v2a6 6 0 0 0 12 0v-2m-6 8v3m-3 0h6"/>',
    refresh:
      '<path d="M20 7v5h-5M4 17v-5h5m10-5a8 8 0 0 0-14-1M5 17a8 8 0 0 0 14 1"/>',
    copy: '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h3"/>',
  };
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] ?? paths.arrow}</svg>`;
};
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
const clock = (value?: number | null): string =>
  value == null
    ? "—"
    : new Date(value * 1000).toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
const count = (value?: number | null): string =>
  value == null ? "—" : value.toLocaleString("en-US");
const ago = (seconds: number): string =>
  seconds < 60
    ? "just now"
    : seconds < 3600
      ? `${Math.floor(seconds / 60)}m ago`
      : `${Math.floor(seconds / 3600)}h ago`;
const friendlyDevice = (value: string): string =>
  value
    .replace(/^扬声器/, "Speakers")
    .replace(/^麦克风阵列/, "Microphone array")
    .replace(/^麦克风/, "Microphone");
const safeLink = (value: string): string => {
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
function html(id: string, value: string): void {
  if (el(id).innerHTML !== value) el(id).innerHTML = value;
}
function remember(key: string, value?: string): string | null {
  try {
    if (value !== undefined) localStorage.setItem(key, value);
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

type AudioDevice = { id: string; name: string; loopback: boolean };
let state: State | null = null;
let csrf = "";
let obsUrl = "";
let connection: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let closing = false;
let initialized = false;
let view: "setup" | "studio" = "setup";
let step = 1;
let copiedOverlay = false;
let working = false;
let welcomeDirty = false;
let devices: AudioDevice[] = [];
const previews = new Map<string, Promise<void>>();

async function api<T = unknown>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Something went wrong. Try again.",
    );
  return data as T;
}
let toastTimer: ReturnType<typeof setTimeout>;
function toast(message: string, error = false): void {
  el("toast").textContent = message;
  el("toast").className = `toast shown${error ? " error" : ""}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el("toast").classList.remove("shown"), 5500);
}
async function refreshState(): Promise<void> {
  const response = await fetch("/api/state");
  if (!response.ok) throw new Error("Cannot reach the local service.");
  render((await response.json()) as State);
}
async function perform(
  work: () => Promise<unknown>,
  success?: string,
): Promise<void> {
  if (working) return;
  working = true;
  if (state) render(state);
  try {
    await work();
    if (success) toast(success);
    await refreshState();
  } catch (error) {
    toast(
      error instanceof Error ? error.message : "Something went wrong.",
      true,
    );
  } finally {
    working = false;
    if (state) render(state);
  }
}
function draftNow(): Draft | null {
  return (
    state?.drafts.find((item) => item.id === state?.raids[0]?.draft_id) ?? null
  );
}
const canSend = (draft: Draft | null): boolean =>
  !!draft && ["pending", "previewed", "failed"].includes(draft.status);

function mount(): void {
  root.innerHTML = `
  <header class="topbar"><a class="brand" href="/" aria-label="Raid Handshake home"><span class="brand-mark">${logo}</span>Raid <b>Handshake</b></a><div class="topbar-right"><span id="channel-label" class="channel-label">Local studio</span><button id="open-settings" class="button quiet">${icon("settings")}<span>Settings</span></button></div></header>
  <main id="main-content" class="app-shell">
    <section id="setup-view" class="setup-view" hidden aria-labelledby="setup-title">
      <div class="page-intro"><p class="overline">A BETTER FIRST HELLO</p><h1 id="setup-title">Make yourself raid-ready.</h1><p>Three small steps. Then just welcome your next community.</p></div>
      <ol class="stepper" aria-label="Setup progress"><li data-step="1"><span>1</span>Connect Twitch</li><li data-step="2"><span>2</span>Choose audio</li><li data-step="3"><span>3</span>Add to OBS</li></ol>
      <div class="setup-card">
        <section id="setup-one" aria-labelledby="connect-title"><span class="step-caption">STEP 1 OF 3</span><h2 id="connect-title">Your receiving channel.</h2><p class="subcopy">Connect the Twitch account that will receive raids.</p><div id="setup-channel-connected"></div><div id="setup-channel-fields"><label for="setup-client-id">Twitch Public Client ID</label><input id="setup-client-id" autocomplete="off" spellcheck="false" placeholder="Paste your Client ID"/><p class="helper">Already registered an app? Use its Public Client ID. <a href="https://dev.twitch.tv/console/apps" target="_blank" rel="noreferrer">Developer Console ↗</a></p></div><div id="setup-auth" class="auth-area"></div></section>
        <section id="setup-two" hidden aria-labelledby="audio-title"><span class="step-caption">STEP 2 OF 3</span><h2 id="audio-title">Let your stream do the talking.</h2><p class="subcopy">Choose the speech your audience hears. We'll turn it into a welcome.</p><div id="setup-key-fields"><label for="setup-openai-key">OpenAI API key</label><input id="setup-openai-key" type="password" autocomplete="new-password" placeholder="Saved securely on this computer"/><p class="helper">Your selected audio and recent chat are sent to OpenAI for context.</p></div><label for="setup-audio-device">Audio source</label><div class="input-row"><select id="setup-audio-device"></select><button type="button" data-refresh-devices class="button icon-button secondary" aria-label="Refresh audio devices">${icon("refresh")}</button></div><p class="helper">Playing a video or HTML page? Choose <b>System audio</b>. Otherwise choose your microphone.</p><div class="audio-feedback"><div class="audio-meter" aria-hidden="true"><i data-audio-meter></i></div><span id="setup-audio-status">Listening starts only when you choose it.</span></div><p id="setup-audio-error" class="error-text" role="status"></p><div id="setup-summary" class="setup-summary" hidden></div></section>
        <section id="setup-three" hidden aria-labelledby="overlay-title"><span class="step-caption">STEP 3 OF 3</span><h2 id="overlay-title">A little space in OBS.</h2><p class="subcopy">Add your private overlay link as a new Browser source.</p><div class="obs-preview"><div class="obs-preview-content">${logo}<span>Your stream</span></div><div class="obs-preview-card"><span class="tiny">RAID HANDSHAKE</span><strong>A new community, in context.</strong><span class="helper">Your guest card will appear here.</span></div></div><ol class="obs-instructions"><li>In OBS, select <b>Sources → + → Browser</b>.</li><li>Paste the overlay URL. Set the size to <b>1920 × 1080</b>.</li><li>Place it above your stream content, then open your studio.</li></ol><p id="overlay-copy-note" class="helper">This link gives read-only access to your overlay. Keep it private.</p></section>
        <div class="setup-actions"><button id="setup-back" class="button quiet" hidden>Back</button><button id="setup-next" class="button primary">Connect Twitch ${icon("arrow")}</button></div>
      </div><button id="return-studio" class="text-button setup-help" hidden>Back to studio</button><a class="setup-help" href="/guide" target="_blank">Need a hand? Open the quick start ↗</a>
    </section>
    <section id="studio-view" class="studio" hidden aria-labelledby="studio-title">
      <div class="studio-heading"><div><p class="overline">YOUR RAID STUDIO</p><h1 id="studio-title">Every community deserves a good hello.</h1></div><span id="studio-state" class="tag">Getting ready</span></div>
      <section class="listening-bar" aria-label="Stream context"><div class="listening-icon">${icon("mic")}</div><div class="listening-copy"><strong id="listening-title">Start listening before your next raid.</strong><span id="listening-description">Your live audio makes the welcome personal.</span></div><div class="audio-meter compact" aria-hidden="true"><i data-audio-meter></i></div><button id="listen-toggle" class="button primary">Start listening</button></section>
      <p id="studio-error" class="error-text" role="status"></p>
      <section id="empty-stage" class="empty-stage"><div class="empty-handshake">${logo}</div><h2>Your next welcome starts here.</h2><p>When a raid arrives, you'll see who is coming<br/>and a welcome message ready for your review.</p><div class="empty-explainer"><span><b>For you</b>A little context about your guests.</span><span><b>For them</b>A quick way into your stream.</span></div></section>
      <div id="raid-workspace" class="raid-workspace" hidden>
        <section class="card welcome-card" aria-labelledby="welcome-title"><div class="card-heading"><h2 id="welcome-title">Their first message.</h2><span id="send-mode" class="tag">Review first</span></div><p class="subcopy">A warm landing, grounded in your stream's recent audio.</p><div class="chat-bubble"><span class="chat-speaker" id="chat-speaker">Your channel</span><p id="welcome-text"></p></div><div class="message-meta"><span id="draft-status">Preparing welcome</span><span id="draft-length"></span></div><p id="draft-error" class="error-text" role="status"></p><button id="send-draft" class="button primary send-button" disabled>Send welcome message ${icon("arrow")}</button><div id="sent-confirmation" class="sent-confirmation" hidden>${icon("check")}<span>Delivered to Twitch chat</span><a id="open-chat" target="_blank" rel="noreferrer">View chat ↗</a></div><p id="hotkey-note" class="helper shortcut-note">Review the message, then confirm. <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Enter</kbd></p><button id="rebuild-draft" class="text-button" hidden>Generate from the latest context</button></section>
        <section id="guest-panel" class="card guest-card" aria-label="Guest cheat sheet"></section>
      </div>
      <details id="context-details" class="disclosure context-disclosure"><summary><span>What your stream is doing</span><span id="context-freshness" class="helper">Waiting for audio</span></summary><div class="disclosure-body"><p id="summary-text" class="summary-text">Your spoken context will appear here.</p><div id="summary-evidence"></div><div class="details-line"><span id="summary-meta" class="helper"></span><button id="refresh-summary" class="text-button">Refresh summary</button></div><details class="transcript-details"><summary>Recent transcript</summary><div id="transcript-list"></div></details></div></details>
      <details id="metrics-panel" class="disclosure metrics-disclosure" hidden aria-label="Chat connection observations"></details>
    </section>
  </main>
  <footer class="page-footer"><span>Local on your computer. Built with Codex.</span><a href="/guide" target="_blank">Quick start ↗</a></footer>
  <dialog id="settings-dialog" class="settings-dialog" aria-labelledby="settings-title"><div class="dialog-heading"><div><p class="overline">MAKE IT YOURS</p><h2 id="settings-title">Settings</h2></div><button id="close-settings" class="button icon-button quiet" aria-label="Close settings">${icon("close")}</button></div><nav class="settings-tabs" aria-label="Settings sections">${["Connections", "Audio", "Welcome", "Advanced"].map((title, i) => `<button class="tab" data-settings-tab="${i}" aria-pressed="${i === 0}">${title}</button>`).join("")}</nav>
    <div class="settings-content">
      <section data-settings-pane="0"><h3>Your receiving channel</h3><div id="settings-channel"></div><button id="run-setup" class="text-button">Open connection setup</button><details class="connection-options"><summary>Connection options</summary><button id="disconnect-twitch" class="button secondary">Disconnect Twitch</button></details><hr/><h3>OpenAI</h3><p id="key-status" class="subcopy"></p><details id="key-editor"><summary>Replace API key</summary><form id="key-form"><label for="openai-key">OpenAI API key</label><input id="openai-key" type="password" autocomplete="new-password" placeholder="Paste your API key"/><button type="submit" class="button primary">Save key</button></form></details><p class="helper">Selected audio and chat context are processed by your OpenAI API project.</p><p id="storage-note" class="helper"></p><hr/><h3>OBS overlay</h3><p class="subcopy">Add the link as a 1920 × 1080 Browser source above your content.</p><button id="copy-obs" class="button secondary">${icon("copy")} Copy overlay URL</button></section>
      <section data-settings-pane="1" hidden><h3>The audio your audience hears.</h3><p class="subcopy">Choose a microphone for live speech, or System audio for a video, game or HTML source.</p><label for="audio-device">Audio source</label><div class="input-row"><select id="audio-device"></select><button type="button" data-refresh-devices class="button icon-button secondary" aria-label="Refresh audio devices">${icon("refresh")}</button></div><p class="helper">For System audio, use the same output device as OBS Desktop Audio. Keep Twitch web players muted on this computer to avoid echo.</p><button id="save-audio" class="button primary">Use this source</button><a class="help-link" href="/guide/audio" target="_blank">OBS audio walkthrough ↗</a></section>
      <section data-settings-pane="2" hidden><form id="welcome-form"><h3>Sound like your channel.</h3><label for="commands">How to join in</label><input id="commands" maxlength="100" placeholder="A real command or a simple participation hint"/><label for="channel-rule">One channel rule</label><input id="channel-rule" maxlength="100"/><label for="language">Message language</label><input id="language" maxlength="40"/><details><summary>Customize the template</summary><label for="template">Welcome template</label><textarea id="template" rows="4" maxlength="350"></textarea><p class="helper">Use {summary}, {commands}, and {rule}. Final messages must fit 500 characters.</p></details><div class="details-line"><button type="submit" class="button primary">Save welcome settings</button><span id="settings-dirty" class="helper"></span></div></form><details class="auto-options"><summary>Automatic sending <span id="auto-status" class="tag">Off</span></summary><p class="subcopy">Optional. Approve the structure and fixed wording above, then let each raid fill in the current summary and send. The final text will change without another per-message review.</p><button id="auto-toggle" class="button secondary">Approve template & turn on</button></details></section>
      <section data-settings-pane="3" hidden><form id="model-form"><h3>OpenAI models</h3><label for="transcription-model">Transcription model</label><input id="transcription-model"/><label for="summary-model">Summary model</label><input id="summary-model"/><button type="submit" class="button primary">Save models</button></form><details class="diagnostics"><summary>Connection diagnostics</summary><dl id="diagnostics-list"></dl><div id="activity-list"></div></details></section>
    </div>
  </dialog><div id="toast" class="toast" role="status" aria-live="polite"></div>`;
  bind();
}

function guestCard(raid: Raid, now: number): string {
  const elapsed = Math.max(0, now - raid.started_at);
  const tokens = [
    ...(raid.learning.emotes ?? []).map(
      (item) =>
        `<span class="tag">${esc(item.name)} ×${count(item.count)}</span>`,
    ),
    ...(raid.learning.tokens ?? []).map(
      (item) =>
        `<span class="tag">${esc(item.text)} ×${count(item.count)}</span>`,
    ),
  ];
  return `<div class="card-heading"><span class="${elapsed < 90 ? "raid-badge" : "tag"}">${elapsed < 90 ? "INCOMING RAID" : "LATEST RAID"}</span><span class="helper">${ago(elapsed)}</span></div><div class="guest-identity"><div class="avatar">${raid.guest.image ? `<img src="${safeLink(raid.guest.image)}" alt=""/>` : esc(raid.source_name.slice(0, 2))}</div><div><h2>${esc(raid.source_name)}</h2><span class="helper">${count(raid.viewers)} ${raid.viewers === 1 ? "raid participant" : "raid participants"}</span></div></div><div class="guest-stream"><span class="tag">${esc(raid.guest.category)}</span><p>${esc(raid.guest.title)}</p></div><div class="guest-section"><h3>Recent clips</h3>${raid.guest.clips.length ? `<ul class="clip-list">${raid.guest.clips.map((clip) => `<li><a href="${safeLink(clip.url)}" target="_blank" rel="noreferrer">${esc(clip.title)} ↗</a></li>`).join("")}</ul>` : `<p class="helper">${esc(raid.guest.error ?? "No recent clips available.")}</p>`}</div><div class="guest-section"><div class="card-heading"><h3>Community signals</h3>${raid.learning.status === "learning" ? `<span class="helper">Learning · ${Math.ceil(Math.max(0, 60 - elapsed))}s</span>` : ""}</div>${tokens.length ? `<div class="signal-tags">${tokens.join("")}</div><p class="helper">Source-owned emotes and observed repeated text. Third-party text identity is unverified.</p>` : `<p class="helper">${raid.learning.status === "learning" ? "Listening to the first minute of chat." : "Not enough samples from different people yet."}</p>`}</div>`;
}
function metricsCard(raid: Raid, now: number): string {
  const elapsed = now - raid.started_at;
  return `<div class="card-heading"><div><h2>After the hello.</h2><p class="helper">${count(raid.population)} estimated new chat connections · ${raid.cohort_finalized ? "arrival window closed" : "collecting arrivals for 90 seconds"}</p></div><span class="tag">CHAT CONNECTIONS</span></div><div class="table-scroll"><table><caption class="sr-only">Real chat-connection observations after the latest raid</caption><thead><tr><th scope="col">Checkpoint</th><th scope="col">Connected</th><th scope="col">Spoke in last 5m</th><th scope="col">Follows*</th><th scope="col">Observed</th></tr></thead><tbody>${[
    5, 15, 30,
  ]
    .map((minute) => {
      const sample = raid.samples.find((item) => item.minute === minute);
      return `<tr><th scope="row">${minute} minutes</th><td>${sample ? count(sample.connected) : "—"}</td><td>${sample ? count(sample.spoken) : "—"}</td><td>${sample ? count(sample.follows) : "—"}</td><td class="helper">${sample ? (sample.error ? esc(sample.error) : clock(sample.observed_at)) : elapsed < minute * 60 ? `in ${Math.ceil((minute * 60 - elapsed) / 60)}m` : "Waiting for sample"}</td></tr>`;
    })
    .join(
      "",
    )}</tbody></table></div><p class="method-note">Chat connections, with update delays. These figures do not measure video viewing. *Follows are counted for the whole channel since this raid.</p>${raid.baseline_at === null ? '<p class="error-text">No fresh pre-raid baseline. Arrival estimates are unknown.</p>' : ""}${!raid.cohort_complete ? '<p class="error-text">A polling gap may have omitted new connections.</p>' : ""}${raid.overlap ? '<p class="error-text">Overlapping raids can share estimated arrivals.</p>' : ""}`;
}
function populateForms(next: State): void {
  el<HTMLInputElement>("setup-client-id").value = next.config.twitch_client_id;
  for (const [id, value] of [
    ["commands", next.config.commands],
    ["channel-rule", next.config.rule],
    ["language", next.config.language],
    ["template", next.config.template],
    ["transcription-model", next.config.transcription_model],
    ["summary-model", next.config.summary_model],
  ])
    el<HTMLInputElement>(id).value = value;
}
function deviceOptions(selected: string): string {
  return (
    `<option value="">Microphone · system default</option>` +
    [false, true]
      .map(
        (loopback) =>
          `<optgroup label="${loopback ? "System audio · playback capture" : "Microphones"}">${devices
            .filter((device) => device.loopback === loopback)
            .map(
              (device) =>
                `<option value="${esc(device.id)}"${device.id === selected ? " selected" : ""}>${loopback ? "System audio" : "Microphone"} · ${esc(friendlyDevice(device.name))}</option>`,
            )
            .join("")}</optgroup>`,
      )
      .join("")
  );
}
async function loadDevices(): Promise<void> {
  const response = await fetch("/api/audio/devices");
  const data = (await response.json()) as {
    devices: AudioDevice[];
    error: string | null;
  };
  devices = data.devices;
  for (const id of ["audio-device", "setup-audio-device"]) {
    const selected =
      el<HTMLSelectElement>(id).value || state?.config.audio_device_id || "";
    el(id).innerHTML = deviceOptions(selected);
  }
  if (data.error) toast(data.error, true);
}
function setupRender(next: State): void {
  el("setup-one").hidden = step !== 1;
  el("setup-two").hidden = step !== 2;
  el("setup-three").hidden = step !== 3;
  document.querySelectorAll<HTMLElement>("[data-step]").forEach((item) => {
    item.classList.toggle("current", Number(item.dataset.step) === step);
    item.classList.toggle("complete", Number(item.dataset.step) < step);
    if (Number(item.dataset.step) === step)
      item.setAttribute("aria-current", "step");
    else item.removeAttribute("aria-current");
  });
  el("setup-back").hidden = step === 1;
  el("return-studio").hidden =
    !next.user ||
    !next.health.openai_configured ||
    !(
      next.raids.length ||
      remember(`raid-handshake:setup:${next.user.id}`) === "done"
    );
  el("setup-channel-fields").hidden = !!next.user;
  html(
    "setup-channel-connected",
    next.user
      ? `<div class="connected-note">${icon("check")} Connected as <b>${esc(next.user.display_name)}</b></div>`
      : "",
  );
  const device = next.device_login;
  html(
    "setup-auth",
    !next.user && device?.status === "pending"
      ? `<div class="activation"><span class="helper">Enter this code on Twitch</span><strong>${esc(device.user_code)}</strong><a class="button secondary" href="${safeLink(device.verification_uri)}" target="_blank" rel="noreferrer">Open Twitch activation ↗</a><span class="helper">Sign in as the receiving channel. Expires in ${Math.ceil(Math.max(0, device.expires_at - next.now) / 60)}m.</span></div>`
      : next.login_error
        ? `<p class="error-text">${esc(next.login_error)}</p>`
        : "",
  );
  el("setup-key-fields").hidden = next.health.openai_configured;
  el("setup-audio-status").textContent = next.summary_ready
    ? "Summary ready. Your stream has context."
    : next.audio.active
      ? "Listening. Waiting for spoken context…"
      : "Listening starts only when you choose it.";
  el("setup-audio-error").textContent =
    next.audio.error ??
    (next.health.openai_configured && next.audio.active
      ? next.summary_error
      : "") ??
    "";
  el("setup-summary").hidden = !next.summary_ready;
  el("setup-summary").textContent = next.summary?.activity ?? "";
  const button = el<HTMLButtonElement>("setup-next");
  const audioChanged =
    el<HTMLSelectElement>("setup-audio-device").value !==
    next.config.audio_device_id;
  const retryAudio = audioChanged || !!next.audio.error;
  button.textContent = working
    ? "One moment…"
    : step === 1
      ? next.user
        ? "Continue →"
        : device?.status === "pending"
          ? "Waiting for Twitch…"
          : "Connect Twitch →"
      : step === 2
        ? next.audio.active && retryAudio
          ? audioChanged
            ? "Use this source →"
            : "Retry listening →"
          : next.audio.active
            ? next.summary_ready
              ? "Continue →"
              : "Building your context…"
            : "Start listening →"
        : copiedOverlay
          ? "Open studio →"
          : "Copy overlay URL";
  button.disabled =
    working ||
    (step === 1 && !next.user && device?.status === "pending") ||
    (step === 2 && next.audio.active && !next.summary_ready && !retryAudio);
}
function render(next: State): void {
  const previous = state;
  state = next;
  if (!initialized) {
    populateForms(next);
    for (const id of ["audio-device", "setup-audio-device"])
      el(id).innerHTML = deviceOptions(next.config.audio_device_id);
    view =
      next.user &&
      next.health.openai_configured &&
      (remember(`raid-handshake:setup:${next.user.id}`) === "done" ||
        next.raids.length > 0)
        ? "studio"
        : "setup";
    step = next.user ? 2 : 1;
    initialized = true;
  }
  if (view === "setup" && step === 1 && next.user && !previous?.user) step = 2;
  if (previous?.user && !next.user) {
    view = "setup";
    step = 1;
    el<HTMLDialogElement>("settings-dialog").close();
  }
  el("setup-view").hidden = view !== "setup";
  el("studio-view").hidden = view !== "studio";
  el("channel-label").textContent = next.user
    ? `● ${next.user.display_name}`
    : "Local studio";
  setupRender(next);

  const freshBaseline =
    next.health.baseline_at !== null &&
    next.now - next.health.baseline_at <= next.config.chatters_poll_seconds * 3;
  const ready =
    next.health.eventsub === "connected" &&
    freshBaseline &&
    next.summary_ready &&
    next.audio.active;
  el("studio-state").textContent = ready
    ? "Ready for a raid"
    : next.audio.active
      ? next.summary_running
        ? "Updating context"
        : !next.summary_ready
          ? "Waiting for speech"
          : "Connecting to Twitch"
      : "Listening paused";
  el("studio-state").classList.toggle("ready", ready);
  const currentDevice = devices.find(
    (device) => device.id === next.config.audio_device_id,
  );
  el("listening-title").textContent = next.audio.active
    ? next.summary_ready
      ? "Your stream context is ready."
      : next.summary_running
        ? "Building your stream context…"
        : "Listening for your stream's speech."
    : "Start listening before your next raid.";
  el("listening-description").textContent = next.audio.active
    ? `${currentDevice?.loopback ? "System audio" : "Microphone"} · ${friendlyDevice(currentDevice?.name ?? "Default input")}`
    : "Use the audio your audience hears. No need to speak separately.";
  document
    .querySelectorAll<HTMLElement>("[data-audio-meter]")
    .forEach(
      (item) =>
        (item.style.width = `${Math.min(100, next.audio.level * 700)}%`),
    );
  const listen = el<HTMLButtonElement>("listen-toggle");
  listen.textContent = next.audio.active ? "Pause" : "Start listening";
  listen.className = `button ${next.audio.active ? "secondary" : "primary"}`;
  listen.disabled = working;
  el("studio-error").textContent =
    next.audio.error ??
    next.health.eventsub_error ??
    next.health.chatters_error ??
    (next.audio.active &&
    !next.summary_error?.startsWith("Waiting for real audio")
      ? next.summary_error
      : "") ??
    "";
  const raid = next.raids[0];
  el("empty-stage").hidden = !!raid;
  el("raid-workspace").hidden = !raid;
  el("metrics-panel").hidden = !raid;
  if (raid) {
    html("guest-panel", guestCard(raid, next.now));
    const latest = raid.samples.at(-1);
    html(
      "metrics-panel",
      `<summary><span>After the hello</span><span class="helper">${latest ? `${latest.minute}m · ${count(latest.connected)} connected · ${count(latest.spoken)} spoke` : "5 / 15 / 30 minute observations"}</span></summary><div class="disclosure-body">${metricsCard(raid, next.now)}</div>`,
    );
  }
  const draft = draftNow();
  const text = el("welcome-text");
  text.textContent =
    draft?.text ??
    "A fresh spoken summary is needed to prepare this welcome. Start listening, then generate it below.";
  text.dataset.draftId = draft?.id ?? "";
  text.dataset.textHash = draft?.text_hash ?? "";
  el("chat-speaker").textContent = next.user?.display_name ?? "Your channel";
  el("send-mode").textContent = next.config.preapproved_enabled
    ? "Template auto"
    : "Review first";
  el("draft-status").textContent =
    draft?.status === "sent"
      ? `Sent at ${clock(draft.sent_at)}`
      : draft?.status === "uncertain"
        ? "Check Twitch chat before continuing"
        : draft?.status === "sending"
          ? "Sending…"
          : draft?.status === "expired"
            ? "Context expired"
            : draft
              ? "Ready for your review"
              : "Waiting for fresh context";
  el("draft-length").textContent = draft
    ? `${Array.from(draft.text).length} / 500`
    : "";
  el("draft-error").textContent = draft?.error ?? "";
  const send = el<HTMLButtonElement>("send-draft");
  send.hidden = draft?.status === "sent";
  send.disabled = !canSend(draft) || working;
  send.textContent = working
    ? "One moment…"
    : draft?.status === "failed"
      ? "Try sending again →"
      : "Send welcome message →";
  send.className = `button ${next.audio.active ? "primary" : "secondary"} send-button`;
  el("sent-confirmation").hidden = draft?.status !== "sent";
  el<HTMLAnchorElement>("open-chat").href =
    `https://www.twitch.tv/popout/${encodeURIComponent(next.user?.login ?? "")}/chat?popout=`;
  el("hotkey-note").hidden =
    draft?.status === "sent" || draft?.status === "uncertain";
  el("hotkey-note").title = next.health.global_hotkey
    ? "Global shortcut is available."
    : (next.health.hotkey_error ??
      "Use the send button or the shortcut while this page is focused.");
  el("rebuild-draft").hidden =
    !raid ||
    (!!draft && ["sent", "sending", "uncertain"].includes(draft.status));
  el("context-freshness").textContent = next.summary_ready
    ? "Summary ready"
    : next.summary_running
      ? "Updating…"
      : "Needs fresh audio";
  el("summary-text").textContent =
    next.summary?.activity ??
    "Start listening to build a summary of what your stream is doing.";
  el("summary-meta").textContent = next.summary
    ? `Spoken context ${clock(next.summary.window_start)}–${clock(next.summary.window_end)}`
    : "Summaries require real spoken context.";
  html(
    "summary-evidence",
    next.summary
      ? next.summary.evidence
          .map((quote) => `<blockquote>“${esc(quote)}”</blockquote>`)
          .join("")
      : "",
  );
  html(
    "transcript-list",
    next.transcript.length
      ? next.transcript
          .map(
            (item) => `<p><time>${clock(item.at)}</time>${esc(item.text)}</p>`,
          )
          .join("")
      : '<p class="helper">No transcript yet.</p>',
  );
  html(
    "settings-channel",
    next.user
      ? `<p class="connected-note">${icon("check")} Connected as <b>${esc(next.user.display_name)}</b></p>`
      : '<p class="subcopy">Connect Twitch using the setup guide.</p>',
  );
  el<HTMLButtonElement>("disconnect-twitch").disabled = !next.user || working;
  el("key-status").textContent = next.health.openai_configured
    ? "Your API key is saved. It is never displayed here."
    : "Add your API key to enable transcription and summaries.";
  el("storage-note").textContent =
    `Credential storage: ${next.health.credential_storage}.`;
  el("auto-status").textContent = next.config.preapproved_enabled
    ? "On"
    : "Off";
  el("auto-toggle").textContent = next.config.preapproved_enabled
    ? "Turn off automatic sending"
    : "Approve template & turn on";
  el<HTMLButtonElement>("auto-toggle").disabled = welcomeDirty || working;
  html(
    "diagnostics-list",
    [
      ["Twitch events", next.health.eventsub],
      ["Chatters", next.health.chatters],
      [
        "Baseline",
        next.health.baseline_at
          ? clock(next.health.baseline_at)
          : "Not yet sampled",
      ],
      ["Connected chatters", count(next.health.chatters_count)],
      ["Audio", next.audio.active ? "Listening" : "Paused"],
      ["Summary", next.summary_ready ? "Ready" : "Not ready"],
    ]
      .map(
        ([name, value]) =>
          `<div><dt>${esc(name)}</dt><dd>${esc(value)}</dd></div>`,
      )
      .join(""),
  );
  html(
    "activity-list",
    next.activity
      .slice(0, 6)
      .map(
        (item) => `<p><time>${clock(item.at)}</time>${esc(item.message)}</p>`,
      )
      .join(""),
  );
  if (draft)
    requestAnimationFrame(() => {
      void markPreview(draft);
    });
}

async function markPreview(draft: Draft, explicit = false): Promise<void> {
  const revision = `${draft.id}:${draft.text_hash}`;
  const message = el("welcome-text");
  const visible = message?.getBoundingClientRect();
  const current =
    view === "studio" &&
    !el<HTMLDialogElement>("settings-dialog").open &&
    document.visibilityState === "visible" &&
    message?.dataset.draftId === draft.id &&
    message?.dataset.textHash === draft.text_hash;
  if (!current) {
    if (explicit)
      throw new Error("Review the current welcome message before sending.");
    return;
  }
  if (
    !explicit &&
    (!visible || visible.top < 50 || visible.bottom > innerHeight)
  )
    return;
  if (!canSend(draft)) return;
  const existing = previews.get(revision);
  if (existing) {
    if (explicit) await existing;
    return;
  }
  const request = api(`/api/drafts/${encodeURIComponent(draft.id)}/preview`, {
    text_hash: draft.text_hash,
  }).then(() => undefined);
  previews.set(revision, request);
  try {
    await request;
  } catch (error) {
    previews.delete(revision);
    if (explicit) throw error;
  }
}
function settingsTab(index: number): void {
  document
    .querySelectorAll<HTMLButtonElement>("[data-settings-tab]")
    .forEach((button) =>
      button.setAttribute(
        "aria-pressed",
        String(Number(button.dataset.settingsTab) === index),
      ),
    );
  document
    .querySelectorAll<HTMLElement>("[data-settings-pane]")
    .forEach(
      (pane) => (pane.hidden = Number(pane.dataset.settingsPane) !== index),
    );
}
function openSettings(index = 0): void {
  settingsTab(index);
  el<HTMLDialogElement>("settings-dialog").showModal();
}
function showSetup(): void {
  view = "setup";
  step = state?.user ? 2 : 1;
  el<HTMLDialogElement>("settings-dialog").close();
  if (state) render(state);
}
async function startAudio(id: string): Promise<void> {
  await api("/api/config", {
    values: { audio_device_id: el<HTMLSelectElement>(id).value },
  });
  await api("/api/audio/start");
}
async function copyOverlay(): Promise<void> {
  if (!obsUrl)
    throw new Error(
      "The local service is reconnecting. Try again in a moment.",
    );
  await navigator.clipboard.writeText(obsUrl);
  toast("Overlay URL copied. Add it as a Browser source in OBS.");
}
function bind(): void {
  el("open-settings").addEventListener("click", () => openSettings());
  el("close-settings").addEventListener("click", () =>
    el<HTMLDialogElement>("settings-dialog").close(),
  );
  el<HTMLDialogElement>("settings-dialog").addEventListener("close", () => {
    const draft = draftNow();
    if (draft) void markPreview(draft);
  });
  document
    .querySelectorAll<HTMLButtonElement>("[data-settings-tab]")
    .forEach((button) =>
      button.addEventListener("click", () =>
        settingsTab(Number(button.dataset.settingsTab)),
      ),
    );
  document
    .querySelectorAll<HTMLButtonElement>("[data-refresh-devices]")
    .forEach((button) =>
      button.addEventListener("click", () => {
        void perform(loadDevices);
      }),
    );
  el("run-setup").addEventListener("click", showSetup);
  el("return-studio").addEventListener("click", () => {
    view = "studio";
    if (state) render(state);
  });
  el("setup-audio-device").addEventListener("change", () => {
    if (state) render(state);
  });
  el("setup-back").addEventListener("click", () => {
    step = Math.max(1, step - 1);
    if (state) render(state);
  });
  el("setup-next").addEventListener("click", () => {
    void perform(async () => {
      if (step === 1) {
        if (state?.user) {
          step = 2;
          return;
        }
        const clientId = el<HTMLInputElement>("setup-client-id").value.trim();
        if (!clientId)
          throw new Error("Paste your Twitch Public Client ID first.");
        await api("/api/config", { values: { twitch_client_id: clientId } });
        await api("/api/twitch/connect");
      } else if (step === 2) {
        if (!state?.health.openai_configured) {
          const key = el<HTMLInputElement>("setup-openai-key").value.trim();
          if (!key)
            throw new Error("Add your OpenAI API key before starting audio.");
          await api("/api/openai/key", { api_key: key });
          el<HTMLInputElement>("setup-openai-key").value = "";
        }
        const changed =
          el<HTMLSelectElement>("setup-audio-device").value !==
          state?.config.audio_device_id;
        if (state?.audio.active && (changed || state.audio.error)) {
          await api("/api/audio/stop");
          await startAudio("setup-audio-device");
        } else if (state?.audio.active && state.summary_ready) step = 3;
        else if (!state?.audio.active) await startAudio("setup-audio-device");
      } else if (!copiedOverlay) {
        await copyOverlay();
        copiedOverlay = true;
        el("overlay-copy-note").textContent =
          "Copied. Once your Browser source is added, open the studio.";
      } else {
        if (state?.user)
          remember(`raid-handshake:setup:${state.user.id}`, "done");
        view = "studio";
      }
    });
  });
  el("listen-toggle").addEventListener("click", () => {
    void perform(async () => {
      if (!state?.health.openai_configured || !state.user) {
        showSetup();
        return;
      }
      if (state.audio.active) await api("/api/audio/stop");
      else await api("/api/audio/start");
    });
  });
  el("save-audio").addEventListener("click", () => {
    void perform(async () => {
      const selected = el<HTMLSelectElement>("audio-device").value;
      const restart =
        !!state?.audio.active && selected !== state.config.audio_device_id;
      if (restart) await api("/api/audio/stop");
      await api("/api/config", { values: { audio_device_id: selected } });
      if (restart) await api("/api/audio/start");
      el<HTMLSelectElement>("setup-audio-device").value = selected;
    }, "Audio source saved.");
  });
  el("copy-obs").addEventListener("click", () => {
    void perform(copyOverlay);
  });
  el("disconnect-twitch").addEventListener("click", () => {
    void perform(() => api("/api/twitch/disconnect"));
  });
  el("key-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void perform(async () => {
      await api("/api/openai/key", {
        api_key: el<HTMLInputElement>("openai-key").value.trim(),
      });
      el<HTMLInputElement>("openai-key").value = "";
      el<HTMLDetailsElement>("key-editor").open = false;
    }, "API key saved.");
  });
  el("send-draft").addEventListener("click", () => {
    void perform(async () => {
      const draft = draftNow();
      if (!draft) throw new Error("Wait for a welcome message first.");
      await markPreview(draft, true);
      const sent = await api<Draft>(
        `/api/drafts/${encodeURIComponent(draft.id)}/send`,
      );
      if (sent.status !== "sent")
        throw new Error(sent.error ?? "The message was not delivered.");
    }, "Welcome message delivered to Twitch.");
  });
  el("rebuild-draft").addEventListener("click", () => {
    void perform(async () => {
      const raid = state?.raids[0];
      if (raid) await api(`/api/raids/${encodeURIComponent(raid.id)}/draft`);
    });
  });
  el("refresh-summary").addEventListener("click", () => {
    void perform(() => api("/api/summary/refresh"));
  });
  el("welcome-form").addEventListener("input", () => {
    welcomeDirty = true;
    el("settings-dirty").textContent = "Unsaved changes";
    el<HTMLButtonElement>("auto-toggle").disabled = true;
  });
  el("welcome-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void perform(async () => {
      await api("/api/config", {
        values: {
          commands: el<HTMLInputElement>("commands").value,
          rule: el<HTMLInputElement>("channel-rule").value,
          language: el<HTMLInputElement>("language").value,
          template: el<HTMLTextAreaElement>("template").value,
        },
      });
      welcomeDirty = false;
      el("settings-dirty").textContent = "";
    }, "Welcome settings saved.");
  });
  el("model-form").addEventListener("submit", (event) => {
    event.preventDefault();
    void perform(
      () =>
        api("/api/config", {
          values: {
            transcription_model: el<HTMLInputElement>("transcription-model")
              .value,
            summary_model: el<HTMLInputElement>("summary-model").value,
          },
        }),
      "Model settings saved.",
    );
  });
  el("auto-toggle").addEventListener("click", () => {
    void perform(async () => {
      if (welcomeDirty || !state)
        throw new Error("Save and review your template first.");
      await api("/api/template/approval", {
        enabled: !state.config.preapproved_enabled,
        template_hash: state.template_hash,
      });
    });
  });
  const previewVisible = () => {
    const draft = draftNow();
    if (draft) void markPreview(draft);
  };
  document.addEventListener("visibilitychange", previewVisible);
  window.addEventListener("scroll", previewVisible, { passive: true });
  window.addEventListener("resize", previewVisible);
  document.addEventListener("keydown", (event) => {
    if (
      event.ctrlKey &&
      event.shiftKey &&
      event.key === "Enter" &&
      !state?.health.global_hotkey &&
      view === "studio" &&
      !el<HTMLDialogElement>("settings-dialog").open
    ) {
      event.preventDefault();
      el<HTMLButtonElement>("send-draft").click();
    }
  });
}

function renderOverlay(next: OverlayState): void {
  const raid = next.raids[0];
  if (!raid || !next.channel) {
    root.innerHTML = `<div class="overlay-standby"><span class="brand-mark">${logo}</span>Raid Handshake · standing by</div>`;
    return;
  }
  const elapsed = next.now - raid.started_at;
  const sample = raid.samples.at(-1);
  const showMetrics =
    sample && next.now - (sample.observed_at ?? sample.scheduled_at) < 45;
  root.innerHTML = `<div class="overlay-guest${elapsed > 90 ? " collapsed" : ""}">${elapsed <= 90 ? guestCard(raid, next.now) : `<span class="tag">RAID HANDSHAKE</span><strong>${esc(raid.source_name)}</strong><span>${count(raid.viewers)} participants</span>`}</div>${next.landing && elapsed < 90 ? `<div class="overlay-landing"><span class="overline">WELCOME TO ${esc(next.channel)}</span><p>${esc(next.landing)}</p></div>` : ""}${showMetrics ? `<div class="overlay-metrics">${metricsCard(raid, next.now)}</div>` : ""}`;
}
function socketConnect(token: string): void {
  const ws = new WebSocket(
    `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`,
  );
  connection = ws;
  ws.addEventListener("open", () =>
    ws.send(JSON.stringify({ token, view: isOverlay ? "overlay" : "admin" })),
  );
  ws.addEventListener("message", (event) => {
    if (isOverlay) renderOverlay(JSON.parse(event.data) as OverlayState);
    else render(JSON.parse(event.data) as State);
  });
  ws.addEventListener("close", () => {
    if (closing) return;
    if (!isOverlay) {
      el("studio-state").textContent = "Reconnecting…";
      el("studio-state").classList.remove("ready");
    }
    clearTimeout(reconnectTimer ?? undefined);
    reconnectTimer = setTimeout(() => {
      void bootSocket();
    }, 2500);
  });
}
async function bootSocket(): Promise<void> {
  try {
    if (isOverlay) {
      socketConnect(new URLSearchParams(location.search).get("key") ?? "");
      return;
    }
    const response = await fetch("/api/session");
    if (!response.ok) throw new Error("Local service unavailable.");
    const session = (await response.json()) as {
      csrf_token: string;
      overlay_url: string;
    };
    csrf = session.csrf_token;
    obsUrl = session.overlay_url;
    socketConnect(csrf);
  } catch {
    if (!isOverlay) toast("Waiting for the local service. Reconnecting…", true);
    reconnectTimer = setTimeout(() => {
      void bootSocket();
    }, 3000);
  }
}
if (isOverlay) {
  document.body.classList.add("overlay");
  root.innerHTML =
    '<div class="overlay-standby">Connecting to Raid Handshake…</div>';
} else mount();
void bootSocket().then(() => {
  if (!isOverlay)
    void loadDevices().catch(() =>
      toast("Could not load audio sources. Try Settings → Audio.", true),
    );
});
window.addEventListener("beforeunload", () => {
  closing = true;
  clearTimeout(reconnectTimer ?? undefined);
  connection?.close();
});
