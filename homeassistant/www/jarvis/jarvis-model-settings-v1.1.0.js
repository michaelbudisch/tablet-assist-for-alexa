/* Server-backed, administrator-only Jarvis model settings. No credentials in the browser. */
const text = (v, de, en) => String(v.h?.language || navigator.language || "en").startsWith("de") ? de : en;
const el = (tag, label) => {const n = document.createElement(tag);if (label != null) n.textContent = label;return n;};
const names = {"qwen3:4b-instruct":"Qwen3 4B Instruct", "qwen3-vl:4b-instruct":"Qwen3-VL 4B Instruct",
  "qwen3-vl:2b-instruct":"Qwen3-VL 2B Instruct", "qwen3-vl:8b-instruct":"Qwen3-VL 8B Instruct", "gemma3:4b":"Gemma 3 4B"};

let serial = 0;
export function mountModelSettings(voice, root) {
  if (!root?.isConnected || root.querySelector("[data-jv-model-settings]")) return;
  const block = el("details");block.dataset.jvModelSettings = "1";
  block.style.cssText = "border-top:1px solid var(--divider-color);padding-top:12px";
  block.append(el("summary", text(voice,"KI-Modelle und Leistung","AI models and performance")));
  const body = el("div");body.style.cssText = "display:grid;gap:12px;margin:12px 0;font-size:13px";
  const status = el("p", text(voice,"Einstellungen werden beim Öffnen geladen.","Open to load settings."));
  status.dataset.jvModelStatus="1";status.setAttribute("role","status");status.style.whiteSpace = "pre-line";
  body.append(status);block.append(body);root.append(block);
  let current, loading = false, saving = false;
  const fields = {};
  const prefix="jv-model-"+(++serial);
  const rpc = data => voice.h.callWS({type:"call_service",domain:"jarvis_tablet_audio",service:"model_settings",service_data:data,return_response:true});
  const unwrap = result => result?.response ?? result?.service_response ?? result;
  const active = () => root.isConnected && block.isConnected;
  const busy = () => !!(voice.session || voice.processing || voice.playing);
  const controls = [];
  function setDisabled(value) {for (const c of [...controls,...body.querySelectorAll("input")]) c.disabled = value;}
  function choice(key, title) {
    const group=el("fieldset");group.append(el("legend",title));
    const row=el("div");row.className="jvs-options";group.append(row);body.append(group);
    fields[key]={row,key,value:""};
  }
  choice("text_model",text(voice,"Textmodell","Text model"));
  choice("vision_model",text(voice,"Bildmodell","Vision model"));
  choice("keep_alive",text(voice,"Modelle warm halten","Keep models loaded"));
  choice("num_ctx",text(voice,"Kontextgröße","Context size"));
  const hint = el("p",text(voice,"Gleiches Text- und Bildmodell vermeidet Modellwechsel. Mehr Kontext benötigt mehr GPU-Speicher. Änderungen gelten für alle Jarvis-Geräte; Kamera-Anzeigen rufen weiterhin keine KI auf.","Using the same text and vision model avoids model switches. More context needs more GPU memory. Settings apply to all Jarvis devices; camera views still bypass AI."));
  hint.style.cssText = "font-size:12px;opacity:.8;margin:0";body.append(hint);
  const row = el("div");row.style.cssText = "display:flex;gap:8px;flex-wrap:wrap";
  function button(label, fn) {
    const b=el("button",label);b.type="button";b.style.cssText="font:inherit;padding:9px 12px;color:inherit;background:var(--secondary-background-color);border:1px solid var(--divider-color);border-radius:9px;cursor:pointer";
    b.onclick=e=>{e.stopPropagation();void fn();};row.append(b);controls.push(b);return b;
  }
  function options(field, values, selected, display = value => String(value)) {
    field.row.replaceChildren();field.value=String(selected);
    for(const value of values){
      const label=el("label");label.className="jvs-option";
      const radio=el("input");radio.type="radio";radio.name=prefix+"-"+field.key;radio.value=String(value);radio.checked=radio.value===field.value;
      radio.onchange=()=>{if(radio.checked)field.value=radio.value;};
      label.append(radio,el("span",display(value)));field.row.append(label);
    }
  }
  function render() {
    options(fields.text_model,current.text_models,current.text_model,m=>names[m]||m);
    options(fields.vision_model,current.vision_models,current.vision_model,m=>names[m]||m);
    options(fields.keep_alive,[0,60,120,300,600],current.keep_alive,n=>n===0?text(voice,"Sofort entladen","Unload immediately"):n/60+" min");
    options(fields.num_ctx,[2048,4096,8192],current.num_ctx,n=>n.toLocaleString()+" tokens");
    const models=(current.loaded||[]).map(m=>(names[m.name]||m.name)+(Number.isFinite(m.size_vram)?" · "+(m.size_vram/1073741824).toFixed(2)+" GiB GPU":""));
    status.textContent = (current.shared?text(voice,"Gemeinsames Text-/Bildmodell.","Shared text/vision model."):text(voice,"Getrennte Text- und Bildmodelle.","Separate text and vision models.")) + "\n" +
      (models.length?text(voice,"Geladen: ","Loaded: ")+models.join(", "):text(voice,"Derzeit kein Ollama-Modell geladen.","No Ollama model currently loaded."));
    if(current.keep_alive!==current.vision_keep_alive || current.num_ctx!==current.vision_num_ctx)status.textContent+="\n"+text(voice,"Text und Bilder verwenden noch unterschiedliche Speicherwerte. Speichern gleicht sie an.","Text and vision currently use different memory settings. Saving aligns them.");
  }
  async function load() {
    if(loading||saving||!active())return;
    loading=true;setDisabled(true);status.textContent=text(voice,"Lade Modellstatus …","Loading model status …");
    try {const value=unwrap(await rpc({action:"get"}));if(!active())return;
      if(!value?.revision||!Array.isArray(value.text_models)||!Array.isArray(value.vision_models))throw Error("Invalid model settings reply");
      current=value;render();
    } catch {if(active())status.textContent=text(voice,"Einstellungen nicht verfügbar. Als HA-Administrator anmelden und GPU Worker ab 1.8.0 starten.","Settings unavailable. Sign in as a HA administrator and start GPU Worker 1.8.0 or newer.");}
    finally {loading=false;if(active()){setDisabled(false);for(const c of body.querySelectorAll("input"))c.disabled=!current;save.disabled=!current;}}
  }
  const save=button(text(voice,"Für Jarvis speichern","Save for Jarvis"),async()=>{
    if(!current||loading||saving||!active())return;
    if(busy()){status.textContent=text(voice,"Warte, bis Jarvis nicht mehr verarbeitet oder spricht.","Wait until Jarvis finishes processing or speaking.");return;}
    saving=true;setDisabled(true);status.textContent=text(voice,"Speichere Modelleinstellungen …","Saving model settings …");
    try {
      const value=unwrap(await rpc({action:"set",revision:current.revision,text_model:fields.text_model.value,
        vision_model:fields.vision_model.value,keep_alive:Number(fields.keep_alive.value),num_ctx:Number(fields.num_ctx.value)}));
      if(!active())return;if(!value?.saved)throw Error("Not saved");current=value;render();
      status.textContent=text(voice,"Gespeichert. Gilt ab der nächsten Anfrage.","Saved. Applies to the next request.")+"\n"+status.textContent;
    } catch {if(active())status.textContent=text(voice,"Nicht gespeichert. Status aktualisieren und erneut versuchen; möglicherweise wurden Einstellungen geändert oder ein Modell ist nicht installiert.","Not saved. Refresh and retry; settings may have changed or a model may be missing.");}
    finally {saving=false;if(active())setDisabled(false);}
  });
  button(text(voice,"Status aktualisieren","Refresh status"),load);body.append(row);
  save.disabled=true;
  block.addEventListener("toggle",()=>{if(block.open&&!current)void load();});
}
