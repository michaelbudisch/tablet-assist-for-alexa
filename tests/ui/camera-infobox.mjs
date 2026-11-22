import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {chromium} from "playwright";

const source = await readFile(new URL("../../homeassistant/www/jarvis/jarvis-camera-preview-v1.2.0.js", import.meta.url), "utf8");
const controller = await readFile(new URL("../../homeassistant/www/jarvis/echo-relay-assist-card-v1.1.0.js", import.meta.url), "utf8");
const browser = await chromium.launch({headless: true,
  ...(process.env.CAMERA_TEST_CHROME ? {executablePath: process.env.CAMERA_TEST_CHROME} : {})});
const page = await browser.newPage({viewport: {width: 1080, height: 800}});
const html = `<!doctype html><html lang="de"><head><meta charset="utf-8"></head><body style="background:#111820;color:#eef;font:16px system-ui"><h1>Jarvis · Kamera-Test</h1><div id="host"></div><script type="module">
import {previewCamera,closeCameraInfo} from '/preview.js';
import '/card.js';
const host=document.querySelector('#host');host.attachShadow({mode:'open'});
window.attached=0;window.detached=0;window.configs=[];
customElements.define('fixture-camera',class extends HTMLElement {
  connectedCallback(){window.attached++;this.style.cssText='display:grid;place-items:center;min-height:260px;background:linear-gradient(160deg,#1c4853,#0c222c);font:20px system-ui';this.textContent='Synthetischer Kamerafeed · Test';}
  disconnectedCallback(){window.detached++;}
});
window.loadCardHelpers=async()=>({createCardElement:config=>{window.configs.push(config);return document.createElement('fixture-camera');}});
window.fixtureHass={language:'de',states:{'camera.door':{state:'idle',attributes:{friendly_name:'Haustür Live-Ansicht'}},'camera.outside':{state:'idle',attributes:{friendly_name:'Vorderseite'}}},callApi:async(method,path,body)=>{
  const viewing=!body.text.startsWith('Wer')&&!body.text.startsWith('Was');
  const all=body.text==='Zeige Kameras';
  return {camera_entity_id:all?null:'camera.door',camera_entity_ids:all?['camera.door','camera.outside']:['camera.door'],source:all?'all':'door',action:viewing?'view':'describe'};
}};
const voice={card:host,session:{},generation:1,mode:'dashboard',h:window.fixtureHass};
window.voice=voice;window.openPreview=()=>previewCamera(voice,'Wer ist an der Haustür?',voice.session);window.closePreview=()=>closeCameraInfo(voice);
window.ready=true;
</script></body></html>`;
await page.route("http://relay-ui.test/**", route => route.fulfill({
  contentType: route.request().url().endsWith(".js") ? "application/javascript" : "text/html",
  body: route.request().url().endsWith("card.js") ? controller : route.request().url().endsWith(".js") ? source : html}));
try {
  await page.goto("http://relay-ui.test/");
  await page.waitForFunction(() => window.ready);
  const dialog = page.getByRole("dialog", {name: "Jarvis Kamera-Infobox"});
  await page.evaluate(() => window.openPreview());
  await dialog.waitFor();
  await page.locator("fixture-camera").waitFor();
  const config = await page.evaluate(() => window.configs[0]);
  assert.equal(config.entity, "camera.door"); assert.equal(config.camera_image, "camera.door");
  assert.equal(config.camera_view, "live"); assert.equal(config.tap_action.action, "none");
  await page.evaluate(() => window.voice.info.cameraView.setReply("Auf dem Einzelbild steht eine Person mit einem Paket."));
  await page.getByText("Auf dem Einzelbild steht eine Person mit einem Paket.").waitFor();
  // HA updates and extending must retain the same stream instead of reconnecting it.
  await page.evaluate(() => {window.voice.info.cameraView.update();window.voice.info.cameraView.update();});
  await page.getByRole("button", {name: "Länger anzeigen (+60 s)", exact: true}).click();
  assert.equal(await page.evaluate(() => window.attached), 1);
  assert.equal(await page.evaluate(() => window.voice.info.extended), true);
  if (process.env.CAMERA_UI_SCREENSHOT) await page.screenshot({path: process.env.CAMERA_UI_SCREENSHOT});
  await page.setViewportSize({width:390,height:844});
  const mobile = await dialog.boundingBox(); assert.ok(mobile.width <= 390 && mobile.height <= 844);
  if (process.env.CAMERA_UI_SCREENSHOT) await page.screenshot({path:process.env.CAMERA_UI_SCREENSHOT.replace(/\.png$/, "-mobile.png")});
  await page.setViewportSize({width:1080,height:800});
  await page.keyboard.press("Escape"); await dialog.waitFor({state: "detached"});
  assert.equal(await page.evaluate(() => window.detached), 1);
  // Closing while card helpers are loading must never attach a late background stream.
  await page.evaluate(() => {window.loadCardHelpers=()=>new Promise(resolve=>window.releaseHelpers=resolve);});
  await page.evaluate(() => window.openPreview());
  await page.getByRole("button", {name: "Schließen ✕", exact: true}).click();
  await page.evaluate(() => window.releaseHelpers({createCardElement:()=>{window.configs.push({late:true});return document.createElement('fixture-camera');}}));
  assert.equal(await page.evaluate(() => window.attached), 1);
  // Automatic closing follows the post-answer delay and always has a hard deadline.
  await page.evaluate(() => {window.loadCardHelpers=async()=>({createCardElement:()=>document.createElement('fixture-camera')});});
  await page.clock.install();
  await page.evaluate(() => window.openPreview());
  await page.evaluate(() => window.voice.info.cameraView.schedule(true));
  await page.clock.fastForward(29900); assert.equal(await dialog.count(), 1);
  await page.clock.fastForward(200); await dialog.waitFor({state:"detached"});
  await page.evaluate(() => window.openPreview());
  await page.clock.fastForward(180100); await dialog.waitFor({state:"detached"});
  // Navigation / hidden documents and replaced requests also stop the existing feed.
  await page.evaluate(() => window.openPreview());
  await page.evaluate(() => window.dispatchEvent(new Event('pagehide')));
  await dialog.waitFor({state:"detached"});
  await page.evaluate(() => window.openPreview());
  await page.evaluate(() => {window.voice.generation++;window.voice.info.cameraView.update();});
  await dialog.waitFor({state:"detached"});
  assert.equal(await page.locator("fixture-camera").count(), 0);
  // Exercise the production controller: view commands must finish before any Assist/TTS subscription.
  await page.evaluate(() => {
    const card=document.createElement('echo-relay-assist-card');card.setConfig({});card.hass=window.fixtureHass;document.body.append(card);
    window.realCard=card;window.assistCalls=0;card.voice.mode='dashboard';
    card.voice.subscribe=async()=>{window.assistCalls++;};
  });
  await page.evaluate(() => window.realCard.voice.intent('Zeige Haustürkamera',false));
  await dialog.waitFor();
  assert.equal(await page.evaluate(() => window.assistCalls),0);
  assert.equal(await page.evaluate(() => window.realCard.voice.session),null);
  assert.equal(await page.locator('.jv-camera-reply:visible').count(),0);
  assert.equal(await page.getByText('Das aktuelle Einzelbild wird ausgewertet …').count(),1);
  await page.clock.fastForward(30100);await dialog.waitFor({state:'detached'});
  await page.evaluate(() => window.realCard.voice.intent('Zeige Kameras',false));
  await page.locator('fixture-camera').nth(1).waitFor();
  assert.equal(await page.locator('fixture-camera').count(),2);
  assert.equal(await page.evaluate(() => window.assistCalls),0);
  if(process.env.CAMERA_UI_SCREENSHOT)await page.screenshot({path:process.env.CAMERA_UI_SCREENSHOT.replace(/\.png$/,'-overview.png')});
  await page.getByRole('button',{name:'Schließen ✕',exact:true}).click();
  assert.equal(await page.locator('fixture-camera').count(),0);
  await page.evaluate(() => window.realCard.voice.intent('Was siehst du in der Haustürkamera?',false));
  assert.equal(await page.evaluate(() => window.assistCalls),1);
  await page.evaluate(() => window.realCard.voice.stop());
  console.log("Camera UI: live configuration, speech text, persistent player, manual/automatic close, hard deadline and cancelled late load passed.");
} finally { await browser.close(); }
