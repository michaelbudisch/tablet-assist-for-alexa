import "/tablet_assist_for_alexa/keepalive.js?v=0.3.1";
const SOURCE_LABELS={"weather":["Weather entity","Wetter-Entität"],"shopping":["Shopping list (Bring! or other to-do list)","Einkaufsliste (Bring! oder andere To-do-Liste)"],"restmuell":["Residual waste dates","Restmüll-Abholtermine"],"bioabfall":["Organic waste dates","Biomüll-Abholtermine"],"papier":["Paper collection dates","Papier-Abholtermine"],"wertstoff":["Recycling collection dates","Wertstoff-Abholtermine"],"vorlauf":["Heating flow temperature (°C)","Vorlauftemperatur (°C)"],"ruecklauf":["Heating return temperature (°C)","Rücklauftemperatur (°C)"],"spreizung":["Temperature difference (K)","Heizungsspreizung (K)"],"preis":["Current electricity price","Aktueller Strompreis"],"guenstig":["Lowest electricity price tomorrow","Niedrigster Strompreis morgen"],"netz":["Signed grid power (+ import, − export)","Netzleistung (+ Bezug, − Einspeisung)"],"solar":["Total PV power","Gesamte PV-Leistung"],"prognose":["Forecast PV yield tomorrow","PV-Ertragsprognose morgen"],"solarheute":["PV yield today","PV-Ertrag heute"],"netzheute":["Grid import today","Netzbezug heute"],"einspeisungheute":["Grid export today","Einspeisung heute"],"heizoel":["Heating oil stock","Heizölbestand"],"oelverbrauch":["Estimated oil use today","Geschätzter Heizölverbrauch heute"],"waschmaschine":["Washing machine power","Waschmaschinenleistung"],"waschkosten":["Washing machine cost today","Waschmaschinenkosten heute"],"waschenergie":["Washing machine energy today","Waschmaschinenverbrauch heute"],"waermepumpe":["Heat pump power","Wärmepumpenleistung"],"wpheute":["Heat pump energy today","Wärmepumpenverbrauch heute"],"wpkosten":["Heat pump cost today","Wärmepumpenkosten heute"],"kuehlschrank":["Refrigerator power","Kühlschrankleistung"],"kuehlschrankheute":["Refrigerator energy today","Kühlschrankverbrauch heute"],"reminders_enabled":["Enable shared reminders","Gemeinsame Erinnerungen aktivieren"],"reminder_room":["Optional Echo room for reminders","Optionaler Echo-Raum für Erinnerungen"]};
const INTENT_LABELS={...SOURCE_LABELS,...{"aktuell":["Current weather","Aktuelles Wetter"],"temperatur":["Outside temperature","Außentemperatur"],"feuchte":["Humidity","Luftfeuchtigkeit"],"wind":["Wind speed","Windgeschwindigkeit"],"druck":["Air pressure","Luftdruck"],"gefuehlt":["Feels like","Gefühlte Temperatur"],"regenjetzt":["Rain now","Regen aktuell"],"regenwahrscheinlichkeit":["Rain probability (if available)","Regenwahrscheinlichkeit"],"heute":["Weather today","Wetter heute"],"morgen":["Weather tomorrow","Wetter morgen"],"uebermorgen":["Weather day after tomorrow","Wetter übermorgen"],"kommendetage":["Weather next days","Wetter nächste Tage"],"frost":["Frost tomorrow","Frost morgen"],"regenuebermorgen":["Rain day after tomorrow","Regen übermorgen"],"regenheute":["Rain today","Regen heute"],"regenmorgen":["Rain tomorrow","Regen morgen"],"regennachher":["Rain next 6 hours","Regen nächste 6 Stunden"],"regenzwei":["Rain next 2 hours","Regen nächste 2 Stunden"],"regenabend":["Rain this evening","Regen heute Abend"],"regennacht":["Rain tonight","Regen heute Nacht"],"regenmorgenfrueh":["Rain tomorrow morning","Regen morgen früh"],"schnee":["Snow next 24 hours","Schnee nächste 24 Stunden"],"schneeheute":["Snow today","Schnee heute"],"schneemorgen":["Snow tomorrow","Schnee morgen"],"abend":["Weather this evening","Wetter heute Abend"],"nacht":["Weather tonight","Wetter heute Nacht"],"morgenfrueh":["Weather tomorrow morning","Wetter morgen früh"],"stunden":["Weather next hours","Wetter nächste Stunden"],"bring_list":["Read shopping list","Einkaufsliste vorlesen"]}};
const ROOM_EN={"Büro":"Office","Wohnzimmer":"Living room","Badezimmer":"Bathroom","Schlafzimmer":"Bedroom","Kinderzimmer":"Children's room"};
const words={
 de:{title:"TAFA Sprachzentrale",sub:"Lokaler Assistent · Tablet & Echo",assist:"Assist starten",assistHint:"Nutzt den nativen Home-Assistant-Assistenten. Wähle dort deine Tablet-Assist-Pipeline. Im Browser kann dabei das Standard-Dashboard geöffnet werden.",status:"Sprachdienste",settings:"Integration konfigurieren",pipelines:"Sprachassistenten",ann:"Alexa-Durchsage",message:"Nicht vertrauliche Nachricht eingeben",send:"Durchsage senden",none:"Keine Räume konfiguriert. Optionale Alexa-Durchsagen in der Integration einrichten.",sending:"Wird erstellt …",sent:"An Notify übergeben. Wiedergabe am Echo prüfen.",error:"Durchsage fehlgeschlagen. Prüfe Konfiguration und Ruhezeiten.",select:"Nachricht und mindestens einen Raum wählen.",empty:"Noch keine Statusdaten",sidebar:"Menü öffnen",dataSources:"Datenquellen",overview:"Übersicht",devices:"Geräte",deviceHint:"Registrierte Tablets verwalten",deviceOffline:"Geräteliste nicht erreichbar",deviceEmpty:"Noch kein Tablet registriert.",deviceMute:"Stumm",deviceUnmute:"Freigeben",deviceRename:"Raumname speichern",deviceWord:"Rufwort",deviceRefresh:"Aktualisieren",learning:"Lernen",learnHelp:"Optional in den Integrationsoptionen aktivieren. Nur allgemeine, nicht erkannte Hausdaten-Fragen aus einer begrenzten Wortliste werden vorgeschlagen. Freigaben führen ausschließlich lesende Abfragen aus.",learnOff:"Lernfunktion ist ausgeschaltet.",suggestions:"Vorschläge",aliases:"Freigegebene Formulierungen",refresh:"Aktualisieren",approve:"Freigeben",dismiss:"Verwerfen",remove:"Löschen",clear:"Alle Lernzuordnungen löschen",emptyLearn:"Keine Einträge vorhanden.",pick:"Absicht auswählen",newPhrase:"Allgemeine Formulierung (ohne persönliche Daten)",learnError:"Die Lernfunktion konnte nicht aktualisiert werden. Prüfe die Auswahl und deine Berechtigungen.",clearConfirm:"Alle Lernvorschläge und freigegebenen Formulierungen löschen?",configured:"Konfiguriert",disabled:"Nicht eingerichtet",configureSources:"Datenquellen konfigurieren",sourceHelp:"Öffne die Integration und wähle Optionen. Dort kannst du Entitäten auswählen oder entfernen. Nur konfigurierte Quellen sind verfügbar."},
 en:{title:"TAFA Voice center",sub:"Local assistant · Tablet & Echo",assist:"Start Assist",assistHint:"Uses native Home Assistant Assist. Select your Tablet Assist pipeline there. In a browser, the default dashboard may open.",status:"Voice services",settings:"Configure integration",pipelines:"Voice assistants",ann:"Alexa announcement",message:"Enter a non-confidential message",send:"Send announcement",none:"No rooms configured. Set up optional Alexa announcements in the integration.",sending:"Generating …",sent:"Handed to Notify. Check playback on Echo.",error:"Announcement failed. Check configuration and quiet times.",select:"Enter a message and select at least one room.",empty:"No status data yet",sidebar:"Open menu",dataSources:"Data sources",overview:"Overview",devices:"Devices",deviceHint:"Manage registered tablets",deviceOffline:"Device list unavailable",deviceEmpty:"No registered tablets.",deviceMute:"Mute",deviceUnmute:"Unmute",deviceRename:"Save room name",deviceWord:"Wake word",deviceRefresh:"Refresh",learning:"Learning",learnHelp:"Optional in integration Options. Suggestions are restricted to unmatched generic home-data questions from a vocabulary allowlist. Approved aliases only perform read-only queries.",learnOff:"Learning is disabled.",suggestions:"Suggestions",aliases:"Approved phrases",refresh:"Refresh",approve:"Approve",dismiss:"Dismiss",remove:"Delete",clear:"Clear learning data",emptyLearn:"No entries.",pick:"Select intent",newPhrase:"Generic phrase (no personal details)",learnError:"Could not update learning. Check the choice and permissions.",clearConfirm:"Delete all suggestions and approved phrases?",configured:"Configured",disabled:"Not configured",configureSources:"Configure data sources",sourceHelp:"Open the integration and choose Options. Select or remove entities there. Only configured sources are available."}
};
class TabletAssistPanel extends HTMLElement {
 constructor(){super();this.attachShadow({mode:"open"});this._rooms=[];this._lang="";this._selected=new Set();this._view="overview";this._deviceBusy=false;}
 set panel(p){const changed=JSON.stringify(p?.config||{})!==JSON.stringify(this._panel?.config||{});this._panel=p;const rooms=(p?.config?.rooms||[]).filter(x=>Object.hasOwn(ROOM_EN,x));if(JSON.stringify(rooms)!==JSON.stringify(this._rooms)){this._rooms=rooms;this._selected=new Set();this.render();}else if(changed&&this.shadowRoot.querySelector("main"))this.render();}
 set hass(h){this._hass=h;const l=(h.locale?.language||h.language||"en").startsWith("de")?"de":"en";if(l!==this._lang){this._lang=l;this.render();}this.update();}
 set narrow(v){this._narrow=v;}
 connectedCallback(){if(!this.shadowRoot.querySelector("main"))this.render();}
 get t(){return words[this._lang]||words.en;}
 render(){
 const previous=this.shadowRoot.querySelector("textarea")?.value||"";
 const t=this.t;
 this.shadowRoot.innerHTML=`<style>:host{display:block;color:var(--primary-text-color);background:var(--primary-background-color);min-height:100%;font:inherit}*{box-sizing:border-box}header{display:flex;align-items:center;gap:12px;position:sticky;top:0;background:var(--app-header-background-color,var(--card-background-color));color:var(--app-header-text-color,var(--primary-text-color));padding:12px 20px;z-index:1}header strong{font-size:20px}header{flex-wrap:wrap}.learnrow{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 0;border-bottom:1px solid var(--divider-color)}.learnrow span{flex:1;min-width:140px;overflow-wrap:anywhere}select,input{font:inherit;color:var(--primary-text-color);background:var(--card-background-color);border:1px solid var(--divider-color);border-radius:8px;padding:8px;max-width:100%}[hidden]{display:none!important}main{max-width:1000px;margin:auto;padding:20px;display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr))}section{background:var(--ha-card-background,var(--card-background-color));border:1px solid var(--divider-color);border-radius:16px;padding:20px;display:grid;gap:12px;align-content:start}.hero{grid-column:1/-1}h1,h2,p{margin:0}h1{font-size:27px}h2{font-size:18px}p{color:var(--secondary-text-color);line-height:1.5}button,a{font:inherit;color:var(--primary-text-color);cursor:pointer}button{border:1px solid var(--divider-color);border-radius:10px;padding:10px 14px;background:var(--card-background-color)}button.primary{background:var(--primary-color);color:var(--text-primary-color,#fff);border:none}button:disabled{opacity:.5;cursor:default}header button{background:transparent;color:inherit;border:none;padding:6px}textarea{font:inherit;background:var(--primary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);border-radius:10px;resize:vertical;width:100%;padding:10px}label{display:flex;gap:8px;align-items:center}#rooms{display:flex;flex-wrap:wrap;gap:12px}#stats{display:grid;gap:6px}.stat{padding:8px 0;border-bottom:1px solid var(--divider-color);overflow-wrap:anywhere}nav{display:flex;flex-wrap:wrap;gap:16px}nav[hidden]{display:none}tablet-assist-bt-keepalive{display:block}</style><header><button id="menu" aria-label="${t.sidebar}">☰</button><strong>TAFA</strong><button id="overview">${t.overview}</button><button id="sources">${t.dataSources}</button><button id="devices">${t.devices}</button><button id="learn" hidden>${t.learning}</button></header><main><section id="sourcesPage" class="hero" hidden><h1>${t.dataSources}</h1><p>${t.sourceHelp}</p><a id="sourceLink" href="/config/integrations/integration/tablet_assist_for_alexa">${t.configureSources}</a><div id="sourceRows"></div></section><section id="devicesPage" class="hero" hidden><h1>${t.devices}</h1><p>${t.deviceHint}</p><button id="refreshDevices">${t.deviceRefresh}</button><p role="status" id="deviceStatus"></p><div id="deviceRows"></div></section><section id="learningPage" class="hero" hidden><h1>${t.learning}</h1><p>${t.learnHelp}</p><p id="learnStatus" role="status"></p><div class="learnrow"><button id="refreshLearn">${t.refresh}</button><button id="clearLearn">${t.clear}</button></div><h2>${t.suggestions}</h2><div id="suggestionRows"></div><div id="manualLearn" class="learnrow"></div><h2>${t.aliases}</h2><div id="aliasRows"></div></section><section class="hero"><h1>${t.title}</h1><p>${t.sub}</p><button class="primary" id="assist">🎙 ${t.assist}</button><p>${t.assistHint}</p><nav><a href="/config/integrations">${t.settings}</a><a href="/config/voice-assistants">${t.pipelines}</a></nav></section><section><h2>${t.status}</h2><div id="stats"></div></section><section><h2>${t.ann}</h2><p id="noRooms"></p><textarea rows="3" maxlength="500" placeholder="${t.message}"></textarea><div id="rooms"></div><button class="primary" id="send">${t.send}</button><p role="status" id="result"></p></section><tablet-assist-bt-keepalive id="keepalive"></tablet-assist-bt-keepalive></main>`;
 const q=s=>this.shadowRoot.querySelector(s);
 const selectView=view=>{
   if(view==="learning"&&!this._hass?.user?.is_admin)view="overview";
   this._view=view;
   for(const el of q("main").children)el.hidden=view==="sources"?el.id!=="sourcesPage":view==="learning"?el.id!=="learningPage":view==="devices"?el.id!=="devicesPage":["sourcesPage","learningPage","devicesPage"].includes(el.id);
   if(view==="learning")this.refreshLearning();if(view==="devices")void this.refreshDevices();
 };
 q("#devices").onclick=()=>selectView("devices");
 q("#refreshDevices").onclick=()=>void this.refreshDevices();
 q("#learn").onclick=()=>selectView("learning");
 q("#refreshLearn").onclick=()=>this.refreshLearning();
 q("#clearLearn").onclick=()=>{if(window.confirm(t.clearConfirm))this.refreshLearning("clear");};
 q("#overview").onclick=()=>selectView("overview");
 q("#sources").onclick=()=>selectView("sources");
 const configured=new Set(this._panel?.config?.sources||[]);
 for(const [key,names] of Object.entries(SOURCE_LABELS)){
   if(key==="reminder_room")continue;
   const line=document.createElement("div");line.className="stat";
   const enabled=key==="reminders_enabled"?this._panel?.config?.reminders:configured.has(key);
   line.textContent=names[this._lang==="de"?1:0]+" · "+(enabled?t.configured:t.disabled);q("#sourceRows").append(line);
 }
 selectView(this._view);
 q("#menu").onclick=()=>this.dispatchEvent(new CustomEvent("hass-toggle-menu",{bubbles:true,composed:true}));
 q("#assist").onclick=()=>{const ext=this._hass?.auth?.external;if(ext?.config?.hasAssist && typeof ext.fireMessage==="function"){ext.fireMessage({type:"assist/show",payload:{pipeline_id:"last_used",start_listening:true}});}else{window.location.assign("/lovelace?conversation=1");}};
 q("textarea").value=previous;
 q("#noRooms").textContent=this._rooms.length?"":t.none;
 for(const room of this._rooms){const label=document.createElement("label"),input=document.createElement("input");input.type="checkbox";input.checked=this._selected.has(room);input.onchange=()=>{input.checked?this._selected.add(room):this._selected.delete(room);};label.append(input,document.createTextNode(this._lang==="de"?room:ROOM_EN[room]));q("#rooms").append(label);}
 q("#send").disabled=!this._rooms.length;
 q("#send").onclick=async()=>{const text=q("textarea").value.trim(),rooms=[...this._selected];if(!text||!rooms.length){q("#result").textContent=t.select;return;}q("#send").disabled=true;q("#result").textContent=t.sending;try{await this._hass.callService("tablet_assist_for_alexa","announce",{text,rooms});q("#result").textContent=t.sent;}catch{q("#result").textContent=t.error;}finally{q("#send").disabled=!this._rooms.length;}};
 q("#keepalive").setConfig({});this.update();
 }
 async refreshDevices(){
   const root=this.shadowRoot,rows=root.querySelector("#deviceRows"),status=root.querySelector("#deviceStatus"),t=this.t;
   if(!rows||!status||!this._hass||this._deviceBusy||this._view!=="devices")return;
   this._deviceBusy=true;status.textContent=t.deviceRefresh+" …";
   try{
     const response=await this._hass.callApi("POST","jarvis_tablet_audio/wake_devices",{action:"list"});
     if(this._view!=="devices"||!rows.isConnected)return;
     rows.replaceChildren();
     const devices=Array.isArray(response?.devices)?response.devices:[];
     if(!devices.length){status.textContent=t.deviceEmpty;return;}
     status.textContent=String(devices.length)+" "+t.devices.toLowerCase();
     for(const d of devices){
       const panel=document.createElement("div");panel.className="stat";
       const heading=document.createElement("h2");heading.textContent=d.room||"TAFA Device Bridge";panel.append(heading);
       const id=document.createElement("small");id.textContent=String(d.device_id||"").slice(0,8);panel.append(id);
       const actions=document.createElement("div");actions.style.cssText="display:flex;flex-wrap:wrap;gap:8px;margin:12px 0";
       const muted=document.createElement("button");muted.textContent=d.muted?t.deviceUnmute:t.deviceMute;
       muted.onclick=()=>void this.configureDevice(d.device_id,{muted:!d.muted});
       actions.append(muted);panel.append(actions);
       const wordLabel=document.createElement("p");wordLabel.textContent=t.deviceWord;panel.append(wordLabel);
       const choices=document.createElement("div");choices.style.cssText="display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 12px";
       for(const [value,label] of [["Hey Jarvis","Hey Jarvis"],["Jarvis","Jarvis"],["Alexa","Alexa"],["Alle drei",this._lang==="de"?"Alle drei":"All three"]]){
         const btn=document.createElement("button");btn.textContent=label;btn.disabled=value===d.word;
         btn.setAttribute("aria-pressed",String(value===d.word));
         btn.onclick=()=>void this.configureDevice(d.device_id,{word:value});choices.append(btn);
       }
       panel.append(choices);
       const rename=document.createElement("div");rename.style.cssText="display:flex;flex-wrap:wrap;gap:8px";
       const input=document.createElement("input");input.type="text";input.maxLength=48;input.value=d.room||"";input.setAttribute("aria-label",t.deviceRename);
       const save=document.createElement("button");save.textContent=t.deviceRename;save.onclick=()=>{if(input.value.trim())void this.configureDevice(d.device_id,{room:input.value.trim()});};
       rename.append(input,save);panel.append(rename);rows.append(panel);
     }
   }catch{
     if(status?.isConnected)status.textContent=t.deviceOffline;
   }finally{this._deviceBusy=false;}
 }
 async configureDevice(id,settings){
   if(this._deviceBusy||!this._hass)return;
   this._deviceBusy=true;
   const status=this.shadowRoot.querySelector("#deviceStatus");
   try{
     await this._hass.callApi("POST","jarvis_tablet_audio/wake_devices",{action:"configure",device_id:id,settings});
     if(status)status.textContent=this._lang==="de"?"Gespeichert":"Saved";
   }catch{
     if(status)status.textContent=this.t.deviceOffline;
   }finally{
     this._deviceBusy=false;
     if(this._view==="devices")void this.refreshDevices();
   }
 }
 async refreshLearning(action="list",phrase="",target=""){
   if(!this._hass?.user?.is_admin)return;
   const q=s=>this.shadowRoot.querySelector(s),t=this.t;
   try{
     const result=await this._hass.callWS({type:"tablet_assist_for_alexa/learning",action,phrase,target});
     if(!this._hass?.user?.is_admin||this._view!=="learning")return;
     q("#learnStatus").textContent=result.enabled?"":t.learnOff;
     const makeSelect=()=>{const select=document.createElement("select"),placeholder=document.createElement("option");placeholder.value="";placeholder.textContent=t.pick;select.append(placeholder);for(const key of result.targets){const option=document.createElement("option");option.value=key;option.textContent=INTENT_LABELS[key]?.[this._lang==="de"?1:0]||key;select.append(option);}return select;};
     const button=(label,fn)=>{const b=document.createElement("button");b.textContent=label;b.onclick=fn;return b;};
     for(const [container,items] of [["#suggestionRows",result.candidates],["#aliasRows",result.aliases]]){
       const el=q(container);el.replaceChildren();
       if(!Object.keys(items).length)el.textContent=t.emptyLearn;
       for(const [p,v] of Object.entries(items)){
         const row=document.createElement("div");row.className="learnrow";
         const text=document.createElement("span");text.textContent=p+" · "+(container==="#aliasRows"?(INTENT_LABELS[v]?.[this._lang==="de"?1:0]||v):v);
         row.append(text);
         if(container==="#suggestionRows"){
           const select=makeSelect(),approve=button(t.approve,()=>{if(select.value)this.refreshLearning("approve",p,select.value);});
           approve.disabled=!result.enabled;row.append(select,approve,button(t.dismiss,()=>this.refreshLearning("dismiss",p)));
         }else row.append(button(t.remove,()=>this.refreshLearning("delete",p)));
         el.append(row);
       }
     }
     const manual=q("#manualLearn");manual.replaceChildren();manual.hidden=!result.enabled;
     if(result.enabled){const input=document.createElement("input");input.maxLength=140;input.placeholder=t.newPhrase;input.setAttribute("aria-label",t.newPhrase);const select=makeSelect();manual.append(input,select,button(t.approve,()=>{if(input.value.trim()&&select.value)this.refreshLearning("approve",input.value,select.value);}));}
   }catch{q("#learnStatus").textContent=t.learnError;}
 }
 update(){
 const q=s=>this.shadowRoot.querySelector(s);if(!this._hass||!q("#stats"))return;
 q("#keepalive").hass=this._hass;
 this.shadowRoot.querySelector("nav").hidden=!this._hass.user?.is_admin;
 q("#sourceLink").hidden=!this._hass.user?.is_admin;
 q("#learn").hidden=!this._hass.user?.is_admin;
 if(!this._hass.user?.is_admin&&this._view==="learning"){this._view="overview";this.render();return;}
 const states=Object.values(this._hass.states||{}).filter(s=>/^(stt|tts|conversation)\./.test(s.entity_id)&&String(s.attributes.friendly_name||"").startsWith("Tablet Assist "));
 const container=q("#stats");container.replaceChildren();
 if(!states.length){container.textContent=this.t.empty;return;}
 for(const state of states){const r=document.createElement("div");r.className="stat";const a=state.attributes;r.textContent=[a.friendly_name, a.letztes_backend||state.state, typeof a.erste_audio_ms==="number"?a.erste_audio_ms+" ms":typeof a.letzte_dauer_ms==="number"?a.letzte_dauer_ms+" ms":""].filter(Boolean).join(" · ");container.append(r);}
 }
}
if(!customElements.get("tablet-assist-panel"))customElements.define("tablet-assist-panel",TabletAssistPanel);
