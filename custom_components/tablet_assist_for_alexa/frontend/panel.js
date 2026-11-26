/* TAFA Dashboard: built-in, cross-device, admin-configurable Home Assistant panel. */
import "./dashboard.js?v=0.4.32-unified";
import "./voice_tools.js?v=0.4.20";
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
// The home page owns its header, quick actions and bottom navigation.
 // Only show local controls when inside a full-screen subview.
const CSS=":host{display:block;min-height:100%;background:#0e1520;color:#e9f3fa;font:14px Inter,Roboto,Arial,sans-serif}"+
  "*{box-sizing:border-box}.subview-nav{display:flex;align-items:center;"+
  "gap:8px;flex-wrap:wrap;padding:9px 16px;background:#101c2d;"+
  "border-bottom:1px solid #2b3e50}.subview-nav button{border:1px solid #344a59;"+
  "border-radius:9px;background:#1b2b3e;color:#e5f5ff;padding:9px 12px;"+
  "font:inherit;font-weight:650;cursor:pointer}.subview-nav button:hover{"+
  "background:#1e4547;border-color:#61d7c6}.subview-nav button:disabled{"+
  "opacity:.48;cursor:default}.subview-nav .primary{background:#176356;"+
  "border-color:#248d7b}.info{padding:8px 18px;color:#aed2db;font-size:12px}"+
  ".layout{min-height:100%}.editor{max-width:1100px;margin:12px auto;"+
  "padding:16px;background:#172333;border-radius:14px}";
class TabletAssistPanel extends HTMLElement {
  constructor(){
    super();this.attachShadow({mode:"open"});this._config=structuredClone(DEFAULT);
    this._mode=new URLSearchParams(window.location.search).get("view")==="voice"?"voice":"home";this._loaded=false;this._loading=null;this._editing=false;
    this._dirty=false;this._message="";this._panel=null;this._hass=null;this._lang="de";
  }
  set panel(p){this._panel=p;if(this._voice)this._voice.panel=p;if(this._home)this._home.panel=p;}
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
    this.shadowRoot.append(style);
    // Keep the overview visually identical to the standalone TAFA Home
    // dashboard: no second header, logo row or duplicate navigation.
    // Voice and configuration subviews provide a minimal way back.
    if(this._mode==="voice"||this._editing){
      const nav=document.createElement("div");nav.className="subview-nav";
      nav.append(this._button(this._lang==="de"?"← Zurück zum Dashboard":"← Back to dashboard","home"));
      if(this._editing){
        nav.append(this._button(L.save,"save"),this._button(L.cancel,"cancel"));
      }
      this.shadowRoot.append(nav);
    }
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
      const editor=document.createElement("tafa-integrated-dashboard-editor");
      editor.setConfig(this._config);editor.hass=this._hass;
      editor.addEventListener("config-changed",event=>{
        this._config=event.detail.config;this._dirty=true;
        const save=this.shadowRoot.querySelector('[data-action="save"]');
        if(save)save.disabled=false;
      });
      wrapper.append(editor);host.append(wrapper);this._editor=editor;return;
    }
    const d=document.createElement("tafa-integrated-dashboard");
    d.setConfig(this._config);d.panel=this._panel;d.hass=this._hass;
    d.addEventListener("tafa-open-voice-tools",()=>{this._mode="voice";this._editing=false;this._render();});
    d.addEventListener("tafa-open-dashboard-editor",()=>{
      if(!this._hass?.user?.is_admin)return;
      this._mode="home";this._editing=true;this._dirty=false;this._render();
    });
    host.append(d);this._home=d;
  }
}
if(!customElements.get("tablet-assist-panel"))
  customElements.define("tablet-assist-panel",TabletAssistPanel);
