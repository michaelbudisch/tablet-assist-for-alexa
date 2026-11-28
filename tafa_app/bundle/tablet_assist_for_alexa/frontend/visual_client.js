/* TAFA v0.4.64: authenticated, per-device visual response stream.
 * This module never requests microphone access and never subscribes to
 * administrator-only Home Assistant bus events. */
export const VISUAL_BINDING_KEY="tafa.dashboard.local_voice_sensor.v1";

export function selectTafaVisualDevice(hass, identity, preference=null) {
  const devices=Array.isArray(identity?.devices)?identity.devices.filter(d=>
    d&&typeof d.device_id==="string"&&d.device_id&&
    typeof d.user_id==="string"&&d.user_id):[];
  let selected=preference;
  if(selected===null){
    try{selected=globalThis.localStorage?.getItem(VISUAL_BINDING_KEY)||"";}
    catch{selected="";}
  }
  if(selected==="none")return null;
  if(selected){
    const match=devices.find(d=>d.device_id===selected||d.sensors?.status===selected);
    if(match)return match;
  }
  // Repair a stale saved device after Android reinstallation only when
  // precisely one tablet belongs to this local display. Desktop admins
  // still require explicit binding; multiple devices are never guessed.
  const android=typeof navigator!=="undefined"&&/Android/i.test(navigator.userAgent||"");
  if(devices.length!==1||(!android&&hass?.user?.is_admin===true))return null;
  if(android&&selected)try{globalThis.localStorage?.setItem(VISUAL_BINDING_KEY,devices[0].device_id);}catch{}
  return devices[0];
}

export async function subscribeTafaVisual(hass, onReply, options={}) {
  const connection=hass?.connection;
  if(typeof connection?.subscribeMessage!=="function"||
     typeof hass?.callWS!=="function")
    throw new Error("TAFA visual_subscribe requires the Home Assistant WebSocket API");
  const identity=await hass.callWS({type:"tablet_assist_for_alexa/visual_identity"});
  if(hass.connection!==connection)return ()=>{};
  const device=selectTafaVisualDevice(hass,identity,options.binding??null);
  if(!device)return ()=>{}; // Passive display: never borrow another room's reply.
  const unsubscribe=await connection.subscribeMessage(packet=>{
    const data=packet?.event?.data||packet?.event||packet?.data||packet;
    if(!data||typeof data!=="object")return;
    if(data.tafa_device_id!==device.device_id||data.user_id!==device.user_id)return;
    if(typeof data.reply!=="string"||!data.reply.trim())return;
    onReply(data);
  },{type:"tablet_assist_for_alexa/visual_subscribe"});
  return typeof unsubscribe==="function"?unsubscribe:()=>{};
}
