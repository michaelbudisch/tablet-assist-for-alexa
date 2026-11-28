/* TAFA local GPU voice inventory and sample playback. No remote browser requests. */
(() => {
  "use strict";
  const root = document.getElementById("tafa-voice-manager");
  const disclosure = document.getElementById("tafa-voice-details");
  const picker = document.querySelector('#tafa-settings select[name="voice_variant"]');
  if (!root || !disclosure || !picker) return;

  const csrf = root.dataset.csrf || "";
  const en = root.dataset.lang === "en";
  const list = document.getElementById("tafa-voice-list");
  const status = document.getElementById("tafa-voice-state");
  const defaultButton = document.getElementById("tafa-voice-default-preview");
  const player = document.getElementById("tafa-voice-audio");
  const word = (de, english) => en ? english : de;
  let info = null, polling = null, busy = false, objectUrl = null;

  function say(value) { status.textContent = value; }
  function clearPoll() { if (polling) clearTimeout(polling); polling = null; }
  function schedule() {
    clearPoll();
    if (disclosure.open && info && info.job.state === "preparing")
      polling = setTimeout(refresh, 4000);
  }
  async function request(path, form) {
    const options = { credentials: "same-origin", cache: "no-store" };
    if (form) {
      options.method = "POST";
      options.headers = {"Content-Type": "application/x-www-form-urlencoded"};
      options.body = new URLSearchParams({csrf, variant: form.variant}).toString();
    }
    const response = await fetch(path, options);
    if (!response.ok) {
      let error;
      try { error = (await response.json()).error; } catch (_) { /* no details */ }
      throw new Error(error || word("GPU-Worker nicht erreichbar", "GPU worker unavailable"));
    }
    return response;
  }
  function errorText(error) {
    const message = String(error && error.message || "");
    if (message.includes("update required"))
      return word("Bitte den GPU-Worker auf Version 2.2.8 aktualisieren.",
                  "Update the GPU worker to version 2.2.8.");
    if (message.includes("not reachable"))
      return word("GPU-Worker nicht erreichbar.", "GPU worker unreachable.");
    if (message.includes("Fixed voice mode") || message.includes("fixed mode required"))
      return word("Stimmenvarianten benötigen STREAM_VOICE_MODE=fixed im GPU-Worker.",
                  "Voice variants require STREAM_VOICE_MODE=fixed on the GPU worker.");
    if (message.includes("busy"))
      return word("GPU-Worker ist beschäftigt. Erneut versuchen.", "GPU worker busy. Try again.");
    if (message.includes("Prepare this voice"))
      return word("Diese Stimme muss zuerst erstellt werden.", "Prepare this voice first.");
    return word("Stimmenverwaltung derzeit nicht verfügbar.", "Voice management unavailable.");
  }
  function updatePicker() {
    for (const option of picker.options) {
      if (!option.dataset.baseLabel) option.dataset.baseLabel = option.textContent;
      option.textContent = option.dataset.baseLabel;
      if (!info || option.value === "default" || !info.available) continue;
      const entry = info.variants.find(item => item.id === option.value);
      if (entry) option.textContent = entry.name_de && !en ? entry.name_de + " (" + entry.id + ")" :
        (en ? entry.name_en : entry.name_de) + " (" + entry.id + ")" +
        (entry.ready ? "" : word(" – fehlt", " – missing"));
    }
  }
  function render() {
    if (!info) return;
    const waiting = busy || info.busy || info.job.state === "preparing";
    defaultButton.disabled = busy || info.busy;
    updatePicker();
    list.replaceChildren();
    if (!info.available) {
      say(info.mode === "fixed" ?
        word("Qwen-Stimmen konnten nicht ausgelesen werden.", "Could not read Qwen voices.") :
        word("Varianten sind nur im GPU-Worker-Modus „fixed“ verfügbar. STREAM_VOICE_MODE=fixed setzen und den GPU-Worker neu starten.",
             "Variants require GPU worker mode fixed. Set STREAM_VOICE_MODE=fixed and restart the GPU worker."));
      return;
    }
    if (info.job.state === "preparing") {
      say(word("Stimme " + info.job.variant + " wird lokal erzeugt. Qwen-TTS ist währenddessen beschäftigt.",
               "Voice " + info.job.variant + " is being prepared locally. Qwen TTS is busy."));
    } else if (info.job.state === "error") {
      say(word("Stimme " + info.job.variant + " konnte nicht erzeugt werden. Bitte GPU-Speicher und Worker-Protokoll prüfen.",
               "Voice " + info.job.variant + " could not be prepared. Check GPU memory and worker logs."));
    } else {
      const entry = info.variants.find(item => item.id === picker.value);
      say(picker.value === "default" ?
        word("Standardstimme ausgewählt.", "Default voice selected.") :
        entry?.ready ? word("Stimme " + picker.value + " ist vorbereitet.", "Voice " + picker.value + " is ready.") :
        word("Stimme " + picker.value + " fehlt – derzeit wird die Standardstimme verwendet.",
             "Voice " + picker.value + " missing – the default voice is used."));
    }
    for (const voice of info.variants) {
      const line = document.createElement("div");
      line.className = "tafa-voice-row";
      const title = document.createElement("strong");
      title.textContent = voice.id + " · " + (en ? voice.name_en : voice.name_de);
      const state = document.createElement("span");
      state.className = "tafa-voice-pill";
      state.dataset.ready = voice.ready ? "yes" : "no";
      state.textContent = voice.ready ? word("Bereit", "Ready") : word("Fehlt", "Missing");
      const create = document.createElement("button");
      create.type = "button";
      create.className = "btn btn-outline";
      create.textContent = word("Erstellen", "Prepare");
      create.disabled = waiting || voice.ready;
      create.addEventListener("click", () => prepare(voice.id));
      const play = document.createElement("button");
      play.type = "button";
      play.className = "btn btn-outline";
      play.textContent = word("Hörprobe", "Preview");
      play.disabled = waiting || !voice.ready;
      play.addEventListener("click", () => preview(voice.id));
      line.append(title, state, create, play);
      list.append(line);
    }
  }
  async function refresh() {
    if (busy || !disclosure.open) return;
    try {
      info = await (await request("./api/voices")).json();
      render();
      schedule();
    } catch (error) {
      info = null;
      list.replaceChildren();
      say(errorText(error));
      clearPoll();
    }
  }
  async function prepare(number) {
    if (busy) return;
    busy = true;
    say(word("Erstellung wird gestartet…", "Starting voice preparation…"));
    render();
    try {
      await request("./api/voices/prepare", {variant: number});
      await refreshAfterAction();
    } catch (error) {
      say(errorText(error));
    } finally {busy = false; render(); schedule();}
  }
  async function refreshAfterAction() {
    info = await (await request("./api/voices")).json();
    render();
  }
  async function preview(number) {
    if (busy) return;
    busy = true;
    say(word("Hörprobe wird erzeugt…", "Generating preview…"));
    render();
    try {
      const result = await request("./api/voices/preview", {variant: number});
      const blob = await result.blob();
      if (blob.type !== "audio/wav" || blob.size > 2 * 1024 * 1024) throw new Error("Invalid WAV");
      player.pause();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = URL.createObjectURL(blob);
      player.src = objectUrl;
      player.hidden = false;
      say(word("Hörprobe bereit.", "Preview ready."));
      try {await player.play();} catch (_) { /* Audio controls remain usable. */ }
    } catch (error) {
      say(errorText(error));
    } finally {busy = false; render();}
  }

  defaultButton.addEventListener("click", () => preview("default"));
  picker.addEventListener("change", () => { if (info) render(); });
  disclosure.addEventListener("toggle", () => {
    if (disclosure.open) refresh();
    else clearPoll();
  });
  if (disclosure.open) refresh();
  window.addEventListener("pagehide", () => {
    clearPoll();
    if (objectUrl) URL.revokeObjectURL(objectUrl);
  });
})();
