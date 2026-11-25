/* Accessible, progressive-enhancement tabs. Never removes or resets form fields. */
(() => {
  "use strict";
  const ids = ["overview", "setup", "connections", "maintenance"];
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
  const manifestFile = document.getElementById("manifest-file");
  const manifestText = document.getElementById("manifest-json");
  if (manifestFile && manifestText) {
    manifestFile.addEventListener("change", async () => {
      const file=manifestFile.files?.[0];
      if (!file) return;
      if (file.size>10000) {
        manifestText.setCustomValidity("JSON file too large (max. 10 KB)");
        manifestText.reportValidity();
        return;
      }
      try {
        manifestText.value=await file.text();
        manifestText.setCustomValidity("");
        select("setup");
      } catch (_) {
        manifestText.setCustomValidity("Could not read the JSON file");
        manifestText.reportValidity();
      }
    });
  }
})();