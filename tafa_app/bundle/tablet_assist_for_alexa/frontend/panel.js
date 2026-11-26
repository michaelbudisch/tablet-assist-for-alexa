/* TAFA Dashboard: built-in, cross-device, admin-configurable Home Assistant panel. */
import "./dashboard.js?v=0.4.15";
import "./voice_tools.js?v=0.4.15";
const DEFAULT={type:"custom:tafa-home-dashboard",version:1,title:"TAFA Dashboard",
  language:"auto",theme:"dark",accent:"teal",density:"comfortable",gridSign:"import",
  modules:["weather","lights","energy","ev","heating","heatpump","fuel",
    "appliances","cameras","waste","shopping","assist"],bindings:{},assist:{}};
const TEXT={
  de:{home:"Dashboard",voice:"Sprachdienste",edit:"Dashboard einrichten",
    save:"Speichern",cancel:"Abbrechen",saved:"Zuordnungen in Home Assistant gespeichert",
    unavailable:"Dashboard-Einstellungen derzeit nicht erreichbar"},
  en:{home:"Dashboard",voice:"Voice services",edit:"Configure dashboard",
    save:"Save",cancel:"Cancel",saved:"Dashboard bindings saved in Home Assistant",
    unavailable:"Dashboard configuration currently unavailable"}
};
const CSS=":host{display:block;min-height:100%;background:#0e1520;color:#e9f3fa;font:14px Inter,Roboto,Arial,sans-serif}"+
  "*{box-sizing:border-box}.toolbar{display:flex;flex-wrap:wrap;align-items:center;"+
  "justify-content:space-between;gap:10px;padding:10px 18px;background:#101c2d;"+
  "border-bottom:1px solid #2b3e50}.brand{display:flex;align-items:center;gap:9px;"+
  "font-weight:800;font-size:17px}.brand img{width:32px;height:32px;border-radius:8px}"+
  ".controls{display:flex;align-items:center;flex-wrap:wrap;gap:8px}"+
  "button{border:1px solid #344a59;border-radius:9px;background:#1b2b3e;"+
  "color:#e5f5ff;padding:8px 12px;font:inherit;font-weight:650;cursor:pointer}"+
  "button:hover,button[aria-pressed=true]{background:#1e4547;border-color:#61d7c6}"+
  "button:disabled{opacity:.48;cursor:default}.primary{background:#176356;"+
  "border-color:#248d7b}.info{padding:8px 18px;color:#aed2db;font-size:12px}"+
  ".layout{min-height:calc(100vh - 74px)}.editor{max-width:1100px;"+
  "margin:20px auto;padding:16px;background:#172333;border-radius:14px}"+
  "@media(max-width:600px){.toolbar{padding:8px}.brand{font-size:14px}"+
  ".controls{gap:5px}button{padding:7px 9px}}";
class TabletAssistPanel extends HTMLElement {
  constructor(){
    super();this.attachShadow({mode:"open"});this._config=structuredClone(DEFAULT);
    this._mode="home";this._loaded=false;this._loading=null;this._editing=false;
    this._dirty=false;this._message="";this._panel=null;this._hass=null;this._lang="de";
  }
  set panel(p){this._panel=p;if(this._voice)this._voice.panel=p;}
  set hass(h){
    this._hass=h;this._lang=String(h?.locale?.language||h?.language||"de").startsWith("de")?"de":"en";
    if(this._home)this._home.hass=h;
    if(this._voice)this._voice.hass=h;
    if(this._editor)this._editor.hass=h;
    if(this.isConnected&&!this._loaded&&!this._loading)void this._load();
  }
  get hass(){return this._hass;}
  connectedCallback(){this._render();if(this._hass&&!this._loaded)void this._load();}
  disconnectedCallback(){this._home=null;this._editor=null;this._voice=null;}
  async _load(){
    if(this._loading||!this._hass)return this._loading;
    this._loading=(async()=>{
      try{
        const result=await this._hass.callWS({type:"tablet_assist_for_alexa/dashboard/get"});
        if(!result||typeof result.config!=="object")throw Error("No dashboard config");
        this._config=result.config;this._loaded=true;this._message="";
      }catch(e){this._message=TEXT[this._lang].unavailable+": "+String(e?.message||e).slice(0,110);}
      finally{this._loading=null;if(this.isConnected)this._render();}
    })();
    return this._loading;
  }
  async _save(){
    if(!this._hass?.user?.is_admin||!this._dirty)return;
    try{
      const reply=await this._hass.callWS({type:"tablet_assist_for_alexa/dashboard/set",
                                        config:this._config});
      if(!reply?.saved)throw Error("Dashboard not saved");
      this._config=reply.config||this._config;this._loaded=true;this._dirty=false;
      this._editing=false;this._message=TEXT[this._lang].saved;
    }catch(e){this._message=String(e?.message||e).slice(0,170);}
    this._render();
  }
  _button(label,action){
    const el=document.createElement("button");el.textContent=label;
    el.type="button";el.dataset.action=action;
    if((action==="home"&&this._mode==="home")||(action==="voice"&&this._mode==="voice"))
      el.setAttribute("aria-pressed","true");
    if(action==="save"&&!this._dirty)el.disabled=true;
    if(action==="save")el.className="primary";
    el.addEventListener("click",()=>{
      if(action==="home"||action==="voice"){this._mode=action;this._editing=false;this._render();}
      else if(action==="edit"){this._editing=true;this._mode="home";this._render();}
      else if(action==="cancel"){this._dirty=false;this._editing=false;this._loaded=false;void this._load();}
      else if(action==="save")void this._save();
    });
    return el;
  }
  _render(){
    if(!this.isConnected)return;
    const L=TEXT[this._lang],admin=!!this._hass?.user?.is_admin;
    this.shadowRoot.replaceChildren();
    const style=document.createElement("style");style.textContent=CSS;
    const bar=document.createElement("div");bar.className="toolbar";
    const brand=document.createElement("div");brand.className="brand";
    const img=document.createElement("img");img.alt="";
    img.src="/tablet_assist_for_alexa/brand.svg?v=0.4.15";
    const name=document.createElement("span");name.textContent="TAFA Dashboard";
    brand.append(img,name);bar.append(brand);
    const controls=document.createElement("div");controls.className="controls";
    controls.append(this._button(L.home,"home"),this._button(L.voice,"voice"));
    if(admin&&!this._editing)controls.append(this._button(L.edit,"edit"));
    if(this._editing){
      controls.append(this._button(L.save,"save"),this._button(L.cancel,"cancel"));
    }
    bar.append(controls);this.shadowRoot.append(style,bar);
    if(this._message){
      const info=document.createElement("div");info.className="info";
      info.setAttribute("role","status");info.textContent=this._message;
      this.shadowRoot.append(info);
    }
    const host=document.createElement("div");host.className="layout";
    this.shadowRoot.append(host);this._home=null;this._voice=null;this._editor=null;
    if(this._mode==="voice"){
      const v=document.createElement("tablet-assist-voice-tools");
      if(this._panel)v.panel=this._panel;v.hass=this._hass;
      host.append(v);this._voice=v;return;
    }
    if(this._editing){
      const wrapper=document.createElement("div");wrapper.className="editor";
      const editor=document.createElement("tafa-home-dashboard-editor");
      editor.setConfig(this._config);editor.hass=this._hass;
      editor.addEventListener("config-changed",event=>{
        this._config=event.detail.config;this._dirty=true;
        const save=this.shadowRoot.querySelector('[data-action="save"]');
        if(save)save.disabled=false;
      });
      wrapper.append(editor);host.append(wrapper);this._editor=editor;return;
    }
    const d=document.createElement("tafa-home-dashboard");
    d.setConfig(this._config);d.hass=this._hass;
    d.addEventListener("tafa-open-voice-tools",()=>{this._mode="voice";this._render();});
    host.append(d);this._home=d;
  }
}
if(!customElements.get("tablet-assist-panel"))
  customElements.define("tablet-assist-panel",TabletAssistPanel);
