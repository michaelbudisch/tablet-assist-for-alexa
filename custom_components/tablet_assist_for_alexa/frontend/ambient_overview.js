const CSS="\n.hz-ambient-head,.hz-ambient-stage{transition:transform .85s cubic-bezier(.2,.85,.2,1),opacity .7s ease;will-change:transform}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-head{transform:translateY(-10px) scale(.91);transform-origin:50% 0}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-stage{transform:translate3d(0,-13vh,0) scale(.62);opacity:.72;transform-origin:50% 8%}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-foot{opacity:0}\n.hz-overview{position:absolute;inset:clamp(225px,36vh,380px) 12px 12px;z-index:6;\ndisplay:flex;flex-direction:column;box-sizing:border-box;min-height:140px;overflow:hidden;padding:11px 12px;\nbackground:linear-gradient(180deg,#10304ae8,#0a1b34f7 68%,#081728f7);\ncolor:#eff8ff;border:1px solid #77d1ed6a;border-radius:17px;box-shadow:0 22px 50px #030b1ad6,0 0 30px #34d7e329;\nbackdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);\nopacity:0;visibility:hidden;pointer-events:none;transform:translate3d(0,107%,0);\ntransition:transform .85s cubic-bezier(.2,.85,.2,1),opacity .55s ease,visibility 0s linear .85s}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview{opacity:1;visibility:visible;pointer-events:auto;\ntransform:translate3d(0,0,0);transition:transform .85s cubic-bezier(.2,.85,.2,1),opacity .55s ease}\n.hz-ambient-body[data-overview=\"open\"]::after{content:\"\";position:absolute;z-index:4;left:50%;top:26%;\nwidth:min(75vw,540px);aspect-ratio:1;border:1.5px solid #64e5f2;border-radius:50%;pointer-events:none;\nanimation:hz-overview-ripple .85s ease-out both;box-shadow:0 0 16px #47daed}\n@keyframes hz-overview-ripple{0%{opacity:.85;transform:translate(-50%,-50%) scale(.14)}100%{opacity:0;transform:translate(-50%,-50%) scale(1.85)}}\n.hz-overview-weather{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin-bottom:9px}\n.hz-overview-weather>div{background:#24567b60;border:1px solid #9cc9dc26;border-radius:8px;padding:7px 8px;min-width:0}\n.hz-overview-weather small{display:block;color:#98bfd5;font-size:clamp(8px,1vw,11px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n.hz-overview-weather b{display:block;font-size:clamp(11px,1.6vw,17px);font-weight:550;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:3px}\n.hz-overview-head{display:flex;align-items:center;justify-content:space-between;gap:6px;margin:0 2px 8px}\n.hz-overview-month{font-size:clamp(14px,1.8vw,18px);font-weight:600;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n.hz-overview-buttons{display:flex;gap:5px;flex-shrink:0}\n.hz-overview button{border:1px solid #78afc463;background:#1b476688;color:#cdeeff;font:500 12px/1.2 inherit;\nborder-radius:8px;padding:6px 8px;min-height:30px;cursor:pointer}\n.hz-overview button:focus-visible{outline:2px solid #69eeee;outline-offset:2px}\n.hz-overview-weekdays,.hz-overview-days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:3px}\n.hz-overview-weekdays{font-size:10px;letter-spacing:.05em;color:#83afc7;text-align:center;margin-bottom:4px}\n.hz-overview-days{flex:1;min-height:0;grid-template-rows:repeat(4,minmax(0,1fr))}\n.hz-overview-day{box-sizing:border-box;min-width:0;min-height:0;overflow:hidden;border:1px solid #81b7db25;\nborder-radius:6px;background:#122d467b;padding:4px 3px;display:flex;flex-direction:column;gap:3px}\n.hz-overview-day[data-today=\"1\"]{background:#16547cac;border-color:#74e5f0b0}\n.hz-overview-day[data-other=\"1\"]{color:#8faec6;background:#071c3166}\n.hz-overview-num{text-align:center;font-size:clamp(12px,1.7vw,18px);line-height:1.1}\n.hz-overview-day[data-today=\"1\"] .hz-overview-num{font-weight:700;color:#7ee8f2}\n.hz-overview-chip{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:clamp(8px,.95vw,11px);\nline-height:1.22;border-left:2px solid #47d9db;border-radius:2px;background:#1477a344;padding:2px 3px}\n.hz-overview-chip[data-all-day=\"1\"]{border-color:#b8b4ee;background:#746db244}\n.hz-overview-more{font-size:9px;color:#c6dce9}\n.hz-overview-foot{display:flex;align-items:center;gap:5px;margin-top:8px}\n.hz-overview-source{font-size:10px;color:#9cc0d3;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n.hz-overview-config{position:absolute;inset:0;z-index:9;padding:18px;box-sizing:border-box;background:#081a30f8;\ndisplay:grid;align-content:center;gap:11px;overflow:auto}\n.hz-overview-config[hidden]{display:none!important}\n.hz-overview-config h3{font-size:17px;margin:0}\n.hz-overview-config label{display:grid;gap:5px;font-size:12px;color:#c9e3f1}\n.hz-overview-config input{box-sizing:border-box;width:100%;border:1px solid #7ebeda;background:#18364c;color:#fff;padding:9px;border-radius:7px;font:inherit}\n.hz-overview-config p{font-size:11px;color:#9bbacd;margin:0}\n.hz-overview-config-buttons{display:flex;justify-content:flex-end;gap:7px}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-info{z-index:15}\n@media(min-width:900px) and (orientation:landscape){.hz-overview{left:max(12px,calc((100% - 970px)/2));right:max(12px,calc((100% - 970px)/2));top:32vh}}\n@media(max-height:640px){.hz-overview{top:30vh;padding:6px 9px}.hz-overview-weather{margin-bottom:4px}\n.hz-overview-weather>div{padding:3px 6px}.hz-overview-day{padding:2px}.hz-overview-num{font-size:11px}.hz-overview-chip{font-size:8px}}\n@media(prefers-reduced-motion:reduce){.hz-ambient-head,.hz-ambient-stage,.hz-overview{transition:none!important}\n.hz-ambient-body[data-overview=\"open\"]::after{animation:none!important;display:none}}\n";
export function mountOverview(card,s){
  if(s.overview||!s.host)return;
  const host=s.host,style=document.createElement("style");style.textContent=CSS;host.append(style);
  const panel=document.createElement("section");panel.className="hz-overview";
  panel.setAttribute("aria-label","Familienkalender und Hausübersicht");panel.setAttribute("aria-hidden","true");
  panel.innerHTML=`
  <div class="hz-overview-weather">
   <div><small>Wetter</small><b data-ow="weather">—</b></div>
   <div><small>Außen</small><b data-ow="outside">—</b></div>
   <div><small>Solar</small><b data-ow="solar">—</b></div>
   <div><small>Strompreis</small><b data-ow="price">—</b></div></div>
  <div class="hz-overview-head"><span class="hz-overview-month">Familienkalender</span>
   <div class="hz-overview-buttons"><button type="button" data-oa="prev" aria-label="Vorherige vier Wochen">‹</button>
   <button type="button" data-oa="today">Heute</button><button type="button" data-oa="next" aria-label="Nächste vier Wochen">›</button></div></div>
  <div class="hz-overview-weekdays" aria-hidden="true"><span>MO</span><span>DI</span><span>MI</span><span>DO</span><span>FR</span><span>SA</span><span>SO</span></div>
  <div class="hz-overview-days" role="grid" aria-label="Kalender für vier Wochen"></div>
  <div class="hz-overview-foot"><span class="hz-overview-source">Kalender wird geprüft …</span>
  <button type="button" data-oa="config" aria-label="Kalender einstellen">⚙</button>
  <button type="button" data-oa="close">Zur Kugel</button></div>
  <div class="hz-overview-config" hidden><h3>Familienübersicht</h3>
    <label>Familienkalender in Home Assistant (leer = automatisch)
      <input data-setting="calendar" placeholder="calendar.familie" autocomplete="off"></label>
    <label>TAFA-Präsenzsensor (optional)
      <input data-setting="presence" placeholder="binary_sensor.tafa_tablet_praesenz" autocomplete="off"></label>
    <label>Rückkehr nach Sekunden
      <input data-setting="idle" type="number" min="15" max="180" step="5"></label>
    <p>Die Kalender- und Präsenz-Entitäten müssen in Home Assistant vorhanden sein. Auf diesem Bildschirm werden keine Gesichtsbilder verarbeitet.</p>
    <div class="hz-overview-config-buttons"><button type="button" data-oa="cancel">Abbrechen</button>
      <button type="button" data-oa="save">Speichern</button></div></div>`;
  host.append(panel);
  const STORE="tafa.ambient.overview.v1";
  let cfg={calendar:"",presence:"",idle:55},monthOffset=0,events=[],requestedCalendar="",lastFetch=0;
  let ongoing=false,serial=0,opened=false,disposed=false,wasPresent=false,lastTouch=0,lastWeather=0;
  try{
    const obj=JSON.parse(localStorage.getItem(STORE)||"{}");
    if(obj&&typeof obj==="object"){
      if(typeof obj.calendar==="string"&&/^calendar\.[a-z0-9_]+$/.test(obj.calendar))cfg.calendar=obj.calendar;
      if(typeof obj.presence==="string"&&/^(sensor|binary_sensor)\.[a-z0-9_]+$/.test(obj.presence))cfg.presence=obj.presence;
      if(Number.isFinite(Number(obj.idle)))cfg.idle=Math.max(15,Math.min(180,Number(obj.idle)));
    }
  }catch{}
  const q=selector=>panel.querySelector(selector);
  const setStatus=text=>{q(".hz-overview-source").textContent=String(text||"");};
  const calendarId=()=>{
    const states=card.h?.states||{};
    if(cfg.calendar)return states[cfg.calendar]?cfg.calendar:"";
    const ids=Object.keys(states).filter(id=>id.startsWith("calendar."));
    return ids.find(id=>/^calendar\.(familie|family)(?:_|$)/i.test(id))||
      ids.find(id=>/\bfamilie\b|\bfamily\b/i.test(states[id]?.attributes?.friendly_name||""))||"";
  };
  const localDay=()=>{const d=new Date();d.setHours(0,0,0,0);
    d.setDate(d.getDate()-(d.getDay()+6)%7+monthOffset*28);return d;};
  const add=(date,count)=>{const v=new Date(date);v.setDate(v.getDate()+count);return v;};
  const key=d=>[d.getFullYear(),String(d.getMonth()+1).padStart(2,"0"),String(d.getDate()).padStart(2,"0")].join("-");
  const eventDate=obj=>{
    const str=typeof obj==="string"?obj:(obj?.dateTime||obj?.date||"");
    if(!str)return null;
    const d=new Date(/^\d{4}-\d\d-\d\d$/.test(str)?str+"T12:00:00":str);
    return Number.isNaN(d.getTime())?null:d;
  };
  const draw=()=>{
    if(!opened||disposed)return;
    const start=localDay(),end=add(start,27);
    const fmt=d=>d.toLocaleDateString("de-DE",{month:"long",year:"numeric"});
    q(".hz-overview-month").textContent=fmt(start)===fmt(end)?fmt(start):fmt(start)+" – "+fmt(end);
    const grouped=new Map();
    for(const item of events.slice(0,300)){
      const a=eventDate(item.start),b=eventDate(item.end);
      if(!a||!b||b<=a)continue;
      const allDay=typeof item.start==="string"&&/^\d{4}-\d\d-\d\d$/.test(item.start);
      const from=new Date(a);from.setHours(0,0,0,0);
      const until=new Date(b);until.setHours(0,0,0,0);
      if(!allDay&&b>until)until.setDate(until.getDate()+1);
      for(let d=from,c=0;d<until&&c<32;d=add(d,1),c++){
        if(d<start||d>=add(start,28))continue;
        const k=key(d);if(!grouped.has(k))grouped.set(k,[]);
        grouped.get(k).push({title:String(item.summary||"Termin").slice(0,120),allDay,start:a});
      }
    }
    const grid=q(".hz-overview-days");grid.replaceChildren();
    const today=key(new Date());
    for(let i=0;i<28;i++){
      const day=add(start,i),k=key(day),items=(grouped.get(k)||[]).sort((a,b)=>a.start-b.start);
      const cell=document.createElement("div");cell.className="hz-overview-day";cell.setAttribute("role","gridcell");
      cell.dataset.today=k===today?"1":"0";cell.dataset.other=day.getMonth()===start.getMonth()?"0":"1";
      cell.setAttribute("aria-label",day.toLocaleDateString("de-DE",{weekday:"long",day:"numeric",month:"long"}));
      const num=document.createElement("span");num.className="hz-overview-num";num.textContent=String(day.getDate());cell.append(num);
      for(const item of items.slice(0,2)){
        const chip=document.createElement("span");chip.className="hz-overview-chip";chip.dataset.allDay=item.allDay?"1":"0";
        chip.textContent=item.title;chip.title=item.title;cell.append(chip);
      }
      if(items.length>2){const more=document.createElement("span");more.className="hz-overview-more";more.textContent="+"+(items.length-2)+" weitere";cell.append(more);}
      grid.append(cell);
    }
  };
  const load=async(force=false)=>{
    if(!opened||disposed||ongoing)return;
    const id=calendarId(),now=Date.now();
    if(!force&&id===requestedCalendar&&now-lastFetch<300000)return;
    requestedCalendar=id;lastFetch=now;events=[];draw();
    if(!id){setStatus(cfg.calendar?"Kalender-Entität nicht vorhanden":"Google Familienkalender noch nicht mit Home Assistant verbunden");return;}
    if(typeof card.h?.callWS!=="function"){setStatus("Home Assistant nicht verbunden");return;}
    ongoing=true;const ticket=++serial,conn=card.h.connection;
    setStatus("Familienkalender · Lade Termine …");
    try{
      const begin=localDay(),end=add(begin,28);
      const result=await card.h.callWS({
        type:"call_service",domain:"calendar",service:"get_events",
        target:{entity_id:id},service_data:{start_date_time:begin.toISOString(),end_date_time:end.toISOString()},
        return_response:true
      });
      if(disposed||ticket!==serial||conn!==card.h?.connection)return;
      const data=result?.response||result?.service_response||result;
      events=Array.isArray(data?.[id]?.events)?data[id].events:[];
      setStatus((card.h?.states?.[id]?.attributes?.friendly_name||"Familienkalender")+" · "+events.length+" Termine");
      draw();
    }catch(err){
      if(disposed||ticket!==serial)return;
      events=[];setStatus("Kalenderdaten derzeit nicht lesbar");draw();
      console.debug("TAFA Übersicht: Kalenderabruf",String(err?.message||err));
    }finally{if(ticket===serial)ongoing=false;}
  };
  const weather=()=>{
    const h=card.h?.states||{},ids=s.metricIds||[];
    const wxId=Object.keys(h).find(id=>id.startsWith("weather.")&&!["unavailable","unknown"].includes(h[id]?.state));
    const names={sunny:"Sonnig",cloudy:"Bewölkt",partlycloudy:"Wolkig",rainy:"Regen",
      pouring:"Starkregen",snowy:"Schnee",snowy_rainy:"Schneeregen",fog:"Nebel",clear_night:"Klar",windy:"Windig"};
    const values={weather:names[h[wxId]?.state]||"Zuhause",
      outside:ids[2]?String(h[ids[2]]?.state||"—"):"—",
      solar:ids[3]?String(h[ids[3]]?.state||"—"):"—",
      price:ids[1]?String(h[ids[1]]?.state||"—"):"—"};
    for(const [name,value] of Object.entries(values)){
      const node=q('[data-ow="'+name+'"]');
      const index={outside:2,solar:3,price:1}[name];
      const unit=index!==undefined&&ids[index]?String(h[ids[index]]?.attributes?.unit_of_measurement||""):"";
      const txt=value!=="—"&&name!=="weather"?value+(unit?" "+unit:""):value;
      if(node&&node.textContent!==txt)node.textContent=txt;
    }
  };
  const open=()=>{
    if(disposed)return;
    lastTouch=Date.now();
    if(opened)return;
    opened=true;host.dataset.overview="open";panel.setAttribute("aria-hidden","false");
    weather();draw();void load(true);
  };
  const close=()=>{
    if(!opened)return;
    opened=false;host.dataset.overview="closed";panel.setAttribute("aria-hidden","true");
    q(".hz-overview-config").hidden=true;serial++;ongoing=false;events=[];
  };
  const setForm=()=>{
    for(const field of ["calendar","presence","idle"])q('[data-setting="'+field+'"]').value=String(cfg[field]??"");
    q(".hz-overview-config").hidden=false;
  };
  const onClick=event=>{
    if(disposed)return;
    const button=event.target.closest?.("[data-oa]");
    if(button&&panel.contains(button)){
      event.preventDefault();event.stopPropagation();lastTouch=Date.now();
      const act=button.dataset.oa;
      if(act==="close")close();
      if(act==="config")setForm();
      if(act==="cancel")q(".hz-overview-config").hidden=true;
      if(["prev","today","next"].includes(act)){
        monthOffset=act==="today"?0:monthOffset+(act==="prev"?-1:1);
        serial++;ongoing=false;events=[];lastFetch=0;draw();void load(true);
      }
      if(act==="save"){
        const cal=q('[data-setting="calendar"]').value.trim(),presence=q('[data-setting="presence"]').value.trim();
        const idle=Number(q('[data-setting="idle"]').value);
        if(cal&&!/^calendar\.[a-z0-9_]+$/.test(cal))return;
        if(presence&&!/^(binary_sensor|sensor)\.[a-z0-9_]+$/.test(presence))return;
        cfg={calendar:cal,presence,idle:Number.isFinite(idle)?Math.max(15,Math.min(180,idle)):55};
        try{localStorage.setItem(STORE,JSON.stringify(cfg));}catch{}
        serial++;ongoing=false;requestedCalendar="";lastFetch=0;wasPresent=false;q(".hz-overview-config").hidden=true;void load(true);
      }
      return;
    }
    if(panel.contains(event.target)){lastTouch=Date.now();return;}
    if(event.target.closest?.(".hz-ambient-info,.hz-ambient-exit"))return;
    if(!opened&&!s.suppressClick)open();
  };
  host.addEventListener("click",onClick);
  const onPresence=event=>{
    const id=card._tafaLocalVoice?.deviceId||card._tafaLocalVoice?.wake_device_id||card._tafaLocalVoice?.device_id;
    if(id&&event?.detail?.device_id===id&&event?.detail?.active===true)open();
  };
  window.addEventListener("tafa:ambient-presence",onPresence);
  s.overview={
    open,close,
    update(){
      if(disposed)return;
      const states=card.h?.states||{};
      let presenceId=cfg.presence;
      if(!presenceId){
        // Same-device only: derive optional presence entity from this tablet's
        // existing (already authenticated) TAFA Rufwortstatus sensor.
        const status=card._tafaLocalVoice?.status||"";
        const prefix=status.replace(/^sensor\./,"").replace(/_rufwortstatus(?:_\d+)?$/,"");
        if(status&&prefix!==status){
          const aliases=[
            // Auto-unlock family appointments only for an explicitly
            // authenticated face-recognition signal, never generic motion.
            "binary_sensor."+prefix+"_gesicht_erkannt",
            "binary_sensor."+prefix+"_berechtigtes_gesicht",
            "binary_sensor."+prefix+"_recognized_face"
          ];
          presenceId=aliases.find(id=>states[id])||"";
        }
      }
      const state=presenceId?String(states[presenceId]?.state||"").toLowerCase():"";
      const presence=["on","present","detected","home"].includes(state);
      if(presence&&!wasPresent)open();
      wasPresent=presence;
      if(!opened)return;
      const now=Date.now();
      if(s.phase!=="idle"||host.dataset.info==="open")lastTouch=now;
      if(presence)lastTouch=now;
      else if(now-lastTouch>cfg.idle*1000)close();
      if(now-lastWeather>10000){lastWeather=now;weather();}
      if(now-lastFetch>300000&&!ongoing)void load();
    },
    dispose(){
      disposed=true;serial++;host.removeEventListener("click",onClick);
      window.removeEventListener("tafa:ambient-presence",onPresence);
      panel.remove();style.remove();
    }
  };
  host.dataset.overview="closed";
}
