/* Accessible, progressive-enhancement tabs. Never removes or resets form fields. */
(() => {
  "use strict";
  const ids = ["overview", "connections", "setup", "devices", "maintenance"];
  const tabs = ids.map(id => document.getElementById("tab-" + id));
  const panels = ids.map(id => document.getElementById(id));
  if (tabs.some(tab => !tab) || panels.some(panel => !panel)) return;

  function select(id, shouldFocus = false) {
    const index = ids.indexOf(id);
    if (index === -1) return false;
    ids.forEach((key, i) => {
      const selected = key === id;
      tabs[i].setAttribute("aria-selected", String(selected));
      tabs[i].tabIndex = selected ? 0 : -1;
      panels[i].hidden = !selected;
    });
    if (shouldFocus) tabs[index].focus();
    for (const link of document.querySelectorAll("[data-language-link]")) {
      const original = link.getAttribute("href").split("#")[0];
      link.setAttribute("href", original + "#" + id);
    }
    return true;
  }
  function activeFromHash() {
    const hash = window.location.hash.replace(/^#/, "");
    return ids.includes(hash) ? hash : document.body.dataset.defaultTab || "overview";
  }
  select(activeFromHash());

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", event => {
      event.preventDefault();
      const id = ids[index];
      select(id);
      window.history.replaceState(null, "", "#" + id);
    });
    tab.addEventListener("keydown", event => {
      const {key} = event;
      let next = -1;
      if (key === "ArrowRight") next = (index + 1) % ids.length;
      if (key === "ArrowLeft") next = (index - 1 + ids.length) % ids.length;
      if (key === "Home") next = 0;
      if (key === "End") next = ids.length - 1;
      if (next < 0) return;
      event.preventDefault();
      select(ids[next], true);
      window.history.replaceState(null, "", "#" + ids[next]);
    });
  });
  window.addEventListener("hashchange", () => select(activeFromHash()));
  // Only JSON file selection, no raw JSON textarea or duplicate editor.
  const manifestFile = document.getElementById("manifest-file");
  const manifestText = document.getElementById("manifest-json");
  const manifestStatus = document.getElementById("manifest-file-status");
  const manifestButton = document.getElementById("manifest-check");
  const en = document.documentElement.lang === "en";
  if (manifestFile && manifestText && manifestButton && manifestStatus) {
    manifestButton.disabled = true;
    manifestFile.addEventListener("change", async () => {
      manifestText.value = "";
      manifestButton.disabled = true;
      const file = manifestFile.files?.[0];
      if (!file) {
        manifestStatus.textContent = en ? "No file selected" : "Keine Datei ausgewählt";
        return;
      }
      if (file.size > 10000 || !/\.json$/i.test(file.name)) {
        manifestStatus.textContent = en ?
          "Select a JSON file of at most 10 KB" : "JSON-Datei mit maximal 10 KB auswählen";
        return;
      }
      try {
        const source = await file.text();
        const decoded = JSON.parse(source);
        if (!decoded || typeof decoded !== "object" || Array.isArray(decoded)) {
          throw new Error("Invalid JSON object");
        }
        if (manifestFile.files?.[0] !== file) return;
        manifestText.value = source;
        manifestButton.disabled = false;
        manifestStatus.textContent = file.name + " · " +
          (en ? "Ready to check" : "Bereit zur Prüfung");
      } catch (_) {
        manifestStatus.textContent = en ?
          "The file is not valid JSON" : "Die Datei enthält kein gültiges JSON";
      }
    });
  }

  // Debounced checks of edited values. The backend validates destination
  // addresses before connecting, returns only fixed statuses, and never
  // returns credentials or reflects the typed URL.
  const connectionForm = document.getElementById("tafa-connections");
  if (connectionForm) {
    const csrf = connectionForm.querySelector('[name="csrf"]')?.value || "";
    const states = {
      missing: [ "Nicht eingerichtet", "Not configured" ],
      invalid: [ "Ungültige Adresse", "Invalid address" ],
      checking: [ "Wird geprüft…", "Checking…" ],
      offline: [ "Nicht erreichbar", "Unreachable" ],
      ready: [ "Dienst bereit", "Service ready" ],
      reachable: [ "Erreichbar – Funktion nicht vollständig geprüft", "Reachable – full service not tested" ],
      not_ready: [ "Erreichbar, Dienst noch nicht bereit", "Reachable, service not ready" ],
      tls_ok: [ "DNS und HTTPS-Zertifikat gültig – Amazon-Abruf ungeprüft", "DNS and HTTPS certificate valid – Amazon fetch not tested" ],
      tls_failed: [ "HTTPS-Zertifikat ungültig", "Invalid HTTPS certificate" ],
      error: [ "Prüfung nicht möglich", "Could not check" ]
    };
    const fields = connectionForm.querySelectorAll("[data-connection-probe]");
    fields.forEach((input, index) => {
      const field = input.getAttribute("data-connection-probe");
      const result = connectionForm.querySelector('[data-probe-result="' + field + '"]');
      if (!result) return;
      let timer, generation = 0, controller;
      const mark = state => {
        result.dataset.state = state;
        result.textContent = (states[state] || states.error)[en ? 1 : 0];
      };
      const check = async () => {
        const seq = ++generation;
        if (controller) controller.abort();
        controller = new AbortController();
        if (!input.value.trim()) { mark("missing"); return; }
        mark("checking");
        try {
          const params = new URLSearchParams({
            csrf, action: "connection_probe", field, value: input.value,
            lang: en ? "en" : "de", tab: "connections"
          });
          const response = await fetch("./", {
            method: "POST", credentials: "same-origin",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: params.toString(), cache: "no-store",
            signal: controller.signal
          });
          if (!response.ok) throw new Error("Probe not available");
          const data = await response.json();
          if (seq === generation) mark(data.status in states ? data.status : "error");
        } catch (error) {
          if (seq === generation && error.name !== "AbortError") mark("error");
        }
      };
      input.addEventListener("input", () => {
        clearTimeout(timer);
        ++generation;
        if (controller) controller.abort();
        mark(input.value.trim() ? "checking" : "missing");
        timer = setTimeout(check, 550);
      });
      // Re-check saved values when this Control Center loads.
      if (input.value.trim()) setTimeout(check, 130 * index);
      else mark("missing");
    });
  }
})();
