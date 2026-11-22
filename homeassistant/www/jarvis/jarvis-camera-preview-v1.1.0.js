/* Camera preview v1.1.0: auto-started HA live view with the Jarvis infobox lifecycle. */
const views = new WeakMap();
const active = voice => voice.mode === "dashboard" && voice.card.isConnected && !document.hidden;
const de = voice => String(voice.h?.language || navigator.language || "en").startsWith("de");
const label = (voice, german, english) => de(voice) ? german : english;
const node = (tag, text, className) => {
  const item = document.createElement(tag);
  if (text != null) item.textContent = text;
  if (className) item.className = className;
  return item;
};

export async function previewCamera(voice, text, session) {
  const generation = voice.generation;
  const current = () => voice.generation === generation && voice.session === session && active(voice);
  if (!current()) return false;
  try {
    const result = await voice.h.callApi("POST", "jarvis_echo_relay/resolve_camera", {text});
    if (!current() || !/^camera\.[a-z0-9_]+$/.test(result?.camera_entity_id || "")) return false;
    voice.closeInfo?.();
    closeCameraInfo(voice);
    session.cameraEntity = result.camera_entity_id;
    voice.lastKnowledge = null;
    voice.infoRequest = (voice.infoRequest || 0) + 1;
    const info = {kind: "camera", id: voice.infoRequest, cameraEntity: result.camera_entity_id,
      hardDeadline: Date.now() + 180000, deadline: null, playbackEnded: false, extended: false};
    const view = new CameraInfo(voice, info, generation);
    info.cameraView = view;
    voice.info = info;
    views.set(voice, view);
    view.open();
    return true;
  } catch {
    // Camera lookup and preview failures never interrupt the spoken answer.
    return false;
  }
}

export function closeCameraInfo(voice) {
  const view = views.get(voice);
  if (!view) return;
  view.dispose();
  if (voice.info === view.info) voice.info = null;
}

class CameraInfo {
  constructor(voice, info, generation) {
    Object.assign(this, {voice, info, generation, disposed: false});
  }
  current() {
    return !this.disposed && this.voice.info === this.info &&
      this.voice.generation === this.generation && active(this.voice);
  }
  close() {
    if (this.voice.info !== this.info) { this.dispose(); return; }
    if (this.voice.closeInfo) this.voice.closeInfo();
    else closeCameraInfo(this.voice);
  }
  open() {
    if (!this.current() || !this.voice.card.shadowRoot) { this.close(); return; }
    const v = this.voice;
    this.previousFocus = this.voice.card.shadowRoot.activeElement;
    this.overlay = node("div", null, "jv-info-overlay jv-camera-overlay");
    this.overlay.dataset.jvKnowledge = String(this.info.id);
    this.overlay.setAttribute("role", "dialog");
    this.overlay.setAttribute("aria-modal", "true");
    this.overlay.setAttribute("aria-label", label(v, "Jarvis Kamera-Infobox", "Jarvis camera info"));
    const style = node("style", `.jv-camera-overlay{position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,.65);display:grid;place-items:center;padding:20px;box-sizing:border-box}.jv-camera-overlay .jv-info{width:min(980px,100%);max-height:90dvh;overflow:auto;background:var(--card-background-color,#1c2026);color:var(--primary-text-color,#eee);border:1px solid var(--divider-color,#46505e);border-radius:20px;padding:20px;box-sizing:border-box}.jv-camera-overlay .jv-info-top{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}.jv-camera-overlay .jv-info-buttons{display:flex;gap:8px;flex-wrap:wrap}.jv-camera-overlay button{font:inherit;color:inherit;background:var(--secondary-background-color,#303844);border:1px solid var(--divider-color,#596474);border-radius:10px;padding:9px 12px;cursor:pointer}.jv-camera-overlay h2{font-size:22px;margin:18px 0 12px}.jv-camera-feed{border-radius:12px;overflow:hidden;min-height:100px;background:#080a0d}.jv-camera-reply{white-space:pre-wrap;line-height:1.5;margin:14px 0}.jv-camera-overlay .jv-info-foot{font-size:12px;opacity:.8;margin-top:12px}.jv-camera-overlay [data-jv-info-countdown]{font-size:12px;text-align:right;margin-top:12px}.jv-camera-overlay [hidden]{display:none!important}@media(max-width:600px){.jv-camera-overlay{padding:10px}.jv-camera-overlay .jv-info{padding:14px;max-height:94dvh}}`);
    const card = node("article", null, "jv-info");
    const top = node("div", null, "jv-info-top");
    top.append(node("small", label(v, "JARVIS · KAMERA", "JARVIS · CAMERA")));
    const buttons = node("div", null, "jv-info-buttons");
    const button = (text, fn) => { const b = node("button", text); b.type = "button"; b.onclick = fn; return b; };
    this.extendButton = button(label(v, "Länger anzeigen (+60 s)", "Keep open (+60 s)"), () => this.extend());
    this.closeButton = button(label(v, "Schließen ✕", "Close ✕"), () => this.close());
    buttons.append(this.extendButton, this.closeButton); top.append(buttons);
    this.title = node("h2");
    this.feed = node("div", null, "jv-camera-feed");
    this.status = node("p", label(v, "Liveansicht wird gestartet …", "Starting live view …"));
    this.feed.append(this.status);
    this.reply = node("p", label(v, "Das aktuelle Einzelbild wird ausgewertet …", "Describing the current snapshot …"), "jv-camera-reply");
    const foot = node("div", label(v, "Liveansicht ohne Ton · Jarvis beschreibt ein Einzelbild.", "Muted live view · Jarvis describes a snapshot."), "jv-info-foot");
    this.countdown = node("div"); this.countdown.dataset.jvInfoCountdown = "1";
    card.append(top, this.title, this.feed, this.reply, foot, this.countdown);
    this.overlay.append(style, card);
    this.overlay.addEventListener("click", e => { if (e.target === this.overlay) this.close(); });
    this.overlay.addEventListener("keydown", e => {
      if (e.key === "Escape") { e.stopPropagation(); this.close(); }
      if (e.key === "Tab") {
        const buttons = [this.extendButton, this.closeButton].filter(b => !b.hidden);
        const first = buttons[0], last = buttons.at(-1), focused = this.voice.card.shadowRoot.activeElement;
        if (e.shiftKey && focused === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && focused === last) { e.preventDefault(); first.focus(); }
      }
    });
    this.onHidden = () => { if (document.hidden) this.close(); };
    this.onPageHide = () => this.close();
    document.addEventListener("visibilitychange", this.onHidden);
    window.addEventListener("pagehide", this.onPageHide);
    this.voice.card.shadowRoot.append(this.overlay);
    this.update();
    this.closeButton.focus({preventScroll: true});
    if (v.scheduleInfo) v.scheduleInfo(); else this.schedule();
    void this.startFeed();
  }
  async startFeed() {
    try {
      const helpers = await window.loadCardHelpers();
      if (!this.current()) return;
      this.player = helpers.createCardElement({type: "picture-entity", entity: this.info.cameraEntity,
        camera_image: this.info.cameraEntity, camera_view: "live", fit_mode: "contain",
        show_name: false, show_state: false, tap_action: {action: "none"}, hold_action: {action: "none"}});
      this.player.hass = this.voice.h;
      this.feed.replaceChildren(this.player);
    } catch {
      if (this.current()) this.status.textContent = label(this.voice,
        "Liveansicht konnte nicht gestartet werden. Prüfe die Kamera in Home Assistant.",
        "Could not start live view. Check the camera in Home Assistant.");
    }
  }
  update() {
    if (!this.current()) { this.close(); return; }
    const state = this.voice.h?.states?.[this.info.cameraEntity];
    this.title.textContent = state?.attributes?.friendly_name || this.info.cameraEntity;
    if (this.player) this.player.hass = this.voice.h;
    this.extendButton.hidden = this.info.extended;
  }
  setReply(text) {
    if (this.current() && typeof text === "string") this.reply.textContent = text;
  }
  seconds() {
    const value = Number(this.voice.pref?.infoSeconds ?? this.voice.cfg?.camera_info_seconds ?? 30);
    return Number.isFinite(value) ? Math.max(15, Math.min(90, value)) : 30;
  }
  schedule(ended = false) {
    const info = this.info;
    if (!this.current()) { this.close(); return; }
    if (ended && !info.playbackEnded) {
      info.playbackEnded = true;
      info.deadline = Math.min(info.hardDeadline, Math.max(info.deadline || 0, Date.now() + this.seconds() * 1000));
    }
    clearTimeout(this.timer); clearInterval(this.ticker);
    const deadline = info.deadline || info.hardDeadline;
    const tick = () => {
      if (!this.current() || Date.now() >= deadline) { this.close(); return; }
      const remaining = Math.ceil((deadline - Date.now()) / 1000);
      this.countdown.textContent = info.deadline
        ? label(this.voice, `Schließt in ${remaining} s`, `Closes in ${remaining} s`)
        : label(this.voice, `Schließt nach der Sprachantwort · spätestens in ${remaining} s`, `Closes after the spoken reply · at most ${remaining} s`);
    };
    this.timer = setTimeout(() => this.close(), Math.max(0, deadline - Date.now()));
    this.ticker = setInterval(tick, 1000); tick();
  }
  extend() {
    if (!this.current() || this.info.extended) return;
    this.info.extended = true;
    this.info.deadline = Math.min(this.info.hardDeadline, Math.max(this.info.deadline || 0, Date.now()) + 60000);
    if (this.voice.scheduleInfo) this.voice.scheduleInfo(); else this.schedule();
    this.update();
    this.closeButton.focus({preventScroll: true});
  }
  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    clearTimeout(this.timer); clearInterval(this.ticker);
    document.removeEventListener("visibilitychange", this.onHidden);
    window.removeEventListener("pagehide", this.onPageHide);
    this.player?.remove();
    this.overlay?.remove();
    this.player = null;
    if (views.get(this.voice) === this) views.delete(this.voice);
    if (!document.hidden && this.previousFocus?.isConnected) this.previousFocus.focus({preventScroll: true});
  }
}
