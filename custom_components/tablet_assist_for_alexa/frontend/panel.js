import "/tablet_assist_for_alexa/keepalive.js?v=0.2.2";
const ROOM_EN={"Büro":"Office","Wohnzimmer":"Living room","Badezimmer":"Bathroom","Schlafzimmer":"Bedroom","Kinderzimmer":"Children's room"};
const words={
 de:{title:"Sprachzentrale",sub:"Lokaler Assistent · Tablet & Echo",assist:"Assist starten",assistHint:"Nutzt den nativen Home-Assistant-Assistenten. Wähle dort deine Tablet-Assist-Pipeline. Im Browser kann dabei das Standard-Dashboard geöffnet werden.",status:"Sprachdienste",settings:"Integration konfigurieren",pipelines:"Sprachassistenten",ann:"Alexa-Durchsage",message:"Nicht vertrauliche Nachricht eingeben",send:"Durchsage senden",none:"Keine Räume konfiguriert. Optionale Alexa-Durchsagen in der Integration einrichten.",sending:"Wird erstellt …",sent:"An Notify übergeben. Wiedergabe am Echo prüfen.",error:"Durchsage fehlgeschlagen. Prüfe Konfiguration und Ruhezeiten.",select:"Nachricht und mindestens einen Raum wählen.",empty:"Noch keine Statusdaten",sidebar:"Menü öffnen"},
 en:{title:"Voice center",sub:"Local assistant · Tablet & Echo",assist:"Start Assist",assistHint:"Uses native Home Assistant Assist. Select your Tablet Assist pipeline there. In a browser, the default dashboard may open.",status:"Voice services",settings:"Configure integration",pipelines:"Voice assistants",ann:"Alexa announcement",message:"Enter a non-confidential message",send:"Send announcement",none:"No rooms configured. Set up optional Alexa announcements in the integration.",sending:"Generating …",sent:"Handed to Notify. Check playback on Echo.",error:"Announcement failed. Check configuration and quiet times.",select:"Enter a message and select at least one room.",empty:"No status data yet",sidebar:"Open menu"}
};
class TabletAssistPanel extends HTMLElement {
 constructor(){super();this.attachShadow({mode:"open"});this._rooms=[];this._lang="";this._selected=new Set();}
 set panel(p){this._panel=p;const rooms=(p?.config?.rooms||[]).filter(x=>Object.hasOwn(ROOM_EN,x));if(JSON.stringify(rooms)!==JSON.stringify(this._rooms)){this._rooms=rooms;this._selected=new Set();this.render();}}
 set hass(h){this._hass=h;const l=(h.locale?.language||h.language||"en").startsWith("de")?"de":"en";if(l!==this._lang){this._lang=l;this.render();}this.update();}
 set narrow(v){this._narrow=v;}
 connectedCallback(){if(!this.shadowRoot.querySelector("main"))this.render();}
 get t(){return words[this._lang]||words.en;}
 render(){
 const previous=this.shadowRoot.querySelector("textarea")?.value||"";
 const t=this.t;
 this.shadowRoot.innerHTML=`<style>:host{display:block;color:var(--primary-text-color);background:var(--primary-background-color);min-height:100%;font:inherit}*{box-sizing:border-box}header{display:flex;align-items:center;gap:12px;position:sticky;top:0;background:var(--app-header-background-color,var(--card-background-color));color:var(--app-header-text-color,var(--primary-text-color));padding:12px 20px;z-index:1}header strong{font-size:20px}main{max-width:1000px;margin:auto;padding:20px;display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr))}section{background:var(--ha-card-background,var(--card-background-color));border:1px solid var(--divider-color);border-radius:16px;padding:20px;display:grid;gap:12px;align-content:start}.hero{grid-column:1/-1}h1,h2,p{margin:0}h1{font-size:27px}h2{font-size:18px}p{color:var(--secondary-text-color);line-height:1.5}button,a{font:inherit;color:var(--primary-text-color);cursor:pointer}button{border:1px solid var(--divider-color);border-radius:10px;padding:10px 14px;background:var(--card-background-color)}button.primary{background:var(--primary-color);color:var(--text-primary-color,#fff);border:none}button:disabled{opacity:.5;cursor:default}header button{background:transparent;color:inherit;border:none;padding:6px}textarea{font:inherit;background:var(--primary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);border-radius:10px;resize:vertical;width:100%;padding:10px}label{display:flex;gap:8px;align-items:center}#rooms{display:flex;flex-wrap:wrap;gap:12px}#stats{display:grid;gap:6px}.stat{padding:8px 0;border-bottom:1px solid var(--divider-color);overflow-wrap:anywhere}nav{display:flex;flex-wrap:wrap;gap:16px}nav[hidden]{display:none}tablet-assist-bt-keepalive{display:block}</style><header><button id="menu" aria-label="${t.sidebar}">☰</button><strong>Tablet Assist</strong></header><main><section class="hero"><h1>${t.title}</h1><p>${t.sub}</p><button class="primary" id="assist">🎙 ${t.assist}</button><p>${t.assistHint}</p><nav><a href="/config/integrations">${t.settings}</a><a href="/config/voice-assistants">${t.pipelines}</a></nav></section><section><h2>${t.status}</h2><div id="stats"></div></section><section><h2>${t.ann}</h2><p id="noRooms"></p><textarea rows="3" maxlength="500" placeholder="${t.message}"></textarea><div id="rooms"></div><button class="primary" id="send">${t.send}</button><p role="status" id="result"></p></section><tablet-assist-bt-keepalive id="keepalive"></tablet-assist-bt-keepalive></main>`;
 const q=s=>this.shadowRoot.querySelector(s);
 q("#menu").onclick=()=>this.dispatchEvent(new CustomEvent("hass-toggle-menu",{bubbles:true,composed:true}));
 q("#assist").onclick=()=>{const ext=this._hass?.auth?.external;if(ext?.config?.hasAssist && typeof ext.fireMessage==="function"){ext.fireMessage({type:"assist/show",payload:{pipeline_id:"last_used",start_listening:true}});}else{window.location.assign("/lovelace?conversation=1");}};
 q("textarea").value=previous;
 q("#noRooms").textContent=this._rooms.length?"":t.none;
 for(const room of this._rooms){const label=document.createElement("label"),input=document.createElement("input");input.type="checkbox";input.checked=this._selected.has(room);input.onchange=()=>{input.checked?this._selected.add(room):this._selected.delete(room);};label.append(input,document.createTextNode(this._lang==="de"?room:ROOM_EN[room]));q("#rooms").append(label);}
 q("#send").disabled=!this._rooms.length;
 q("#send").onclick=async()=>{const text=q("textarea").value.trim(),rooms=[...this._selected];if(!text||!rooms.length){q("#result").textContent=t.select;return;}q("#send").disabled=true;q("#result").textContent=t.sending;try{await this._hass.callService("tablet_assist_for_alexa","announce",{text,rooms});q("#result").textContent=t.sent;}catch{q("#result").textContent=t.error;}finally{q("#send").disabled=!this._rooms.length;}};
 q("#keepalive").setConfig({});this.update();
 }
 update(){
 const q=s=>this.shadowRoot.querySelector(s);if(!this._hass||!q("#stats"))return;
 q("#keepalive").hass=this._hass;
 this.shadowRoot.querySelector("nav").hidden=!this._hass.user?.is_admin;
 const states=Object.values(this._hass.states||{}).filter(s=>/^(stt|tts|conversation)\./.test(s.entity_id)&&String(s.attributes.friendly_name||"").startsWith("Tablet Assist "));
 const container=q("#stats");container.replaceChildren();
 if(!states.length){container.textContent=this.t.empty;return;}
 for(const state of states){const r=document.createElement("div");r.className="stat";const a=state.attributes;r.textContent=[a.friendly_name, a.letztes_backend||state.state, typeof a.erste_audio_ms==="number"?a.erste_audio_ms+" ms":typeof a.letzte_dauer_ms==="number"?a.letzte_dauer_ms+" ms":""].filter(Boolean).join(" · ");container.append(r);}
 }
}
if(!customElements.get("tablet-assist-panel"))customElements.define("tablet-assist-panel",TabletAssistPanel);
