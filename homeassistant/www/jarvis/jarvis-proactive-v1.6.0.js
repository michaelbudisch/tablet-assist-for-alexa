/* Opt-in proactive greetings. One HA-coordinated speaker; no face recognition. */
const rpc=(v,data)=>v.h.callWS({type:'call_service',domain:'jarvis_tablet_audio',service:'proactive',service_data:data,return_response:true}).then(r=>r?.response??r?.service_response??r);
const historyPrefix='JVD1 ';
const historyEntity='automation.jarvis_tablet_bewegung_mit_vision';
const skippedChecks=new Set(['cooldown','disabled','outside_window','already_today','no_idle_dashboard','no_fresh_motion','busy']);
async function historyLog(v,record){try{await v.h.callService('logbook','log',{name:'Jarvis Vision Diagnose',entity_id:historyEntity,message:historyPrefix+JSON.stringify(record)});return true;}catch{return false;}}
async function visionModel(v){try{const r=await v.h.callWS({type:'call_service',domain:'jarvis_tablet_audio',service:'camera_vision_status',service_data:{},return_response:true});return (r?.response??r?.service_response??r)?.model||'';}catch{return '';}}
function mountHistory(v,section,root,names){
 const history=node('details');history.open=true;
 history.append(node('summary',t(v,'Erkennungsverlauf','Detection history')));
 const content=node('div',null,'jvs-panel');history.append(content);section.append(history);
 content.append(node('p',t(v,'Letzte 50 Einträge aus dem HA-Logbuch (bis zu 7 Tage, abhängig von der Recorder-Aufbewahrung). Nur Text, keine Bilder. Kategorien sind Schätzungen, keine Identitäten.','Latest 50 entries from the HA logbook (up to 7 days, subject to recorder retention). Text only, no images. Categories are estimates, not identities.'),'jvs-muted'));
 const list=node('div',null,'jvs-panel');const refresh=node('button',t(v,'Verlauf aktualisieren','Refresh history'));refresh.type='button';content.append(refresh,list);
 let busy=false,loaded=false;
 async function loadHistory(){if(busy||!root.isConnected||root.hidden)return;busy=true;refresh.disabled=true;
 try{const end=new Date(),start=new Date(end.getTime()-7*86400000);const response=await v.h.callWS({type:'logbook/get_events',start_time:start.toISOString(),end_time:end.toISOString(),entity_ids:[historyEntity]});const events=Array.isArray(response)?response:response?.result;if(!Array.isArray(events))throw Error('Invalid logbook response');
 const rows=events.filter(e=>typeof e.message==='string'&&e.message.startsWith(historyPrefix)).map(e=>{try{return {entry:e,data:JSON.parse(e.message.slice(historyPrefix.length))};}catch{return null;}}).filter(Boolean).sort((a,b)=>Number(b.entry.when)-Number(a.entry.when)).slice(0,50);
 list.replaceChildren();if(!rows.length)list.append(node('p',t(v,'Noch keine protokollierten Auswertungen.','No recorded checks yet.'),'jvs-muted'));
 for(const {entry,data} of rows){const card=node('div',null,'jvs-section');const when=typeof entry.when==='number'?new Date(entry.when*1000):new Date(entry.when);const type=data.kind==='greeting'?t(v,'Begrüßung','Greeting'):data.kind==='manual'?t(v,'Manueller Test','Manual check'):data.kind==='setup'?t(v,'Diagnose','Diagnostics'):t(v,'Automatik','Automatic');card.append(node('strong',(Number.isNaN(when.getTime())?'':when.toLocaleString())+' · '+type),node('span',data.kind==='setup'?t(v,'Verlauf eingerichtet','History enabled'):statusText(v,data.status||'unknown')));
 if(Array.isArray(data.labels)&&data.labels.length)card.append(node('span',t(v,'Kategorien: ','Categories: ')+data.labels.map(k=>names[k]||k).join(', ')));
 if(data.model)card.append(node('span',t(v,'Konfiguriertes Modell: ','Configured model: ')+data.model,'jvs-muted'));
 if(Number.isFinite(data.ms))card.append(node('span',t(v,'Prüfdauer: ','Check duration: ')+(data.ms/1000).toFixed(2)+' s','jvs-muted'));
 if(data.message)card.append(node('span',t(v,'Ausgabe begonnen: ','Playback started: ')+String(data.message)));
 list.append(card);}
 loaded=true;
 }catch{list.replaceChildren(node('p',t(v,'Verlauf konnte nicht geladen werden. HA-Logbuch prüfen.','Unable to load history. Check the HA logbook.'),'jvs-muted'));}
 finally{busy=false;refresh.disabled=false;}}
 refresh.onclick=()=>void loadHistory();history.addEventListener('toggle',()=>{if(history.open)void loadHistory();});const observer=new MutationObserver(()=>{if(!root.hidden&&!loaded)void loadHistory();});observer.observe(root,{attributes:true,attributeFilter:['hidden']});const cleanup=new MutationObserver(()=>{if(!root.isConnected){observer.disconnect();cleanup.disconnect();}});cleanup.observe(root.getRootNode(),{childList:true,subtree:true});if(!root.hidden)void loadHistory();
 return loadHistory;
}
const t=(v,de,en)=>String(v.h?.language||navigator.language).startsWith('de')?de:en;
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
const makeId=()=>[...crypto.getRandomValues(new Uint8Array(16))].map(x=>x.toString(16).padStart(2,'0')).join('');
const statuses={idle:['Noch keine Auswertung','No check yet'],disabled:['Ausgeschaltet','Disabled'],cooldown:['Sperrzeit aktiv','Cooldown active'],busy:['Sprachverarbeitung oder Vision beschäftigt','Speech or vision is busy'],no_fresh_motion:['Kein frisches Bewegungsbild','No fresh motion image'],no_idle_dashboard:['Kein freies Dashboard mit Echo Relay','No idle dashboard with Echo Relay'],outside_window:['Außerhalb des Morgen-Zeitfensters','Outside the morning window'],already_today:['Heute bereits ausgeführt','Already acted today'],worker_unavailable:['Vision-Worker nicht verfügbar','Vision worker unavailable'],worker_update_required:['Vision-Worker ab 1.9.0 erforderlich','Vision worker 1.9.0+ required'],expired:['Bild oder Einstellungen inzwischen veraltet','Image or settings expired'],uncertain:['Unsicheres Bild: keine Aktion','Uncertain image: no action'],empty:['Keine Person und kein Hund erkannt','No person or dog detected'],no_match:['Keine ausgewählte Kategorie erkannt','No selected category detected'],detected:['Erkennung erfolgreich','Detection successful'],claimed:['Begrüßung wird vorbereitet','Preparing greeting'],greeting_started:['Wiedergabe vom Tablet bestätigt','Playback confirmed by tablet'],playback_skipped:['Wiedergabe übersprungen','Playback skipped']};
const statusText=(v,key)=>statuses[key]?t(v,...statuses[key]):key;
export function canAccept(v){
 const endpoint=v.session?.endpoint;
 const quietContinuous=v.continuous&&v.session?.stage==='listen'&&endpoint&&!endpoint.started&&endpoint.leading>=100&&!endpoint.recent?.some(Boolean);
 const passive=v.session?.stage==='wake'&&!v.session?.wakeDetected||quietContinuous;
 return !!(v.card?.isConnected&&!document.hidden&&v.mode==='dashboard'&&v.output==='native_audio'&&v.nativeAudioReady()&&!v.processing&&!v.playing&&(!v.continuous||!v.session||quietContinuous)&&(!v.session||passive)&&v.retryTimer==null&&!v._proactiveRunning);
}
export function resolveProactiveFollowup(v,text){
 const follow=v._proactiveFollowup;v._proactiveFollowup=null;
 if(!follow||Date.now()>follow.until)return text;
 const normalized=String(text).toLocaleLowerCase('de').replace(/[^\p{L}\p{N} ]/gu,'').trim();
 if(/^(?:ja|ja bitte|ja gerne|gerne|bitte|mach das|erzähl|erzähl mal|yes|yes please|sure)$/.test(normalized))return 'Was steht heute an?';
 if(/^(?:nein|nein danke|danke|nicht jetzt|später|no|no thanks)$/.test(normalized))return null;
 return text;
}
export function connectProactive(v){
 if(v._proactiveConnection||!v.card?.isConnected||!v.h?.connection?.subscribeEvents)return;
 const state={disposed:false,unsub:null,heartbeatTimer:null,updateTimer:null,signature:null};v._proactiveConnection=state;
 const client=makeId();
 async function heartbeat(){if(state.disposed||!v.card.isConnected)return;try{await rpc(v,{action:'heartbeat',client_id:client,busy:!canAccept(v)});}catch{}void bridgeHeartbeat();}
 const oldUpdate=v.update;v.update=function(...args){const result=oldUpdate.apply(this,args),signature=String(canAccept(v));if(state.signature!==signature){state.signature=signature;clearTimeout(state.updateTimer);state.updateTimer=setTimeout(heartbeat,100);}return result;};
 const oldDestroy=v.destroy;v.destroy=function(...args){state.disposed=true;clearInterval(state.heartbeatTimer);clearTimeout(state.updateTimer);state.unsub?.();state.unsubSpeech?.();void bridgeHeartbeat(true);document.removeEventListener('visibilitychange',onVisibility);return oldDestroy.apply(this,args);};
 const oldIntent=v.intent;v.intent=async function(text,follow){const resolved=resolveProactiveFollowup(this,text);if(resolved===null){this.processing=false;this.endDialog();this.state('Bereit',t(this,'Kein Tagesüberblick angefordert','No daily overview requested'));if(this.wake||this.continuous)this.rearm(1200);return;}return oldIntent.call(this,resolved,follow);};
 function onVisibility(){void heartbeat();}document.addEventListener('visibilitychange',onVisibility);
 async function receive(event){
  const id=event?.data?.request_id;if(!/^[a-f0-9]{32}$/.test(id||'')||!canAccept(v))return;
  const generation=v.generation;let claimed=false,running=false;
  try{
   await heartbeat();if(!canAccept(v))return;
   const answer=await rpc(v,{action:'claim',client_id:client,request_id:id});if(!answer?.accepted)return;claimed=true;
   if(!canAccept(v)||generation!==v.generation||state.disposed)return;
   const path=new URL(answer.audio_path,location.origin);if(path.origin!==location.origin||!/^\/api\/tts_proxy\/[A-Za-z0-9_.~-]{1,200}$/.test(path.pathname)||path.search||path.hash)throw Error('Invalid local audio path');
   const session=v.session;if(session){v.finish(session);if(session.closePromise)await session.closePromise;}
   if(generation!==v.generation||!canAccept(v))return;
   running=true;v._proactiveRunning=true;v.beginDialog();v.lastReply=answer.message;v.lastAudio=path.href;v.showCaption?.('',answer.message);
   v._proactiveFollowup=answer.offer_overview?{until:Date.now()+120000}:null;
   const statusEntity=v.cfg?.relay_status_entity||'input_text.jarvis_native_audio_status';let started=false;
   // playNativeAudio resolves after playback; acknowledge only a confirmed playing state.
   const monitor=setInterval(()=>{const status=String(v.h?.states?.[statusEntity]?.state||'');if(!started&&v._nativeRequest&&status.startsWith(v._nativeRequest+'|playing')){started=true;void rpc(v,{action:'ack',client_id:client,request_id:id,started:true}).then(r=>{if(r?.accepted)void historyLog(v,{kind:'greeting',status:'greeting_started',message:String(answer.message||'').slice(0,800)});}).catch(()=>{});}},100);
   try{await v.playNativeAudio(path.href,!!answer.offer_overview);}finally{clearInterval(monitor);if(!started)await rpc(v,{action:'ack',client_id:client,request_id:id,started:false});claimed=false;}
  }catch{/* Backend status and the regular player display contain actionable errors. */}
  finally{if(claimed)void rpc(v,{action:'ack',client_id:client,request_id:id,started:false}).catch(()=>{});if(running)v._proactiveRunning=false;void heartbeat();}
 }
 const conn=v.h?.connection;
 if(conn?.subscribeEvents){Promise.resolve(conn.subscribeEvents(receive,'jarvis_echo_relay_proactive')).then(unsub=>{if(state.disposed)unsub();else state.unsub=unsub;}).catch(()=>{});}

 // Generic HA speech requests. One active local tablet, no persistent audio or mic state.
 const isTablet=()=>/Android/i.test(navigator.userAgent+" "+(navigator.userAgentData?.platform||""))||!!window.externalApp||(navigator.maxTouchPoints>1&&/Linux/i.test(navigator.platform||""));
 const entity='input_text.jarvis_sprechstatus',bridge='input_text.jarvis_sprachbridge_status';
 let lastBridge='',lastBridgeAt=0;
 async function bridgeHeartbeat(offline=false){if(!isTablet()||!v.h||(!offline&&!state.speechSubscribed))return;const mode=offline||document.hidden?'offline':canAccept(v)&&!v.info&&!v.card._jvActive?'ready':'busy';const now=Date.now();if(lastBridge===mode&&now-lastBridgeAt<20000)return;lastBridge=mode;lastBridgeAt=now;try{await v.h.callService('input_text','set_value',{entity_id:bridge,value:mode+'|'+now+'|1.4.0'});}catch{}}
 async function pending(id){try{const r=await v.h.callApi('GET','states/'+entity);return r?.state===id+'|pending'&&Date.now()-Date.parse(r.last_changed)<30000;}catch{return false;}}
 const reportSpeech=async(id,status)=>{try{if(await pending(id))await v.h.callService('input_text','set_value',{entity_id:entity,value:id+'|'+status});}catch{}};
 async function receiveSpeech(event){
  const data=event?.data||{},id=String(data.request_id||''),message=String(data.message||'').trim().slice(0,800);
  if(!isTablet()||state.disposed||!v.card?.isConnected||document.hidden||!/^[0-9]{12,20}$/.test(id)||!message)return;
  if(!await pending(id))return;
  if(!canAccept(v)||v.info||v.card._jvActive){await reportSpeech(id,'skipped');return;}
  const generation=v.generation;let monitor=null,started=false,owned=false;
  try{
   v._proactiveRunning=true;owned=true;
   const prior=v.session;if(prior){v.finish(prior);if(prior.closePromise)await prior.closePromise;}
   if(state.disposed||v.generation!==generation||document.hidden||!v.nativeAudioReady()||v.playing||v.processing){await reportSpeech(id,'skipped');return;}
   const audio=await v.h.callApi('POST','tts_get_url',{engine_id:'tts.jarvis_tablet_stream',message,language:'de',cache:false});
   const path=new URL(audio?.path||audio?.url||'',location.origin);
   if(path.origin!==location.origin||!/^\/api\/tts_proxy\/[A-Za-z0-9_.~-]{1,200}$/.test(path.pathname)||path.search||path.hash)throw Error('Invalid TTS path');
   if(state.disposed||v.generation!==generation||document.hidden||!v.nativeAudioReady()||v.playing||v.processing||v.session||!await pending(id)){await reportSpeech(id,'skipped');return;}
   const keep=data.followup===true||data.followup==='true';
   v.beginDialog();v.lastReply=message;v.lastAudio=path.href;v.showCaption?.('',message);
   v._proactiveFollowup=keep&&(data.daily_overview===true||data.daily_overview==='true')?{until:Date.now()+120000}:null;
   monitor=setInterval(()=>{const status=String(v.h?.states?.[v.cfg?.relay_status_entity||'input_text.jarvis_native_audio_status']?.state||'');if(!started&&v._nativeRequest&&status.startsWith(v._nativeRequest+'|playing')){started=true;void reportSpeech(id,'started');}},100);
   await v.playNativeAudio(path.href,keep);
   if(!started){v._proactiveFollowup=null;await reportSpeech(id,'error');}
  }catch{v._proactiveFollowup=null;await reportSpeech(id,'error');}
  finally{clearInterval(monitor);if(owned){v._proactiveRunning=false;if(!v.playing&&!v.processing&&!v.session&&v.retryTimer==null&&(v.wake||v.continuous))v.rearm(1200);}void heartbeat();}
 }
 if(conn?.subscribeEvents){Promise.resolve(conn.subscribeEvents(receiveSpeech,'jarvis_speech_request')).then(unsub=>{if(state.disposed)unsub();else{state.unsubSpeech=unsub;state.speechSubscribed=true;void bridgeHeartbeat();}}).catch(()=>{});}
 state.heartbeatTimer=setInterval(heartbeat,10000);void heartbeat();
}

export function mountProactiveSettings(v,root){
 connectProactive(v);
 const section=node('div',null,'jvs-section');
 section.append(node('h3',t(v,'Familienmitglieder','Family members')),node('p',t(v,'Lege die Namen für die Begrüßung fest. Zeitfenster und weitere Regeln werden in Home Assistant verwaltet.','Set the names used for greetings. Time windows and other rules are managed in Home Assistant.'),'jvs-muted'));
 const body=node('div',null,'jvs-panel');section.append(body);root.append(section);
 const names=[['input_text.jarvis_name_frau','Name der Frau','Woman’s name'],['input_text.jarvis_name_mann','Name des Mannes','Man’s name'],['input_text.jarvis_name_kind','Name des Kindes','Child’s name']];
 const fields=new Map();let loading=false,loaded=false;
 for(const [id,de,en]of names){const label=node('label',null,'jvs-range'),input=node('input');input.type='text';input.maxLength=40;input.autocomplete='off';input.setAttribute('aria-label',t(v,de,en));input.disabled=true;label.append(node('strong',t(v,de,en)),input);body.append(label);fields.set(id,input);}
 const actions=node('div',null,'jvs-actions'),save=node('button',t(v,'Namen speichern','Save names')),status=node('p','','jvs-muted');save.type='button';save.disabled=true;status.setAttribute('role','status');actions.append(save);section.append(actions,status);
 function disable(value){for(const input of fields.values())input.disabled=value;save.disabled=value||!loaded;}
 async function readNames(){return await Promise.all(names.map(async ([id])=>{const r=await v.h.callApi('GET','states/'+id);if(typeof r?.state!=='string'||['unknown','unavailable'].includes(r.state))throw Error('Name helper unavailable');return [id,r.state];}));}
 async function load(){if(loading||!root.isConnected)return;loading=true;disable(true);try{const values=await readNames();if(root.isConnected){for(const [id,value]of values)fields.get(id).value=value;loaded=true;status.textContent='';}}catch{loaded=false;status.textContent=t(v,'Namensfelder konnten nicht geladen werden.','Could not load name fields.');}finally{loading=false;disable(false);}}
 save.onclick=async()=>{if(loading||!loaded)return;loading=true;disable(true);let saved=0;try{const desired=[...fields].map(([id,input])=>[id,input.value.trim().slice(0,40)]);for(const [id,value]of desired){await v.h.callService('input_text','set_value',{entity_id:id,value});saved++;}const actual=await readNames();if(actual.some(([id,value])=>value!==desired.find(([key])=>key===id)?.[1]))throw Error('Name values not confirmed');if(root.isConnected){for(const [id,value]of actual)fields.get(id).value=value;status.textContent=t(v,'Namen gespeichert.','Names saved.');}}catch{status.textContent=t(v,'Speichern nicht vollständig bestätigt. Bitte erneut versuchen.','Saving was not fully confirmed. Please try again.');}finally{loading=false;disable(false);}};
 const observer=new MutationObserver(()=>{if(!root.hidden&&!loading)void load();});observer.observe(root,{attributes:true,attributeFilter:['hidden']});const cleanup=new MutationObserver(()=>{if(!root.isConnected){observer.disconnect();cleanup.disconnect();}});cleanup.observe(root.getRootNode(),{childList:true,subtree:true});if(!root.hidden)void load();
}
