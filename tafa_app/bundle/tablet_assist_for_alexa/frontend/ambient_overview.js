const CSS="\n.hz-ambient-head,.hz-ambient-stage{transition:transform .85s cubic-bezier(.2,.85,.2,1),opacity .7s ease;will-change:transform}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-head{transform:translateY(-10px) scale(.91);transform-origin:50% 0}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-stage{transform:translate3d(0,-13vh,0) scale(.62);opacity:.72;transform-origin:50% 8%}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-foot{opacity:0}\n.hz-overview{position:absolute;inset:clamp(225px,36vh,380px) 12px 12px;z-index:6;\ndisplay:flex;flex-direction:column;box-sizing:border-box;min-height:140px;overflow:hidden;padding:11px 12px;\nbackground:linear-gradient(180deg,#10304ae8,#0a1b34f7 68%,#081728f7);\ncolor:#eff8ff;border:1px solid #77d1ed6a;border-radius:17px;box-shadow:0 22px 50px #030b1ad6,0 0 30px #34d7e329;\nbackdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);\nopacity:0;visibility:hidden;pointer-events:none;transform:translate3d(0,107%,0);\ntransition:transform .85s cubic-bezier(.2,.85,.2,1),opacity .55s ease,visibility 0s linear .85s}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview{opacity:1;visibility:visible;pointer-events:auto;\ntransform:translate3d(0,0,0);transition:transform .85s cubic-bezier(.2,.85,.2,1),opacity .55s ease}\n.hz-ambient-body[data-overview=\"open\"]::after{content:\"\";position:absolute;z-index:4;left:50%;top:26%;\nwidth:min(75vw,540px);aspect-ratio:1;border:1.5px solid #64e5f2;border-radius:50%;pointer-events:none;\nanimation:hz-overview-ripple .85s ease-out both;box-shadow:0 0 16px #47daed}\n@keyframes hz-overview-ripple{0%{opacity:.85;transform:translate(-50%,-50%) scale(.14)}100%{opacity:0;transform:translate(-50%,-50%) scale(1.85)}}\n.hz-overview-weather{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin-bottom:9px}\n.hz-overview-weather>div{background:#24567b60;border:1px solid #9cc9dc26;border-radius:8px;padding:7px 8px;min-width:0}\n.hz-overview-weather small{display:block;color:#98bfd5;font-size:clamp(8px,1vw,11px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n.hz-overview-weather b{display:block;font-size:clamp(11px,1.6vw,17px);font-weight:550;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:3px}\n.hz-overview-head{display:flex;align-items:center;justify-content:space-between;gap:6px;margin:0 2px 8px}\n.hz-overview-month{font-size:clamp(14px,1.8vw,18px);font-weight:600;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n.hz-overview-buttons{display:flex;gap:5px;flex-shrink:0}\n.hz-overview button{border:1px solid #78afc463;background:#1b476688;color:#cdeeff;font:500 12px/1.2 inherit;\nborder-radius:8px;padding:6px 8px;min-height:30px;cursor:pointer}\n.hz-overview button:focus-visible{outline:2px solid #69eeee;outline-offset:2px}\n.hz-overview-weekdays,.hz-overview-days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:3px}\n.hz-overview-weekdays{font-size:10px;letter-spacing:.05em;color:#83afc7;text-align:center;margin-bottom:4px}\n.hz-overview-days{flex:1;min-height:0;grid-template-rows:repeat(4,minmax(0,1fr))}\n.hz-overview-day{box-sizing:border-box;min-width:0;min-height:0;overflow:hidden;border:1px solid #81b7db25;\nborder-radius:6px;background:#122d467b;padding:4px 3px;display:flex;flex-direction:column;gap:3px}\n.hz-overview-day[data-today=\"1\"]{background:#16547cac;border-color:#74e5f0b0}\n.hz-overview-day[data-other=\"1\"]{color:#8faec6;background:#071c3166}\n.hz-overview-num{text-align:center;font-size:clamp(12px,1.7vw,18px);line-height:1.1}\n.hz-overview-day[data-today=\"1\"] .hz-overview-num{font-weight:700;color:#7ee8f2}\n.hz-overview-chip{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:clamp(8px,.95vw,11px);\nline-height:1.22;border-left:2px solid #47d9db;border-radius:2px;background:#1477a344;padding:2px 3px}\n.hz-overview-chip[data-all-day=\"1\"]{border-color:#b8b4ee;background:#746db244}\n.hz-overview-more{font-size:9px;color:#c6dce9}\n.hz-overview-foot{display:flex;align-items:center;gap:5px;margin-top:8px}\n.hz-overview-source{font-size:10px;color:#9cc0d3;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n.hz-overview-config{position:absolute;inset:0;z-index:9;padding:18px;box-sizing:border-box;background:#081a30f8;\ndisplay:grid;align-content:center;gap:11px;overflow:auto}\n.hz-overview-config[hidden]{display:none!important}\n.hz-overview-config h3{font-size:17px;margin:0}\n.hz-overview-config label{display:grid;gap:5px;font-size:12px;color:#c9e3f1}\n.hz-overview-config input{box-sizing:border-box;width:100%;border:1px solid #7ebeda;background:#18364c;color:#fff;padding:9px;border-radius:7px;font:inherit}\n.hz-overview-config p{font-size:11px;color:#9bbacd;margin:0}\n.hz-overview-config-buttons{display:flex;justify-content:flex-end;gap:7px}\n.hz-ambient-body[data-overview=\"open\"] .hz-ambient-info{z-index:15}\n@media(min-width:900px) and (orientation:landscape){.hz-overview{left:max(12px,calc((100% - 970px)/2));right:max(12px,calc((100% - 970px)/2));top:32vh}}\n@media(max-height:640px){.hz-overview{top:30vh;padding:6px 9px}.hz-overview-weather{margin-bottom:4px}\n.hz-overview-weather>div{padding:3px 6px}.hz-overview-day{padding:2px}.hz-overview-num{font-size:11px}.hz-overview-chip{font-size:8px}}\n@media(prefers-reduced-motion:reduce){.hz-ambient-head,.hz-ambient-stage,.hz-overview{transition:none!important}\n.hz-ambient-body[data-overview=\"open\"]::after{animation:none!important;display:none}}\n\n/* 0.4.76: Build the overview from the orb, like TAFA's traced information cards. */\n.hz-overview{isolation:isolate;box-shadow:0 23px 52px #030b1bd3,0 0 36px #39dfee18,inset 0 1px #aff6ff18}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview{\n animation:hz-overview-construct 1.15s cubic-bezier(.17,.78,.2,1) .2s both;\n transition:none;will-change:transform,opacity\n}\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview{\n visibility:visible;pointer-events:none;animation:hz-overview-unbuild .69s cubic-bezier(.52,0,.8,.37) both;\n transition:none\n}\n@keyframes hz-overview-construct{\n 0%{opacity:0;filter:blur(5px);clip-path:inset(0 0 100% 0 round 17px);transform:translate3d(0,38px,0) scale(.97)}\n 17%{opacity:.93;filter:blur(0);clip-path:inset(0 0 95% 0 round 17px);transform:translate3d(0,28px,0) scale(.985)}\n 46%{opacity:1;clip-path:inset(0 0 48% 0 round 17px);transform:translate3d(0,13px,0) scale(.994)}\n 79%{opacity:1;clip-path:inset(0 0 6% 0 round 17px);transform:translate3d(0,2px,0) scale(.999)}\n 100%{opacity:1;filter:none;clip-path:inset(0 0 0 0 round 17px);transform:translate3d(0,0,0) scale(1)}\n}\n@keyframes hz-overview-unbuild{\n 0%{opacity:1;clip-path:inset(0 0 0 0 round 17px);transform:translate3d(0,0,0)}\n 48%{opacity:.9;clip-path:inset(0 0 45% 0 round 17px);transform:translate3d(0,15px,0)}\n 88%{opacity:.65;clip-path:inset(0 0 91% 0 round 17px);transform:translate3d(0,36px,0)}\n 100%{opacity:0;clip-path:inset(0 0 100% 0 round 17px);transform:translate3d(0,47px,0)}\n}\n/* An actual travelling light streak draws the panel border in four sections. */\n.hz-overview-edge{position:absolute;inset:0;z-index:8;pointer-events:none;border-radius:inherit}\n.hz-overview-edge i{position:absolute;display:block;background:#9ff7ffed;\n box-shadow:0 0 5px #b1f8ff,0 0 14px #58e8ff99,0 0 24px #31e6ee50}\n.hz-overview-edge .edge-n{left:16px;right:16px;top:0;height:1px;transform-origin:left}\n.hz-overview-edge .edge-e{right:0;top:16px;bottom:16px;width:1px;transform-origin:top}\n.hz-overview-edge .edge-s{bottom:0;right:16px;left:16px;height:1px;transform-origin:right}\n.hz-overview-edge .edge-w{left:0;top:16px;bottom:16px;width:1px;transform-origin:bottom}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-edge .edge-n{animation:hz-overview-trace-x .4s ease .42s both}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-edge .edge-e{animation:hz-overview-trace-y .33s ease .79s both}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-edge .edge-s{animation:hz-overview-trace-x .37s ease 1.08s both}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-edge .edge-w{animation:hz-overview-trace-y .3s ease 1.4s both}\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-edge{opacity:0;transition:opacity .22s ease}\n@keyframes hz-overview-trace-x{from{opacity:0;transform:scaleX(0)}12%{opacity:1}to{opacity:.46;transform:scaleX(1)}}\n@keyframes hz-overview-trace-y{from{opacity:0;transform:scaleY(0)}12%{opacity:1}to{opacity:.46;transform:scaleY(1)}}\n.hz-overview-scan{position:absolute;inset:0;z-index:5;pointer-events:none;border-radius:inherit;\n background:linear-gradient(180deg,transparent 0%,#53e6fc00 44%,#8af8ff33 49%,#d3feff99 50%,#5dcdf933 51%,transparent 58%);\n opacity:0;transform:translate3d(0,-112%,0)}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-scan{animation:hz-overview-grid-scan 1.15s ease-out .43s both}\n@keyframes hz-overview-grid-scan{0%{opacity:0;transform:translate3d(0,-115%,0)}15%{opacity:1}75%{opacity:.6}100%{opacity:0;transform:translate3d(0,116%,0)}}\n/* Interior elements have separate arrival times instead of appearing as one finished rectangle. */\n.hz-overview[data-intro=\"1\"] .hz-overview-weather>div{animation:hz-overview-tile-rise .38s cubic-bezier(.2,.8,.2,1) both}\n.hz-overview[data-intro=\"1\"] .hz-overview-weather>div:nth-child(1){animation-delay:.66s}\n.hz-overview[data-intro=\"1\"] .hz-overview-weather>div:nth-child(2){animation-delay:.76s}\n.hz-overview[data-intro=\"1\"] .hz-overview-weather>div:nth-child(3){animation-delay:.86s}\n.hz-overview[data-intro=\"1\"] .hz-overview-weather>div:nth-child(4){animation-delay:.96s}\n.hz-overview[data-intro=\"1\"] .hz-overview-head{animation:hz-overview-tile-rise .37s ease .89s both}\n.hz-overview[data-intro=\"1\"] .hz-overview-weekdays{animation:hz-overview-tile-rise .32s ease 1.02s both}\n.hz-overview[data-intro=\"1\"] .hz-overview-day{animation:hz-overview-cell-in .31s cubic-bezier(.13,.79,.23,1.0) var(--hz-enter-delay,1.12s) both}\n.hz-overview[data-intro=\"1\"] .hz-overview-chip{animation:hz-overview-chip-in .3s ease var(--hz-event-delay,1.55s) both}\n.hz-overview[data-intro=\"1\"] .hz-overview-foot{animation:hz-overview-tile-rise .34s ease 1.61s both}\n@keyframes hz-overview-tile-rise{from{opacity:0;transform:translate3d(0,9px,0);filter:brightness(1.9)}to{opacity:1;transform:translate3d(0,0,0);filter:brightness(1)}}\n@keyframes hz-overview-cell-in{\n from{opacity:0;transform:translate3d(0,11px,0) scale(.97);border-color:#aef9ffb8}\n 62%{opacity:1;transform:translate3d(0,0,0) scale(1);border-color:#79e2ee88}\n to{opacity:1;transform:translate3d(0,0,0) scale(1)}\n}\n@keyframes hz-overview-chip-in{from{opacity:0;clip-path:inset(0 100% 0 0)}25%{opacity:1}to{opacity:1;clip-path:inset(0 0 0 0)}}\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-weather,\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-head,\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-weekdays,\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-days,\n.hz-ambient-body[data-overview=\"closing\"] .hz-overview-foot{animation:hz-overview-content-out .24s ease both}\n@keyframes hz-overview-content-out{from{opacity:1;transform:translateY(0)}to{opacity:0;transform:translateY(-8px)}}\n.hz-overview-beam{position:absolute;inset:0;width:100%;height:100%;z-index:7;pointer-events:none;\n overflow:visible;opacity:0;will-change:opacity}\n.hz-overview-beam path{fill:none;stroke:#73f4ff;stroke-width:1.6;\n filter:drop-shadow(0 0 5px #73f8ff);stroke-linecap:round}\n.hz-overview-beam circle{fill:#defbff;filter:drop-shadow(0 0 8px #5ce8fe)}\n.hz-overview-bloom{position:absolute;z-index:4;left:50%;top:29%;width:180px;height:180px;\n border-radius:50%;pointer-events:none;opacity:0;transform:translate(-50%,-50%) scale(.25);\n background:radial-gradient(circle,#61faee4d 0%,#28f1e92b 23%,#0b9e9e00 66%);\n box-shadow:0 0 0 1px #86faff50,0 0 40px #55f5e638}\n.hz-ambient-body[data-overview=\"open\"] .hz-overview-bloom{\n animation:hz-overview-bloom 1.05s cubic-bezier(.14,.9,.23,1) both}\n@keyframes hz-overview-bloom{\n 0%{opacity:0;transform:translate(-50%,-50%) scale(.18)}\n 20%{opacity:.85}\n 66%{opacity:.55;transform:translate(-50%,-50%) scale(2)}\n 100%{opacity:0;transform:translate(-50%,-50%) scale(2.7)}\n}\n/* Reduced motion still gives an instantly usable family calendar. */\n@media(prefers-reduced-motion:reduce){\n .hz-ambient-body[data-overview=\"open\"] .hz-overview,\n .hz-ambient-body[data-overview=\"closing\"] .hz-overview,\n .hz-overview[data-intro=\"1\"] .hz-overview-weather>div,\n .hz-overview[data-intro=\"1\"] .hz-overview-head,\n .hz-overview[data-intro=\"1\"] .hz-overview-weekdays,\n .hz-overview[data-intro=\"1\"] .hz-overview-day,\n .hz-overview[data-intro=\"1\"] .hz-overview-chip,\n .hz-overview[data-intro=\"1\"] .hz-overview-foot,\n .hz-ambient-body[data-overview=\"open\"] .hz-overview-edge i,\n .hz-ambient-body[data-overview=\"open\"] .hz-overview-bloom,\n .hz-ambient-body[data-overview=\"open\"] .hz-overview-scan{animation:none!important}\n .hz-ambient-body[data-overview=\"open\"] .hz-overview{opacity:1;clip-path:none;transform:none;visibility:visible}\n .hz-overview-edge,.hz-overview-beam,.hz-overview-bloom,.hz-overview-scan{display:none!important}\n}\n";
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
  // Visual trace elements are independent of HA events and Android audio.
  const edge=document.createElement("div");
  edge.className="hz-overview-edge";edge.setAttribute("aria-hidden","true");
  edge.innerHTML='<i class="edge-n"></i><i class="edge-e"></i><i class="edge-s"></i><i class="edge-w"></i>';
  const scan=document.createElement("div");
  scan.className="hz-overview-scan";scan.setAttribute("aria-hidden","true");
  panel.append(edge,scan);
  const bloom=document.createElement("div");bloom.className="hz-overview-bloom";bloom.setAttribute("aria-hidden","true");
  const SVGNS="http://www.w3.org/2000/svg";
  const beam=document.createElementNS(SVGNS,"svg");beam.setAttribute("class","hz-overview-beam");
  beam.setAttribute("aria-hidden","true");
  const ray=document.createElementNS(SVGNS,"path");
  const spark=document.createElementNS(SVGNS,"circle");
  spark.setAttribute("r","3.25");beam.append(ray,spark);
  host.append(bloom,beam,panel);
  const STORE="tafa.ambient.overview.v1";
  let cfg={calendar:"",presence:"",idle:55},monthOffset=0,events=[],requestedCalendar="",lastFetch=0;
  let ongoing=false,serial=0,opened=false,disposed=false,wasPresent=false,lastTouch=0,lastWeather=0;
  let revealTimer=null,collapseTimer=null,beamFrame=null,beamToken=0;
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
      cell.style.setProperty("--hz-enter-delay",String(1030+Math.floor(i/7)*125+(i%7)*25)+"ms");
      cell.style.setProperty("--hz-event-delay",String(1360+Math.floor(i/7)*125+(i%7)*25)+"ms");
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
  const playBeam=()=>{
    // One short-lived curve extracts the panel from the sphere. No render loop
    // remains active after the entrance animation.
    const reduced=typeof matchMedia==="function"&&matchMedia("(prefers-reduced-motion: reduce)").matches;
    if(reduced)return;
    const token=++beamToken;
    if(beamFrame!=null)cancelAnimationFrame(beamFrame);
    const hostRect=host.getBoundingClientRect();
    const sphere=s.canvas?.getBoundingClientRect();
    const destination=panel.getBoundingClientRect();
    if(!sphere||!hostRect.width||!hostRect.height)return;
    const sx=sphere.left+sphere.width*.52-hostRect.left;
    const sy=sphere.top+sphere.height*.48-hostRect.top;
    const tx=destination.left+destination.width*.5-hostRect.left;
    const ty=destination.top-hostRect.top+2;
    const cx=(sx+tx)/2+(tx-sx)*.08;
    const cy=(sy+ty)/2-28;
    beam.setAttribute("viewBox","0 0 "+hostRect.width+" "+hostRect.height);
    ray.setAttribute("d","M "+sx+" "+sy+" Q "+cx+" "+cy+" "+tx+" "+ty);
    const length=ray.getTotalLength();
    beam.style.opacity="1";
    const started=performance.now(),duration=710,delay=120;
    const ease=t=>1-Math.pow(1-t,3);
    const frame=t=>{
      if(disposed||!opened||token!==beamToken)return;
      const progress=Math.max(0,Math.min(1,(t-started-delay)/duration));
      const traveled=length*ease(progress);
      const point=ray.getPointAtLength(traveled);
      ray.setAttribute("stroke-dasharray",String(Math.max(1,traveled))+" "+String(length+5));
      ray.setAttribute("stroke-dashoffset","0");
      ray.style.opacity=String(Math.min(1,progress*5)*Math.min(1,(1-progress)*3));
      spark.setAttribute("cx",String(point.x));spark.setAttribute("cy",String(point.y));
      spark.style.opacity=String(Math.min(1,progress*8)*Math.min(1,(1-progress)*5));
      if(progress<1)beamFrame=requestAnimationFrame(frame);
      else{beamFrame=null;beam.style.opacity="0";}
    };
    beamFrame=requestAnimationFrame(frame);
  };
  const open=()=>{
    if(disposed)return;
    lastTouch=Date.now();
    if(opened)return;
    clearTimeout(collapseTimer);clearTimeout(revealTimer);
    beamToken++;if(beamFrame!=null)cancelAnimationFrame(beamFrame);
    panel.dataset.intro="1";
    opened=true;host.dataset.overview="open";panel.setAttribute("aria-hidden","false");
    weather();draw();void load(true);
    requestAnimationFrame(()=>{if(opened&&!disposed)playBeam();});
    revealTimer=setTimeout(()=>{if(!disposed)panel.dataset.intro="0";},2250);
  };
  const close=()=>{
    if(!opened)return;
    opened=false;clearTimeout(revealTimer);clearTimeout(collapseTimer);
    beamToken++;if(beamFrame!=null)cancelAnimationFrame(beamFrame);
    beamFrame=null;beam.style.opacity="0";panel.dataset.intro="0";
    host.dataset.overview="closing";panel.setAttribute("aria-hidden","true");
    collapseTimer=setTimeout(()=>{
      if(!disposed&&!opened)host.dataset.overview="closed";
    },720);
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
      disposed=true;serial++;beamToken++;
      clearTimeout(revealTimer);clearTimeout(collapseTimer);
      if(beamFrame!=null)cancelAnimationFrame(beamFrame);
      host.removeEventListener("click",onClick);
      window.removeEventListener("tafa:ambient-presence",onPresence);
      panel.remove();beam.remove();bloom.remove();style.remove();
    }
  };
  host.dataset.overview="closed";
}
