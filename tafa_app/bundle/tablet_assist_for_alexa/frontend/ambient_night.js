import {subscribeTafaVisual} from './visual_client.js?v=0.5.2';
import {subscribeOwnAmbientProfile} from './ambient_profiles_client.js?v=0.5.3';
/* TAFA dashboard asset version 0.4.64 - cache-busted file delivery; existing code preserved */
(function ambientModule(){
  "use strict";
  const bag=globalThis[Symbol.for("tafa-ambient.integration.v1")]??={parts:Object.create(null)};
  const active=new WeakMap();
  const metrics=[
    {name:"NETZ",ids:[],pattern:/tibber.*pulse|netz.*leistung|grid.*power|wirkleistung aktuell/i},
    {name:"STROMPREIS",ids:[],pattern:/aktueller.*strompreis|electricity.*price|strompreis/i},
    {name:"AUßEN",ids:[],pattern:/au.ss.en.*temperatur|aussentemperatur|outside.*temp|outdoor.*temp/i},
    {name:"SOLAR",ids:[],pattern:/pv.*leistung|solar.*power|solar.*leistung|photovoltaik.*leistung|growatt.*leistung/i},
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
  .hz-ambient-indicator{display:inline-block;width:7px;height:7px;border-radius:50%;background:#7f9bb5;box-shadow:0 0 9px #7f9bb545;transition:background-color .42s ease,box-shadow .52s ease}
  .hz-ambient-foot [data-ambient-state]{display:inline-block;transition:color .3s ease}
  @keyframes hz-ambient-status-enter{from{opacity:.38;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
  .hz-ambient-body[data-phase="listening"] .hz-ambient-indicator{background:#3ce4ed;box-shadow:0 0 12px #3ce4ed}
  .hz-ambient-body[data-phase="processing"] .hz-ambient-indicator{background:#b6a2ff;box-shadow:0 0 12px #b6a2ff}
  .hz-ambient-body[data-phase="speaking"] .hz-ambient-indicator{background:#f3d6ff;box-shadow:0 0 12px #f3d6ff}
  .hz-ambient-info{position:absolute;z-index:4;left:50%;bottom:clamp(12px,3vh,30px);width:min(740px,calc(100% - 32px));margin:0;background:linear-gradient(125deg,#173050e8,#0a233ddf);border:1px solid #61a9d18c;box-shadow:0 13px 45px #020d20a0,0 0 28px #3b9cbe20,inset 0 1px #b8ddf33c;border-radius:17px;backdrop-filter:blur(14px);padding:16px 20px 18px;max-height:33vh;overflow:auto;animation:hz-ambient-enter .38s cubic-bezier(.18,.85,.32,1.08) both}
  .hz-ambient-info[hidden]{display:none!important}
  .hz-ambient-body[data-ambient-info-state="open"] .hz-ambient-foot{opacity:0}
  .hz-ambient-info-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}
  .hz-ambient-info-kicker{font:600 10px/1.3 inherit;letter-spacing:.14em;color:#63dbeb}
  .hz-ambient-info-title{font-size:clamp(17px,2.1vw,24px);font-weight:500;color:#ecf5ff;margin:6px 0 8px}
  .hz-ambient-info-message{font-size:clamp(13px,1.5vw,16px);line-height:1.45;color:#c5dcef;overflow-wrap:anywhere;white-space:pre-wrap}
  .hz-ambient-info-x{font:inherit;color:#b8d0e6;background:#284c674a;border:1px solid #7ca9c43b;border-radius:8px;padding:5px 9px;cursor:pointer}
  .hz-ambient-items{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:7px;margin-top:11px}
  .hz-ambient-item{border:1px solid #8aadd134;background:#0a213956;border-radius:10px;padding:7px 9px;min-width:0;font-size:12px;color:#cde2f3;overflow-wrap:anywhere}
  .hz-ambient-item b{color:#fff;font-weight:500}
  @keyframes hz-ambient-enter{from{opacity:0;transform:translate(-50%,28px) scale(.97)}to{opacity:1;transform:translate(-50%,0) scale(1)}}

  /* Materialized reply: a line from the sphere traces the card, then the
     surface, title and content appear in staggered steps. */
  .hz-ambient-body .hz-ambient-info{
    transform-origin:50% 0;animation:hz-info-unfold .75s cubic-bezier(.18,.83,.2,1) both;
    overflow:visible!important;
    border-color:#a7d5f6aa;box-shadow:0 14px 50px #020d20a8,0 0 35px #50cfff22,inset 0 1px #e3f9ff40
  }
  .hz-ambient-info::before{
    content:"";position:absolute;left:50%;top:-48px;height:48px;width:2px;
    background:linear-gradient(180deg,transparent,#7fe3ffcc 70%,#dff9ff);
    transform:translateX(-50%);transform-origin:50% 0;pointer-events:none;
    filter:drop-shadow(0 0 7px #73eaff);animation:hz-info-conduit .48s ease both
  }
  .hz-ambient-info-trace{position:absolute;inset:0;pointer-events:none;z-index:1;border-radius:inherit}
  .hz-ambient-info-trace i{position:absolute;display:block;background:#a9e7ffd9;box-shadow:0 0 9px #9bdfff88}
  .hz-ambient-info-trace .top{top:0;left:14px;width:calc(100% - 28px);height:1px;transform-origin:left;animation:hz-trace-x .30s ease .16s both}
  .hz-ambient-info-trace .right{top:12px;right:0;width:1px;height:calc(100% - 24px);transform-origin:top;animation:hz-trace-y .20s ease .36s both}
  .hz-ambient-info-trace .bottom{bottom:0;right:14px;width:calc(100% - 28px);height:1px;transform-origin:right;animation:hz-trace-x .24s ease .51s both}
  .hz-ambient-info-trace .left{bottom:12px;left:0;width:1px;height:calc(100% - 24px);transform-origin:bottom;animation:hz-trace-y .20s ease .68s both}
  .hz-ambient-info-content{position:relative;z-index:2;min-width:0;max-height:calc(33vh - 34px);overflow-y:auto;scrollbar-width:thin;scrollbar-color:#7799b370 transparent}
  .hz-ambient-info-kicker{animation:hz-info-appear .32s ease .46s both}
  .hz-ambient-info-title{animation:hz-info-appear .35s ease .57s both}
  .hz-ambient-info-message{animation:hz-info-reveal .55s steps(20,end) .70s both}
  .hz-ambient-info-content .hz-ambient-items{animation:hz-info-appear .38s ease .94s both}
  .hz-ambient-info-symbol{
    position:absolute;right:11px;bottom:10px;display:flex;align-items:center;justify-content:center;
    width:41px;height:41px;pointer-events:none;opacity:.77;color:#c5e9ff;
    filter:drop-shadow(0 0 10px #5ab4ff77);animation:hz-info-symbol .55s ease 1.01s both
  }
  .hz-ambient-info-symbol ha-icon{--mdc-icon-size:29px}
  .hz-ambient-info-content.has-symbol .hz-ambient-info-message{padding-right:46px}
  @keyframes hz-info-conduit{
    0%{opacity:0;transform:translateX(-50%) scaleY(0)}
    45%{opacity:1;transform:translateX(-50%) scaleY(1)}
    100%{opacity:0;transform:translateX(-50%) scaleY(.6)}
  }
  @keyframes hz-info-unfold{
    0%{opacity:0;transform:translate(-50%,-20px) scale(.14,.025);filter:blur(6px)}
    30%{opacity:1;transform:translate(-50%,0) scale(.98,.055);filter:blur(1px)}
    75%{opacity:1;transform:translate(-50%,0) scale(1,1);filter:blur(0)}
    100%{opacity:1;transform:translate(-50%,0) scale(1,1);filter:none}
  }
  @keyframes hz-trace-x{from{opacity:0;transform:scaleX(0)}to{opacity:1;transform:scaleX(1)}}
  @keyframes hz-trace-y{from{opacity:0;transform:scaleY(0)}to{opacity:1;transform:scaleY(1)}}
  @keyframes hz-info-appear{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
  @keyframes hz-info-reveal{
    from{opacity:0;clip-path:inset(0 100% 0 0)}
    15%{opacity:1}
    to{opacity:1;clip-path:inset(0 0 0 0)}
  }
  @keyframes hz-info-symbol{
    0%{opacity:0;transform:scale(.35) rotate(-20deg)}
    70%{opacity:1;transform:scale(1.12) rotate(5deg)}
    100%{opacity:.77;transform:scale(1) rotate(0)}
  }
  @media(prefers-reduced-motion:reduce){
    .hz-ambient-body .hz-ambient-info,.hz-ambient-info::before,
    .hz-ambient-info-trace i,.hz-ambient-info-kicker,.hz-ambient-info-title,
    .hz-ambient-info-message,.hz-ambient-info-symbol,.hz-ambient-info-content .hz-ambient-items{
      animation:none!important;clip-path:none!important;filter:none!important
    }
  }
  @media(max-width:800px){.hz-ambient-head{margin-top:72px}.hz-ambient-stage{width:100%;max-width:610px;height:clamp(270px,49dvh,570px);min-height:270px}.hz-ambient-time{font-size:clamp(60px,11vw,96px)}.hz-ambient-metric small{font-size:9px}.hz-ambient-metric b{font-size:12px}}
  @media(max-width:500px){.hz-ambient-body{padding:0 6px!important}.hz-ambient-head{margin-top:68px}.hz-ambient-stage{width:100%;min-height:280px;height:45dvh}.hz-ambient-time{font-size:clamp(56px,13vw,82px)}.hz-ambient-metric small{font-size:8px;letter-spacing:.06em}.hz-ambient-metric b{font-size:11px}}
  @media(prefers-reduced-motion:reduce){.hz-ambient-info,.hz-ambient-foot [data-ambient-state]{animation:none!important}}
  `;
  const safe=(s)=>String(s??"").replace(/[&<>"']/g,a=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[a]));
  const isValid=v=>v&&!["unknown","unavailable","none",""].includes(String(v.state).toLowerCase());
  const fmt=(entity)=>{
    if(!isValid(entity))return "—";
    const n=Number(entity.state),unit=String(entity.attributes?.unit_of_measurement||"");
    return (Number.isFinite(n)&&String(entity.state).trim()!==""?new Intl.NumberFormat("de-DE",{maximumFractionDigits:unit==="W"?0:1}).format(n):String(entity.state).slice(0,24))+(unit?" "+unit:"");
  };
  const validForMetric=(entity,entry)=>{
    if(!isValid(entity))return false;
    if(entry.name==="SOLAR"||entry.name==="NETZ")
      return ["W","kW"].includes(String(entity.attributes?.unit_of_measurement||""))&&
        Number.isFinite(Number(entity.state))&&
        (entity.attributes?.device_class==="power"||entity.attributes?.state_class==="measurement");
    return true;
  };
  const choose=(states,entry)=>{
    for(const id of entry.ids)if(validForMetric(states[id],entry))return id;
    return Object.keys(states).find(id=>id.startsWith("sensor.")&&
      entry.pattern.test(id+" "+(states[id]?.attributes?.friendly_name||""))&&
      validForMetric(states[id],entry))||null;
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
    const device=card._tafaLocalVoice||{};
    const wake=String(h[device.status]?.state||"").toLowerCase();
    const mic=String(h[device.mic]?.state||"").toLowerCase();
    const voice=card._tafaIntegratedVoice;
    if(voice?.playing)return "speaking";
    if(voice?.processing)return "processing";
    if(voice?.info)return "listening";
    if(s.host?.dataset?.info==="open"&&s.forceUntil>Date.now())return "speaking";
    // A permanently armed native wakeword detector reports "listening: hey_jarvis".
    // That is standby, NOT active Assist capture: keep the sphere quiet.
    // Match the app's native Assist lifecycle exactly. A WebSocket
    // handshake is still listening/setup, not an AI inference result.
    if(/^native_(?:waiting_for_playback|buffering|playing|speaking)/.test(wake)||/^(?:speaking|playing|tts)$/.test(mic))return "speaking";
    if(/^native_(?:processing|thinking|generating_voice|transcribing|sending_audio|waiting_for_stt)/.test(wake)||/^(?:processing|thinking|busy)$/.test(mic))return "processing";
    if(/^(?:detected(?::|$)|native_(?:connecting|authenticating|connected|followup|starting_microphone|listening))/.test(wake)||mic==="assist")return "listening";
    const last=h[device.last]?.state;
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
    s.attachProfile?.();
    if(!s.metricIds)s.metricIds=[];
    for(let i=0;i<metrics.length;i++){
      const node=stage.querySelector(`[data-ambient-metric="${i}"] b`);
      if(!node)continue;
      const entry=s.metricEntries?s.metricEntries[i]:metrics[i];const id=entry?choose(h,entry):null;s.metricIds[i]=id;const str=fmt(id?h[id]:null);
      if(node.textContent!==str)node.textContent=str;
    }
    const nextPhase=resolvePhase(card,s);
    if(nextPhase!==s.phase){
      const previousPhase=s.phase,when=performance.now();
      // Exactly one soft expanding circular pulse at each significant edge.
      // Listening->processing marks the end of capture; processing->speaking
      // marks the handoff to audio output. Never pulse continuously in idle.
      if((previousPhase==="listening"&&nextPhase==="processing")||
         (previousPhase==="processing"&&nextPhase==="speaking")){
        if(!s.phaseRings)s.phaseRings=[];
        s.phaseRings.push({born:when,kind:nextPhase});
        if(s.phaseRings.length>3)s.phaseRings.shift();
      }
      s.phase=nextPhase;s.phaseChangeAt=when;
    }
    stage.dataset.phase=s.phase;
    s.overview?.update?.();
    const label=stage.querySelector("[data-ambient-state]");
    const labels={idle:"TAFA · Bereit",listening:"TAFA · Ich höre zu",processing:"TAFA · Verarbeite Anfrage",speaking:"TAFA · Antwort"};
    if(label&&label.textContent!==labels[s.phase]){
      label.textContent=labels[s.phase];
      label.style.animation="none";
      void label.offsetWidth;
      label.style.animation="hz-ambient-status-enter .36s cubic-bezier(.2,.8,.2,1) both";
    }
    stage.querySelector(".hz-ambient-indicator")?.setAttribute("title",s.phase);
  }
  function close(card){
    const s=active.get(card);if(!s)return;
    clearTimeout(s.infoTimer);
    const info=s.host?.querySelector("[data-ambient-info]");
    if(info){info.hidden=true;info.replaceChildren();s.host.dataset.ambientInfoState="closed";s.infoKey=null;s.infoLastMessage=null;}
  }
  function show(card,input){
    const s=active.get(card);if(!s||!card._hzNight)return false;
    const data=input&&typeof input==="object"?input:{message:String(input??"")};
    const title=String(data.title||data.topic||"TAFA Antwort").slice(0,120);
    const message=String(data.message??data.reply??data.answer??"").slice(0,2500);
    const info=s.host.querySelector("[data-ambient-info]");if(!info)return false;
    // Streaming updates for the same answer must not restart its reveal.
    const infoKey=String(data.request_id||data.id||"")+"|"+String(data.topic||"")+"|"+title;
    if(!info.hidden&&s.infoKey===infoKey&&message.startsWith(s.infoLastMessage||"")
        &&!Array.isArray(data.results)&&!data.sources){
      s.infoLastMessage=message;
      const target=info.querySelector(".hz-ambient-info-message");
      if(target)target.textContent=message;
      clearTimeout(s.infoTimer);
      const seconds=Math.max(8,Math.min(180,Number(data.seconds)||30));
      s.infoTimer=setTimeout(()=>close(card),seconds*1000);
      s.forcedPhase="speaking";s.forceUntil=Date.now()+7000;
      update(card);return true;
    }
    s.infoKey=infoKey;s.infoLastMessage=message;
    info.replaceChildren();
    const trace=document.createElement("div");trace.className="hz-ambient-info-trace";
    for(const edge of ["top","right","bottom","left"]){
      const line=document.createElement("i");line.className=edge;trace.append(line);
    }
    info.append(trace);
    const content=document.createElement("div");content.className="hz-ambient-info-content";info.append(content);
    const head=document.createElement("div");head.className="hz-ambient-info-head";
    const left=document.createElement("div"),kick=document.createElement("div"),h=document.createElement("div");
    kick.className="hz-ambient-info-kicker";kick.textContent="TAFA / "+(data.topic==="search"?"INTERNETSUCHE":data.camera?"KAMERA":"ASSIST");
    h.className="hz-ambient-info-title";h.textContent=title;left.append(kick,h);
    const x=document.createElement("button");x.type="button";x.className="hz-ambient-info-x";x.textContent="✕";x.setAttribute("aria-label","Infobox schließen");x.onclick=()=>close(card);
    head.append(left,x);content.append(head);
    if(message){const p=document.createElement("div");p.className="hz-ambient-info-message";p.textContent=message;content.append(p);}
    if(typeof data.camera==="string"&&data.camera.startsWith("camera.")){
      const entity=card.h?.states?.[data.camera];
      const picture=entity?.attributes?.entity_picture;
      if(typeof picture==="string"&&picture.startsWith("/api/camera_proxy/")&&!picture.startsWith("//")){
        const image=document.createElement("img");
        image.src=picture;image.alt="Ring · letzte Aufnahme";image.loading="eager";
        image.style.cssText="display:block;width:100%;max-height:min(38vh,350px);object-fit:contain;background:#071525;border-radius:10px;margin:12px 0";
        image.onerror=()=>image.remove();content.append(image);
        const caption=document.createElement("div");caption.className="hz-ambient-info-message";
        caption.style.fontSize="11px";caption.textContent="Letztes Kamerabild · kein Livestream";content.append(caption);
      }
    }
    const list=[];
    if(Array.isArray(data.results))for(const result of data.results.slice(0,5)){
      const text=typeof result==="string"?result:result?.title||result?.name||result?.snippet;
      if(text)list.push(String(text).slice(0,220));
    }
    if(data.sources&&typeof data.sources==="object")for(const [key,id] of Object.entries(data.sources).slice(0,6)){
      if(typeof id==="string"&&card.h?.states?.[id])list.push(key+": "+fmt(card.h.states[id]));
    }
    if(data.camera&&typeof data.camera==="string"&&!card.h?.states?.[data.camera])list.push("Kamera: "+data.camera.replace(/^camera\./,"").replace(/_/g," "));
    if(list.length){const items=document.createElement("div");items.className="hz-ambient-items";for(const value of list){const el=document.createElement("div");el.className="hz-ambient-item";el.textContent=value;items.append(el);}content.append(items);}
    // A neutral context icon, never an unverified success indicator.
    const topic=String(data.topic||"").toLowerCase(),hint=(title+" "+message).toLowerCase();
    let icon=null;
    if(typeof data.icon==="string"&&/^mdi:[a-z0-9-]{1,65}$/.test(data.icon))icon=data.icon;
    else if(topic==="search")icon="mdi:magnify";
    else if(data.camera||topic==="camera")icon="mdi:cctv";
    else if(/wetter|weather/.test(topic+" "+hint))icon="mdi:weather-partly-cloudy";
    else if(/licht|lampe|light|lamp/.test(topic+" "+hint))icon="mdi:lightbulb-outline";
    else if(/musik|music/.test(topic+" "+hint))icon="mdi:music-note";
    if(icon){
      const badge=document.createElement("span");badge.className="hz-ambient-info-symbol";
      const glyph=document.createElement("ha-icon");glyph.setAttribute("icon",icon);badge.append(glyph);
      content.classList.add("has-symbol");content.append(badge);
    }
    info.hidden=false;s.host.dataset.ambientInfoState="open";info.style.animation="none";void info.offsetWidth;info.style.animation="";
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

  // Construct paths through the actual connected mesh. A carrier visits
  // 5–8 successive nodes, then reverses at the end: never jumps between
  // unrelated edges. All coordinates are projected by the same 3D camera.
  const adjacency=Array.from({length:mesh.points.length},()=>[]);
  for(const [a,b] of mesh.edges){adjacency[a].push(b);adjacency[b].push(a);}
  const flowRoutes=Array.from({length:23},(_,seed)=>{
    const nodes=[(seed*19+11)%mesh.points.length];
    let previous=-1;
    for(let hop=0;hop<5+(seed%3);hop++){
      const current=nodes[nodes.length-1];
      const neighbors=adjacency[current];
      if(!neighbors.length)break;
      let choice=(seed*7+hop*5+current)%neighbors.length;
      if(neighbors.length>1&&neighbors[choice]===previous)choice=(choice+1)%neighbors.length;
      const next=neighbors[choice];
      previous=current;
      nodes.push(next);
    }
    return nodes;
  });
  function flowPosition(route,travel,projected){
    const segments=route.length-1;
    if(segments<1)return projected[route[0]];
    const cycle=segments*2;
    let k=((travel%cycle)+cycle)%cycle;
    if(k>segments)k=cycle-k;
    const index=Math.min(segments-1,Math.floor(k));
    const f=k-index,from=projected[route[index]],to=projected[route[index+1]];
    return [from[0]+(to[0]-from[0])*f,from[1]+(to[1]-from[1])*f,
            from[2]+(to[2]-from[2])*f];
  }
  function drawPhaseRings(ctx,s,t,cx,cy,radius,dpr){
    if(!s.phaseRings?.length)return;
    s.phaseRings=s.phaseRings.filter(r=>t-r.born<1000&&t-r.born>=-120);
    const savedCap=ctx.lineCap;
    // The transition pulse belongs *inside* the sphere. External orbiting
    // comets are an entirely separate rendering layer.
    ctx.save();
    ctx.beginPath();ctx.arc(cx,cy,radius*.97,0,Math.PI*2);ctx.clip();
    ctx.lineCap="round";
    for(const ring of s.phaseRings){
      const age=Math.max(0,t-ring.born);
      for(let echo=0;echo<2;echo++){
        const u=Math.max(0,(age-echo*105)/780);
        if(u>=1||age<echo*105)continue;
        const ease=1-Math.pow(1-u,2.3);
        const size=radius*(.14+.77*ease);
        // Fade away approaching the globe's edge, rather than leaving it.
        const rimFade=Math.max(0,Math.min(1,(.92-size/radius)/.16));
        const envelope=Math.sin(Math.PI*u)*rimFade;
        const strength=ring.kind==="processing"?.21:.27;
        const alpha=Math.max(0,strength*envelope*(echo===0?1:.48));
        const hue=ring.kind==="processing"?197:264;
        const sat=ring.kind==="processing"?77:24;
        ctx.strokeStyle="hsla("+hue+","+sat+"%,88%,"+alpha.toFixed(3)+")";
        ctx.lineWidth=(1.08+(1-u)*1.12)*dpr;
        ctx.beginPath();ctx.arc(cx,cy,size,0,Math.PI*2);ctx.stroke();
        // One diffuse halo, not a solid disk or a distracting shockwave.
        if(echo===0&&u>.09&&u<.87){
          ctx.strokeStyle="hsla("+hue+","+sat+"%,82%,"+(alpha*.16).toFixed(3)+")";
          ctx.lineWidth=(9*(1-u)+2)*dpr;
          ctx.beginPath();ctx.arc(cx,cy,size,0,Math.PI*2);ctx.stroke();
        }
      }
    }
    ctx.lineCap=savedCap;
    ctx.restore();
  }


  function drawSignals(ctx,s,t,projected,dpr,visual){
    const dt=Math.max(0,Math.min(90,t-(s.lastFlowFrame??t)));
    s.lastFlowFrame=t;
    s.flowClock=(s.flowClock||0)+dt*(.00022+visual.listening*.00114
      +visual.processing*.00203+visual.speaking*.00146);
    const listen=visual.listening,think=visual.processing,speak=visual.speaking;
    const activity=Math.max(0,Math.min(1,listen+think+speak));
    const packets=listen*12+think*22+speak*17;
    const total=Math.min(flowRoutes.length,/Android/i.test(navigator.userAgent)?14:23);
    const sat=(91*listen+18*think+36*speak)/Math.max(.01,listen+think+speak);
    const hue=(185*listen+252*think+285*speak)/Math.max(.01,listen+think+speak);
    if(!s.pathLastSteps)s.pathLastSteps=new Array(flowRoutes.length).fill(null);
    if(!s.nodeFlashAt)s.nodeFlashAt=new Array(mesh.points.length).fill(-Infinity);
    if(!s.nodeFlashHue)s.nodeFlashHue=new Array(mesh.points.length).fill(185);
    const oldCap=ctx.lineCap;
    // Constrain all network pulses, trails and impact flares to the sphere.
    // This clip is restored before drawing the outer orbital shooting stars.
    ctx.save();
    ctx.beginPath();ctx.arc(s.signalCx,s.signalCy,s.signalRadius,0,Math.PI*2);ctx.clip();
    ctx.lineCap="round";
    for(let i=0;i<total;i++){
      const enabled=Math.max(0,Math.min(1,(packets-i+1)/2.8));
      const route=flowRoutes[i],count=route.length-1;
      if(count<2)continue;
      const travel=s.flowClock*(.23+.031*(i%5))*count+i*2.17;
      const step=Math.floor(travel);
      const previous=s.pathLastSteps[i];
      if(previous!=null&&step>previous&&enabled>.015){
        // Each boundary crossed represents an actual visited node. Flash it,
        // not a disconnected random dot. The subsequent segment continues
        // from exactly that node, including when a path reverses direction.
        const last=Math.min(step,previous+4);
        for(let k=previous+1;k<=last;k++){
          const cycle=count*2;
          const edge=((k%cycle)+cycle)%cycle;
          const node=route[edge<=count?edge:cycle-edge];
          s.nodeFlashAt[node]=t;
          s.nodeFlashHue[node]=hue;
          s.pathHops=(s.pathHops||0)+1;
        }
      }
      s.pathLastSteps[i]=step;
      if(enabled<.025||activity<.015)continue;
      const head=flowPosition(route,travel,projected);
      const depth=Math.max(.28,Math.min(1,(head[2]+1)*.54));
      const gate=Math.min(1,(travel-Math.floor(travel))/.22+.24);
      const alpha=enabled*activity*depth*gate;
      if(alpha<.015)continue;
      let prior=head;
      // The trailing packet spans successive *connected* edges, so it
      // remains continuous as the head crosses a graph vertex.
      for(let j=1;j<=7;j++){
        const earlier=flowPosition(route,travel-j*.20,projected);
        const strength=Math.pow(1-j/8,1.5);
        ctx.strokeStyle="hsla("+hue.toFixed(1)+","+sat.toFixed(0)+"%,92%,"+
          Math.min(.9,alpha*strength*.82).toFixed(3)+")";
        ctx.lineWidth=(.68+1.75*alpha*strength)*dpr;
        ctx.beginPath();ctx.moveTo(prior[0],prior[1]);ctx.lineTo(earlier[0],earlier[1]);ctx.stroke();
        prior=earlier;
      }
      ctx.fillStyle="hsla("+hue.toFixed(1)+","+Math.min(100,sat+7).toFixed(0)+
        "%,96%,"+Math.min(1,alpha*.94).toFixed(3)+")";
      ctx.beginPath();ctx.arc(head[0],head[1],(1.2+2.25*alpha)*dpr,0,Math.PI*2);ctx.fill();
    }
    ctx.lineCap=oldCap;
    // The hit flare belongs to the actual mesh node and is drawn with its
    // 3D projection. A new hit refreshes its lifetime rather than blinking
    // every node uniformly.
    for(let i=0;i<s.nodeFlashAt.length;i++){
      const age=t-s.nodeFlashAt[i];
      if(age<0||age>680)continue;
      const p=projected[i];
      const rise=Math.min(1,age/38+.25);
      const decay=Math.exp(-age/235);
      const strength=rise*decay*Math.max(.1,activity);
      if(strength<.055)continue;
      const depth=Math.max(.30,Math.min(1,(p[2]+1)/2));
      const intensity=Math.min(.98,strength*depth*1.45);
      const color=s.nodeFlashHue[i];
      ctx.fillStyle="hsla("+color.toFixed(0)+",28%,98%,"+intensity.toFixed(3)+")";
      ctx.beginPath();ctx.arc(p[0],p[1],(2.5+4*strength)*dpr,0,Math.PI*2);ctx.fill();
      if(intensity>.2){
        const halo=ctx.createRadialGradient(p[0],p[1],0,p[0],p[1],(8+10*strength)*dpr);
        halo.addColorStop(0,"rgba(244,250,255,"+(intensity*.46).toFixed(3)+")");
        halo.addColorStop(.46,"rgba(185,225,255,"+(intensity*.13).toFixed(3)+")");
        halo.addColorStop(1,"rgba(165,220,255,0)");
        ctx.fillStyle=halo;
        ctx.beginPath();ctx.arc(p[0],p[1],(8+10*strength)*dpr,0,Math.PI*2);ctx.fill();
      }
    }
    // In processing mode dozens of independent, brief white node flares
    // carry the rhythm. Unlike the listening state, the accents are white.
    const whiteIntensity=Math.min(1,think*1.4+speak*.55);
    if(whiteIntensity>.012){
      for(let i=1;i<projected.length;i+=(/Android/i.test(navigator.userAgent)?4:3)){
        const p=projected[i],wave=(Math.sin(t*.0065+i*2.391)+1)*.5;
        const flash=Math.pow(wave,13)*whiteIntensity;
        if(flash<.07)continue;
        const depth=Math.max(.28,Math.min(1,(p[2]+1)*.6));
        const alpha=flash*depth;
        ctx.fillStyle="rgba(244,246,255,"+Math.min(.95,alpha*.9).toFixed(3)+")";
        ctx.beginPath();ctx.arc(p[0],p[1],(1.7+3.1*flash)*dpr,0,Math.PI*2);ctx.fill();
        if(flash>.55&&(i%4)===1){
          const soft=ctx.createRadialGradient(p[0],p[1],0,p[0],p[1],10*dpr);
          soft.addColorStop(0,"rgba(250,250,255,"+(alpha*.40).toFixed(3)+")");
          soft.addColorStop(1,"rgba(240,240,255,0)");
          ctx.fillStyle=soft;ctx.beginPath();ctx.arc(p[0],p[1],10*dpr,0,Math.PI*2);ctx.fill();
        }
      }
    }
    ctx.restore();
  }


  function spawnComet(t,initial=false,mode="idle"){
  const r=(lo,hi)=>lo+Math.random()*(hi-lo);
  return {
    born:t-(initial?r(150,1100):0),
    duration:mode==="processing"?r(1300,2350):mode==="listening"?r(1750,2800):r(2100,3700),
    start:r(-Math.PI,Math.PI),
    speed:(Math.random()<.5?-1:1)*(mode==="processing"?r(.00075,.00138):mode==="listening"?r(.00042,.00096):r(.00032,.00078)),
    orbit:mode==="processing"?r(.86,1.30):mode==="listening"?r(.96,1.32):r(1.03,1.32),
    incline:r(-1.05,1.05),
    turn:r(-Math.PI,Math.PI),
    flatten:r(.68,1.06),
    tailMs:mode==="processing"?r(220,460):mode==="listening"?r(340,640):r(330,670),
    color:mode==="processing"?255:mode==="speaking"?290:Math.random()<.76?182:205,
    strength:mode==="processing"?r(.8,1.17):r(.66,1),
    size:mode==="processing"?r(1.55,2.95):r(1.55,2.5)
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
  function drawComets(ctx,s,t,cx,cy,radius,dpr,activity,hue,visual){
  if(!s.comets){
    s.comets=[spawnComet(t,true,"idle"),spawnComet(t,true,"idle"),spawnComet(t,true,"idle")];
    s.nextCometAt=t+600;
  }
  s.comets=s.comets.filter(c=>t-c.born<c.duration);
  if(t>=s.nextCometAt){
    const mode=visual.processing>visual.listening&&visual.processing>visual.speaking?"processing":
      visual.listening>visual.speaking&&visual.listening>.25?"listening":
      visual.speaking>.25?"speaking":"idle";
    const capacity=Math.round(3+3*visual.listening+6*visual.processing+4*visual.speaking);
    if(s.comets.length<capacity)s.comets.push(spawnComet(t,false,mode));
    s.nextCometAt=t+(650-370*activity)+Math.random()*(790-340*activity);
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
      const stepHue=c.color+(hue-c.color)*activity;
      const saturation=83*visual.idle+92*visual.listening+18*visual.processing+33*visual.speaking;
      const luminosity=78*visual.idle+81*visual.listening+94*visual.processing+91*visual.speaking;
      ctx.strokeStyle="hsla("+stepHue.toFixed(1)+","+saturation.toFixed(0)+"%,"+luminosity.toFixed(1)+"%,"+(alpha*power*.76).toFixed(3)+")";
      ctx.lineWidth=(.45+power*1.45)*dpr;
      ctx.beginPath();
      ctx.moveTo(previous.x,previous.y);
      ctx.lineTo(earlier.x,earlier.y);
      ctx.stroke();
      previous=earlier;
    }
    // Brief, bright cyan/white tip with a very soft halo.
    const cometHue=c.color+(hue-c.color)*activity;
    const glowRadius=(6+c.size*2)*dpr;
    const glow=ctx.createRadialGradient(head.x,head.y,0,head.x,head.y,glowRadius);
    const whiteMix=Math.min(1,visual.processing+visual.speaking*.8);
    const tipSat=98-68*whiteMix;
    glow.addColorStop(0,"hsla("+cometHue+","+tipSat.toFixed(0)+"%,97%,"+(alpha*.38).toFixed(3)+")");
    glow.addColorStop(.28,"hsla("+cometHue+","+tipSat.toFixed(0)+"%,87%,"+(alpha*.16).toFixed(3)+")");
    glow.addColorStop(1,"hsla("+cometHue+","+tipSat.toFixed(0)+"%,70%,0)");
    ctx.fillStyle=glow;
    ctx.beginPath();ctx.arc(head.x,head.y,glowRadius,0,Math.PI*2);ctx.fill();
    ctx.fillStyle="hsla("+cometHue+","+tipSat.toFixed(0)+"%,96%,"+(alpha*.94).toFixed(3)+")";
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
  // One continuously blended palette drives the entire 3D scene. A new
  // voice phase retargets the weights instead of restarting an animation.
  // This is stable even when native Assist rapidly changes its phase.
  const visualDelta=Math.max(0,Math.min(90,t-(s.lastVisualFrame??t)));
  s.lastVisualFrame=t;
  if(!s.visual){
    s.visual={idle:0,listening:0,processing:0,speaking:0};
    s.visual[phase in s.visual?phase:"idle"]=1;
  }
  const visual=s.visual;
  const fade=1-Math.exp(-visualDelta/(phase==="idle"?490:170));
  for(const key of ["idle","listening","processing","speaking"])
    visual[key]+=((phase===key?1:0)-visual[key])*fade;
  const activity=Math.max(0,Math.min(1,1-visual.idle));
  const energy=visual.listening*.58+visual.processing*1+visual.speaking*.83;
  const phaseAge=Math.max(0,t-(s.phaseChangeAt??t));
  const onset=s.phase==="idle"?0:Math.exp(-phaseAge/470);
  const hue=215*visual.idle+184*visual.listening+260*visual.processing+295*visual.speaking;
  const speed=.55*visual.idle+1.05*visual.listening+1.68*visual.processing+1.24*visual.speaking;
  const pulse=visual.listening*Math.sin(t*.0035)*.014
    +visual.processing*Math.sin(t*.0082)*.029
    +visual.speaking*(Math.sin(t*.0052)*.020+Math.sin(t*.0118)*.007);
  const radius=Math.min(w*.42,h*.41)*(1+pulse);
  const cx=w*.5,cy=h*.51;
  // Cyan on activation; diffuse pearl-white while reasoning; silver
  // on output. The core flashes softly when a phase begins.
  const coreSat=38*visual.idle+92*visual.listening+16*visual.processing+32*visual.speaking;
  const coreLight=72*visual.idle+65*visual.listening+94*visual.processing+88*visual.speaking;
  const glow=ctx.createRadialGradient(cx,cy,0,cx,cy,radius*1.22);
  glow.addColorStop(0,`hsla(${hue.toFixed(1)},${coreSat.toFixed(1)}%,${coreLight.toFixed(1)}%,${(.12+.18*energy+.07*onset).toFixed(3)})`);
  glow.addColorStop(.56,`hsla(${hue.toFixed(1)},${coreSat.toFixed(1)}%,${coreLight.toFixed(1)}%,${(.052+.09*energy+.02*onset).toFixed(3)})`);
  glow.addColorStop(1,"rgba(12,22,42,0)");
  ctx.fillStyle=glow;ctx.fillRect(0,0,w,h);
  drawPhaseRings(ctx,s,t,cx,cy,radius,dpr);

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
    // Full 360° vertical turns remain free even while inertia fades.
    s.manualPitch+=oldPitch*step;
    s.inertiaYaw=oldYaw*spinFade;
    s.inertiaPitch=oldPitch*spinFade;
    const from=s.autoBlend??1;
    s.autoBlend=1-(1-from)*Math.exp(-frameDelta/780);
    s.orbitTime+=frameDelta*s.autoBlend;
  }
  const orbit=s.orbitTime;
  // Integrate angular velocity, not time * current velocity. Multiplying
  // an absolute timestamp by a phase-dependent speed causes the sphere to
  // teleport when listening changes to thinking or speaking.
  if(s.autoYaw===undefined)s.autoYaw=orbit*.00015*.55;
  else s.autoYaw+=Math.max(0,orbit-(s.lastHeadingOrbit??orbit))*.00015*speed;
  s.lastHeadingOrbit=orbit;
  const ay=s.autoYaw+(s.manualYaw||0);
  const ax=-.23+Math.sin(orbit*.00006)*(.022+.096*energy)+(s.manualPitch||0);
  const az=Math.sin(orbit*.000054)*(.012+.11*energy);
  const cosa=Math.cos(ay),sina=Math.sin(ay);
  const cosx=Math.cos(ax),sinx=Math.sin(ax);
  const cosz=Math.cos(az),sinz=Math.sin(az);
  const projected=mesh.points.map((p,i)=>{
    const movement=1+energy*(Math.sin(t*.00042+p[3])*.028+Math.cos(t*.00023+p[3]*1.7)*.017);
    const px=p[0]*movement+energy*.012*Math.sin(t*.00033+p[3]*2);
    const py=p[1]*movement+energy*.012*Math.cos(t*.00027+p[3]);
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
    const meshSat=36*visual.idle+91*visual.listening+19*visual.processing+36*visual.speaking;
    ctx.strokeStyle=`hsla(${hue.toFixed(1)},${meshSat.toFixed(0)}%,${(89+3*visual.processing).toFixed(1)}%,${opacity})`;
    ctx.beginPath();ctx.moveTo(u[0],u[1]);ctx.lineTo(v[0],v[1]);ctx.stroke();
  }
  for(let i=0;i<projected.length;i++){
    const p=projected[i],bright=i%11===0||mesh.anchorIndices.includes(i);
    const depth=(p[2]+1)/2,alpha=.21+.73*depth;
    const nodeSat=43*visual.idle+95*visual.listening+17*visual.processing+35*visual.speaking;
    ctx.fillStyle=`hsla(${hue.toFixed(1)},${nodeSat.toFixed(0)}%,95%,${alpha})`;
    ctx.beginPath();ctx.arc(p[0],p[1],(bright?1.7:.88)*dpr,0,Math.PI*2);ctx.fill();
    if(bright){
      ctx.fillStyle=`hsla(${hue.toFixed(1)},${nodeSat.toFixed(0)}%,92%,${(.07+.13*depth+.10*onset).toFixed(3)})`;
      ctx.beginPath();ctx.arc(p[0],p[1],(4.5+depth*2)*dpr,0,Math.PI*2);ctx.fill();
    }
  }
  // Short-lived 3D shooting stars around the sphere (no persistent orbit lines).
  s.signalCx=cx;s.signalCy=cy;s.signalRadius=radius*.98;
  drawSignals(ctx,s,t,projected,dpr,visual);
  // Outer comets deliberately remain free to orbit beyond the sphere.
  drawComets(ctx,s,t,cx,cy,radius,dpr,activity,hue,visual);
    // Sensor labels are tied to actual 3D nodes, including perspective/depth.
  if(++s.labelFrame>=1){
    for(let i=0;i<mesh.anchorIndices.length;i++){
      const label=s.metricNodes[i],p=projected[mesh.anchorIndices[i]];
      if(!label||!p)continue;
      const px=p[0]/dpr,py=p[1]/dpr,z=p[2];
      const mid=rect.width/2;
      const x=Math.max(43,Math.min(rect.width-43,mid+(px-mid)*1.08));
      const y=Math.max(25,Math.min(rect.height-23,rect.height*.51+(py-rect.height*.51)*1.07));
      const depthScale=.79+.22*Math.max(0,Math.min(1,(z+1)/2));
      const scale=.94*(1-activity)+depthScale*activity;
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
    const s={host,canvas,phase:"idle",lastFrame:0,lastOrbitFrame:null,lastHeadingOrbit:null,lastVisualFrame:null,visual:null,autoYaw:undefined,orbitTime:undefined,manualYaw:0,manualPitch:0,manualDragging:false,inertiaYaw:0,inertiaPitch:0,autoBlend:1,dragPointer:null,suppressClick:false,forceUntil:0,forcedPhase:"idle",infoTimer:null,controlsTimer:null,raf:null,unsubscribe:null,closing:false,labelFrame:0,metricNodes:Array.from(host.querySelectorAll("[data-ambient-metric]"))};
    active.set(card,s);
    const subscribeVisual=async binding=>{
      const connection=card.h?.connection;
      if(!connection?.subscribeMessage||!card.h?.callWS)return;
      const token=(s.visualToken||0)+1;s.visualToken=token;
      try{s.unsubscribe?.();}catch{}s.unsubscribe=null;
      try{
        const stop=await subscribeTafaVisual(card.h,data=>{
          if(active.get(card)!==s)return;
          const configured=Number(card.cfg?.presentation?.infoSeconds);
          const seconds=Number.isFinite(configured)&&configured>=5&&configured<=180?configured:30;
          show(card,{...data,title:data.title||data.topic||"TAFA Antwort",message:data.reply,seconds});
        },{binding:binding||null});
        if(active.get(card)!==s||s.visualToken!==token||card.h?.connection!==connection)stop?.();
        else s.unsubscribe=stop;
      }catch(err){console.debug("TAFA: Ambient Visualstream nicht verfügbar",err);}
    };
    const applyProfile=(profile,deviceId,revision)=>{
      if(active.get(card)!==s)return;
      s.profile=profile;s.deviceId=deviceId;s.profileRevision=revision;
      s.metricEntries=Array.isArray(profile?.metrics)?profile.metrics.slice(0,6).map(m=>({name:m.name||m.id,ids:[m.id],pattern:/(?!)/})):null;
      s.metricNodes.forEach((node,i)=>{
        const entry=s.metricEntries?.[i]||(s.metricEntries?null:metrics[i]);
        node.hidden=!entry;
        const title=node.querySelector("small");
        if(title&&entry)title.textContent=entry.name;
      });
      s.overview?.applyProfile?.(profile);
      // The local tablet identity arrives after the initial mount.
      // Rebind the response stream to the new installation ID now.
      if(card._tafaLocalVoice?.deviceId===deviceId)void subscribeVisual(deviceId);
      update(card);
    };
    const attachProfile=()=>{
      const connection=card.h?.connection;
      if(!connection||s.profileConnection===connection)return;
      s.profileConnection=connection;
      try{s.profileUnsub?.();}catch{}s.profileUnsub=null;
      Promise.resolve(subscribeOwnAmbientProfile(card,applyProfile))
        .then(stop=>{if(active.get(card)!==s||s.profileConnection!==connection)stop?.();else s.profileUnsub=stop;})
        .catch(error=>console.debug("TAFA Ambient profile unavailable",error));
    };
    s.attachProfile=attachProfile;attachProfile();
    // Load the optional calendar only for an active ambient display.
    void import("./ambient_overview.js?v=0.5.1")
      .then(mod=>{if(active.get(card)===s)mod.mountOverview(card,s);})
      .catch(err=>console.debug("TAFA ambient calendar unavailable",err));
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
      // Keep the vertical angle unbounded: any number of complete turns.
      s.manualPitch+=pitchDelta;
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
      // During the calendar materialization, give the tablet CPU/GPU
      // some headroom for the extra compositor and comet overlay.
      const android=/Android/i.test(navigator.userAgent);
      const building=android&&host.dataset.overviewBuilding==="1";
      if(time-s.lastFrame<(building?40:android?31:15))return;
      s.lastFrame=time;
      if(++frames%(android?4:13)===1)update(card);
      draw(card,s,time);
    };
    s.raf=requestAnimationFrame(loop);
    update(card);
    // Initial subscription is optional; applyProfile will rebind it once
    // pairing/profile resolution finishes, even after a fresh install.
    void subscribeVisual(card._tafaLocalVoice?.deviceId||card._tafaLocalVoice?.status||null);
  }
  function dispose(card){
    const s=active.get(card);if(!s)return;
    s.overview?.dispose?.();
    active.delete(card);s.visualToken=(s.visualToken||0)+1;cancelAnimationFrame(s.raf);
    clearTimeout(s.infoTimer);
    clearTimeout(s.controlsTimer);
    clearTimeout(s.dragPointer?.timer);
    s.dragPointer=null;
    s.manualDragging=false;
    try{s.unsubscribe?.();}catch{}
    try{s.profileUnsub?.();}catch{}
  }
  bag.parts.ambient={body,mount,update,show,close,dispose};
  // Optional enhancement: never take part in the required dashboard boot gate.
  try{document.dispatchEvent(new Event("tafa-integration-ambient-ready"));}catch(e){console.debug("TAFA Ambient ready",e);}
})();
