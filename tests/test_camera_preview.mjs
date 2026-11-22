import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
const file = new URL("../homeassistant/www/jarvis/jarvis-camera-preview-v1.0.0.js", import.meta.url);
const source = await readFile(file, "utf8");
const {previewCamera} = await import("data:text/javascript;base64," + Buffer.from(source).toString("base64"));
const currentSource = await readFile(new URL("../homeassistant/www/jarvis/jarvis-camera-preview-v1.1.0.js", import.meta.url), "utf8");
const current = await import("data:text/javascript;base64," + Buffer.from(currentSource).toString("base64"));
const viewSource = await readFile(new URL("../homeassistant/www/jarvis/jarvis-camera-preview-v1.2.0.js", import.meta.url), "utf8");
const viewVersion = await import("data:text/javascript;base64," + Buffer.from(viewSource).toString("base64"));
globalThis.document = {hidden: false};
globalThis.CustomEvent = class {constructor(type, options) {this.type=type;Object.assign(this,options);}};
function fixture(result={camera_entity_id:"camera.door"}) {
  const events=[],calls=[],session={};
  const voice={session,generation:1,mode:"dashboard",card:{isConnected:true,dispatchEvent:e=>events.push(e)},
    h:{callApi:async(...args)=>{calls.push(args);return result;}}};
  return {voice,session,events,calls};
}
{
  const f=fixture();assert.equal(await previewCamera(f.voice,"Wer ist an der Haustür?",f.session),true);
  assert.deepEqual(f.calls,[["POST","jarvis_echo_relay/resolve_camera",{text:"Wer ist an der Haustür?"}]]);
  assert.equal(f.events[0].type,"hass-more-info");assert.equal(f.events[0].detail.entityId,"camera.door");
  assert.equal(f.events[0].bubbles,true);assert.equal(f.events[0].composed,true);
  assert.equal(f.session.cameraEntity,"camera.door");assert.equal(f.voice.lastKnowledge,null);
}
const previewVersions = [{previewCamera}, current, viewVersion];
for (const {previewCamera} of previewVersions) {
for (const result of [{camera_entity_id:null},{camera_entity_id:"light.door"},{camera_entity_id:"camera.bad<script>"}]) {
  const f=fixture(result);assert.equal(await previewCamera(f.voice,"normal question",f.session),false);assert.equal(f.events.length,0);
}
for (const cancel of [f=>f.voice.generation++,f=>f.voice.session=null,f=>f.voice.card.isConnected=false,f=>document.hidden=true,f=>f.voice.mode="native"]) {
  const f=fixture();let release;f.voice.h.callApi=()=>new Promise(resolve=>release=resolve);
  const pending=previewCamera(f.voice,"door",f.session);cancel(f);release({camera_entity_id:"camera.door"});
  assert.equal(await pending,false);assert.equal(f.events.length,0);document.hidden=false;
}
{
  const f=fixture();f.voice.h.callApi=async()=>{throw Error("403");};
  assert.equal(await previewCamera(f.voice,"door",f.session),false);assert.equal(f.events.length,0);
}
}
for (const result of [{camera_entity_ids:[]},{camera_entity_ids:["camera.door","light.bad"]},
    {camera_entity_ids:["camera.door","camera.door"]},{camera_entity_ids:["camera.a","camera.b","camera.c","camera.d"]}]) {
  const f=fixture(result);assert.equal(await viewVersion.previewCamera(f.voice,"Zeige Kameras",f.session),false);
}
console.log("Camera preview: targeted dialog, valid entity, no stale/hidden/native popup, failure isolation passed.");
