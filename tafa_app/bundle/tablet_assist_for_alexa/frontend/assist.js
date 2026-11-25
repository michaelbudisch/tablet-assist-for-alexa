/* Jarvis Dashboard v1.4.0 — native Assist, no dashboard microphone or audio session */
(function(){
const PIPELINE="";
const EN = {
  "Jarvis · Assist öffnen": "Jarvis · Open Assist",
  "Jarvis Sprachassistent öffnen": "Open Jarvis voice assistant",
  "Sprachaufnahme und Sprachausgabe übernimmt die Home-Assistant-App. Diese Karte startet keine eigene Mikrofonaufnahme. Wakeword in den Assist-Einstellungen der Android-App konfigurieren.": "The Home Assistant app handles speech input and output. This card does not start a separate microphone session. Configure the wake word in the Android app's Assist settings.",
  "Jarvis öffnen": "Open Jarvis",
  "Im normalen Browser wird der Home-Assistant-Assistent geöffnet.": "In a regular browser, the Home Assistant voice assistant opens.",
  "Öffnet den nativen Assist statt eigener Mikrofonaufnahme": "Opens native Assist instead of recording microphone audio separately"
};
function language(hass){ return String(hass?.locale?.language || hass?.language || document.querySelector("home-assistant")?.hass?.locale?.language || document.documentElement.lang || navigator.language || "en").toLowerCase().startsWith("de") ? "de" : "en"; }
function tr(s,hass){return language(hass)==="de" ? s : (EN[s] || s);}
function localize(html,hass){if(language(hass)==="de")return html;for(const [de,en] of Object.entries(EN))html=html.split(de).join(en);return html;}

function openAssist(el,pipeline=PIPELINE){
  el.dispatchEvent(new CustomEvent("hass-action",{bubbles:true,composed:true,detail:{config:{tap_action:{action:"assist",...(pipeline?{pipeline_id:pipeline}:{}),start_listening:true}},action:"tap"}}));
}
class JarvisHeaderBadge extends HTMLElement{
  constructor(){
    super();
    this.attachShadow({mode:"open"});
    this.render();
  }
  set hass(h){const l=language(h);this._hass=h;if(l!==this._lang)this.render();}
  render(){this._lang=language(this._hass);
    this.shadowRoot.innerHTML=localize('<style>:host{display:inline-flex;flex-shrink:0}button{display:inline-flex;align-items:center;gap:6px;min-height:34px;padding:7px 10px;border:1px solid #36bb9a80;border-radius:999px;background:#36bb9a12;color:#36bb9a;font:inherit;font-size:12px;font-weight:600;white-space:nowrap;cursor:pointer}ha-icon{--mdc-icon-size:19px}button:focus-visible{outline:2px solid currentColor;outline-offset:2px}@media(max-width:700px){button{padding:6px}.label{display:none}}</style><button type="button" title="Jarvis · Assist öffnen" aria-label="Jarvis Sprachassistent öffnen"><ha-icon icon="mdi:microphone-outline"></ha-icon><span class="label">Jarvis</span></button>',this._hass);
    this.shadowRoot.querySelector("button").onclick=()=>openAssist(this);
  }
}
if(!customElements.get("tablet-assist-header-badge"))customElements.define("tablet-assist-header-badge",JarvisHeaderBadge);
class JarvisConversationCard extends HTMLElement{
  constructor(){super();this.attachShadow({mode:"open"});}
  setConfig(cfg){this.cfg=cfg||{};this.render();}
  render(){this._lang=language(this._hass);this.shadowRoot.innerHTML=localize('<ha-card><style>.body{padding:20px;display:grid;gap:12px}h3,p{margin:0}p{color:var(--secondary-text-color);font-size:13px}button{padding:12px;display:flex;align-items:center;justify-content:center;gap:8px;background:var(--primary-color);color:var(--text-primary-color,#fff);border:0;border-radius:12px;font:inherit;cursor:pointer}</style><div class="body"><h3>Jarvis · Assist</h3><p>Sprachaufnahme und Sprachausgabe übernimmt die Home-Assistant-App. Diese Karte startet keine eigene Mikrofonaufnahme. Wakeword in den Assist-Einstellungen der Android-App konfigurieren.</p><button type="button"><ha-icon icon="mdi:microphone"></ha-icon>Jarvis öffnen</button><p>Im normalen Browser wird der Home-Assistant-Assistent geöffnet.</p></div></ha-card>',this._hass);this.shadowRoot.querySelector("button").onclick=()=>openAssist(this,this.cfg.pipeline||PIPELINE);}
  set hass(h){const l=language(h);this._hass=h;if(this.cfg&&l!==this._lang)this.render();}
  getCardSize(){return 3;}
  getGridOptions(){return {columns:12,rows:"auto"};}
}
if(!customElements.get("tablet-assist-conversation-card"))customElements.define("tablet-assist-conversation-card",JarvisConversationCard);
window.customCards=window.customCards||[];
if(!window.customCards.some(x=>x.type==="tablet-assist-conversation-card"))window.customCards.push({type:"tablet-assist-conversation-card",name:"Jarvis Assist",description:tr("Öffnet den nativen Assist statt eigener Mikrofonaufnahme")});
})();