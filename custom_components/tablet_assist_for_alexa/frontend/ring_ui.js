/* TAFA Ring notices + memory-only vision diagnosis. No household-specific IDs. */
const safe=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const isReady=s=>!!s&&s.state!=="unavailable"&&s.state!=="unknown";
const proxyPicture=s=>{
 const url=s?.attributes?.entity_picture;
 return typeof url==="string"&&url.startsWith("/api/camera_proxy/")&&!url.startsWith("//")?url:"";
};
const formatDate=x=>{
 const date=new Date(x||"");
 return Number.isFinite(date.getTime())?date.toLocaleString(undefined,{dateStyle:"short",timeStyle:"short"}):"—";
};
const modes={
 structured_12:"12 frames · structured vision",
 joint_12:"12 frames · fallback",
 independent_4:"4 frames · fallback"
};
class TafaRingVisionDiagnostics extends HTMLElement{
 constructor(){super();this.attachShadow({mode:"open"});this._h=null;}
 set hass(h){this._h=h;if(this.isConnected)this.render();}
 get hass(){return this._h;}
 connectedCallback(){this.shadowRoot.addEventListener("click",e=>{
   const button=e.target.closest?.("button[data-refresh]");
   if(button)this.render();
 });this.render();}
 render(){
  const h=this._h,language=String(h?.locale?.language||h?.language||"de").startsWith("de")?"de":"en";
  const states=h?.states||{},items=Object.entries(states).filter(([id,s])=>
    id.startsWith("camera.")&&s?.attributes?.stored_for_seconds===3600&&
    Object.hasOwn(s.attributes,"frames_extracted")).slice(0,6);
  const title=language==="de"?"Ring · Vision-Diagnose":"Ring · vision diagnostics";
  const text=language==="de"?"Hier siehst du die Bildfolgen, die TAFA an Qwen übergeben hat. Sie bleiben maximal 60 Minuten im Arbeitsspeicher und verschwinden nach einem Neustart.":"The frame selection sent to Qwen, retained in memory for up to 60 minutes.";
  const meta=(label,val)=>'<span class="meta"><small>'+safe(label)+'</small><b>'+safe(val)+'</b></span>';
  const cards=items.map(([id,state])=>{
   const a=state.attributes||{},url=isReady(state)?proxyPicture(state):"";
   const label=String(a.friendly_name||id),description=String(a.summary||"").slice(0,1100);
   const mode=modes[a.analysis_mode]||a.analysis_mode||"—";
   const reports=Array.isArray(a.frame_results)?a.frame_results.slice(0,12):[];
   const individual=reports.length?'<details><summary>'+(language==="de"?"Einzelbild-Auswertung":"Per-frame analysis")+'</summary>'+reports.map((x,i)=>{
     const time=Number.isFinite(Number(x.second))?Number(x.second).toFixed(1)+"s":"";
     return '<article class="frame"><b>#'+safe(x.frame||i+1)+' · '+safe(time)+'</b><p>'+safe([x.description,x.person_status].filter(v=>typeof v==="string").join(" · "))+'</p></article>';
   }).join("")+'</details>':"";
   return '<article class="item"><h3>'+safe(label)+'</h3>'+(url?'<img src="'+safe(url)+'" alt="'+safe(label)+'" loading="lazy" decoding="async">':
   '<p class="empty">'+(language==="de"?"Noch keine zwischengespeicherten Bilder":"No recent frames in memory")+'</p>')+
   '<div class="stats">'+meta(language==="de"?"Aufnahme":"Recorded",formatDate(a.recorded_at))+
   meta(language==="de"?"Modus":"Mode",mode)+
   meta(language==="de"?"Bilder extrahiert":"Extracted",a.frames_extracted??"—")+
   meta(language==="de"?"Bilder analysiert":"Analyzed",a.frames_analyzed??"—")+'</div>'+
   (description?'<p class="summary"><b>Qwen:</b> '+safe(description)+'</p>':"")+individual+'</article>';
  }).join("");
  this.shadowRoot.innerHTML='<style>:host{display:block;margin-top:18px;color:var(--fg,var(--primary-text-color));font:14px Roboto,Arial,sans-serif}*{box-sizing:border-box}.heading{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}.heading h2{font-size:18px;margin:0}.heading p{color:var(--muted,var(--secondary-text-color));line-height:1.5;max-width:700px}button{padding:9px 13px;color:inherit;background:var(--card,var(--card-background-color));border:1px solid var(--border,var(--divider-color));border-radius:9px;cursor:pointer}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,350px),1fr));gap:15px}.item{padding:14px;border-radius:14px;border:1px solid var(--border,var(--divider-color));background:var(--card,var(--card-background-color));min-width:0}.item h3{margin:0 0 12px;font-size:16px}.item img{width:100%;height:auto;aspect-ratio:16/9;object-fit:contain;background:#071525;border-radius:10px}.stats{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:10px 0}.meta{padding:8px;border:1px solid var(--border,var(--divider-color));border-radius:8px;overflow-wrap:anywhere}.meta small{display:block;color:var(--muted,var(--secondary-text-color));font-size:11px}.meta b{font-size:12px}.summary,.frame p{line-height:1.5;overflow-wrap:anywhere}.empty{padding:28px;text-align:center;border:1px dashed var(--border,var(--divider-color));border-radius:9px}.frame{padding:8px 10px;margin:6px 0;border-left:2px solid var(--acc,#38c5ae);background:var(--card2,var(--secondary-background-color));border-radius:7px}</style>'+
  '<section><div class="heading"><div><h2>'+safe(title)+'</h2><p>'+safe(text)+'</p></div><button type="button" data-refresh="1">'+(language==="de"?"Aktualisieren":"Refresh")+'</button></div>'+
  (cards?'<div class="grid">'+cards+'</div>':'<p class="empty">'+(language==="de"?"Keine TAFA Ring-KI-Frames gefunden. Die Diagnose erscheint nach der ersten erfolgreichen Ring-Videoanalyse.":"No TAFA Ring vision frames yet.")+'</p>')+
  '</section>';
 }
}
if(!customElements.get("tafa-ring-vision-diagnostics"))
 customElements.define("tafa-ring-vision-diagnostics",TafaRingVisionDiagnostics);

const subscribers=new WeakMap();
const clearNotice=card=>{
 const item=subscribers.get(card);
 clearTimeout(item?.hideTimer);
 card.shadowRoot?.querySelector("[data-tafa-ring-notice]")?.remove();
};
function showNotice(card,event){
 if(!card?.isConnected||document.hidden)return;
 if(card._hzNight){
   try{const part=globalThis[Symbol.for("tafa-ambient.integration.v1")]?.parts?.ambient;
     if(part?.show?.(card,{title:event.title,topic:"camera",message:"Bewegung erkannt",
       camera:event.camera,seconds:event.seconds,request_id:event.request_id}))return;
   }catch(error){console.debug("TAFA ring ambient info",error);}
 }
 const camera=card.h?.states?.[event.camera],image=proxyPicture(camera);
 clearNotice(card);
 const root=card.shadowRoot;
 if(!root)return;
 const box=document.createElement("section");
 box.dataset.tafaRingNotice="1";
 box.setAttribute("role","status");
 box.style.cssText="position:fixed;z-index:10001;bottom:18px;right:16px;width:min(480px,calc(100vw - 32px));max-height:85vh;overflow:auto;background:var(--card,#18334a);color:var(--fg,#eaf7ff);border:1px solid var(--acc,#65e0cb);border-radius:15px;padding:15px;box-shadow:0 12px 40px #0009;font:14px Roboto,Arial,sans-serif";
 const title=document.createElement("h3");
 title.textContent=String(event.title||"Ring · Bewegung").slice(0,100);
 title.style.margin="0 40px 6px 0";
 const close=document.createElement("button");close.textContent="✕";
 close.type="button";close.setAttribute("aria-label","Close Ring notification");
 close.style.cssText="position:absolute;right:12px;top:12px;color:inherit;background:transparent;border:1px solid #8ba6b277;border-radius:7px;padding:3px 8px;cursor:pointer";
 close.onclick=()=>clearNotice(card);
 const message=document.createElement("p");
 message.textContent="Bewegung erkannt";message.style.margin="0 0 11px";
 box.append(title,close,message);
 if(image){
  const picture=document.createElement("img");picture.src=image;picture.alt="Latest Ring camera snapshot";
  picture.style.cssText="width:100%;max-height:46vh;object-fit:contain;background:#081525;border-radius:9px";
  picture.onerror=()=>picture.remove();
  box.append(picture);
 }
 root.append(box);
 const current=subscribers.get(card);
 if(current)current.hideTimer=setTimeout(()=>clearNotice(card),Math.max(5,Math.min(90,Number(event.seconds)||45))*1000);
}
export function connectRingNotices(card){
 const h=card?.h,conn=h?.connection;
 if(!card?.isConnected||!conn?.subscribeMessage)return;
 const old=subscribers.get(card);
 if(old?.connection===conn)return;
 if(old){try{old.unsubscribe?.();}catch{}clearNotice(card);}
 const state={connection:conn,unsubscribe:null,hideTimer:null};
 subscribers.set(card,state);
 Promise.resolve(conn.subscribeMessage(data=>{
  if(subscribers.get(card)!==state||!data||typeof data!=="object")return;
  if(typeof data.camera!=="string"||!data.camera.startsWith("camera."))return;
  showNotice(card,data);
 },{type:"tablet_assist_for_alexa/ring_notice_subscribe"})).then(stop=>{
  if(subscribers.get(card)!==state)stop?.();else state.unsubscribe=stop;
 }).catch(error=>console.debug("TAFA Ring notices unavailable",error));
}
export function disconnectRingNotices(card){
 const old=subscribers.get(card);if(!old)return;
 subscribers.delete(card);try{old.unsubscribe?.();}catch{}
 clearTimeout(old.hideTimer);
 card.shadowRoot?.querySelector("[data-tafa-ring-notice]")?.remove();
}
