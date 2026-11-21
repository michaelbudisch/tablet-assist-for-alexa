/* Jarvis Dashboard v1.4.0 — native Assist, no dashboard microphone or audio session */
(function(){
const PIPELINE="__JARVIS_PIPELINE_ID__";
function openAssist(el,pipeline=PIPELINE){
  el.dispatchEvent(new CustomEvent("hass-action",{bubbles:true,composed:true,detail:{config:{tap_action:{action:"assist",pipeline_id:pipeline,start_listening:true}},action:"tap"}}));
}
class JarvisHeaderBadge extends HTMLElement{
  constructor(){
    super();
    this.attachShadow({mode:"open"});
    this.shadowRoot.innerHTML='<style>:host{display:inline-flex;flex-shrink:0}button{display:inline-flex;align-items:center;gap:6px;min-height:34px;padding:7px 10px;border:1px solid #36bb9a80;border-radius:999px;background:#36bb9a12;color:#36bb9a;font:inherit;font-size:12px;font-weight:600;white-space:nowrap;cursor:pointer}ha-icon{--mdc-icon-size:19px}button:focus-visible{outline:2px solid currentColor;outline-offset:2px}@media(max-width:700px){button{padding:6px}.label{display:none}}</style><button type="button" title="Jarvis · Assist öffnen" aria-label="Jarvis Sprachassistent öffnen"><ha-icon icon="mdi:microphone-outline"></ha-icon><span class="label">Jarvis</span></button>';
    this.shadowRoot.querySelector("button").onclick=()=>openAssist(this);
  }
}
if(!customElements.get("jarvis-header-badge"))customElements.define("jarvis-header-badge",JarvisHeaderBadge);
class JarvisConversationCard extends HTMLElement{
  constructor(){super();this.attachShadow({mode:"open"});}
  setConfig(cfg){this.cfg=cfg||{};this.shadowRoot.innerHTML='<ha-card><style>.body{padding:20px;display:grid;gap:12px}h3,p{margin:0}p{color:var(--secondary-text-color);font-size:13px}button{padding:12px;display:flex;align-items:center;justify-content:center;gap:8px;background:var(--primary-color);color:var(--text-primary-color,#fff);border:0;border-radius:12px;font:inherit;cursor:pointer}</style><div class="body"><h3>Jarvis · Assist</h3><p>Sprachaufnahme und Sprachausgabe übernimmt die Home-Assistant-App. Diese Karte startet keine eigene Mikrofonaufnahme. Wakeword in den Assist-Einstellungen der Android-App konfigurieren.</p><button type="button"><ha-icon icon="mdi:microphone"></ha-icon>Jarvis öffnen</button><p>Im normalen Browser wird der Home-Assistant-Assistent geöffnet.</p></div></ha-card>';this.shadowRoot.querySelector("button").onclick=()=>openAssist(this,this.cfg.pipeline||PIPELINE);}
  set hass(h){this._hass=h;}
  getCardSize(){return 3;}
  getGridOptions(){return {columns:12,rows:"auto"};}
}
if(!customElements.get("jarvis-conversation-card"))customElements.define("jarvis-conversation-card",JarvisConversationCard);
window.customCards=window.customCards||[];
if(!window.customCards.some(x=>x.type==="jarvis-conversation-card"))window.customCards.push({type:"jarvis-conversation-card",name:"Jarvis Assist",description:"Öffnet den nativen Assist statt eigener Mikrofonaufnahme"});
})();