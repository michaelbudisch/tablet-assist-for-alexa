import {readFile} from 'node:fs/promises';
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const web=new URL('../../homeassistant/www/jarvis/',import.meta.url);
const files=Object.fromEntries(await Promise.all(['echo-relay-assist-card-v1.2.0.js','jarvis-settings-v1.1.0.js','jarvis-model-settings-v1.1.0.js','jarvis-proactive-v1.0.0.js'].map(async key=>[key,await readFile(new URL(key,web),'utf8')])));
const html=`<!doctype html><meta charset="utf-8"><style>body{font:14px system-ui;margin:20px;--primary-color:#167867;--primary-text-color:#192330;--card-background-color:#fff;--divider-color:#ccd6df}</style><script type="module">
import '/echo-relay-assist-card-v1.2.0.js';
window.calls=[];window.handler=null;window.rearms=[];
window.current={enabled:true,test_mode:true,cooldown:60,start:'06:00',end:'10:00',classes:['person','dog'],greeting:true,greeting_class:'adult',name:'Fixture',offer_overview:true,weather_entity:'weather.fixture',script_entity:'',revision:'first',weather_entities:[{entity_id:'weather.fixture',name:'Fixture weather'}],script_entities:[],last:{status:'idle'}};
const h={language:'de',states:{'input_text.jarvis_native_audio_status':{state:'ready|'+Date.now()}},connection:{subscribeEvents:async callback=>{window.handler=callback;return()=>window.unsubscribed=true;}},callWS:async request=>{calls.push(request);const d=request.service_data;
 if(d.action==='heartbeat')return{response:{enabled:true}};
 if(d.action==='claim')return {response:{accepted:true,message:'Guten Abend, Fixture. Möchtest du deinen Tagesüberblick hören?',offer_overview:true,audio_path:'/api/tts_proxy/fixture'}};
 if(d.action==='ack')return {response:{accepted:true}};
 if(d.action==='get')return {response:current};
 if(d.action==='set'){current={...current,...d.settings,revision:'saved'};return {response:current};}
 if(d.action==='check')return {response:{status:'cooldown'}};
},callService:async()=>{}};window.h=h;
const card=document.createElement('echo-relay-assist-card');card.setConfig({});card.hass=h;document.body.append(card);window.card=card;
</script>`;
const browser=await chromium.launch({headless:true,...(process.env.CAMERA_TEST_CHROME?{executablePath:process.env.CAMERA_TEST_CHROME}:{})});
const page=await browser.newPage({viewport:{width:1000,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.route('http://proactive.test/**',route=>{const path=new URL(route.request().url()).pathname;return route.fulfill({contentType:path.endsWith('.js')?'application/javascript':'text/html',body:files[path.split('/').at(-1)]||html});});
try{
 await page.goto('http://proactive.test/');await page.waitForFunction(()=>window.handler);
 await page.getByText('Assistent und Audio · Einstellungen',{exact:true}).click();await page.getByRole('tab',{name:'Proaktive Aktionen',exact:true}).click();
 await page.getByRole('checkbox',{name:'Testmodus: wiederholt und zu jeder Uhrzeit',exact:true}).waitFor();
 assert.equal(await page.getByRole('checkbox',{name:'Testmodus: wiederholt und zu jeder Uhrzeit',exact:true}).isChecked(),true);
 await page.getByRole('group',{name:'Sperrzeit zwischen Auswertungen',exact:true}).getByRole('radio',{name:'2 min',exact:true}).check();
 await page.getByRole('button',{name:'Proaktive Einstellungen speichern',exact:true}).click();await page.getByText(/^Gespeichert\. Letzter Status:/).waitFor();
 const settings=await page.evaluate(()=>calls.find(c=>c.service_data.action==='set').service_data);assert.equal(settings.settings.cooldown,120);assert.equal(settings.settings.test_mode,true);assert.equal(settings.revision,'first');
 await page.getByRole('button',{name:'Jetzt prüfen und Aktionen ausführen',exact:true}).click();await page.getByText('Prüfergebnis: Sperrzeit aktiv',{exact:true}).waitFor();
 // Running speech blocks even claiming a proactive job.
 await page.evaluate(async()=>{card.voice.processing=true;await handler({data:{request_id:'a'.repeat(32)}});card.voice.processing=false;});assert.equal(await page.evaluate(()=>calls.filter(c=>c.service_data.action==='claim').length),0);
 assert.deepEqual(await page.evaluate(async()=>{const {canAccept}=await import('/jarvis-proactive-v1.0.0.js');const v=card.voice;v.continuous=true;v.session={stage:'listen',endpoint:{started:false,leading:101,recent:[false,false]}};const quiet=canAccept(v);v.session.endpoint.recent=[true];const voiced=canAccept(v);v.session=null;v.continuous=false;return [quiet,voiced];}),[true,false]);
 // Passive wake word may be paused, but no live listening or active utterance is interrupted.
 await page.evaluate(async()=>{const v=card.voice;v.wake=true;v.session={stage:'wake',wakeDetected:false};v.rearm=(ms,follow)=>rearms.push({ms,follow});v.playNativeAudio=async(url,keep)=>{v._nativeRequest='fixture-request';v.playing=true;h.states['input_text.jarvis_native_audio_status'].state='fixture-request|playing';await new Promise(r=>setTimeout(r,180));v._nativeRequest=null;v.playing=false;h.states['input_text.jarvis_native_audio_status'].state='ready|'+Date.now();v.finishPlayback(keep);};await handler({data:{request_id:'b'.repeat(32)}});});
 assert.equal(await page.evaluate(()=>calls.filter(c=>c.service_data.action==='ack'&&c.service_data.started).length),1);
 assert.equal(await page.evaluate(()=>card.voice.wake),true);assert.equal(await page.evaluate(()=>rearms.at(-1).follow),true);
 await page.evaluate(async()=>{const v=card.voice;v.wake=false;v.continuous=true;v.session={stage:'listen',endpoint:{started:false,leading:101,recent:[false,false]}};await handler({data:{request_id:'c'.repeat(32)}});});
 assert.equal(await page.evaluate(()=>card.voice.continuous),true);assert.equal(await page.evaluate(()=>calls.filter(c=>c.service_data.action==='ack'&&c.service_data.started).length),2);
 assert.equal(await page.evaluate(async()=>{const m=await import('/jarvis-proactive-v1.0.0.js');return m.resolveProactiveFollowup(card.voice,'ja bitte');}),'Was steht heute an?');
 assert.equal(await page.evaluate(async()=>{card.voice._proactiveFollowup={until:Date.now()+10000};const m=await import('/jarvis-proactive-v1.0.0.js');return m.resolveProactiveFollowup(card.voice,'nein danke');}),null);
 await page.evaluate(()=>card.remove());assert.equal(await page.evaluate(()=>window.unsubscribed),true);assert.deepEqual(errors,[]);
 console.log('Proactive UI: central test-mode settings, cooldown, active-speech exclusion, passive-wake preservation, confirmed playback acknowledgement, yes/no follow-up and disposal passed.');
}finally{await browser.close();}
