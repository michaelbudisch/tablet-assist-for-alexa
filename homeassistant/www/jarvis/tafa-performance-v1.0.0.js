/* TAFA performance monitor v1.0.0: per-browser measurements, no network. */
export function installPerformance(HZ) {
 const p=HZ?.prototype;if(!p||p.hzPerfPage)return;
 const sample=c=>c._hzPerf??={render:[],refresh:[],fps:null,measuring:false};
 const measure=(c,k,ms)=>{if(!Number.isFinite(ms))return;const a=sample(c)[k];a.push(+ms.toFixed(2));if(a.length>100)a.shift();};
 for(const k of ["render","refresh"]){const orig=p[k];if(typeof orig!=="function")continue;
  p[k]=function(...args){const t=performance.now();try{return orig.apply(this,args);}finally{measure(this,k,performance.now()-t);}};
 }
 const summary=a=>{if(!a.length)return {n:0,mean:0,p95:0,max:0};
  const s=[...a].sort((x,y)=>x-y);return {n:a.length,mean:a.reduce((x,y)=>x+y,0)/a.length,p95:s[Math.ceil(.95*s.length)-1],max:s.at(-1)};};
 p.hzPerfSnapshot=function(){const d=sample(this);return {render:summary(d.render),refresh:summary(d.refresh),fps:d.fps};};
 p.hzPerfPage=function(){const x=this.hzPerfSnapshot(),fmt=n=>Number(n).toFixed(1);
  const line=(name,s)=>'<div class="hz-edit-row"><strong>'+name+'</strong><small>'+s.n+' Messungen · Ø '+fmt(s.mean)+' ms · p95 '+fmt(s.p95)+' ms · Max '+fmt(s.max)+' ms</small></div>';
  return '<section class="hz-settings-group" data-hz-perf-panel><h3>TAFA · Performance-Monitor</h3>'+
  '<p class="hz-settings-desc">Laufzeitmessung in diesem Browser. Eine Bildratenmessung startet nur auf Knopfdruck.</p>'+
  line('Dashboard-Aktualisierung',x.refresh)+line('Seitenaufbau',x.render)+
  '<p>Bildrate: <strong>'+(x.fps===null?'Noch nicht gemessen':fmt(x.fps)+' FPS')+'</strong></p>'+
  '<button class="btn" data-hz-perf="fps">3 Sekunden FPS messen</button> '+
  '<button class="btn" data-hz-perf="refresh">Aktualisieren</button> '+
  '<button class="btn" data-hz-perf="reset">Zurücksetzen</button></section>';
 };
 p.hzPerfRefreshPanel=function(){const old=this.shadowRoot?.querySelector('[data-hz-perf-panel]');if(!old)return;
  const tmp=document.createElement('div');tmp.innerHTML=this.hzPerfPage();if(tmp.firstElementChild)old.replaceWith(tmp.firstElementChild);};
 p.hzPerfMeasureFPS=function(){const s=sample(this);if(s.measuring||typeof requestAnimationFrame!=="function")return;
  s.measuring=true;let prev=0,count=0,elapsed=0;const begun=performance.now();
  const frame=t=>{if(!this.isConnected||document.hidden||this.page!=="einstellungen"||this.settingsTab!=="diagnose"){s.measuring=false;return;}
   if(prev){elapsed+=t-prev;count++;}prev=t;
   if(t-begun<3000){requestAnimationFrame(frame);return;}
   s.fps=elapsed>0?Math.round(10000*count/elapsed)/10:null;s.measuring=false;this.hzPerfRefreshPanel();};
  requestAnimationFrame(frame);
 };
 const click=p.click;if(typeof click==="function")p.click=function(e){
  const b=e.target?.closest?.('[data-hz-perf]');if(!b)return click.call(this,e);
  e.preventDefault();e.stopPropagation();
  if(b.dataset.hzPerf==="reset"){this._hzPerf=undefined;this.hzPerfRefreshPanel();}
  if(b.dataset.hzPerf==="fps")this.hzPerfMeasureFPS();
  if(b.dataset.hzPerf==="refresh")this.hzPerfRefreshPanel();
 };
}
