(function ambientModule(){
  "use strict";
  const bag=globalThis[Symbol.for("hauszentrale-kiosk.modules.v1")]??={parts:Object.create(null)};
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
  .wrap.hz-night-view {--ambient:#9fcef4;background:#07111d!important;color:#eff5ff!important}
  .hz-night-view>aside {display:none!important}
  .hz-night-view>main {width:100%;max-width:none!important;min-height:100%;background:#07111d!important;padding:0!important;overflow-x:hidden}
  .hz-night-view .top {position:absolute!important;z-index:12;top:0;right:0;left:0;margin:0!important;padding:14px 20px!important;background:transparent!important;border:0!important;box-shadow:none!important;pointer-events:none}
  .hz-night-view .top>div:first-child,.hz-night-view .hz-header-clock,.hz-night-view .hz-subnav{display:none!important}
  .hz-night-view .top .hz-header-right,.hz-night-view .top .hz-header-actions{pointer-events:auto}
  .hz-night-view .top .hz-header-button {background:#132a3d88!important;color:#a9c8e4!important;border:1px solid #9fd1fa32!important;backdrop-filter:blur(6px)}
  .wrap.hz-night-view>main>header:not(.hz-ambient-head){position:absolute!important;right:12px;top:0;left:auto;z-index:16;min-height:0!important;width:auto;margin:0!important;padding:12px!important;max-width:none!important;background:transparent!important;border:0;box-shadow:none}
  .wrap.hz-night-view>main>header>div:first-child,.wrap.hz-night-view>main>header .header-clock{display:none!important}
  .wrap.hz-night-view>main>header .quick{background:#132a3dbb!important;color:#b9d8f2!important;border:1px solid #9fd1fa32!important;backdrop-filter:blur(6px)}
  .wrap.hz-night-view .body{max-width:none!important;margin:0!important;width:100%}
  .wrap.hz-night-view .subnav,.wrap.hz-night-view .native,.wrap.hz-night-view .native-details{display:none!important}
  .hz-ambient-body {margin:0!important;position:relative;isolation:isolate;display:flex;flex-direction:column;align-items:center;min-height:var(--hz-available-height,100dvh);overflow:hidden;background:radial-gradient(ellipse at 50% 48%,#14213c 0%,#0a1425 43%,#070e1b 84%);color:#edf5ff;font:inherit}
  .hz-ambient-body:before{content:"";position:absolute;inset:0;z-index:-1;opacity:.38;pointer-events:none;background:radial-gradient(circle at 22% 22%,#284d7644 0,transparent 28%),radial-gradient(circle at 76% 78%,#102a4d55 0,transparent 30%)}
  .hz-ambient-head{position:relative;z-index:2;margin-top:clamp(52px,8vh,96px);text-align:center}
  .hz-ambient-time{font-size:clamp(62px,10.4vw,116px);font-weight:300;letter-spacing:-.063em;font-variant-numeric:tabular-nums;line-height:1.04;text-shadow:0 0 26px #9dcaf723}
  .hz-ambient-date{margin-top:8px;color:#9db1c6;font-size:clamp(13px,1.55vw,17px);font-weight:400;letter-spacing:.025em}
  .hz-ambient-stage{width:min(82vw,750px);height:clamp(300px,48vh,560px);position:relative;flex:1 0 auto;max-height:62vh;min-height:290px;margin:clamp(0px,2vh,20px) auto 14px}
  .hz-ambient-canvas{display:block;width:100%;height:100%;pointer-events:none}
  .hz-ambient-metric{position:absolute;z-index:2;transform:translate(-50%,-50%);min-width:90px;max-width:160px;text-align:center;font-variant-numeric:tabular-nums;white-space:nowrap;pointer-events:none;text-shadow:0 1px 5px #051220}
  .hz-ambient-metric small{display:block;color:#8ca8c3;letter-spacing:.12em;font-size:clamp(8px,.85vw,10px);margin-bottom:4px}
  .hz-ambient-metric b{display:block;font-weight:500;font-size:clamp(11px,1.15vw,15px);color:#e4f1ff}
  .hz-ambient-metric i{position:absolute;top:50%;width:20px;height:1px;background:#7da6cb77}
  .hz-ambient-metric:nth-of-type(1){left:14%;top:24%}
  .hz-ambient-metric:nth-of-type(2){left:85%;top:24%}
  .hz-ambient-metric:nth-of-type(3){left:6%;top:53%}
  .hz-ambient-metric:nth-of-type(4){left:92%;top:56%}
  .hz-ambient-metric:nth-of-type(5){left:22%;top:82%}
  .hz-ambient-metric:nth-of-type(6){left:80%;top:82%}
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
  @media(max-width:800px){.hz-ambient-head{margin-top:76px}.hz-ambient-stage{width:min(100vw,610px);height:45vh;min-height:270px}.hz-ambient-time{font-size:clamp(66px,13vw,96px)}.hz-ambient-metric:nth-of-type(3){left:11%}.hz-ambient-metric:nth-of-type(4){left:89%}}
  @media(max-width:500px){.hz-ambient-stage{min-height:290px;height:42vh}.hz-ambient-metric{min-width:65px}.hz-ambient-metric:nth-of-type(1){left:17%;top:16%}.hz-ambient-metric:nth-of-type(2){left:82%;top:16%}.hz-ambient-metric:nth-of-type(3){left:12%;top:51%}.hz-ambient-metric:nth-of-type(4){left:88%;top:51%}.hz-ambient-metric:nth-of-type(5){left:24%;top:86%}.hz-ambient-metric:nth-of-type(6){left:77%;top:86%}}
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
    return `<style>${style}</style><section class="hz-ambient-body" data-phase="idle" aria-label="TAFA Ambient Nachtansicht">
      <header class="hz-ambient-head"><div id="hz-night-clock" class="hz-ambient-time">--:--</div><div id="hz-night-date" class="hz-ambient-date"></div></header>
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
    if(/speaking|playing|antwort|tts/.test(mic))return "speaking";
    if(/process|thinking|busy|verarbeit|erkenn|sent|gesendet/.test(mic+" "+wake))return "processing";
    if(/listen|record|wake|detect|active|aufnah|hör|hoer/.test(mic+" "+wake)&&!/inactive|not_active/.test(mic+" "+wake))return "listening";
    const last=h["sensor.tafa_jarvis_tablet_letztes_rufwort"]?.state;
    if(last&&Date.now()-Date.parse(last)<7000)return "listening";
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
    const points=[];
    for(let i=0;i<105;i++){
      const z=1-2*(i+.5)/105;
      const t=i*2.399963229728653;
      const r=Math.sqrt(1-z*z);
      points.push([r*Math.cos(t),z,r*Math.sin(t)]);
    }
    const edges=[];
    for(let i=0;i<points.length;i++){
      const closest=[];
      for(let j=i+1;j<points.length;j++){
        const d=Math.hypot(points[i][0]-points[j][0],points[i][1]-points[j][1],points[i][2]-points[j][2]);
        if(d<.53)closest.push([j,d]);
      }
      closest.sort((a,b)=>a[1]-b[1]);
      for(const [j] of closest.slice(0,3))edges.push([i,j]);
    }
    return {points,edges};
  }
  const mesh=makeMesh();
  function draw(card,s,t){
    const canvas=s.canvas,rect=canvas.getBoundingClientRect();
    if(!rect.width||!rect.height)return;
    const dpr=Math.min(window.devicePixelRatio||1,1.5);
    const w=Math.round(rect.width*dpr),h=Math.round(rect.height*dpr);
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
    const ctx=canvas.getContext("2d");if(!ctx)return;
    ctx.clearRect(0,0,w,h);
    const phase=s.phase;
    const hue=phase==="listening"?186:phase==="processing"?264:phase==="speaking"?296:214;
    const speed=phase==="idle"?1:1.55;
    const pulse=phase==="idle"?.0:Math.sin(t*.006)*.03;
    const radius=Math.min(w,h)*(.35+pulse);
    const cx=w*.5,cy=h*.49;
    const ambient=ctx.createRadialGradient(cx,cy,0,cx,cy,radius*1.32);
    ambient.addColorStop(0,`hsla(${hue},90%,55%,${phase==="idle"?.09:.23})`);
    ambient.addColorStop(.66,`hsla(${hue},76%,48%,.045)`);
    ambient.addColorStop(1,`hsla(${hue},50%,20%,0)`);
    ctx.fillStyle=ambient;ctx.fillRect(0,0,w,h);
    const ay=t*.00014*speed,ax=-.22+Math.sin(t*.00018)*.2,az=Math.sin(t*.00011)*.13;
    const projected=mesh.points.map(([x,y,z])=>{
      let rx=x*Math.cos(ay)+z*Math.sin(ay);
      let rz=z*Math.cos(ay)-x*Math.sin(ay);
      let ry=y*Math.cos(ax)-rz*Math.sin(ax);
      rz=y*Math.sin(ax)+rz*Math.cos(ax);
      const px=rx*Math.cos(az)-ry*Math.sin(az);
      const py=rx*Math.sin(az)+ry*Math.cos(az);
      const f=2.3/(2.3-rz*.35);
      return [cx+radius*px*f,cy+radius*py*f,rz];
    });
    ctx.lineWidth=Math.max(.6,dpr*.85);
    for(const [a,b] of mesh.edges){
      const p=projected[a],q=projected[b];
      ctx.strokeStyle=`hsla(${hue},${phase==="idle"?34:85}%,${phase==="idle"?82:76}%,${.12+.33*(2+p[2]+q[2])/4})`;
      ctx.beginPath();ctx.moveTo(p[0],p[1]);ctx.lineTo(q[0],q[1]);ctx.stroke();
    }
    for(let i=0;i<projected.length;i++){
      const p=projected[i],bright=i%13===0,alpha=.3+.52*(p[2]+1)/2;
      ctx.fillStyle=`hsla(${hue},${phase==="idle"?33:87}%,${bright?97:87}%,${alpha})`;
      ctx.beginPath();ctx.arc(p[0],p[1],(bright?1.9:1.05)*dpr,0,Math.PI*2);ctx.fill();
      if(bright){ctx.fillStyle=`hsla(${hue},90%,72%,.085)`;ctx.beginPath();ctx.arc(p[0],p[1],6*dpr,0,Math.PI*2);ctx.fill();}
    }
    ctx.lineWidth=.8*dpr;
    for(let i=0;i<4;i++){
      const start=t*.00010*(i%2?1:-1)+i*1.56;
      ctx.strokeStyle=`hsla(${hue},75%,72%,${i%2?.18:.1})`;
      ctx.beginPath();ctx.ellipse(cx,cy,radius*(1.09+i*.055),radius*(.28+.15*(i%3)),start*.29,-.5+start,.4+start);ctx.stroke();
    }
    for(let i=0;i<7;i++){
      const a=t*.00021*(i%2?1:-1)+i*1.913;
      const x=cx+Math.cos(a)*radius*(.87+.06*(i%3));
      const y=cy+Math.sin(a)*radius*(.68+.05*(i%2));
      ctx.fillStyle=`hsla(${hue},92%,83%,.75)`;
      ctx.beginPath();ctx.arc(x,y,(i%3===0?2.3:1.25)*dpr,0,Math.PI*2);ctx.fill();
    }
  }
  function mount(card){
    dispose(card);
    if(!card?._hzNight||!card.shadowRoot)return;
    const host=card.shadowRoot.querySelector(".hz-ambient-body"),canvas=host?.querySelector("canvas");
    if(!host||!canvas)return;
    const s={host,canvas,phase:"idle",lastFrame:0,forceUntil:0,forcedPhase:"idle",infoTimer:null,raf:null,unsubscribe:null,closing:false};
    active.set(card,s);
    let frames=0;
    const loop=(time)=>{
      if(active.get(card)!==s||!card.isConnected||!card._hzNight||!host.isConnected)return;
      s.raf=requestAnimationFrame(loop);
      if(document.hidden)return;
      if(time-s.lastFrame<40)return;
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
    try{s.unsubscribe?.();}catch{}
  }
  bag.parts.ambient={body,mount,update,show,close,dispose};
  // Optional enhancement: never take part in the required dashboard boot gate.
  try{document.dispatchEvent(new Event("tafa-ambient-ready"));}catch(e){console.debug("TAFA Ambient ready",e);}
})();
