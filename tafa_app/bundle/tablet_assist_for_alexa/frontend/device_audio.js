/* Administrator-controlled Multiroom pairing for the TAFA Devices page.
 * Deliberately no stored tokens, account creation, or automatic reassignments.
 */
const STRINGS={
  de:{
    title:"Multiroom-Audio", wake:"Rufwortgerät registriert",
    ready:"Audio verbunden und bereit",online:"Audio verbunden · Wiedergabe noch nicht bereit",
    offline:"Audio-Raum zugeordnet · Player offline",missing:"Audio-Raum noch nicht zugeordnet",
    user:"HA-Benutzer (ohne Administratorrechte)",room:"Audio-Raumkennung",
    pair:"Audio-Raum verbinden",update:"Zuordnung speichern",
    hint:"Wähle einen aktiven HA-Benutzer ohne Administratorrechte. Auf dem Tablet denselben Benutzer-Token verwenden, Multiroom-Audio aktivieren und den Player starten. Kein YAML nötig.",
    select:"Benutzer auswählen",
    noUsers:"Kein aktiver Benutzer ohne Administratorrechte gefunden. Unter Einstellungen → Personen → Benutzer anlegen.",
    admin:"Die Audio-Raumzuordnung kann nur ein HA-Administrator vornehmen.",
    unavailable:"Die Audio-Raumverwaltung ist nicht erreichbar. Prüfe, ob die aktuelle TAFA-Integration geladen ist.",
    mismatch:"Dieses Rufwortgerät wurde mit einem anderen HA-Benutzer registriert. Auf dem Tablet zuerst den Token des ausgewählten Benutzers verwenden und die Rufwort-Erkennung neu starten.",
    success:"Audio-Raum gespeichert. Auf dem Tablet Multiroom-Audio aktivieren und Player starten.",
    replace:"Dieser Raum gehört schon einem anderen Benutzer. Die Zuordnung überschreiben und seinen Player trennen?",
    failed:"Die Zuordnung ist fehlgeschlagen. Prüfe die Benutzerwahl und ob der Tablet-Token zu diesem Benutzer gehört.",
    invalid:"Eine gültige Raumkennung eingeben (Kleinbuchstaben, Zahlen, _ oder -)."
  },
  en:{
    title:"Multiroom audio",wake:"Wake device registered",
    ready:"Audio connected and ready",online:"Audio connected · Playback not ready",
    offline:"Audio room assigned · Player offline",missing:"Audio room not assigned yet",
    user:"HA user (non-admin)",room:"Audio room identifier",
    pair:"Connect audio room",update:"Save pairing",
    hint:"Choose an active non-admin HA user. On the tablet, use that account's access token, enable Multiroom audio and start the player. No YAML required.",
    select:"Select a user",
    noUsers:"No active non-admin HA users found. Create one in Settings → People → Users.",
    admin:"Only an HA administrator can pair audio rooms.",
    unavailable:"Audio room management is unavailable. Check that the current TAFA integration is loaded.",
    mismatch:"This wake device was registered using a different HA account. First use the selected user's token in the tablet app and restart wake recognition.",
    success:"Audio room saved. On the tablet, enable Multiroom audio and start the player.",
    replace:"This room belongs to another user. Overwrite the assignment and disconnect their player?",
    failed:"Could not pair this room. Check the HA user selection and tablet token.",
    invalid:"Enter a valid room ID (lowercase letters, digits, _ or -)."
  }
};
export const roomSlug=value=>String(value||"tablet").toLowerCase().replaceAll("ß","ss")
  .normalize("NFD").replace(/[\u0300-\u036f]/g,"")
  .replace(/[^a-z0-9_-]+/g,"_").replace(/^_+|_+$/g,"").slice(0,64)||"tablet";

export async function fetchAudioPairings(hass){
  return hass.callApi("POST","jarvis_tablet_audio/room_admin",{action:"list"});
}
const el=(tag,text)=>{
  const node=document.createElement(tag);
  if(text!==undefined)node.textContent=text;
  return node;
};
export function renderAudioPairing({container,hass,device,audio,language,onChanged}){
  const t=STRINGS[language==="de"?"de":"en"];
  const wrap=el("div");
  wrap.style.cssText="margin-top:16px;padding:14px;border:1px solid var(--divider-color);border-radius:12px;display:grid;gap:10px";
  wrap.append(el("h2",t.title));
  const paragraph=txt=>{const p=el("p",txt);wrap.append(p);return p;};
  paragraph(t.wake);
  if(!hass.user?.is_admin){
    paragraph(t.admin);container.append(wrap);return;
  }
  if(!audio||audio.unavailable){
    paragraph(t.unavailable);container.append(wrap);return;
  }
  const deviceId=String(device.device_id||"");
  const info=(Array.isArray(audio.devices)?audio.devices:[]).find(x=>x.device_id===deviceId);
  const ownerId=info?.owner_user_id||"";
  const rooms=Array.isArray(audio.rooms)?audio.rooms:[];
  const ownerDevices=(Array.isArray(audio.devices)?audio.devices:[]).filter(x=>x.owner_user_id===ownerId);
  // Existing assignments without a device binding (prior versions) are read
  // without changing or dropping the assigned user or active playback session.
  const current=rooms.find(x=>x.wake_device_id===deviceId) ||
    (ownerId&&ownerDevices.length===1?rooms.find(x=>x.user_id===ownerId&&!x.wake_device_id):undefined);
  paragraph(!current?t.missing:current.online?(current.ready?t.ready:t.online):t.offline);
  paragraph(t.hint);
  const users=Array.isArray(audio.users)?audio.users:[];
  if(!users.length){
    paragraph(t.noUsers);container.append(wrap);return;
  }
  const label=el("label",t.user);
  label.style.cssText="display:grid;gap:6px";
  const select=el("select");
  select.setAttribute("aria-label",t.user);
  const blank=el("option",t.select);blank.value="";select.append(blank);
  for(const user of users){
    const option=el("option",user.name);option.value=user.id;select.append(option);
  }
  select.value=current?.user_id||ownerId;
  label.append(select);wrap.append(label);
  const roomLabel=el("label",t.room);
  roomLabel.style.cssText="display:grid;gap:6px";
  const slug=el("input");
  slug.type="text";slug.maxLength=64;slug.value=current?.room||roomSlug(device.room);
  slug.setAttribute("aria-label",t.room);
  roomLabel.append(slug);wrap.append(roomLabel);
  const status=el("p");
  status.setAttribute("role","status");wrap.append(status);
  const btn=el("button",current?t.update:t.pair);
  btn.className="primary";btn.disabled=!select.value;
  const warn=()=>{
    const mismatch=Boolean(ownerId&&select.value&&ownerId!==select.value);
    status.textContent=mismatch?t.mismatch:"";
    btn.disabled=!select.value||mismatch;
  };
  select.onchange=warn;warn();
  btn.onclick=async()=>{
    const userId=select.value,room=slug.value.trim();
    if(!userId||!/^[a-z0-9][a-z0-9_-]{0,63}$/.test(room)){status.textContent=t.invalid;return;}
    const occupied=rooms.find(x=>x.room===room&&x.user_id!==userId);
    let replace=false;
    if(occupied){if(!window.confirm(t.replace))return;replace=true;}
    btn.disabled=true;status.textContent="";
    try{
      await hass.callApi("POST","jarvis_tablet_audio/room_admin",{
        action:"pair",device_id:deviceId,user_id:userId,room,replace
      });
      status.textContent=t.success;
      if(typeof onChanged==="function")await onChanged();
    }catch(err){
      const msg=String(err?.body?.error||err?.message||"");
      status.textContent=/another HA account|different HA account/i.test(msg)?t.mismatch:t.failed;
    }finally{btn.disabled=false;}
  };
  wrap.append(btn);container.append(wrap);
}
