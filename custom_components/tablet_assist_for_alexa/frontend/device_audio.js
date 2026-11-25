/* Administrator-controlled Multiroom pairing for the TAFA Devices page.
 * Deliberately no stored tokens, account creation, or automatic reassignments.
 */
const STRINGS={
  de:{
    title:"Multiroom-Audio", wake:"Rufwortgerät registriert",
    camera:"Kamerazugriff für diesen Raum erlauben",cameraLive:"Kamera sendet gerade Bilder",cameraOff:"Kamera aus oder nicht aktiv",
    cameraHint:"Aus Datenschutzgründen zunächst deaktiviert. Die Freigabe allein schaltet keine Kamera ein: Der Stream muss auf dem Tablet ausdrücklich gestartet werden. Beim Ausschalten werden gespeicherte Momentaufnahmen verworfen.",
    cameraSaved:"Kameraberechtigung gespeichert. Auf dem Tablet Multiroom-Audio aktiviert lassen und die Kameraübertragung ausdrücklich starten.",cameraFailed:"Kamerafreigabe konnte nicht gespeichert werden.",
    ready:"Audio verbunden und bereit",online:"Audio verbunden · Wiedergabe noch nicht bereit",
    offline:"Audio-Raum zugeordnet · Player offline",missing:"Audio-Raum noch nicht zugeordnet",
    user:"HA-Benutzer (ohne Administratorrechte)",room:"Audio-Raumkennung",
    pair:"Audio-Raum verbinden",update:"Zuordnung speichern",
    hint:"Wähle einen aktiven HA-Benutzer ohne Administratorrechte. Auf dem Tablet denselben Benutzer-Token verwenden, Multiroom-Audio aktivieren und den Player starten. Kein YAML nötig.",
    select:"Benutzer auswählen",
    noUsers:"Kein aktiver Benutzer ohne Administratorrechte gefunden. Unter Einstellungen → Personen → Benutzer anlegen.",
    admin:"Die Audio-Raumzuordnung kann nur ein HA-Administrator vornehmen.",
    unavailable:"Die Audio-Raumverwaltung ist nicht erreichbar. Prüfe, ob die aktuelle TAFA-Integration geladen ist.",
    mismatch:"Das Rufwortgerät gehört noch zu einem anderen HA-Benutzer. Beim Speichern kann ein Administrator die Zuordnung ausdrücklich übertragen. Anschließend den ausgewählten Benutzer-Token auf dem Tablet verwenden.",
    success:"Audio-Raum gespeichert. Auf dem Tablet Multiroom-Audio aktivieren und Player starten.",
    replace:"Dieser Raum gehört schon einem anderen Benutzer. Die Zuordnung überschreiben und seinen Player trennen?",
    transfer:"Das Gerät gehört noch einem anderen HA-Benutzer. Die Geräteverwaltung auf den ausgewählten Benutzer übertragen? Danach auf dem Tablet dessen Token verwenden.",
    failed:"Die Zuordnung ist fehlgeschlagen. Prüfe die Benutzerwahl und ob der Tablet-Token zu diesem Benutzer gehört.",
    invalid:"Eine gültige Raumkennung eingeben (Kleinbuchstaben, Zahlen, _ oder -)."
  },
  en:{
    title:"Multiroom audio",wake:"Wake device registered",
    camera:"Allow camera access for this room",cameraLive:"Camera is currently sending frames",cameraOff:"Camera off or not streaming",
    cameraHint:"Off by default for privacy. Enabling access never starts the camera by itself: explicitly start streaming on the tablet. Turning access off clears any stored frames.",
    cameraSaved:"Camera permission saved. Keep Multiroom audio enabled and explicitly start camera sharing on the tablet.",cameraFailed:"Could not save camera permission.",
    ready:"Audio connected and ready",online:"Audio connected · Playback not ready",
    offline:"Audio room assigned · Player offline",missing:"Audio room not assigned yet",
    user:"HA user (non-admin)",room:"Audio room identifier",
    pair:"Connect audio room",update:"Save pairing",
    hint:"Choose an active non-admin HA user. On the tablet, use that account's access token, enable Multiroom audio and start the player. No YAML required.",
    select:"Select a user",
    noUsers:"No active non-admin HA users found. Create one in Settings → People → Users.",
    admin:"Only an HA administrator can pair audio rooms.",
    unavailable:"Audio room management is unavailable. Check that the current TAFA integration is loaded.",
    mismatch:"This wake device belongs to another HA user. An administrator can explicitly approve transfer when saving; then use the selected user's token on the tablet.",
    success:"Audio room saved. On the tablet, enable Multiroom audio and start the player.",
    replace:"This room belongs to another user. Overwrite the assignment and disconnect their player?",
    transfer:"This device is owned by another HA user. Transfer device management to the selected account? Then use that account token on the tablet.",
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
  if(current){
    const cameraBox=el("div");
    cameraBox.style.cssText="display:grid;gap:8px;border-top:1px solid var(--divider-color);padding-top:12px";
    const cameraLabel=el("label");
    cameraLabel.style.cssText="display:flex;align-items:center;gap:8px";
    const cameraToggle=el("input");
    cameraToggle.type="checkbox";cameraToggle.checked=current.camera_enabled===true;
    cameraLabel.append(cameraToggle,document.createTextNode(t.camera));
    cameraBox.append(cameraLabel);
    const cameraState=el("p",current.camera_online?t.cameraLive:t.cameraOff);
    cameraBox.append(cameraState);
    cameraBox.append(el("p",t.cameraHint));
    const cameraFeedback=el("p");
    cameraFeedback.setAttribute("role","status");cameraBox.append(cameraFeedback);
    cameraToggle.onchange=async()=>{
      cameraToggle.disabled=true;cameraFeedback.textContent="";
      try{
        await hass.callApi("POST","jarvis_tablet_audio/room_admin",{
          action:"camera",room:current.room,device_id:deviceId,enabled:cameraToggle.checked
        });
        cameraFeedback.textContent=t.cameraSaved;
        if(typeof onChanged==="function")await onChanged();
      }catch{
        cameraToggle.checked=!cameraToggle.checked;
        cameraFeedback.textContent=t.cameraFailed;
      }finally{cameraToggle.disabled=false;}
    };
    wrap.append(cameraBox);
  }
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
    btn.disabled=!select.value;
  };
  select.onchange=warn;warn();
  btn.onclick=async()=>{
    const userId=select.value,room=slug.value.trim();
    if(!userId||!/^[a-z0-9][a-z0-9_-]{0,63}$/.test(room)){status.textContent=t.invalid;return;}
    const occupied=rooms.find(x=>x.room===room&&x.user_id!==userId);
    let replace=false;
    if(occupied){if(!window.confirm(t.replace))return;replace=true;}
    let transfer_device=false;
    if(ownerId&&ownerId!==userId){if(!window.confirm(t.transfer))return;transfer_device=true;}
    btn.disabled=true;status.textContent="";
    try{
      await hass.callApi("POST","jarvis_tablet_audio/room_admin",{
        action:"pair",device_id:deviceId,user_id:userId,room,replace,transfer_device
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


/** The proven room Assist flow, now exposed as a self-test in TAFA → Devices.
 * Works with the current HA room-account token, or through a scoped
 * administrator test of the exact room shown on the registered tablet.
 */
export function renderSpeechTest({container,hass,device,audio,pipelines,language}){
  const de=language==="de";
  const title=de?"Sprachtest · Einmal sprechen":"Voice test · Speak once";
  const wrap=el("details");
  wrap.style.cssText="margin:16px 0;padding:12px;border:1px solid var(--divider-color);border-radius:12px";
  const summary=el("summary",title);
  summary.style.cssText="font-weight:600;cursor:pointer;padding:8px 0";
  wrap.append(summary);
  const body=el("div");
  body.style.cssText="display:grid;gap:10px;padding:10px 0";
  wrap.append(body);
  const choices=Array.isArray(pipelines)?pipelines.filter(p=>p?.id&&p?.stt_engine&&p?.tts_engine):[];
  const devices=Array.isArray(audio?.devices)?audio.devices:[];
  const rooms=Array.isArray(audio?.rooms)?audio.rooms:[];
  const owner=devices.find(d=>d.device_id===device.device_id)?.owner_user_id||"";
  const ownerDevices=devices.filter(d=>d.owner_user_id===owner);
  const current=rooms.find(r=>r.wake_device_id===device.device_id)||
    (owner&&ownerDevices.length===1?rooms.find(r=>r.user_id===owner&&!r.wake_device_id):null);
  const admin=Boolean(hass.user?.is_admin);
  if(admin&&!current){
    body.append(el("p",de?
      "Bitte zuerst unter Multiroom-Audio einen Raum mit diesem Tablet verbinden.":
      "First connect this tablet to a room under Multiroom audio."));
    container.append(wrap);return;
  }
  if(!choices.length){
    body.append(el("p",de?
      "Keine vollständige Assist-Pipeline (Whisper + TTS) gefunden. Richte zuerst TAFA Lokal unter Sprachassistenten ein.":
      "No complete Assist pipeline (speech recognition + TTS) found. Configure TAFA Lokal in Voice assistants first."));
    const link=el("a",de?"Sprachassistenten öffnen":"Open Voice assistants");
    link.href="/config/voice-assistants";body.append(link);container.append(wrap);return;
  }
  const help=el("p",de?
    "Wie im bisherigen Dashboard: Mikrofon aktivieren, Frage sprechen, Whisper erkennt sie und Qwen/Piper antwortet über den gekoppelten Tablet-Player.":
    "Same as the original dashboard: activate the mic, ask a question, Whisper transcribes it and Qwen/Piper responds on the paired tablet player.");
  body.append(help);
  if(typeof window!=="undefined"&&!window.isSecureContext){
    body.append(el("p",de?
      "Mikrofontest benötigt eine vertrauenswürdige HTTPS-Adresse (oder localhost).":
      "Microphone test requires trusted HTTPS (or localhost)."));
  }
  const label=el("label",de?"Assist-Pipeline":"Assist pipeline");
  label.style.cssText="display:grid;gap:6px";
  const select=el("select");
  const preferred=choices.find(p=>/tafa lokal/i.test(p.name||"")&&/tablet_assist.*stream/.test(p.tts_engine||""))
    ||choices.find(p=>/tafa/i.test(p.name||"")&&/tablet_assist.*stream/.test(p.tts_engine||""))
    ||choices.find(p=>/tablet_assist.*stream/.test(p.tts_engine||""))
    ||choices[0];
  for(const p of choices){
    const opt=el("option",p.name||p.id);
    opt.value=p.id;select.append(opt);
  }
  select.value=preferred.id;label.append(select);body.append(label);
  // A speech synthesis and Android playback check does not access the
  // browser microphone and therefore also works on a private HTTP HA URL.
  // Reuse HA's existing TTS proxy and the exact authenticated room transport.
  const playback=el("div");
  playback.style.cssText="display:grid;gap:8px;padding:12px;border:1px solid var(--divider-color);border-radius:10px";
  playback.append(el("strong",de?"Sprachausgabe testen (ohne Mikrofon)":"Test speech output (no microphone)"));
  const phrase=el("input");
  phrase.type="text";phrase.maxLength=200;
  phrase.value=de?"Hallo, hier ist TAFA. Die Sprachausgabe auf deinem Tablet funktioniert.":
    "Hello, this is TAFA. Speech playback on your tablet is working.";
  phrase.setAttribute("aria-label",de?"Gesprochener Testtext":"Spoken test message");
  playback.append(phrase);
  const send=el("button",de?"Sprachausgabe testen":"Test speech output");
  send.className="primary";playback.append(send);
  const progress=el("p");
  progress.setAttribute("role","status");progress.setAttribute("aria-live","polite");playback.append(progress);
  body.append(playback);

  send.onclick=async()=>{
    const message=phrase.value.trim();
    if(!message)return;
    if(!admin&&!current&&!hass.user){
      progress.textContent=de?"Melde dich mit dem Tablet-Benutzer an.":"Sign in with the tablet user.";
      return;
    }
    const pipeline=choices.find(p=>p.id===select.value);
    if(!pipeline?.tts_engine){
      progress.textContent=de?"Die Assist-Pipeline besitzt keine Sprachausgabe.":"Assist pipeline has no TTS engine.";
      return;
    }
    send.disabled=true;let id="";
    const rpc=async(operation,params={})=>hass.callApi("POST",admin?
      "jarvis_tablet_audio/room_admin":"jarvis_tablet_audio/room_audio",
      admin?{action:"test",room:current.room,device_id:device.device_id,operation,...params}:
        {action:operation,...params});
    try{
      const check=await rpc("status");
      if(!check?.ready){
        throw Error(de?"Tablet-Player ist offline, beschäftigt oder noch nicht bereit.":
          "Tablet player is offline, busy, or not yet ready.");
      }
      progress.textContent=de?"Qwen/Piper erzeugt die Testansage …":"Generating the test voice with Qwen/Piper …";
      const created=await hass.callApi("POST","tts_get_url",{
        engine_id:pipeline.tts_engine,message,cache:false
      });
      const raw=created?.path||created?.url;
      if(typeof raw!=="string")throw Error(de?"TTS hat keine Audio-Adresse geliefert.":"TTS did not return an audio URL.");
      const link=new URL(raw,window.location.origin);
      if(link.origin!==window.location.origin||link.search||link.hash||
        !/^\/api\/tts_proxy\/[A-Za-z0-9_.~-]{1,200}$/.test(link.pathname))
        throw Error(de?"Die erzeugte Audio-Adresse ist ungültig.":"Invalid generated audio path.");
      const result=await rpc("submit",{path:link.pathname});
      if(!result?.accepted||!(/^[a-f0-9]{32}$/).test(result.id||"")){
        throw Error(de?"Tablet-Player nimmt gerade keine Ansage an.":"Tablet player cannot accept an audio job now.");
      }
      id=result.id;
      progress.textContent=de?"Ansage gesendet · Warte auf Wiedergabe …":
        "Audio sent · Waiting for playback …";
      let stage="";
      // Status is reported by the Android room player (not just TTS HTTP success).
      for(let attempt=0;attempt<120;attempt++){
        if(!wrap.isConnected)break;
        const result=await rpc("status",{id});
        stage=result?.stage||"unknown";
        if(stage==="done"){
          progress.textContent=de?"Erfolgreich: Tablet hat die Wiedergabe bestätigt.":
            "Success: tablet confirmed playback.";
          id="";return;
        }
        if(["error","cancelled","expired","unknown"].includes(stage)){
          throw Error(de?"Audio-Wiedergabe fehlgeschlagen ("+stage+").":
            "Audio playback failed ("+stage+").");
        }
        if(stage==="buffering")progress.textContent=de?"Tablet lädt die Audiodatei …":
          "Tablet is buffering audio …";
        if(stage==="playing")progress.textContent=de?"Tablet spielt die Testansage ab …":
          "Tablet is playing test audio …";
        await new Promise(resolve=>setTimeout(resolve,700));
      }
      throw Error(de?"Keine Wiedergabebestätigung vom Tablet.":"Tablet did not confirm playback.");
    }catch(error){
      if(wrap.isConnected)progress.textContent=String(error?.message||error||
        (de?"Sprachausgabe fehlgeschlagen.":"Speech output failed.")).slice(0,260);
    }finally{
      if(id)void rpc("cancel",{id}).catch(()=>{});
      if(wrap.isConnected)send.disabled=false;
    }
  };
  if(typeof window!=="undefined"&&!window.isSecureContext){
    body.append(el("p",de?
      "Der Mikrofontest ist hier gesperrt, weil Home Assistant über HTTP geöffnet wurde. Der Sprachausgabe-Test oben funktioniert trotzdem. Für Fragen per Mikrofon Home Assistant über vertrauenswürdiges HTTPS öffnen.":
      "Microphone testing is blocked because Home Assistant is using HTTP. The speech-output test above still works. To ask spoken questions, open Home Assistant over trusted HTTPS."));
    container.append(wrap);return;
  }
  const holder=el("div");body.append(holder);
  const mount=()=>{
    holder.replaceChildren();
    if(!wrap.open)return;
    const card=el("tafa-room-assist-test");
    holder.append(card);
    card.setConfig({
      title: de?"TAFA · Sprachtest":"TAFA · Voice test",
      instance_id:"tafa-test-"+device.device_id,
      pipeline_id:select.value,
      admin_room:admin?current.room:undefined,
      device_id:device.device_id,
      output:"native_audio"
    });
    card.hass=hass;
  };
  select.onchange=mount;
  wrap.addEventListener("toggle",()=>{if(wrap.open)mount();else holder.replaceChildren();});
  container.append(wrap);
}
