import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {chromium} from "playwright";
const source=await readFile(new URL("../../homeassistant/www/jarvis/jarvis-model-settings-v1.1.0.js",import.meta.url),"utf8");
const shared=await readFile(new URL("../../homeassistant/www/jarvis/jarvis-settings-v1.1.0.js",import.meta.url),"utf8");
const proactive=await readFile(new URL('../../homeassistant/www/jarvis/jarvis-proactive-v1.0.0.js',import.meta.url),'utf8');
const card=await readFile(new URL("../../homeassistant/www/jarvis/echo-relay-assist-card-v1.2.0.js",import.meta.url),"utf8");
const html=`<!doctype html><meta charset="utf-8"><body style="background:#151b23;color:#eee;font:16px system-ui;padding:24px"><script type="module">
import '/card.js';
window.calls=[];window.failSave=false;
window.settings={text_model:'qwen3:4b-instruct',vision_model:'qwen3-vl:4b-instruct',keep_alive:120,num_ctx:4096,vision_keep_alive:0,vision_num_ctx:4096,
 revision:'first',shared:false,text_models:['qwen3:4b-instruct','qwen3-vl:4b-instruct'],vision_models:['qwen3-vl:4b-instruct'],loaded:[]};
const h={language:'de',states:{},callWS:async request=>{window.calls.push(request);if(request.service_data.action==='set'){
  if(window.failSave)throw Error('stale settings');const d=request.service_data;window.settings={...window.settings,...d,vision_keep_alive:d.keep_alive,vision_num_ctx:d.num_ctx,revision:'saved',shared:d.text_model===d.vision_model,saved:true};}
 return {response:{...window.settings}};}};
const c=document.createElement('echo-relay-assist-card');c.setConfig({title:'Jarvis · Assistent und Audio'});c.hass=h;document.body.append(c);window.card=c;window.ready=true;
</script>`;
const browser=await chromium.launch({headless:true,...(process.env.CAMERA_TEST_CHROME?{executablePath:process.env.CAMERA_TEST_CHROME}:{})});
const page=await browser.newPage({viewport:{width:850,height:1000}});
await page.route("http://relay-models.test/**",route=>route.fulfill({contentType:route.request().url().endsWith('.js')?'application/javascript':'text/html',
 body:route.request().url().endsWith('card.js')?card:route.request().url().includes('jarvis-settings-')?shared:route.request().url().includes('jarvis-proactive-')?proactive:route.request().url().endsWith('.js')?source:html}));
try{
 await page.goto('http://relay-models.test/');await page.waitForFunction(()=>window.ready);
 await page.getByText('Assistent und Audio · Einstellungen',{exact:true}).click();
 await page.getByRole('tab',{name:'KI & Leistung',exact:true}).click();
 await page.getByText('Getrennte Text- und Bildmodelle.',{exact:false}).waitFor();
 await page.getByRole('group',{name:'Textmodell',exact:true}).getByRole('radio',{name:'Qwen3-VL 4B Instruct',exact:true}).check();
 await page.getByRole('group',{name:'Modelle warm halten',exact:true}).getByRole('radio',{name:'5 min',exact:true}).check();
 await page.evaluate(()=>window.card.voice.processing=true);
 await page.getByRole('button',{name:'Für Jarvis speichern',exact:true}).click();
 assert.equal(await page.evaluate(()=>window.calls.filter(c=>c.service_data.action==='set').length),0);
 await page.evaluate(()=>window.card.voice.processing=false);
 await page.getByRole('button',{name:'Für Jarvis speichern',exact:true}).click();
 await page.getByText('Gespeichert. Gilt ab der nächsten Anfrage.',{exact:false}).waitFor();
 const saved=await page.evaluate(()=>window.calls.find(c=>c.service_data.action==='set'));
 assert.equal(saved.type,'call_service');assert.equal(saved.return_response,true);
 assert.equal(saved.service_data.keep_alive,300);assert.equal(saved.service_data.num_ctx,4096);
 assert.equal(saved.service_data.text_model,saved.service_data.vision_model);assert.equal(saved.service_data.revision,'first');
 if(process.env.MODEL_UI_SCREENSHOT)await page.screenshot({path:process.env.MODEL_UI_SCREENSHOT,fullPage:true});
 await page.evaluate(()=>window.failSave=true);
 await page.getByRole('button',{name:'Für Jarvis speichern',exact:true}).click();
 await page.getByText('Nicht gespeichert.',{exact:false}).waitFor();
 await page.getByRole('button',{name:'Status aktualisieren',exact:true}).click();
 await page.getByText('Gemeinsames Text-/Bildmodell.',{exact:false}).waitFor();
 assert.equal(await page.getByRole('group',{name:'Textmodell',exact:true}).getByRole('radio',{name:'Qwen3-VL 4B Instruct',exact:true}).isChecked(),true);
 console.log('Model settings UI: actual controller mount, installed-model choices, busy guard, versioned save, errors and refresh passed.');
}finally{await browser.close();}
