/* Per-tablet Ambient profiles. No household IDs or server-side secrets. */
const COMMAND="tablet_assist_for_alexa/ambient_profiles";
const LOCAL_DEVICE="tafa.ambient.local_device.v1";
const escapeHtml=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const defaults=()=>({calendar:"",presence:"",dismiss:"sensor",idle:55,enabled:true,autoOpen:true,metrics:null});
const normalize=p=>p&&typeof p==="object"?{...defaults(),...p}:defaults();
const deviceFor=(card,devices)=>{
 const own=card?._tafaLocalVoice||{};
 const primary=own.deviceId||own.device_id||own.wake_device_id||"";
 if(devices.some(d=>d.device_id===primary))return primary;
 let stored="";
 try{stored=localStorage.getItem(LOCAL_DEVICE)||"";}catch{}
 if(devices.some(d=>d.device_id===stored))return stored;
 // A fresh Android install replaces the device ID. Repair only an
 // unambiguous local tablet binding; never auto-bind an admin desktop.
 const android=typeof navigator!=="undefined"&&/Android/i.test(navigator.userAgent||"");
 if(devices.length===1&&(android||card?.h?.user?.is_admin!==true)){
   const next=devices[0].device_id;
   if(android)try{localStorage.setItem(LOCAL_DEVICE,next);}catch{}
   return next;
 }
 return "";
};
export async function subscribeOwnAmbientProfile(card,onProfile){
 if(!card?.h?.callWS)return ()=>{};
 const h=card.h,connection=h.connection;
 let closed=false,stop=null;
 const list=await h.callWS({type:COMMAND,action:"list"});
 if(closed)return ()=>{};
 const deviceId=deviceFor(card,Array.isArray(list?.devices)?list.devices:[]);
 if(!deviceId)return ()=>{};
 try{
  const identity=await h.callWS({type:"tablet_assist_for_alexa/visual_identity"});
  const own=(identity?.devices||[]).find(d=>d.device_id===deviceId);
  if(own&&!closed&&card.h?.connection===connection)
   card._tafaLocalVoice={...(card._tafaLocalVoice||{}),deviceId,room:own.room,
     label:own.label,status:own.sensors?.status||"",mic:own.sensors?.mic||"",
     last:own.sensors?.last||""};
 }catch(error){console.debug("TAFA device identity unavailable",error);}
 const reload=async()=>{
  try{
   const value=await h.callWS({type:COMMAND,action:"get",device_id:deviceId});
   if(!closed&&card.h?.connection===connection)onProfile(normalize(value?.profile),deviceId,Number(value?.revision)||0);
  }catch(error){console.debug("TAFA Ambient profile read",error);}
 };
 await reload();
 if(connection?.subscribeMessage){
  try{stop=await connection.subscribeMessage(event=>{
   if(!closed&&event?.device_id===deviceId)void reload();
  },{type:COMMAND,action:"subscribe",device_id:deviceId});
  if(closed)stop?.();
  }catch(error){console.debug("TAFA Ambient profile updates",error);}
 }
 return ()=>{closed=true;try{stop?.();}catch{}};
}
class TafaAmbientProfilesEditor extends HTMLElement{
 constructor(){
  super();this.attachShadow({mode:"open"});
  this._h=null;this.devices=[];this.deviceId="";this.profile=null;this.revision=0;
  this.loading=false;this.dirty=false;this.message="";this.readToken=0;this.unsubscribe=null;
 }
 set hass(h){
  const previousConnection=this._h?.connection;
  this._h=h;
  if(this.isConnected&&(this.devices.length===0||previousConnection!==h?.connection))
   void this.loadDevices();
 }
 get hass(){return this._h;}
 connectedCallback(){
  this.shadowRoot.addEventListener("change",e=>{
   const t=e.target;
   if(t.matches("[data-device]")){this.deviceId=t.value;void this.loadProfile();return;}
   if(t.matches("[data-metric-mode]")){
    const root=this.shadowRoot,prior=this.profile||defaults();
    if(Array.isArray(prior.metrics)){
     this._metricCache=[...root.querySelectorAll("[data-metric-row]")].map(row=>({
      id:row.querySelector("[data-mid]")?.value.trim()||"",
      name:row.querySelector("[data-mname]")?.value.trim()||""
     }));
    }
    const get=key=>root.querySelector('[data-setting="'+key+'"]');
    this.profile={...prior,
      calendar:get("calendar")?.value||"",presence:get("presence")?.value||"",
      dismiss:get("dismiss")?.value||"sensor",
      idle:Number(get("idle")?.value??55),
      enabled:!!get("enabled")?.checked,autoOpen:!!get("autoOpen")?.checked,
      metrics:t.value==="custom"?(this._metricCache||[]):null};
    this.dirty=true;this.render();return;
   }
   this.dirty=true;
  });
  this.shadowRoot.addEventListener("input",e=>{if(e.target.matches("input,select"))this.dirty=true;});
  this.shadowRoot.addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
   if(b.dataset.reload!==undefined){void this.loadProfile();return;}
   if(b.dataset.save!==undefined){void this.save();return;}
   if(b.dataset.add!==undefined){this.dirty=true;this.addMetric();return;}
   if(b.dataset.remove!==undefined){this.dirty=true;b.closest("[data-metric-row]")?.remove();return;}
   if(b.dataset.local!==undefined){try{localStorage.setItem(LOCAL_DEVICE,this.deviceId);this.message="Nur auf diesem Browser: Antworten des ausgewählten Tablets als Vorschau anzeigen.";this.render();}catch(error){this.message=String(error.message||error);this.render();}}
  });
  void this.loadDevices();
 }
 disconnectedCallback(){this.readToken++;try{this.unsubscribe?.();}catch{}this.unsubscribe=null;}
 async loadDevices(){
  if(!this._h?.callWS)return;
  const ticket=++this.readToken;
  try{
   const response=await this._h.callWS({type:COMMAND,action:"list"});
   if(ticket!==this.readToken||!this.isConnected)return;
   this.devices=Array.isArray(response?.devices)?response.devices:[];
   if(!this.devices.some(d=>d.device_id===this.deviceId))
    this.deviceId=this.devices[0]?.device_id||"";
   await this.loadProfile();
  }catch(error){if(ticket===this.readToken){this.message="Geräteliste nicht verfügbar: "+String(error.message||error);this.render();}}
 }
 async loadProfile(){
  const ticket=++this.readToken;this.loading=true;this.message="";this.dirty=false;this.render();
  try{
   if(!this.deviceId){this.profile=null;this.loading=false;this.render();return;}
   const response=await this._h.callWS({type:COMMAND,action:"get",device_id:this.deviceId});
   if(ticket!==this.readToken||!this.isConnected)return;
   this.profile=normalize(response.profile);this._metricCache=Array.isArray(this.profile.metrics)?this.profile.metrics:[];this.revision=Number(response.revision)||0;this.loading=false;
   try{this.unsubscribe?.();}catch{}this.unsubscribe=null;
   const connection=this._h?.connection;
   if(connection?.subscribeMessage){
    Promise.resolve(connection.subscribeMessage(ev=>{
      if(ev?.device_id!==this.deviceId)return;
      if(this.dirty){this.message="Profil wurde auf einem anderen Gerät geändert. Vor dem Speichern bitte aktualisieren.";this.status();return;}
      void this.loadProfile();
    },{type:COMMAND,action:"subscribe",device_id:this.deviceId})).then(stop=>{if(ticket!==this.readToken)stop?.();else this.unsubscribe=stop;}).catch(error=>console.debug("TAFA Ambient editor subscription",error));
   }
   this.render();
  }catch(error){if(ticket===this.readToken){this.loading=false;this.message=String(error.message||error);this.render();}}
 }
 values(){
  const root=this.shadowRoot,p=this.profile||defaults();
  const val=name=>root.querySelector('[data-setting="'+name+'"]')?.value;
  const checked=name=>!!root.querySelector('[data-setting="'+name+'"]')?.checked;
  const metricMode=root.querySelector("[data-metric-mode]")?.value||"automatic";
  const metrics=metricMode==="automatic"?null:[...root.querySelectorAll("[data-metric-row]")].map(row=>({
   id:row.querySelector("[data-mid]")?.value.trim()||"",
   name:row.querySelector("[data-mname]")?.value.trim()||""
  })).filter(row=>row.id);
  if(metrics&&metrics.some(row=>!/^(sensor|binary_sensor|number|input_number)\.[a-z0-9_]+$/.test(row.id)))throw Error("Ungültige Sensor-Entität");
  const duration=Number(val("idle")??p.idle);
  if(!Number.isFinite(duration)||duration<0||duration>86400)throw Error("Anzeigezeit: 0 bis 86400 Sekunden");
  return {calendar:val("calendar")?.trim()||"",presence:val("presence")?.trim()||"",
   dismiss:val("dismiss")||"sensor",idle:duration,enabled:checked("enabled"),
   autoOpen:checked("autoOpen"),metrics};
 }
 async save(){
  if(!this.deviceId||this.loading||!this._h?.callWS)return;
  let profile;try{profile=this.values();}catch(error){this.message=String(error.message||error);this.status();return;}
  this.loading=true;this.message="Speichere …";this.status();
  try{
   const response=await this._h.callWS({type:COMMAND,action:"save",
     device_id:this.deviceId,revision:this.revision,profile});
   this.profile=normalize(response.profile);this._metricCache=Array.isArray(this.profile.metrics)?this.profile.metrics:[];this.revision=Number(response.revision)||this.revision+1;
   this.dirty=false;this.message="Gespeichert · Revision "+this.revision;
   this.loading=false;this.render();
   try{dispatchEvent(new CustomEvent("tafa:ambient-profile-saved",{detail:{device_id:this.deviceId,profile:this.profile}}));}catch{}
  }catch(error){this.loading=false;this.message="Speichern fehlgeschlagen: "+String(error.message||error);this.status();}
 }
 status(){const node=this.shadowRoot.querySelector("[data-status]");if(node)node.textContent=this.message;}
 addMetric(){
  const host=this.shadowRoot.querySelector("[data-metrics]");
  if(!host||host.querySelectorAll("[data-metric-row]").length>=12)return;
  host.insertAdjacentHTML("beforeend",this.metricRow({id:"",name:""}));
 }
 metricRow(row){return '<div class="metricrow" data-metric-row><input data-mname placeholder="Beschriftung" maxlength="40" value="'+escapeHtml(row.name||"")+'"><input data-mid placeholder="sensor.…" value="'+escapeHtml(row.id||"")+'"><button type="button" data-remove aria-label="Sensor entfernen">×</button></div>';}
 render(){
  const p=this.profile||defaults(),language=String(this._h?.locale?.language||"de").startsWith("de")?"de":"en";
  const isAndroid=typeof navigator!=="undefined"&&/Android/i.test(navigator.userAgent||"");
  const devices=this.devices.map(d=>'<option value="'+escapeHtml(d.device_id)+'"'+(d.device_id===this.deviceId?" selected":"")+'>'+escapeHtml(d.room||d.label||"Tablet")+(d.online?" · online":" · offline")+'</option>').join("");
  const sourceList=Object.entries(this._h?.states||{}).filter(([id])=>/^(sensor|binary_sensor|number|input_number|calendar)\./.test(id)).slice(0,400)
   .map(([id,state])=>'<option value="'+escapeHtml(id)+'" label="'+escapeHtml(state.attributes?.friendly_name||id)+'"></option>').join("");
  const mode=p.metrics===null?"automatic":"custom";
  const rowHtml=(p.metrics||[]).map(x=>this.metricRow(x)).join("");
  const field=(label,name,value,type="text")=>'<label>'+label+'<input data-setting="'+name+'" type="'+type+'" value="'+escapeHtml(value)+'" list="'+(type==="text"?"tafa-ambient-entities":"")+'"></label>';
  const checkbox=(label,key)=>'<label class="check"><input type="checkbox" data-setting="'+key+'"'+(p[key]?" checked":"")+'">'+label+'</label>';
  const opts=(v,text)=>'<option value="'+v+'"'+(p.dismiss===v?" selected":"")+'>'+text+'</option>';
  this.shadowRoot.innerHTML='<style>:host{display:block;margin-top:16px;font:14px Roboto,Arial,sans-serif;color:var(--fg,var(--primary-text-color))}*{box-sizing:border-box}.panel{border:1px solid var(--border,var(--divider-color));background:var(--card,var(--card-background-color));border-radius:15px;padding:16px;max-width:950px}.row{display:flex;flex-wrap:wrap;gap:12px;align-items:end}.row>*{flex:1;min-width:190px}label{display:flex;flex-direction:column;gap:6px;font-size:12px;margin:11px 0}.check{flex-direction:row;align-items:center;font-size:13px}input:not([type=checkbox]),select{width:100%;padding:9px 10px;border:1px solid var(--border,var(--divider-color));background:var(--card2,var(--secondary-background-color));color:inherit;border-radius:8px;font:inherit}button{border:1px solid var(--border,var(--divider-color));color:inherit;background:var(--card2,var(--secondary-background-color));padding:9px 12px;border-radius:8px;cursor:pointer}.metricrow{display:grid;grid-template-columns:minmax(90px,1fr) minmax(150px,2fr) auto;gap:8px;align-items:center;margin:7px 0}.metricrow input{min-width:0}.help{color:var(--muted,var(--secondary-text-color));font-size:12px;line-height:1.5}.actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:13px}.primary{border-color:var(--acc,var(--primary-color))}.status{font-size:12px;margin-top:10px;color:var(--muted,var(--secondary-text-color))}h2{font-size:16px;margin:0 0 8px}h3{font-size:14px;margin:18px 0 6px}@media(max-width:540px){.metricrow{grid-template-columns:1fr;gap:5px}.row>*{min-width:100%}}</style>'+
  '<section class="panel"><h2>TAFA Ambient · '+(language==="de"?"Einstellungen pro Tablet":"Settings per tablet")+'</h2>'+
  '<p class="help">Kalender, Näherungssensor, Einblenddauer und Sensorkacheln gelten nur für das gewählte Tablet. Die Konfiguration wird zentral in Home Assistant gespeichert.</p>'+
  '<div class="row"><label>Ambient-Profil bearbeiten für Tablet<select data-device>'+devices+'</select></label><button data-reload type="button">Neu laden</button></div>'+ 
  (isAndroid?'':'<details><summary>Nur Browser-Vorschau (keine HA-Raumzuordnung)</summary><p class="help">Optional für PC-Dashboards: Auf diesem Browser die Antworten eines bereits zugeordneten Tablets anzeigen. Ändert weder Raum noch Gerätezuordnung.</p><button data-local type="button">Auf diesem Browser als Vorschau anzeigen</button></details>')+
  (!this.deviceId?'<p class="help">Noch kein TAFA-Tablet gekoppelt.</p>':
  '<div class="row">'+checkbox("Ambient aktiv","enabled")+checkbox("Automatisch bei Annäherung öffnen","autoOpen")+'</div>'+
  '<div class="row">'+field("Kalender-Entität","calendar",p.calendar)+field("Annäherungssensor","presence",p.presence)+'</div>'+
  '<div class="row"><label>Schließen<select data-setting="dismiss">'+opts("sensor","Wenn Sensor frei meldet")+opts("time","Nach Ablauf der Zeit")+opts("either","Sensor oder Zeit")+'</select></label>'+field("Anzeigezeit (Sekunden, 0 = kein Timer)","idle",p.idle,"number")+'</div>'+
  '<h3>Sensordaten auf der Ambient-Kugel</h3><label>Auswahl<select data-metric-mode><option value="automatic"'+(mode==="automatic"?" selected":"")+'>Automatisch</option><option value="custom"'+(mode==="custom"?" selected":"")+'>Manuell</option></select></label>'+
  (mode==="custom"?'<div data-metrics>'+rowHtml+'</div><button type="button" data-add>Sensor hinzufügen</button><p class="help">Bis zu 12 Sensoren; auf kleineren Bildschirmen werden die ersten 6 angezeigt.</p>':'<p class="help">Automatische Sensorauswahl anhand verfügbarer Entitäten.</p>')+
  '<div class="actions"><button class="primary" data-save type="button"'+(this.loading?" disabled":"")+'>Einstellungen speichern</button></div>')+
  '<datalist id="tafa-ambient-entities">'+sourceList+'</datalist><p class="status" data-status>'+escapeHtml(this.message|| (this.loading?"Wird geladen …":this.deviceId?"Profilrevision "+this.revision:""))+'</p></section>';
 }
}
if(!customElements.get("tafa-ambient-profiles-editor"))customElements.define("tafa-ambient-profiles-editor",TafaAmbientProfilesEditor);
