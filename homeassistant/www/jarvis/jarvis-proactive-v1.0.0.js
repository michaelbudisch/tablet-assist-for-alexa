/* Opt-in proactive greetings. One HA-coordinated speaker; no face recognition. */
const rpc=(v,data)=>v.h.callWS({type:'call_service',domain:'jarvis_tablet_audio',service:'proactive',service_data:data,return_response:true}).then(r=>r?.response??r?.service_response??r);
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
 async function heartbeat(){if(state.disposed||!v.card.isConnected)return;try{await rpc(v,{action:'heartbeat',client_id:client,busy:!canAccept(v)});}catch{}}
 const oldUpdate=v.update;v.update=function(...args){const result=oldUpdate.apply(this,args),signature=String(canAccept(v));if(state.signature!==signature){state.signature=signature;clearTimeout(state.updateTimer);state.updateTimer=setTimeout(heartbeat,100);}return result;};
 const oldDestroy=v.destroy;v.destroy=function(...args){state.disposed=true;clearInterval(state.heartbeatTimer);clearTimeout(state.updateTimer);state.unsub?.();document.removeEventListener('visibilitychange',onVisibility);return oldDestroy.apply(this,args);};
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
   const monitor=setInterval(()=>{const status=String(v.h?.states?.[statusEntity]?.state||'');if(!started&&v._nativeRequest&&status.startsWith(v._nativeRequest+'|playing')){started=true;void rpc(v,{action:'ack',client_id:client,request_id:id,started:true}).catch(()=>{});}},100);
   try{await v.playNativeAudio(path.href,!!answer.offer_overview);}finally{clearInterval(monitor);if(!started)await rpc(v,{action:'ack',client_id:client,request_id:id,started:false});claimed=false;}
  }catch{/* Backend status and the regular player display contain actionable errors. */}
  finally{if(claimed)void rpc(v,{action:'ack',client_id:client,request_id:id,started:false}).catch(()=>{});if(running)v._proactiveRunning=false;void heartbeat();}
 }
 const conn=v.h?.connection;
 if(conn?.subscribeEvents){Promise.resolve(conn.subscribeEvents(receive,'jarvis_echo_relay_proactive')).then(unsub=>{if(state.disposed)unsub();else state.unsub=unsub;}).catch(()=>{});}
 state.heartbeatTimer=setInterval(heartbeat,10000);void heartbeat();
}

export function mountProactiveSettings(v,root){
 connectProactive(v);
 const section=node('div',null,'jvs-section');section.append(node('h3',t(v,'Proaktive Aktionen','Proactive actions')),node('p',t(v,'Bewegung kann ein aktuelles Einzelbild lokal auswerten lassen. Die KI liefert nur Kategorien; Aktionen legst du hier oder in HA fest.','Motion can trigger a local still-image check. AI returns categories only; you configure actions here or in HA.'),'jvs-muted'));
 const status=node('p',t(v,'Beim Öffnen werden die zentralen Einstellungen geladen.','Open to load shared settings.'),'jvs-muted');status.setAttribute('role','status');section.append(status);root.append(section);
 let current=null,loading=false;const fields={},controls=[];
 const body=node('div',null,'jvs-panel');section.append(body);
 const label=(key,title,input)=>{const row=node('label',null,input.type==='checkbox'?'jvs-check':'jvs-range');if(input.type==='checkbox')row.append(input,node('strong',title));else row.append(node('strong',title),input);input.setAttribute('aria-label',title);fields[key]=input;controls.push(input);body.append(row);};
 for(const [key,de,en]of[['enabled','Bewegungsauswertung aktiv','Enable motion checks'],['test_mode','Testmodus: wiederholt und zu jeder Uhrzeit','Test mode: repeat at any time'],['greeting','Begrüßung über Echo Relay','Greet through Echo Relay'],['offer_overview','Tagesüberblick anbieten und Antwort abwarten','Offer daily overview and listen for a reply']]){const input=node('input');input.type='checkbox';label(key,t(v,de,en),input);}
 for(const [key,de,en,type]of[['name','Feste Anrede (optional)','Fixed greeting name (optional)','text'],['start','Morgen-Zeitfenster ab','Morning window from','time'],['end','Morgen-Zeitfenster bis','Morning window until','time']]){const input=node('input');input.type=type;if(key==='name')input.maxLength=40;label(key,t(v,de,en),input);}
 body.append(node('p',t(v,'Die feste Anrede wird für jeden passenden Treffer verwendet. Sie ist keine erkannte Identität. Im Normalmodus gilt das Zeitfenster mit höchstens einer Aktion pro Tag. Testmodus hebt beide Grenzen auf; die Sperrzeit bleibt aktiv.','The fixed greeting name applies to every matching detection, not an identified person. Normal mode uses the morning window and at most one action per day. Test mode bypasses both limits; the cooldown remains.'),'jvs-muted'));
 const options={};
 function choices(key,title,values,multiple=false){const group=node('fieldset');group.append(node('legend',title));const row=node('div',null,'jvs-options');group.append(row);body.append(group);options[key]={row,multiple,values};}
 choices('cooldown',t(v,'Sperrzeit zwischen Auswertungen','Cooldown between checks'),[30,60,120,300,600,1800].map(n=>[n,n<60?n+' s':n/60+' min']));
 const names={person:t(v,'Person','Person'),adult:t(v,'Vermutlich erwachsen','Apparently adult'),child:t(v,'Vermutlich Kind','Apparently child'),dog:t(v,'Hund','Dog')};
 choices('classes',t(v,'Erkennungen für HA-Aktionen','Detections for HA actions'),Object.entries(names),true);
 choices('greeting_class',t(v,'Begrüßung auslösen bei','Greet when detecting'),Object.entries(names).filter(([k])=>k!=='dog'));
 choices('weather_entity',t(v,'Wetter für den Regenhinweis','Weather for rain advice'),[]);
 choices('script_entity',t(v,'Zusätzliches HA-Skript','Additional HA script'),[]);
 const note=node('p',t(v,'Ein HA-Administrator muss die native Bewegungsautomation einmalig einrichten (Vorlage im Git-Projekt). Unsichere Ergebnisse lösen keine Aktion aus. Kein Bildarchiv; keine Namens-, Gesichts- oder Geschlechtserkennung.','A HA administrator must install the native motion automation once (template in the Git project). Uncertain results trigger no action. No image archive, identity, face or gender recognition.'),'jvs-muted');body.append(note);
 function group(de,en,keys,choiceKeys){const details=node('details'),content=node('div',null,'jvs-panel');details.append(node('summary',t(v,de,en)),content);for(const key of keys)content.append(fields[key].closest('label'));for(const key of choiceKeys)content.append(options[key].row.closest('fieldset'));body.append(details);}
 group('Begrüßung und Wetter','Greeting and weather',['name','offer_overview'],['greeting_class','weather_entity']);
 group('Normalbetrieb: Morgen-Zeitfenster','Normal mode: morning window',['start','end'],[]);
 group('Erkennungen und HA-Automationen','Detections and HA automations',[],['classes','script_entity']);
 options.script_entity.row.style.cssText='max-height:280px;overflow:auto;';
 const actions=node('div',null,'jvs-actions');section.append(actions);
 function button(de,en,fn){const b=node('button',t(v,de,en));b.type='button';b.onclick=()=>void fn();controls.push(b);actions.append(b);return b;}
 function disable(value){for(const c of [...controls,...body.querySelectorAll('input')])c.disabled=value;}
 function render(value){current=value;for(const [key,input]of Object.entries(fields)){if(input.type==='checkbox')input.checked=value[key];else input.value=value[key];}
  options.weather_entity.values=[['',t(v,'Kein Wetterhinweis','No weather advice')],...(value.weather_entities||[]).map(x=>[x.entity_id,x.name])];options.script_entity.values=[['',t(v,'Kein zusätzliches Skript','No additional script')],...(value.script_entities||[]).map(x=>[x.entity_id,x.name])];
  const prefix=makeId();for(const [key,o]of Object.entries(options)){o.row.replaceChildren();for(const [id,name]of o.values){const l=node('label',null,'jvs-option'),input=node('input');input.type=o.multiple?'checkbox':'radio';input.name=prefix+'-'+key;input.value=String(id);input.checked=o.multiple?value[key].includes(id):String(value[key])===String(id);l.append(input,node('span',name));o.row.append(l);}}
  status.textContent=t(v,'Letzter Status: ','Last status: ')+statusText(v,value.last?.status||'idle')+(value.last?.labels?.length?' · '+value.last.labels.map(k=>names[k]||k).join(', '):'');}
 async function load(){if(loading||!root.isConnected)return;loading=true;disable(true);try{const value=await rpc(v,{action:'get'});if(!value?.revision)throw Error();if(root.isConnected)render(value);}catch{status.textContent=t(v,'Nicht verfügbar. HA-Administrator und Jarvis Tablet Audio ab 1.6.0 erforderlich.','Unavailable. Requires a HA administrator and Jarvis Tablet Audio 1.6.0+.');}finally{loading=false;disable(false);save.disabled=!current;check.disabled=!current;}}
 const save=button('Proaktive Einstellungen speichern','Save proactive settings',async()=>{if(!current||loading)return;const settings={};for(const [key,input]of Object.entries(fields))settings[key]=input.type==='checkbox'?input.checked:input.value;for(const [key,o]of Object.entries(options)){const checked=[...o.row.querySelectorAll('input:checked')].map(i=>i.value);settings[key]=o.multiple?checked:key==='cooldown'?Number(checked[0]):checked[0];}loading=true;disable(true);try{const value=await rpc(v,{action:'set',revision:current.revision,settings});if(root.isConnected){render(value);status.textContent=t(v,'Gespeichert. ','Saved. ')+status.textContent;}}catch{status.textContent=t(v,'Nicht gespeichert. Status aktualisieren und Werte prüfen.','Not saved. Refresh status and check values.');}finally{loading=false;disable(false);}});
 button('Status aktualisieren','Refresh status',load);
 const check=button('Jetzt prüfen und Aktionen ausführen','Check now and run actions',async()=>{if(loading||!current)return;loading=true;disable(true);try{const value=await rpc(v,{action:'check',manual:true});status.textContent=t(v,'Prüfergebnis: ','Check result: ')+statusText(v,value.status||'unknown');}catch{status.textContent=t(v,'Prüfung fehlgeschlagen. Worker, Kamera und Sperrzeit prüfen.','Check failed. Check worker, camera and cooldown.');}finally{loading=false;disable(false);}});
 save.disabled=true;check.disabled=true;
 // The parent tab is hidden until opened; avoid background admin requests.
 const observer=new MutationObserver(()=>{if(!root.hidden&&!current&&!loading)void load();});observer.observe(root,{attributes:true,attributeFilter:['hidden']});
 const cleanup=new MutationObserver(()=>{if(!root.isConnected){observer.disconnect();cleanup.disconnect();}});cleanup.observe(root.getRootNode(),{childList:true,subtree:true});
 if(!root.hidden)void load();
}
