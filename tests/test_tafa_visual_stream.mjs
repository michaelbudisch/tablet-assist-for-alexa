/* node --test tests/test_tafa_visual_stream.mjs */
import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const source=await readFile(new URL("../custom_components/tablet_assist_for_alexa/frontend/visual_client.js",import.meta.url),"utf8");
const {selectTafaVisualDevice,subscribeTafaVisual}=await import("data:text/javascript,"+encodeURIComponent(source));
const room=(device_id,user_id,status="sensor.room_rufwortstatus")=>({device_id,user_id,sensors:{status}});
const identity={devices:[room("a","room-user")]};

test("normal room account resolves its single paired display",()=>{
  assert.equal(selectTafaVisualDevice({user:{is_admin:false}},identity)?.device_id,"a");
});
test("admin dashboard never claims a room implicitly",()=>{
  assert.equal(selectTafaVisualDevice({user:{is_admin:true}},identity),null);
  assert.equal(selectTafaVisualDevice({user:{is_admin:true}},identity,"sensor.room_rufwortstatus")?.device_id,"a");
});
test("multiple tablets require explicit per-display selection",()=>{
  const two={devices:[room("a","room-user","sensor.a"),room("b","room-user","sensor.b")]};
  assert.equal(selectTafaVisualDevice({user:{is_admin:false}},two),null);
  assert.equal(selectTafaVisualDevice({user:{is_admin:false}},two,"sensor.b")?.device_id,"b");
  assert.equal(selectTafaVisualDevice({user:{is_admin:false}},two,"none"),null);
});
test("the authenticated stream admits only the selected device and its user",async()=>{
  let cb,command,unsubscribed=false,received=[];
  const conn={subscribeMessage:async(fn,msg)=>{cb=fn;command=msg;return ()=>{unsubscribed=true;};}};
  const hass={user:{is_admin:false},connection:conn,callWS:async msg=>{
    assert.equal(msg.type,"tablet_assist_for_alexa/visual_identity");return identity;
  }};
  const unsub=await subscribeTafaVisual(hass,data=>received.push(data));
  assert.equal(command.type,"tablet_assist_for_alexa/visual_subscribe");
  cb({event:{tafa_device_id:"b",user_id:"room-user",reply:"wrong device"}});
  cb({event:{tafa_device_id:"a",user_id:"another-user",reply:"wrong user"}});
  cb({event:{tafa_device_id:"a",user_id:"room-user",reply:" "}});
  cb({event:{tafa_device_id:"a",user_id:"room-user",reply:"richtige Antwort"}});
  assert.deepEqual(received.map(x=>x.reply),["richtige Antwort"]);
  unsub();assert.equal(unsubscribed,true);
});
test("no legacy event fallback is attempted when identity fails",async()=>{
  let called=false;
  const hass={user:{is_admin:false},connection:{subscribeMessage:()=>{called=true;}},callWS:async()=>{throw Error("unpaired");}};
  await assert.rejects(subscribeTafaVisual(hass,()=>{}),/unpaired/);
  assert.equal(called,false);
});
