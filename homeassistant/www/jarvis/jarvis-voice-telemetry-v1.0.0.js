/* Jarvis voice phase timings v1.0.0. No audio, text, names or tokens. */
const KEY="jarvis.dashboard.voice.timing.v1",MAX=50;
const clock=()=>performance.now();
const millis=(a,b)=>Number.isFinite(a)&&Number.isFinite(b)&&b>=a?Math.round(b-a):null;
function load(){try{const x=JSON.parse(localStorage.getItem(KEY)||"[]");return Array.isArray(x)?x.slice(-MAX):[];}catch{return []}}
function save(entry){const data=load();data.push(entry);try{localStorage.setItem(KEY,JSON.stringify(data.slice(-MAX)));}catch{}}
function fmt(row){return Math.round(Number(row)||0)}
export function voiceTimingSamples(){return load()}
export function clearVoiceTiming(){try{localStorage.removeItem(KEY)}catch{}}
export function voiceTimingSummary(){
 const rows=load().filter(x=>x.ok),keys=["whisperMs","routerMs","ttsMs","relayMs","wakeToAudioMs"];
 const result={count:rows.length,failures:load().filter(x=>!x.ok).length};
 for(const key of keys){const a=rows.map(x=>x[key]).filter(Number.isFinite).sort((a,b)=>a-b);
  result[key]=a.length?{n:a.length,avg:fmt(a.reduce((p,c)=>p+c,0)/a.length),p95:a[Math.ceil(.95*a.length)-1],max:a.at(-1)}:null;}
 return result;
}
export function installVoiceTelemetry(Voice){
 const p=Voice?.prototype;if(!p||p._timingInstrumented)return;
 Object.defineProperty(p,"_timingInstrumented",{value:true});
 const oldCapture=p.capture;
 if(typeof oldCapture==="function")p.capture=function(wake,follow=false){
  if(!wake)this._jvTiming={model:follow?"Anschlussfrage":"Manuell",from:clock()};
  return oldCapture.call(this,wake,follow);
 };
 const oldEndMic=p.endMic;
 if(typeof oldEndMic==="function")p.endMic=function(s,signal=false){
  if(signal&&this._jvTiming&&!Number.isFinite(this._jvTiming.audioSent))this._jvTiming.audioSent=clock();
  return oldEndMic.call(this,s,signal);
 };
 const oldEvent=p.event;
 if(typeof oldEvent==="function")p.event=function(s,e){
  const type=e?.type,ts=clock();
  if(type==="wake_word-end"){this._jvTiming={model:s?.wakeModel||"Rufwort",from:ts,wakeAt:ts};}
  const t=this._jvTiming;
  if(t&&type){
   if(type==="stt-start")t.sttStart=ts;
   if(type==="stt-end")t.sttEnd=ts;
   if(type==="intent-start")t.intentStart=ts;
   if(type==="intent-end")t.intentEnd=ts;
   if(type==="tts-start")t.ttsStart=ts;
   if(type==="tts-end")t.ttsEnd=ts;
  }
  return oldEvent.call(this,s,e);
 };
 const oldState=p.state;
 if(typeof oldState==="function")p.state=function(phase,detail){
  const t=this._jvTiming;
  if(t&&!Number.isFinite(t.playAt)&&(/^Spricht/.test(String(phase))||phase==="Spricht · Echo Relay")){
   t.playAt=clock();t.route=this._playbackRoute||this.output||"unbekannt";
   t.confirmed=phase==="Spricht · Echo Relay";
  }
  return oldState.call(this,phase,detail);
 };
 function flush(self,ok){
  const t=self._jvTiming;if(!t)return;
  self._jvTiming=null;
  save({ts:Date.now(),model:String(t.model||"unbekannt").slice(0,28),route:String(t.route||self._playbackRoute||"unbekannt").slice(0,30),
   ok:!!ok,confirmed:!!t.confirmed,
   whisperMs:millis(t.audioSent,t.sttEnd),
   routerMs:millis(t.intentStart,t.intentEnd),
   ttsMs:millis(t.ttsStart,t.ttsEnd),
   relayMs:millis(t.ttsEnd,t.playAt),
   wakeToAudioMs:millis(t.wakeAt,t.playAt)});
 }
 const oldFinishPlayback=p.finishPlayback;
 if(typeof oldFinishPlayback==="function")p.finishPlayback=function(keep){flush(this,true);return oldFinishPlayback.call(this,keep);};
 const oldPlayError=p.playError;
 if(typeof oldPlayError==="function")p.playError=function(msg){flush(this,false);return oldPlayError.call(this,msg);};
 const oldFail=p.fail;
 if(typeof oldFail==="function")p.fail=function(s,msg){flush(this,false);return oldFail.call(this,s,msg);};
 const oldSilent=p.finishSilent;
 if(typeof oldSilent==="function")p.finishSilent=function(s){this._jvTiming=null;return oldSilent.call(this,s);};
 const oldStop=p.stop;
 if(typeof oldStop==="function")p.stop=function(...args){this._jvTiming=null;return oldStop.apply(this,args);};
}
