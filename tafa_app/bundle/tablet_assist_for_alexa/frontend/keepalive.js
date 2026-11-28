// TAFA Bluetooth Keepalive v1.1.0
// One silent playback session per frontend document. No microphone access.
(function () {
  if (customElements.get("tablet-assist-bt-keepalive")) return;
const EN = {
  "Bereit · ausgeschaltet": "Ready · off",
  "Manuell beendet": "Stopped manually",
  "Wird gestartet …": "Starting …",
  "Vom System pausiert · bei Bedarf neu starten": "Paused by system · restart if needed",
  "Audiowiedergabe nicht möglich": "Audio playback unavailable",
  "Wiedergabe beendet · bei Bedarf neu starten": "Playback ended · restart if needed",
  "Wiedergabe wartet …": "Waiting for playback …",
  "Aktiv · Dauerbetrieb ohne Zeitlimit": "Active · continuous playback",
  "Wiedergabe blockiert oder nicht möglich": "Playback blocked or unavailable",
  "Seite beendet · neu starten": "Page closed · restart",
  "Nur auf diesem Gerät. Lautloser Dauerbetrieb, auch beim Dashboard-Wechsel innerhalb derselben Seite. Kein Mikrofonzugriff.": "On this device only. Silent continuous playback across dashboard navigation within the same page. No microphone access.",
  "Dauerbetrieb starten": "Start continuous playback",
  "Stoppen": "Stop",
  "Endet beim Schließen oder Neuladen der Seite, beim manuellen Stoppen oder wenn Android die Wiedergabe beendet. Bluetooth-Wirkung nicht messbar.": "Ends when the page closes or reloads, when stopped manually or when Android ends playback. Bluetooth effectiveness cannot be measured.",
  "Manuell gesteuerter Silent-Audio-Dauerbetrieb": "Manually controlled continuous silent audio"
};
function language(hass){ return String(hass?.locale?.language || hass?.language || document.querySelector("home-assistant")?.hass?.locale?.language || document.documentElement.lang || navigator.language || "en").toLowerCase().startsWith("de") ? "de" : "en"; }
function tr(s,hass){return language(hass)==="de" ? s : (EN[s] || s);}
function localize(html,hass){if(language(hass)==="de")return html;for(const [de,en] of Object.entries(EN))html=html.split(de).join(en);return html;}
  const listeners = new Set();
  let audio = null, url = null, message = "Bereit · ausgeschaltet";

  function publish(text) {
    message = text;
    listeners.forEach(function (fn) { fn(); });
  }

  function stop(reason) {
    const old = audio, oldUrl = url;
    audio = null;
    url = null;
    if (old) {
      old.pause();
      old.removeAttribute("src");
      old.load();
    }
    if (oldUrl) URL.revokeObjectURL(oldUrl);
    publish(reason || "Manuell beendet");
  }

  async function start() {
    if (audio) return;
    let a = null;
    try {
      const n = 16000 * 10;
      const b = new ArrayBuffer(44 + n * 2), v = new DataView(b);
      const str = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
      str(0, "RIFF"); v.setUint32(4, 36 + n * 2, true); str(8, "WAVE");
      str(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
      v.setUint16(22, 1, true); v.setUint32(24, 16000, true); v.setUint32(28, 32000, true);
      v.setUint16(32, 2, true); v.setUint16(34, 16, true); str(36, "data");
      v.setUint32(40, n * 2, true);
      url = URL.createObjectURL(new Blob([b], {type: "audio/wav"}));
      a = new Audio(url);
      audio = a;
      a.loop = true;
      publish("Wird gestartet …");
      a.addEventListener("pause", function () {
        if (audio === a) stop("Vom System pausiert · bei Bedarf neu starten");
      });
      a.addEventListener("error", function () {
        if (audio === a) stop("Audiowiedergabe nicht möglich");
      });
      a.addEventListener("ended", function () {
        if (audio === a) stop("Wiedergabe beendet · bei Bedarf neu starten");
      });
      a.addEventListener("waiting", function () {
        if (audio === a) publish("Wiedergabe wartet …");
      });
      a.addEventListener("playing", function () {
        if (audio === a) publish("Aktiv · Dauerbetrieb ohne Zeitlimit");
      });
      await a.play();
      if (audio === a && !a.paused) publish("Aktiv · Dauerbetrieb ohne Zeitlimit");
    } catch (e) {
      if (audio === a) stop("Wiedergabe blockiert oder nicht möglich");
    }
  }

  // SPA navigation does not unload the document. A real page/app reload does.
  window.addEventListener("pagehide", function () { stop("Seite beendet · neu starten"); });

  class TafaBtKeepalive extends HTMLElement {
    constructor() {
      super();
      this.updateStatus = this.updateStatus.bind(this);
    }
    setConfig(config) {
      this.config = config;
      if (!this.shadowRoot) this.attachShadow({mode: "open"});
      this.render();
    }
    set hass(h) { const l=language(h); this._hass=h; if(this.shadowRoot && l!==this._lang)this.render(); }
    getCardSize() { return 3; }
    connectedCallback() {
      listeners.add(this.updateStatus);
      this.updateStatus();
    }
    disconnectedCallback() {
      // Retain the audio session across views, release this card's listener.
      listeners.delete(this.updateStatus);
    }
    render() {
      this._lang=language(this._hass);
      this.shadowRoot.innerHTML = localize('<ha-card><style>.body{padding:16px;display:grid;gap:12px}h3{margin:0;font-size:16px}p{margin:0;color:var(--secondary-text-color);font-size:13px}button{font:inherit;padding:9px 12px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);color:var(--primary-text-color)}button:disabled{opacity:.5}.row{display:flex;flex-wrap:wrap;gap:8px}</style><div class="body"><h3>Bluetooth · Audio-Keepalive</h3><p>Nur auf diesem Gerät. Lautloser Dauerbetrieb, auch beim Dashboard-Wechsel innerhalb derselben Seite. Kein Mikrofonzugriff.</p><div class="row"><button id="start">Dauerbetrieb starten</button><button id="stop">Stoppen</button></div><p id="status" role="status" aria-live="polite"></p><p>Endet beim Schließen oder Neuladen der Seite, beim manuellen Stoppen oder wenn Android die Wiedergabe beendet. Bluetooth-Wirkung nicht messbar.</p></div></ha-card>',this._hass);
      this.shadowRoot.querySelector("#start").onclick = start;
      this.shadowRoot.querySelector("#stop").onclick = function () { stop("Manuell beendet"); };
      this.updateStatus();
    }
    updateStatus() {
      if (!this.shadowRoot) return;
      const s = this.shadowRoot.querySelector("#start"), t = this.shadowRoot.querySelector("#stop"), m = this.shadowRoot.querySelector("#status");
      if (s) s.disabled = Boolean(audio);
      if (t) t.disabled = !audio;
      if (m) m.textContent = tr(message,this._hass);
    }
  }
  customElements.define("tablet-assist-bt-keepalive", TafaBtKeepalive);
  window.customCards = window.customCards || [];
  if (!window.customCards.some(function (c) { return c.type === "tablet-assist-bt-keepalive"; })) {
    window.customCards.push({type: "tablet-assist-bt-keepalive", name: "TAFA Bluetooth Keepalive", description: tr("Manuell gesteuerter Silent-Audio-Dauerbetrieb")});
  }
})();
