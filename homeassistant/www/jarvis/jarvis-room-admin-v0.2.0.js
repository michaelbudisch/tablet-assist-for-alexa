/* Jarvis Multiroom: administrator-only configuration; no credentials in the card. */
class JarvisRoomAdmin extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});}
  setConfig(){this.render();}
  set hass(h){this._h=h;if(this.isConnected&&!this.loaded){this.loaded=true;this.refresh();}}
  connectedCallback(){if(this._h&&!this.loaded){this.loaded=true;this.refresh();}}
  disconnectedCallback(){this.loaded=false;}
  getCardSize(){return 5;}
  tr(de,en){return String(this._h?.language||navigator.language).startsWith("de")?de:en;}
  el(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;}
  async rpc(data){const r=await this._h.callWS({type:"call_service",domain:"jarvis_tablet_audio",service:"room_audio",service_data:data,return_response:true});return r?.response??r?.service_response??r;}
  async refresh(){
    if(!this._h?.user?.is_admin){this.rooms=[];this.users=[];this.error=this.tr("Administrator erforderlich.","Administrator required.");this.render();return;}
    try{const [r,u]=await Promise.all([this.rpc({action:"list"}),this.rpc({action:"users"})]);this.rooms=r.rooms||[];this.users=u.users||[];this.error="";}catch(e){this.error=this.tr("Raumverwaltung nicht verfügbar.","Room management unavailable.");}
    this.render();
  }
  render(){
    const root=this.shadowRoot;root.replaceChildren();const style=this.el("style");style.textContent="ha-card{padding:16px}h3{margin:0 0 10px}p{color:var(--secondary-text-color)}section{padding:12px 0;border-top:1px solid var(--divider-color);display:grid;gap:8px}label{display:grid;gap:4px;font-size:13px}input,select,button{font:inherit;min-height:38px;border:1px solid var(--divider-color);border-radius:8px;padding:6px 9px;background:var(--secondary-background-color);color:var(--primary-text-color);box-sizing:border-box;max-width:100%}button{cursor:pointer}button:disabled{opacity:.5}.row{display:flex;gap:8px;flex-wrap:wrap}.muted{font-size:12px;color:var(--secondary-text-color)}";root.append(style);
    const card=this.el("ha-card");root.append(card);card.append(this.el("h3",this.tr("Jarvis · Räume","Jarvis · Rooms")));if(this.error){card.append(this.el("p",this.error));return;}if(!this._h?.user?.is_admin)return;
    const feedback=this.el("p",this.notice||"");feedback.setAttribute("role","status");
    const button=(label,fn)=>{const b=this.el("button",label);b.type="button";b.onclick=async()=>{b.disabled=true;try{await fn();}catch(e){feedback.textContent=String(e?.message||this.tr("Aktion fehlgeschlagen","Action failed"));}finally{b.disabled=false;}};return b;};
    const input=(label,value="",type="text")=>{const l=this.el("label",label),i=this.el("input");i.type=type;i.value=value;l.append(i);return [l,i];};
    card.append(button(this.tr("Status aktualisieren","Refresh status"),()=>this.refresh()));
    const selected=new Set();const userNames=Object.fromEntries((this.users||[]).map(u=>[u.id,u.name]));
    for(const r of this.rooms||[]){
      const s=this.el("section"),head=this.el("strong",r.room+" · "+(r.ready?this.tr("Bereit","Ready"):r.online?this.tr("Beschäftigt","Busy"):this.tr("Offline","Offline")));s.append(head,this.el("span",userNames[r.user_id]||r.user_id));
      const check=this.el("input");check.type="checkbox";check.onchange=()=>check.checked?selected.add(r.room):selected.delete(r.room);const choose=this.el("label",this.tr("Für Durchsage auswählen","Select for announcement"));choose.append(check);s.append(choose);
      const [sl,si]=input(this.tr("Ruhe ab","Quiet from"),r.quiet_start||"","time"),[el,ei]=input(this.tr("Ruhe bis","Quiet until"),r.quiet_end||"","time"),[dl,di]=input(this.tr("HA-Geräte-ID (optional)","HA device ID (optional)"),r.device_id||"");
      const camera=this.el("input");camera.type="checkbox";camera.checked=r.camera_enabled===true;
      const cl=this.el("label",this.tr("Kamera für gemeinsam genutzten Raum erlauben (alle Anwesenden informieren)","Allow camera in shared room (inform everyone present)"));cl.append(camera);
      s.append(sl,el,dl,cl,this.el("span",this.tr("Kamera: ","Camera: ")+(r.camera_online?this.tr("Livebilder verfügbar","Live images available"):this.tr("Aus / offline","Off / offline"))),this.el("span",r.camera_entity_id||""),this.el("span",r.motion_entity_id||""));const row=this.el("div");row.className="row";row.append(button(this.tr("Speichern","Save"),async()=>{await this.rpc({action:"configure",room:r.room,quiet_start:si.value,quiet_end:ei.value,device_id:di.value.trim(),camera_enabled:camera.checked});await this.refresh();}),button(this.tr("Entfernen","Remove"),async()=>{if(!window.confirm(this.tr("Raum wirklich entkoppeln?","Revoke this room?")))return;await this.rpc({action:"revoke",room:r.room});await this.refresh();}));s.append(row);card.append(s);
    }
    const create=this.el("section"),[rl,ri]=input(this.tr("Neuer Raum (z. B. wohnzimmer)","New room (e.g. living_room)"));ri.maxLength=64;const ul=this.el("label",this.tr("Separater HA-Benutzer","Dedicated HA user")),us=this.el("select");for(const u of this.users||[]){const op=this.el("option",u.name);op.value=u.id;us.append(op);}ul.append(us);create.append(rl,ul,button(this.tr("Raum hinzufügen","Add room"),async()=>{await this.rpc({action:"provision",room:ri.value.trim(),user_id:us.value});await this.refresh();}));card.append(create);
    const ann=this.el("section"),[ml,mi]=input(this.tr("Durchsage an ausgewählte Räume","Announcement to selected rooms"));mi.maxLength=500;ann.append(ml,button(this.tr("Senden","Send"),async()=>{if(!selected.size||!mi.value.trim())throw Error(this.tr("Räume und Text auswählen.","Select rooms and enter text."));const r=await this.rpc({action:"announce",rooms:[...selected],message:mi.value.trim()});feedback.textContent=Object.entries(r.results||{}).map(([room,v])=>room+": "+v.status).join(" · ");}));card.append(ann,feedback,this.el("p",this.tr("Raumkonten müssen getrennt sein. Ruhezeiten gelten für automatische Durchsagen, nicht für bewusst gestellte Fragen.","Room accounts must be distinct. Quiet hours apply to announcements, not intentional questions.")));
  }
}
if(!customElements.get("jarvis-room-admin"))customElements.define("jarvis-room-admin",JarvisRoomAdmin);
window.customCards=window.customCards||[];window.customCards.push({type:"jarvis-room-admin",name:"Jarvis Multiroom",description:"Opt-in room provisioning and announcements"});
