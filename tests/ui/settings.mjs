import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {chromium} from 'playwright';
const dir=new URL('../../homeassistant/www/jarvis/',import.meta.url);
const files=Object.fromEntries(await Promise.all(['echo-relay-assist-card-v1.1.0.js','jarvis-settings-v1.0.0.js','jarvis-model-settings-v1.1.0.js','jarvis-control-panel-v1.6.0.js'].map(async name=>[name,await readFile(new URL(name,dir),'utf8')])));
const html=`<!doctype html><meta charset="utf-8"><style>
:root{--hz-bg:#10151d;--hz-surface:#1b2430;--hz-surface-alt:#242f3d;--hz-line:#354150;--hz-text:#e9eef5;--hz-muted:#aebbc9;--hz-accent:#38c5ae;--primary-text-color:var(--hz-text);--secondary-text-color:var(--hz-muted);--card-background-color:var(--hz-surface);--divider-color:var(--hz-line);--primary-color:var(--hz-accent)}body{background:var(--hz-bg);color:var(--hz-text);font:14px system-ui;margin:0;padding:24px}ha-card{display:block;background:var(--hz-surface);border-radius:16px}main{max-width:900px;margin:auto;display:grid;gap:24px}
</style><main></main><script type="module">
import '/local/jarvis/echo-relay-assist-card-v1.1.0.js';import '/local/jarvis/jarvis-control-panel-v1.6.0.js';
window.errors=[];window.calls=[];window.waiters=[];window.rejectChoice=false;
const states={};for(const id of ['jarvis_stt_profil','jarvis_stimme','jarvis_klangprofil','jarvis_live_klangprofil','jarvis_gesprachsmodus','jarvis_android_lautsprecher'])states['input_select.'+id]={state:'Natürlich',attributes:{options:['Natürlich','Studio','Klar']}};
for(const key of ['waschen','spuelen','solar','wallbox','abfall','regen'])states['input_text.jarvis_hinweis_'+key]={state:JSON.stringify({enabled:false,rooms:['Büro'],start:'08:00',end:'22:00',priority:'Normal'})};
window.h={language:'de',states,callWS:async()=>{throw Error('Offline')},callService:async(domain,service,data)=>{window.calls.push({domain,service,data});if(domain==='input_select'){if(window.rejectChoice)throw Error('Test abgelehnt');await new Promise(resolve=>window.waiters.push(resolve));}}};
const card=document.createElement('echo-relay-assist-card');card.setConfig({title:'HA Jarvis Echo Relay'});card.hass=h;document.querySelector('main').append(card);window.card=card;
const panel=document.createElement('jarvis-control-panel');panel.setConfig({});panel.hass=h;document.querySelector('main').append(panel);window.panel=panel;
window.refresh=()=>{card.hass={...h};panel.hass={...h};};window.ready=true;
</script>`;
const browser=await chromium.launch({headless:true,...(process.env.CAMERA_TEST_CHROME?{executablePath:process.env.CAMERA_TEST_CHROME}:{})});
const page=await browser.newPage({viewport:{width:1050,height:1100}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.route('http://settings.test/**',route=>{const path=new URL(route.request().url()).pathname,name=path.split('/').at(-1);return route.fulfill({contentType:path.endsWith('.js')?'application/javascript':'text/html',body:files[name]||html});});
try{
 await page.goto('http://settings.test/');await page.waitForFunction(()=>window.ready);
 await page.getByText('Assistent und Audio · Einstellungen',{exact:true}).click();
 await page.getByRole('tab',{name:'Sprache & Audio',exact:true}).waitFor();
 assert.equal(await page.locator('[data-jarvis-integrated] [role=tabpanel]:visible').count(),1);
 assert.equal(await page.locator('[data-jarvis-integrated] select').count(),0);
 // Updating hass must preserve controls and keyboard focus.
 await page.getByRole('slider',{name:'Sprechpause',exact:true}).focus();await page.keyboard.press('End');await page.keyboard.press('Tab');
 assert.equal(await page.evaluate(()=>card.voice.pref.pause),3200);
 await page.getByRole('radio',{name:'Nur auf Assist-Anfrage',exact:true}).check();
 await page.evaluate(()=>{for(let i=0;i<30;i++)refresh();});
 assert.equal(await page.getByRole('radio',{name:'Nur auf Assist-Anfrage',exact:true}).isChecked(),true);
 assert.deepEqual(await page.evaluate(()=>{const v=card.voice;v.beginDialog();return [v.shouldFollow({reply:'Hallo.',keep:false}),v.shouldFollow({reply:'Hallo.',keep:true})]}),[false,true]);
 // Real endpointer consumes synthetic PCM frames; no microphone or device audio.
 assert.deepEqual(await page.evaluate(()=>{const v=card.voice;v.pref.pause=3200;v.pref.sensitivity=150;const s=v.makeSession(false,'stt');s.stage='listen';s.handler=1;s.socket={readyState:1,bufferedAmount:0,send(){}};for(let i=0;i<12;i++)v.frame(s,new Int16Array(320).fill(5000));const result=[s.endpoint.silenceFrames,s.endpoint.sensitivity];v.finish(s);return result;}),[160,1.5]);
 await page.getByRole('tab',{name:'Anzeige & Kameras',exact:true}).click();
 await page.getByRole('slider',{name:'Infobox-Anzeige',exact:true}).focus();await page.keyboard.press('End');await page.keyboard.press('Tab');
 assert.equal(await page.evaluate(()=>card.voice.pref.infoSeconds),90);
 await page.getByRole('checkbox',{name:'Live-Untertitel',exact:true}).uncheck();
 await page.getByRole('tab',{name:'Verlauf & Diagnose',exact:true}).click();
 await page.getByRole('checkbox',{name:'Verlauf dieser Sitzung speichern',exact:true}).check();
 await page.evaluate(()=>card.voice.rememberTurn({question:'Testfrage',reply:'Testantwort'}));await page.getByText('Testantwort',{exact:true}).waitFor();
 await page.getByRole('button',{name:'Verlauf leeren',exact:true}).click();assert.equal(await page.getByText('Testantwort',{exact:true}).count(),0);
 await page.reload();await page.waitForFunction(()=>window.ready);await page.getByText('Assistent und Audio · Einstellungen',{exact:true}).click();await page.getByRole('tab',{name:'Anzeige & Kameras',exact:true}).click();
 assert.equal(await page.getByRole('checkbox',{name:'Live-Untertitel',exact:true}).isChecked(),false);assert.equal(await page.getByRole('slider',{name:'Infobox-Anzeige',exact:true}).inputValue(),'90');assert.equal(await page.evaluate(()=>card.voice.history.length),0);
 // Model failure is visible and retryable; no phantom save controls.
 await page.getByRole('tab',{name:'KI & Leistung',exact:true}).click();await page.getByText('Einstellungen nicht verfügbar.',{exact:false}).waitFor();assert.equal(await page.getByRole('button',{name:'Für Jarvis speichern',exact:true}).isDisabled(),true);
 // Legacy central controls: delayed acknowledgement, unrelated updates and rejection.
 const voice=page.getByRole('radiogroup',{name:'Stimme',exact:true});await voice.getByRole('radio',{name:'Studio',exact:true}).check();
 await page.evaluate(()=>{for(let i=0;i<30;i++)refresh();});assert.equal(await voice.getByRole('radio',{name:'Studio',exact:true}).isChecked(),true);assert.equal(await voice.getByRole('radio',{name:'Klar',exact:true}).isDisabled(),true);
 await page.evaluate(()=>{h.states['input_select.jarvis_stimme'].state='Studio';refresh();waiters.shift()();});await voice.getByRole('radio',{name:'Klar',exact:true}).waitFor({state:'visible'});assert.equal(await voice.getByRole('radio',{name:'Klar',exact:true}).isEnabled(),true);
 await page.evaluate(()=>window.rejectChoice=true);await voice.getByRole('radio',{name:'Klar',exact:true}).click();await page.getByText('Nicht gespeichert: Test abgelehnt',{exact:true}).waitFor();assert.equal(await voice.getByRole('radio',{name:'Studio',exact:true}).isChecked(),true);
 await page.getByRole('tab',{name:'Hinweise & Räume',exact:true}).click();await page.getByText('Waschmaschine',{exact:true}).click();await page.getByRole('radiogroup',{name:'Priorität',exact:true}).first().getByRole('radio',{name:'Hoch',exact:true}).check();await page.evaluate(()=>refresh());assert.equal(await page.getByRole('radiogroup',{name:'Priorität',exact:true}).first().getByRole('radio',{name:'Hoch',exact:true}).isChecked(),true);
 // A second rule has an independent radio group.
 await page.getByText('Spülmaschine',{exact:true}).click();assert.equal(await page.getByRole('radiogroup',{name:'Priorität',exact:true}).nth(1).getByRole('radio',{name:'Normal',exact:true}).isChecked(),true);
 for(const viewport of [{width:1050,height:1100},{width:390,height:844}]){await page.setViewportSize(viewport);for(const tab of ['Sprache & Audio','Anzeige & Kameras','KI & Leistung','Verlauf & Diagnose']){await page.getByRole('tab',{name:tab,exact:true}).click();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,tab+' overflows');}await page.getByRole('tab',{name:'Sprache & Audio',exact:true}).click();if(process.env.SETTINGS_SCREENSHOT_PREFIX)await page.screenshot({path:process.env.SETTINGS_SCREENSHOT_PREFIX+'-'+viewport.width+'.png',fullPage:true});}
 await page.evaluate(()=>{document.documentElement.style.cssText='--hz-bg:#f1f4f7;--hz-surface:#fff;--hz-surface-alt:#e8edf2;--hz-line:#cbd5df;--hz-text:#192330;--hz-muted:#566579;--hz-accent:#167867';});
 if(process.env.SETTINGS_SCREENSHOT_PREFIX)await page.screenshot({path:process.env.SETTINGS_SCREENSHOT_PREFIX+'-light.png',fullPage:true});
 // English labels from the same shared implementation.
 await page.evaluate(()=>{h.language='en';card.voice.ui.remove();card.voice.ui=null;refresh();});await page.getByRole('tab',{name:'Voice & audio',exact:true}).waitFor();await page.getByRole('tab',{name:'Display & cameras',exact:true}).click();await page.getByRole('slider',{name:'Infobox duration',exact:true}).waitFor();
 assert.deepEqual(errors,[]);console.log('Settings: responsive DE/EN tabs, persistence, real endpoint preferences, history, model error, stable delayed HA choice and rejected save passed.');
}finally{await browser.close();}
