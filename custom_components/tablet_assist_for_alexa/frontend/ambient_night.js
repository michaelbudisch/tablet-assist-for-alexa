/* TAFA dashboard asset version 0.4.55 - cache-busted file delivery; existing code preserved */
(function ambientModule(){
  "use strict";
  const bag=globalThis[Symbol.for("tafa-ambient.integration.v1")]??={parts:Object.create(null)};
  const active=new WeakMap();
  const metrics=[
    {name:"NETZ",ids:["sensor.tibber_pulse_0100100700ff"],pattern:/tibber.*pulse|netz.*leistung|grid.*power|wirkleistung aktuell/i},
    {name:"STROMPREIS",ids:["sensor.hauptstr_23a_aktueller_strompreis"],pattern:/aktueller.*strompreis|electricity.*price|strompreis/i},
    {name:"AUßEN",ids:[],pattern:/au.ss.en.*temperatur|aussentemperatur|outside.*temp|outdoor.*temp/i},
    {name:"SOLAR",ids:[],pattern:/pv.*leistung|solar.*power|solar.*leistung|photovoltaik.*leistung/i},
    {name:"WÄRMEPUMPE",ids:[],pattern:/w.rmepumpe.*(speicher.*temp|temperatur)|warmwasser.*(temp|speicher)/i},
    {name:"HEIZÖL",ids:[],pattern:/heiz.l.*(bestand|rest|liter|tank)/i}
  ];
  const style=`
  .wrap.hz-night-view {--ambient:#9fcef4;background:#07111d!important;color:#eff5ff!important;display:block!important;grid-template-columns:none!important;grid-template-rows:none!important;min-width:0!important;width:100%!important;max-width:none!important;margin:0!important;padding:0!important;overflow:hidden!important}
  .wrap.hz-night-view>aside{display:none!important;visibility:hidden!important;width:0!important}
  .wrap.hz-night-view>main {display:block!important;position:relative!important;grid-column:auto!important;min-width:0!important;width:100%!important;max-width:none!important;min-height:100%!important;left:auto!important;right:auto!important;margin:0!important;padding:0!important;box-sizing:border-box!important;background:#07111d!important;overflow-x:hidden!important;overflow-y:auto}
  .hz-night-view .top {position:absolute!important;z-index:12;top:0;right:0;left:0;margin:0!important;padding:14px 20px!important;background:transparent!important;border:0!important;box-shadow:none!important;pointer-events:none}
  .hz-night-view .top>div:first-child,.hz-night-view .hz-header-clock,.hz-night-view .hz-subnav{display:none!important}
  .hz-night-view .top .hz-header-right,.hz-night-view .top .hz-header-actions{pointer-events:auto}
  .hz-night-view .top .hz-header-button {background:#132a3d88!important;color:#a9c8e4!important;border:1px solid #9fd1fa32!important;backdrop-filter:blur(6px)}
  /* Night mode is intentionally minimal on desktop and Android alike. */
  .wrap.hz-night-view>main>header:not(.hz-ambient-head){display:none!important}
  .wrap.hz-night-view .top,.wrap.hz-night-view .hz-header-actions{display:none!important}
  .wrap.hz-night-view>main>header>div:first-child,.wrap.hz-night-view>main>header .header-clock{display:none!important}
  .wrap.hz-night-view>main>header .quick{background:#132a3dbb!important;color:#b9d8f2!important;border:1px solid #9fd1fa32!important;backdrop-filter:blur(6px)}
  .wrap.hz-night-view .body{max-width:none!important;min-width:0!important;margin:0!important;width:100%!important}
  .wrap.hz-night-view .subnav,.wrap.hz-night-view .native,.wrap.hz-night-view .native-details{display:none!important}
  .hz-ambient-body {margin:0!important;padding:0 12px!important;width:100%!important;min-width:0!important;max-width:none!important;box-sizing:border-box!important;position:relative;isolation:isolate;display:flex;flex-direction:column;align-items:center;min-height:var(--hz-available-height,100dvh);overflow:hidden;background:radial-gradient(ellipse at 50% 48%,#14213c 0%,#0a1425 43%,#070e1b 84%);color:#edf5ff;font:inherit}
  /* Tablet WebViews: escape Home Assistant's responsive grid/card width entirely. */
  .hz-ambient-body[data-tablet="1"]{position:fixed!important;inset:0!important;top:0!important;left:0!important;right:0!important;bottom:0!important;z-index:2147483000!important;width:100vw!important;height:100vh!important;min-height:100vh!important;max-width:none!important;margin:0!important;padding:0 8px!important;overflow:hidden!important;box-sizing:border-box!important;transform:none!important}
  .hz-ambient-body[data-tablet="1"] .hz-ambient-stage{width:100%!important;max-width:680px!important;min-width:0!important;min-height:180px!important;max-height:60vh!important;height:48vh!important;flex:1 1 auto!important}
  .hz-ambient-body[data-tablet="1"] .hz-ambient-head{margin-top:clamp(48px,9vh,80px)!important}
  .hz-ambient-body[data-tablet="1"] .hz-ambient-time{font-size:clamp(56px,10vw,90px)!important}
  /* The day button is reveal-on-tap, not part of the permanent ambient display. */
  .hz-ambient-exit{display:inline-flex;position:absolute;top:12px;right:12px;z-index:30;border:1px solid #89bbe066;background:#152a3cbf;color:#d1e9ff;padding:9px 11px;border-radius:12px;font:500 13px/1.25 inherit;cursor:pointer;opacity:0;visibility:hidden;pointer-events:none;transform:translateY(-6px);transition:opacity .24s ease,transform .24s ease,visibility 0s linear .24s}
  .hz-ambient-body[data-controls="visible"] .hz-ambient-exit{opacity:1;visibility:visible;pointer-events:auto;transform:translateY(0);transition:opacity .24s ease,transform .24s ease,visibility 0s}
  .hz-ambient-body:before{content:"";position:absolute;inset:0;z-index:-1;opacity:.38;pointer-events:none;background:radial-gradient(circle at 22% 22%,#284d7644 0,transparent 28%),radial-gradient(circle at 76% 78%,#102a4d55 0,transparent 30%)}
  .hz-ambient-head{position:relative;z-index:2;margin-top:clamp(52px,8vh,96px);text-align:center}
  .hz-ambient-time{font-size:clamp(62px,10.4vw,116px);font-weight:300;letter-spacing:-.063em;font-variant-numeric:tabular-nums;line-height:1.04;text-shadow:0 0 26px #9dcaf723}
  .hz-ambient-date{margin-top:8px;color:#9db1c6;font-size:clamp(13px,1.55vw,17px);font-weight:400;letter-spacing:.025em}
  .hz-ambient-stage{width:min(100%,750px);height:clamp(280px,50dvh,590px);position:relative;flex:1 0 auto;max-height:62dvh;min-height:280px;margin:clamp(0px,2vh,20px) auto 14px;box-sizing:border-box}
  .hz-ambient-canvas{display:block;width:100%;height:100%;max-width:100%;pointer-events:auto;touch-action:none;-webkit-touch-callout:none;user-select:none;-webkit-user-select:none;cursor:grab}
  .hz-ambient-canvas.hz-manual-dragging{cursor:grabbing}
  .hz-ambient-metric{position:absolute;z-index:2;left:50%;top:50%;transform:translate(-50%,-50%);width:max-content;max-width:150px;min-width:0;text-align:center;font-variant-numeric:tabular-nums;white-space:nowrap;pointer-events:none;text-shadow:0 1px 5px #051220;opacity:0;will-change:left,top,opacity,transform}
  .hz-ambient-metric small{display:block;color:#8ca8c3;letter-spacing:.12em;font-size:clamp(8px,.85vw,10px);margin-bottom:4px}
  .hz-ambient-metric b{display:block;font-weight:500;font-size:clamp(11px,1.15vw,15px);color:#e4f1ff}
  .hz-ambient-metric i{position:absolute;top:50%;width:20px;height:1px;background:#7da6cb77}
  /* Position of sensor 1: derived from 3D projected node. */
  /* Position of sensor 2: derived from 3D projected node. */
  /* Position of sensor 3: derived from 3D projected node. */
  /* Position of sensor 4: derived from 3D projected node. */
  /* Position of sensor 5: derived from 3D projected node. */
  /* Position of sensor 6: derived from 3D projected node. */
  .hz-ambient-foot{z-index:3;display:flex;align-items:center;justify-content:center;min-height:39px;gap:9px;margin-bottom:12px;color:#8197b0;font-size:12px;letter-spacing:.07em}
  .hz-ambient-indicator{display:inline-block;width:7px;height:7px;border-radius:50%;background:#7f9bb5;box-shadow:0 0 9px #7f9bb545}
  .hz-ambient-body[data-phase="listening"] .hz-ambient-indicator{background:#3ce4ed;box-shadow:0 0 12px #3ce4ed}
  .hz-ambient-body[data-phase="processing"] .hz-ambient-indicator{background:#b6a2ff;box-shadow:0 0 12px #b6a2ff}
  .hz-ambient-body[data-phase="speaking"] .hz-ambient-indicator{background:#f3d6ff;box-shadow:0 0 12px #f3d6ff}
  .hz-ambient-info{position:absolute;z-index:4;left:50%;bottom:clamp(12px,3vh,30px);width:min(740px,calc(100% - 32px));margin:0;background:linear-gradient(125deg,#173050e8,#0a233ddf);border:1px solid #61a9d18c;box-shadow:0 13px 45px #020d20a0,0 0 28px #3b9cbe20,inset 0 1px #b8ddf33c;border-radius:17px;backdrop-filter:blur(14px);padding:16px 20px 18px;max-height:33vh;overflow:auto;animation:hz-ambient-enter .38s cubic-bezier(.18,.85,.32,1.08) both}
  .hz-ambient-info[hidden]{display:none!important}
  .hz-ambient-body[data-info="open"] .hz-ambient-foot{opacity:0}
  .hz-ambient-info-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}
  .hz-ambient-info-kicker{font:600 10px/1.3 inherit;letter-spacing:.14em;color:#63dbeb}
  .hz-ambient-info-title{font-size:clamp(17px,2.1vw,24px);font-weight:500;color:#ecf5ff;margin:6px 0 8px}
  .hz-ambient-info-message{font-size:clamp(13px,1.5vw,16px);line-height:1.45;color:#c5dcef;overflow-wrap:anywhere;white-space:pre-wrap}
  .hz-ambient-info-x{font:inherit;color:#b8d0e6;background:#284c674a;border:1px solid #7ca9c43b;border-radius:8px;padding:5px 9px;cursor:pointer}
  .hz-ambient-items{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:7px;margin-top:11px}
  .hz-ambient-item{border:1px solid #8aadd134;background:#0a213956;border-radius:10px;padding:7px 9px;min-width:0;font-size:12px;color:#cde2f3;overflow-wrap:anywhere}
  .hz-ambient-item b{color:#fff;font-weight:500}
  @keyframes hz-ambient-enter{from{opacity:0;transform:translate(-50%,28px) scale(.97)}to{opacity:1;transform:translate(-50%,0) scale(1)}}
  @media(max-width:800px){.hz-ambient-head{margin-top:72px}.hz-ambient-stage{width:100%;max-width:610px;height:clamp(270px,49dvh,570px);min-height:270px}.hz-ambient-time{font-size:clamp(60px,11vw,96px)}.hz-ambient-metric small{font-size:9px}.hz-ambient-metric b{font-size:12px}}
  @media(max-width:500px){.hz-ambient-body{padding:0 6px!important}.hz-ambient-head{margin-top:68px}.hz-ambient-stage{width:100%;min-height:280px;height:45dvh}.hz-ambient-time{font-size:clamp(56px,13vw,82px)}.hz-ambient-metric small{font-size:8px;letter-spacing:.06em}.hz-ambient-metric b{font-size:11px}}
  @media(prefers-reduced-motion:reduce){.hz-ambient-info{animation:none}}
  `;
  const safe=(s)=>String(s??"").replace(/[&<>"']/g,a=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[a]));
  const isValid=v=>v&&!["unknown","unavailable","none",""].includes(String(v.state).toLowerCase());
  const fmt=(entity)=>{
    if(!isValid(entity))return "—";
    const n=Number(entity.state),unit=String(entity.attributes?.unit_of_measurement||"");
    return (Number.isFinite(n)&&String(entity.state).trim()!==""?new Intl.NumberFormat("de-DE",{maximumFractionDigits:unit==="W"?0:1}).format(n):String(entity.state).slice(0,24))+(unit?" "+unit:"");
  };
  const choose=(states,entry)=>{
    for(const id of entry.ids)if(isValid(states[id]))return id;
    const ids=Object.keys(states);
    return ids.find(id=>id.startsWith("sensor.")&&entry.pattern.test(id+" "+(states[id]?.attributes?.friendly_name||""))&&isValid(states[id]))||null;
  };
  function body(){
    return `<style>${style}</style><section class="hz-ambient-body" data-tablet="${typeof navigator!=="undefined"&&(/Android/i.test(navigator.userAgent)||(typeof matchMedia==="function"&&matchMedia("(pointer:coarse)").matches&&window.innerWidth<=1300))?"1":"0"}" data-phase="idle" data-controls="hidden" tabindex="0" aria-label="TAFA Ambient Nachtansicht">
      <button type="button" class="hz-ambient-exit" data-hz-header="night" aria-label="Tagesansicht öffnen">☀ Tagesansicht</button><header class="hz-ambient-head"><div id="hz-night-clock" class="hz-ambient-time">--:--</div><div id="hz-night-date" class="hz-ambient-date"></div></header>
      <div class="hz-ambient-stage"><canvas class="hz-ambient-canvas" aria-label="Animierte, vernetzte Kugel"></canvas>
      ${metrics.map((m,i)=>`<div class="hz-ambient-metric" data-ambient-metric="${i}"><small>${safe(m.name)}</small><b>—</b></div>`).join("")}</div>
      <div class="hz-ambient-foot"><span class="hz-ambient-indicator"></span><span data-ambient-state>TAFA · Bereit</span></div>
      <section class="hz-ambient-info" data-ambient-info hidden aria-live="polite"></section>
    </section>`;
  }
  function resolvePhase(card,s){
    const h=card.h?.states||{};
    const wake=String(h["sensor.tafa_jarvis_tablet_rufwortstatus"]?.state||"").toLowerCase();
    const mic=String(h["sensor.tafa_jarvis_tablet_mikrofonstatus"]?.state||"").toLowerCase();
    const voice=card._jarvisIntegratedVoice;
    if(voice?.playing)return "speaking";
    if(voice?.processing)return "processing";
    if(voice?.info)return "listening";
    // A permanently armed native wakeword detector reports "listening: hey_jarvis".
    // That is standby, NOT active Assist capture: keep the sphere quiet.
    if(/^native_(?:waiting_for_playback|playing|speaking)/.test(wake)||/^(?:speaking|playing|tts)$/.test(mic))return "speaking";
    if(/^native_(?:processing|thinking|generating_voice|transcribing|sending_audio|waiting_for_stt|authenticating|connected)/.test(wake)||/^(?:processing|thinking|busy)$/.test(mic))return "processing";
    if(/^(?:detected(?::|$)|native_(?:connecting|followup|starting_microphone|listening))/.test(wake)||mic==="assist")return "listening";
    const last=h["sensor.tafa_jarvis_tablet_letztes_rufwort"]?.state;
    const ms=Date.now()-Date.parse(last||"");
    if(Number.isFinite(ms)&&ms>=0&&ms<2000)return "listening";
    if(s.forceUntil>Date.now())return s.forcedPhase;
    return "idle";
  }
  function update(card){
    const s=active.get(card);if(!s)return;
    const h=card.h?.states||{},stage=s.host;
    if(!stage?.isConnected)return;
    const time=new Date(),clock=stage.querySelector("#hz-night-clock"),date=stage.querySelector("#hz-night-date");
    if(clock)clock.textContent=time.toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"});
    if(date)date.textContent=time.toLocaleDateString("de-DE",{weekday:"long",day:"numeric",month:"long"});
    for(let i=0;i<metrics.length;i++){
      const node=stage.querySelector(`[data-ambient-metric="${i}"] b`);
      if(!node)continue;
      const id=choose(h,metrics[i]);const str=fmt(id?h[id]:null);
      if(node.textContent!==str)node.textContent=str;
    }
    s.phase=resolvePhase(card,s);
    stage.dataset.phase=s.phase;
    const label=stage.querySelector("[data-ambient-state]");
    const labels={idle:"TAFA · Bereit",listening:"TAFA · Ich höre zu",processing:"TAFA · Verarbeite Anfrage",speaking:"TAFA · Antwort"};
    if(label)label.textContent=labels[s.phase];
    stage.querySelector(".hz-ambient-indicator")?.setAttribute("title",s.phase);
  }
  function close(card){
    const s=active.get(card);if(!s)return;
    clearTimeout(s.infoTimer);
    const info=s.host?.querySelector("[data-ambient-info]");
    if(info){info.hidden=true;info.replaceChildren();s.host.dataset.info="closed";}
  }
  function show(card,input){
    const s=active.get(card);if(!s||!card._hzNight)return false;
    const data=input&&typeof input==="object"?input:{message:String(input??"")};
    const title=String(data.title||data.topic||"TAFA Antwort").slice(0,120);
    const message=String(data.message??data.reply??data.answer??"").slice(0,2500);
    const info=s.host.querySelector("[data-ambient-info]");if(!info)return false;
    info.replaceChildren();
    const head=document.createElement("div");head.className="hz-ambient-info-head";
    const left=document.createElement("div"),kick=document.createElement("div"),h=document.createElement("div");
    kick.className="hz-ambient-info-kicker";kick.textContent="TAFA / "+(data.topic==="search"?"INTERNETSUCHE":"ASSIST");
    h.className="hz-ambient-info-title";h.textContent=title;left.append(kick,h);
    const x=document.createElement("button");x.type="button";x.className="hz-ambient-info-x";x.textContent="✕";x.setAttribute("aria-label","Infobox schließen");x.onclick=()=>close(card);
    head.append(left,x);info.append(head);
    if(message){const p=document.createElement("div");p.className="hz-ambient-info-message";p.textContent=message;info.append(p);}
    const list=[];
    if(Array.isArray(data.results))for(const result of data.results.slice(0,5)){
      const text=typeof result==="string"?result:result?.title||result?.name||result?.snippet;
      if(text)list.push(String(text).slice(0,220));
    }
    if(data.sources&&typeof data.sources==="object")for(const [key,id] of Object.entries(data.sources).slice(0,6)){
      if(typeof id==="string"&&card.h?.states?.[id])list.push(key+": "+fmt(card.h.states[id]));
    }
    if(data.camera&&typeof data.camera==="string")list.push("Kamera: "+data.camera.replace(/^camera\./,"").replace(/_/g," "));
    if(list.length){const items=document.createElement("div");items.className="hz-ambient-items";for(const value of list){const el=document.createElement("div");el.className="hz-ambient-item";el.textContent=value;items.append(el);}info.append(items);}
    info.hidden=false;s.host.dataset.info="open";info.style.animation="none";void info.offsetWidth;info.style.animation="";
    clearTimeout(s.infoTimer);
    const seconds=Math.max(8,Math.min(180,Number(data.seconds)||30));
    s.infoTimer=setTimeout(()=>close(card),seconds*1000);
    s.forcedPhase="speaking";s.forceUntil=Date.now()+7000;
    update(card);
    return true;
  }
  function makeMesh(){
  let seed=0x3c6ef372;
  const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  const points=[];
  const count=96,angle=2.399963229728653;
  for(let i=0;i<count;i++){
    const z=i<74?1-2*(i+.5)/74:(random()*2-1);
    const az=i<74?i*angle+(random()-.5)*.53:random()*Math.PI*2;
    const r=Math.sqrt(Math.max(0,1-z*z))*(.83+random()*.25);
    const d=.87+random()*.21;
    points.push([Math.cos(az)*r*d,z*d,Math.sin(az)*r*d,random()*Math.PI*2,random()]);
  }
  const edges=[],seen=new Set();
  for(let i=0;i<count;i++){
    const near=[];
    for(let j=0;j<count;j++){
      if(i===j)continue;
      const a=points[i],b=points[j];
      const dist=Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);
      near.push([j,dist]);
    }
    near.sort((a,b)=>a[1]-b[1]);
    const picked=3+(i%5===0?1:0);
    for(let j=0;j<picked;j++){
      const selected=near[j===2?3:j===3?5:j];
      if(!selected)continue;
      const k=selected[0],sig=Math.min(i,k)+":"+Math.max(i,k);
      if(seen.has(sig))continue;
      seen.add(sig);
      edges.push([i,k,random()*.6+.4]);
    }
    if(i%9===0){
      const other=near[7];
      if(other){const j=other[0],sig=Math.min(i,j)+":"+Math.max(i,j);
        if(!seen.has(sig)){seen.add(sig);edges.push([i,j,.48]);}}
    }
  }
  const anchorIndices=[7,24,41,57,76,92];
  return {points,edges,anchorIndices};
}
  const mesh=makeMesh();

  function spawnComet(t,initial=false){
  const r=(lo,hi)=>lo+Math.random()*(hi-lo);
  return {
    born:t-(initial?r(150,1100):0),
    duration:r(2100,3700),
    start:r(-Math.PI,Math.PI),
    speed:(Math.random()<.5?-1:1)*r(.00032,.00078),
    orbit:r(1.03,1.32),
    incline:r(-1.05,1.05),
    turn:r(-Math.PI,Math.PI),
    flatten:r(.68,1.06),
    tailMs:r(330,670),
    color:Math.random()<.76?182:205,
    strength:r(.66,1),
    size:r(1.55,2.5)
  };
}
  function cometAt(c,time,cx,cy,radius){
  const angle=c.start+(time-c.born)*c.speed;
  // Project tilted, elongated orbital paths into the same depth space as the globe.
  const x=Math.cos(angle);
  const y=Math.sin(angle)*Math.cos(c.incline)*c.flatten;
  const z=Math.sin(angle)*Math.sin(c.incline);
  const sin=Math.sin(c.turn),cos=Math.cos(c.turn);
  const depth=2.6/(2.6-z*.34);
  return {
    x:cx+radius*c.orbit*(x*cos-y*sin)*depth,
    y:cy+radius*c.orbit*(x*sin+y*cos)*depth,
    z
  };
}
  function drawComets(ctx,s,t,cx,cy,radius,dpr,isIdle,hue){
  if(!s.comets){
    s.comets=[spawnComet(t,true),spawnComet(t,true),spawnComet(t,true)];
    s.nextCometAt=t+600;
  }
  s.comets=s.comets.filter(c=>t-c.born<c.duration);
  if(t>=s.nextCometAt){
    if(s.comets.length<(isIdle?5:7))s.comets.push(spawnComet(t));
    s.nextCometAt=t+(isIdle?600+Math.random()*900:370+Math.random()*660);
  }
  const oldLineCap=ctx.lineCap;
  ctx.lineCap="round";
  for(const c of s.comets){
    const age=t-c.born;
    if(age<0||age>=c.duration)continue;
    const gate=Math.min(1,age/340,(c.duration-age)/610);
    if(gate<=0)continue;
    const head=cometAt(c,t,cx,cy,radius);
    const dep=Math.max(.28,Math.min(1,(head.z+1)*.52));
    const alpha=gate*dep*c.strength;
    // Each trail segment occupies a different point on the current 3D orbit;
    // there are no permanently drawn rings or stationary decorative arcs.
    const tailSteps=12;
    let previous=head;
    for(let step=1;step<=tailSteps;step++){
      const lag=c.tailMs*step/tailSteps;
      const earlier=cometAt(c,Math.max(c.born,t-lag),cx,cy,radius);
      const fade=1-step/(tailSteps+1);
      const power=fade*fade;
      const stepHue=isIdle?c.color:hue;
      ctx.strokeStyle="hsla("+stepHue+",90%,"+(isIdle?78:83)+"%,"+(alpha*power*.76).toFixed(3)+")";
      ctx.lineWidth=(.45+power*1.45)*dpr;
      ctx.beginPath();
      ctx.moveTo(previous.x,previous.y);
      ctx.lineTo(earlier.x,earlier.y);
      ctx.stroke();
      previous=earlier;
    }
    // Brief, bright cyan/white tip with a very soft halo.
    const cometHue=isIdle?c.color:hue;
    const glowRadius=(6+c.size*2)*dpr;
    const glow=ctx.createRadialGradient(head.x,head.y,0,head.x,head.y,glowRadius);
    glow.addColorStop(0,"hsla("+cometHue+",98%,91%,"+(alpha*.38).toFixed(3)+")");
    glow.addColorStop(.28,"hsla("+cometHue+",95%,75%,"+(alpha*.16).toFixed(3)+")");
    glow.addColorStop(1,"hsla("+cometHue+",90%,65%,0)");
    ctx.fillStyle=glow;
    ctx.beginPath();ctx.arc(head.x,head.y,glowRadius,0,Math.PI*2);ctx.fill();
    ctx.fillStyle="hsla("+cometHue+",94%,91%,"+(alpha*.94).toFixed(3)+")";
    ctx.beginPath();ctx.arc(head.x,head.y,c.size*dpr,0,Math.PI*2);ctx.fill();
    ctx.fillStyle="rgba(255,255,255,"+(alpha*.84).toFixed(3)+")";
    ctx.beginPath();ctx.arc(head.x,head.y,.85*dpr,0,Math.PI*2);ctx.fill();
  }
  ctx.lineCap=oldLineCap;
}
  function draw(card,s,t){
  const canvas=s.canvas,rect=canvas.getBoundingClientRect();
  if(!rect.width||!rect.height)return;
  const dpr=Math.min(window.devicePixelRatio||1,/Android/i.test(navigator.userAgent)?1.2:1.5);
  const w=Math.max(1,Math.round(rect.width*dpr)),h=Math.max(1,Math.round(rect.height*dpr));
  if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
  const ctx=canvas.getContext("2d");if(!ctx)return;
  ctx.clearRect(0,0,w,h);
  const phase=s.phase;
  const hue=phase==="listening"?184:phase==="processing"?260:phase==="speaking"?295:215;
  const isIdle=phase==="idle";
  const speed=isIdle?.55:1.32;
  const pulse=isIdle?0:Math.sin(t*.004)*.023;
  const radius=Math.min(w*.42,h*.41)*(1+pulse);
  const cx=w*.5,cy=h*.51;
  const glow=ctx.createRadialGradient(cx,cy,0,cx,cy,radius*1.22);
  glow.addColorStop(0,isIdle?"rgba(211,210,240,.12)":`hsla(${hue},82%,70%,.24)`);
  glow.addColorStop(.56,isIdle?"rgba(174,182,219,.052)":`hsla(${hue},84%,50%,.09)`);
  glow.addColorStop(1,"rgba(12,22,42,0)");
  ctx.fillStyle=glow;ctx.fillRect(0,0,w,h);

  // All particles and metric anchors pass through the same rotating camera.
  // An independent orbit clock prevents a jump after dragging.
  // On release, auto-rotation starts in the very next frame and smoothly
  // fades up while the last manual angular velocity gradually fades out.
  const frameDelta=Math.max(0,Math.min(120,t-(s.lastOrbitFrame??t)));
  s.lastOrbitFrame=t;
  if(s.orbitTime===undefined)s.orbitTime=t;
  if(!s.manualDragging){
    const spinFade=Math.exp(-frameDelta/560);
    const oldYaw=s.inertiaYaw||0,oldPitch=s.inertiaPitch||0;
    const step=frameDelta>0?(1-spinFade)*560:0;
    s.manualYaw+=oldYaw*step;
    s.manualPitch=Math.max(-1.2,Math.min(1.2,s.manualPitch+oldPitch*step));
    s.inertiaYaw=oldYaw*spinFade;
    s.inertiaPitch=oldPitch*spinFade;
    const from=s.autoBlend??1;
    s.autoBlend=1-(1-from)*Math.exp(-frameDelta/780);
    s.orbitTime+=frameDelta*s.autoBlend;
  }
  const orbit=s.orbitTime;
  const ay=orbit*.00015*speed+(s.manualYaw||0);
  const ax=-.23+Math.sin(orbit*(isIdle?.000045:.00013))*(isIdle?.022:.17)+(s.manualPitch||0);
  const az=Math.sin(orbit*(isIdle?.000037:.000075))*(isIdle?.012:.12);
  const cosa=Math.cos(ay),sina=Math.sin(ay);
  const cosx=Math.cos(ax),sinx=Math.sin(ax);
  const cosz=Math.cos(az),sinz=Math.sin(az);
  const projected=mesh.points.map((p,i)=>{
    const movement=isIdle?1:1+Math.sin(t*.00042+p[3])*.028+Math.cos(t*.00023+p[3]*1.7)*.017;
    const px=p[0]*movement+(isIdle?0:.012*Math.sin(t*.00033+p[3]*2));
    const py=p[1]*movement+(isIdle?0:.012*Math.cos(t*.00027+p[3]));
    const pz=p[2]*movement;
    const rx=px*cosa+pz*sina;
    const rz=pz*cosa-px*sina;
    const ry=py*cosx-rz*sinx;
    const rz2=py*sinx+rz*cosx;
    const xx=rx*cosz-ry*sinz,yy=rx*sinz+ry*cosz;
    const depth=2.65/(2.65-rz2*.32);
    return [cx+radius*xx*depth,cy+radius*yy*depth,rz2];
  });

  ctx.lineWidth=Math.max(.55,dpr*.65);
  for(const [a,b,weight] of mesh.edges){
    const u=projected[a],v=projected[b];
    const depth=(2+u[2]+v[2])/4;
    const shimmer=.84+.16*Math.sin(t*.0014+(a+b)*.37);
    const opacity=(.10+.47*depth)*weight*shimmer;
    ctx.strokeStyle=isIdle?`rgba(211,223,246,${opacity})`:`hsla(${hue},80%,82%,${opacity})`;
    ctx.beginPath();ctx.moveTo(u[0],u[1]);ctx.lineTo(v[0],v[1]);ctx.stroke();
  }
  for(let i=0;i<projected.length;i++){
    const p=projected[i],bright=i%11===0||mesh.anchorIndices.includes(i);
    const depth=(p[2]+1)/2,alpha=.21+.73*depth;
    ctx.fillStyle=isIdle?`rgba(239,242,255,${alpha})`:`hsla(${hue},94%,91%,${alpha})`;
    ctx.beginPath();ctx.arc(p[0],p[1],(bright?1.7:.88)*dpr,0,Math.PI*2);ctx.fill();
    if(bright){
      ctx.fillStyle=isIdle?`rgba(236,232,255,${.07+.13*depth})`:`hsla(${hue},94%,84%,.17)`;
      ctx.beginPath();ctx.arc(p[0],p[1],(4.5+depth*2)*dpr,0,Math.PI*2);ctx.fill();
    }
  }
  // Short-lived 3D shooting stars around the sphere (no persistent orbit lines).
  drawComets(ctx,s,t,cx,cy,radius,dpr,isIdle,hue);
    // Sensor labels are tied to actual 3D nodes, including perspective/depth.
  if(++s.labelFrame>=1){
    for(let i=0;i<mesh.anchorIndices.length;i++){
      const label=s.metricNodes[i],p=projected[mesh.anchorIndices[i]];
      if(!label||!p)continue;
      const px=p[0]/dpr,py=p[1]/dpr,z=p[2];
      const mid=rect.width/2;
      const x=Math.max(43,Math.min(rect.width-43,mid+(px-mid)*1.08));
      const y=Math.max(25,Math.min(rect.height-23,rect.height*.51+(py-rect.height*.51)*1.07));
      const scale=isIdle?.94:.79+.22*Math.max(0,Math.min(1,(z+1)/2));
      const alpha=z<-.34?.24:(.49+.43*Math.max(0,Math.min(1,(z+1)/2)));
      label.style.left=x.toFixed(1)+"px";
      label.style.top=y.toFixed(1)+"px";
      label.style.opacity=alpha.toFixed(2);
      label.style.transform=`translate(-50%,-50%) scale(${scale.toFixed(3)})`;
    }
  }
}
  function mount(card){
    dispose(card);
    if(!card?._hzNight||!card.shadowRoot)return;
    const host=card.shadowRoot.querySelector(".hz-ambient-body"),canvas=host?.querySelector("canvas");
    if(!host||!canvas)return;
    const s={host,canvas,phase:"idle",lastFrame:0,lastOrbitFrame:null,orbitTime:undefined,manualYaw:0,manualPitch:0,manualDragging:false,inertiaYaw:0,inertiaPitch:0,autoBlend:1,dragPointer:null,suppressClick:false,forceUntil:0,forcedPhase:"idle",infoTimer:null,controlsTimer:null,raf:null,unsubscribe:null,closing:false,labelFrame:0,metricNodes:Array.from(host.querySelectorAll("[data-ambient-metric]"))};
    active.set(card,s);
    const exit=host.querySelector(".hz-ambient-exit");
    const revealControls=()=>{
      if(active.get(card)!==s||!host.isConnected)return;
      host.dataset.controls="visible";
      exit?.removeAttribute("tabindex");
      clearTimeout(s.controlsTimer);
      s.controlsTimer=setTimeout(()=>{
        if(active.get(card)!==s)return;
        host.dataset.controls="hidden";
        exit?.setAttribute("tabindex","-1");
        if(document.activeElement===exit)exit.blur();
      },6000);
    };
    exit?.setAttribute("tabindex","-1");
    // Ordinary taps reveal the day control; holding a globe point is a drag.
    host.addEventListener("pointerdown",event=>{
      if(!event.target.closest?.(".hz-ambient-stage"))revealControls();
    },{passive:true});
    host.addEventListener("click",event=>{
      if(s.suppressClick){
        s.suppressClick=false;
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      revealControls();
    });

    // Press-and-drag works immediately on real pointer motion. Stationary
    // presses still enter drag mode after 280ms. Unlike 0.4.52, movement
    // during that interval must NEVER cancel the gesture.
    const HOLD_MS=280;
    const activateDrag=pointer=>{
      if(pointer.active||s.dragPointer!==pointer||active.get(card)!==s||!host.isConnected)return;
      clearTimeout(pointer.timer);
      pointer.active=true;
      s.manualDragging=true;
      s.inertiaYaw=0;
      s.inertiaPitch=0;
      clearTimeout(s.controlsTimer);
      host.dataset.controls="hidden";
      exit?.setAttribute("tabindex","-1");
      canvas.classList.add("hz-manual-dragging");
    };
    const stopDrag=(event,cancelled=false)=>{
      const pointer=s.dragPointer;
      if(!pointer||(event&&pointer.id!==event.pointerId))return;
      clearTimeout(pointer.timer);
      if(pointer.active){
        s.manualDragging=false;
        // Never pause after release. Use the last measured motion for a
        // gentle inertial glide; ramp the usual automatic speed back in.
        s.inertiaYaw=cancelled?0:(pointer.velocityYaw||0);
        s.inertiaPitch=cancelled?0:(pointer.velocityPitch||0);
        // Begin auto-rotation immediately at a gentle fraction of its normal
        // speed, then ease toward full speed while the manual spin fades.
        s.autoBlend=.18;
        s.suppressClick=true;
        canvas.classList.remove("hz-manual-dragging");
        if(event&&!cancelled)event.preventDefault();
      }
      s.dragPointer=null;
      if(event&&canvas.hasPointerCapture?.(event.pointerId)){
        try{canvas.releasePointerCapture(event.pointerId);}catch{}
      }
    };
    canvas.addEventListener("pointerdown",event=>{
      if(event.button!==0||s.dragPointer)return;
      s.suppressClick=false;
      const pointer={id:event.pointerId,x:event.clientX,y:event.clientY,lastX:event.clientX,lastY:event.clientY,lastMoveAt:performance.now(),velocityYaw:0,velocityPitch:0,active:false,timer:null};
      s.dragPointer=pointer;
      try{canvas.setPointerCapture?.(event.pointerId);}catch{}
      pointer.timer=setTimeout(()=>activateDrag(pointer),HOLD_MS);
    });
    canvas.addEventListener("pointermove",event=>{
      const pointer=s.dragPointer;
      if(!pointer||pointer.id!==event.pointerId)return;
      if(!pointer.active){
        if(Math.hypot(event.clientX-pointer.x,event.clientY-pointer.y)<6)return;
        activateDrag(pointer);
      }
      if(!pointer.active)return;
      event.preventDefault();
      const rect=canvas.getBoundingClientRect();
      const sensitivity=Math.PI/Math.max(180,Math.min(rect.width,rect.height)*.65);
      const yawDelta=(event.clientX-pointer.lastX)*sensitivity;
      const pitchDelta=-(event.clientY-pointer.lastY)*sensitivity;
      s.manualYaw+=yawDelta;
      s.manualPitch=Math.max(-1.2,Math.min(1.2,s.manualPitch+pitchDelta));
      const now=performance.now();
      const dt=Math.max(12,Math.min(100,now-pointer.lastMoveAt));
      const weight=pointer.velocityYaw===0&&pointer.velocityPitch===0?.65:.32;
      pointer.velocityYaw=Math.max(-.0028,Math.min(.0028,pointer.velocityYaw*(1-weight)+yawDelta/dt*weight));
      pointer.velocityPitch=Math.max(-.0018,Math.min(.0018,pointer.velocityPitch*(1-weight)+pitchDelta/dt*weight));
      pointer.lastMoveAt=now;
      pointer.lastX=event.clientX;
      pointer.lastY=event.clientY;
    });
    canvas.addEventListener("pointerup",event=>stopDrag(event));
    canvas.addEventListener("pointercancel",event=>stopDrag(event,true));
    canvas.addEventListener("lostpointercapture",event=>stopDrag(event,true));
    canvas.addEventListener("contextmenu",event=>event.preventDefault());
    canvas.addEventListener("click",event=>{
      if(s.suppressClick){
        event.preventDefault();
        event.stopPropagation();
        s.suppressClick=false;
      }
    });
    host.addEventListener("keydown",event=>{
      if((event.key==="Enter"||event.key===" "||event.key==="Escape")&&host.dataset.controls!=="visible"){
        if(event.key===" ")event.preventDefault();
        revealControls();
      }
    });
    if(exit)exit.addEventListener("click",event=>{
      event.stopPropagation();
      if(typeof card.hzHeaderAction==="function")void card.hzHeaderAction("night");
      else if(typeof card.quickAction==="function")card.quickAction("ambient");
    });
    let frames=0;
    const loop=(time)=>{
      if(active.get(card)!==s||!card.isConnected||!card._hzNight||!host.isConnected)return;
      s.raf=requestAnimationFrame(loop);
      if(document.hidden)return;
      if(time-s.lastFrame<(/Android/i.test(navigator.userAgent)?48:38))return;
      s.lastFrame=time;
      if(++frames%13===1)update(card);
      draw(card,s,time);
    };
    s.raf=requestAnimationFrame(loop);
    update(card);
    if(card.h?.connection?.subscribeEvents){
      Promise.resolve(card.h.connection.subscribeEvents(event=>{
        if(active.get(card)!==s)return;
        const data=event?.data||event;
        if(data?.user_id&&card.h?.user?.id&&data.user_id!==card.h.user.id)return;
        if(String(data?.reply||"").trim())show(card,{...data,title:data.title||data.topic||"TAFA Antwort",message:data.reply,seconds:data.topic==="search"?65:30});
      },"tafa_assist_response")).then(unsub=>{
        if(active.get(card)!==s)unsub?.();else s.unsubscribe=unsub;
      }).catch(()=>{});
    }
  }
  function dispose(card){
    const s=active.get(card);if(!s)return;
    active.delete(card);cancelAnimationFrame(s.raf);
    clearTimeout(s.infoTimer);
    clearTimeout(s.controlsTimer);
    clearTimeout(s.dragPointer?.timer);
    s.dragPointer=null;
    s.manualDragging=false;
    try{s.unsubscribe?.();}catch{}
  }
  bag.parts.ambient={body,mount,update,show,close,dispose};
  // Optional enhancement: never take part in the required dashboard boot gate.
  try{document.dispatchEvent(new Event("tafa-integration-ambient-ready"));}catch(e){console.debug("TAFA Ambient ready",e);}
})();
