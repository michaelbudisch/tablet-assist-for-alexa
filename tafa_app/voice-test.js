/* TAFA native Android device controls + optional single-shot browser diagnostics.
   No browser wakeword loop. Device changes require explicit admin action. */
(() => {
  "use strict";
  const root = document.getElementById("tafa-voice-test");
  if (!root) return;
  const en = root.dataset.lang === "en";
  const tr = (de, eng) => en ? eng : de;
  const el = id => document.getElementById(id);
  const csrf = root.dataset.csrf || "";
  const nativeModes = root.querySelectorAll("[data-native-mode]");
  const deviceSelect = el("voice-device-select");
  const voicePanel = document.getElementById("voice");
  const history = el("voice-history-list");
  const audio = new Audio();
  audio.preload = "none";
  let generation = 0, recording = null, controller = null;
  let devices = [], nativeBusy = false, deviceLoading = false;
  let conversationId = "", lastAudioId = "", latestError = "", running = false;
  const totals = [];
  let lastStatus = null;
  let loaded = false;

  function mark(message, phase) {
    el("voice-live").textContent = message;
    if (phase) el("voice-phase").textContent = phase;
  }
  function indicator(message, active = false) {
    const output = el("voice-mic-indicator");
    output.textContent = message;
    output.dataset.listening = String(active);
  }
  function setError(message) {
    latestError = message || "";
    el("voice-error").textContent = latestError || "—";
    mark(latestError || tr("Bereit", "Ready"), latestError ? tr("Fehler", "Error") : tr("Bereit", "Ready"));
  }
  function ms(value) {
    return Number.isFinite(value) && value >= 0 ? Math.round(value) + " ms" : "—";
  }
  function validStatus(data) {
    if (!data || !data.entities) return;
    lastStatus = data;
    el("voice-pipeline").textContent = data.pipeline || "TAFA Lokal";
    const items = data.entities;
    const stt = items.stt || {}, conv = items.conversation || {}, tts = items.tts || {};
    el("voice-stt-backend").textContent = stt.backend || "—";
    el("voice-tts-backend").textContent = tts.backend || "—";
    el("voice-stt-entity").textContent = stt.entity || "—";
    el("voice-conv-entity").textContent = conv.entity || "—";
    el("voice-tts-entity").textContent = tts.entity || "—";
    el("voice-time-first").textContent = ms(tts.first_audio_ms);
    el("voice-native-stt-time").textContent = ms(stt.duration_ms);
  }
  async function postForm(action, additional = {}, signal) {
    const params = new URLSearchParams({csrf, action, tab:"voice", lang:en?"en":"de", ...additional});
    const response = await fetch("./", {method:"POST", credentials:"same-origin",
      headers:{"Content-Type":"application/x-www-form-urlencoded"},
      body:params.toString(), cache:"no-store", signal});
    const data = await response.json();
    if (!response.ok) throw Error(data.error || tr("Sprachtest nicht erreichbar", "Speech test unavailable"));
    return data;
  }
  async function refresh() {
    try {
      const data = await postForm("voice_status");
      validStatus(data);
      loaded = true;
    } catch (_) {
      if (!loaded) el("voice-pipeline").textContent = tr("TAFA Lokal nicht erreichbar", "TAFA Lokal unavailable");
    }
  }
  function releaseRecording() {
    if (!recording) return;
    const current = recording;
    recording = null;
    try { current.finish(null); } catch (_) {}
  }
  function stopLoop(message) {
    generation += 1;
    releaseRecording();
    if (controller) { controller.abort(); controller = null; }
    running = false;
    if (message) mark(message, tr("Bereit", "Ready"));
    indicator(tr("Mikrofon aus", "Mic off"), false);
  }
  function activePage() {
    return !document.hidden && voicePanel && !voicePanel.hidden;
  }
  function showDevice() {
    const device = devices.find(item => item.device_id === deviceSelect.value);
    const telemetry = device?.telemetry || {};
    const control = device?.control || {};
    const status = el("voice-native-status");
    for (const button of nativeModes) {
      const selected = button.dataset.nativeMode;
      const current=!device?"":device.muted?"mute":
        device.voice_mode==="continuous"?"continuous":"wake";
      button.setAttribute("aria-pressed", String(!!device && selected===current));
      const version=(telemetry.app_version||"0.0.0").split(".").map(v=>Number.parseInt(v,10)||0);
      const supported=version[0]>1||(version[0]===1&&
        (version[1]>2||(version[1]===2&&version[2]>=1)));
      button.disabled = nativeBusy || !device?.online || (selected==="continuous"&&!supported);
    }
    el("voice-native-word").textContent = device?.word || "—";
    el("voice-native-microphone").textContent = telemetry.microphone || (device ? (
      device.muted ? tr("Stumm", "Muted") :
      device.voice_mode==="continuous" ? tr("Immer an", "Always on") :
      tr("Rufwort", "Wake word")) : "—");
    const channel=control.channel || telemetry.control_channel;
    el("voice-control-channel").textContent=!device?.online?tr("Offline","Offline"):
      channel==="websocket"?"WebSocket":channel==="poll"?tr("500-ms-Abgleich","500 ms fallback"):
      channel==="inactive"?tr("Nicht aktiv","Inactive"):tr("Noch unbekannt","Not yet reported");
    const acked=Number.isInteger(control.ack_revision)&&
      control.ack_revision===control.revision;
    el("voice-control-confirm").textContent=control.pending?tr("Wird übertragen","Pending"):
      acked?tr("Vom Tablet bestätigt","Acknowledged by tablet"):
      tr("Noch keine Bestätigung","No acknowledgment yet");
    el("voice-control-latency").textContent=Number.isInteger(control.latency_ms)&&
      !control.pending?ms(control.latency_ms):"—";
    el("voice-control-last").textContent=Number.isInteger(control.applied_at)?
      new Date(control.applied_at).toLocaleTimeString():"—";
    const followups=el("voice-followups-select");
    const selectedLimit=Number.isInteger(device?.followup_limit)?device.followup_limit:-1;
    if(followups.dataset.dirty!=="true"){
      followups.value=String(selectedLimit);
      if(followups.value==="")followups.value="-1";
    }
    const local=Number.isInteger(telemetry.local_followup_limit)?telemetry.local_followup_limit:null;
    el("voice-followups-effective").textContent=local===null?
      tr("App-Grenze noch nicht gemeldet. Für unbegrenzt in der App ausdrücklich „Unbegrenzt“ wählen.",
         "App limit not reported yet. Explicitly choose Unlimited in the Android app."):
      tr("App-Grenze: ","App limit: ")+(local===-1?tr("Unbegrenzt","Unlimited"):String(local))+
      " · "+tr("HA-Grenze: ","HA ceiling: ")+(selectedLimit===-1?tr("App-Einstellung","App setting"):String(selectedLimit));
    followups.disabled=!device?.online||nativeBusy;
    el("voice-followups-save").disabled=!device?.online||nativeBusy;
    el("voice-native-audio").textContent = telemetry.audio || "—";
    el("voice-native-bluetooth").textContent = telemetry.bluetooth || "—";
    el("voice-native-indicator").textContent = device ? (
      device.online ? tr("Online", "Online") : tr("Offline", "Offline")) : tr("Kein Tablet", "No tablet");
    el("voice-native-indicator").dataset.listening = String(!!device?.online && !device.muted);
    if (!nativeBusy) status.textContent = !device ? tr(
      "Kein TAFA-Tablet angemeldet.", "No enrolled TAFA tablet.") : (
      device.online ? (telemetry.wake_status || tr("Verbunden", "Connected")) :
      tr("Tablet offline · Änderungen derzeit nicht möglich", "Tablet offline · controls unavailable"));
  }
  function renderDevices(next) {
    if (!next || !Array.isArray(next.devices)) throw Error(tr("Gerätestatus ungültig", "Invalid device status"));
    devices = next.devices.filter(item => /^[a-f0-9]{32}$/.test(item.device_id || ""));
    const chosen = deviceSelect.value;
    deviceSelect.replaceChildren();
    if (!devices.length) {
      const option=document.createElement("option");
      option.value="";option.textContent=tr("Kein Tablet", "No tablet");
      deviceSelect.append(option);
    } else {
      for (const device of devices) {
        const option=document.createElement("option");
        option.value=device.device_id;
        option.textContent=(device.room||"Tablet")+" · "+(device.online ? "Online" : "Offline");
        deviceSelect.append(option);
      }
      deviceSelect.value=devices.some(item=>item.device_id===chosen)?chosen:devices[0].device_id;
    }
    showDevice();
  }
  async function loadDevices() {
    if (deviceLoading || nativeBusy) return;
    deviceLoading=true;
    try {
      const response=await postForm("voice_devices");
      renderDevices(response);
    } catch(_) {
      el("voice-native-status").textContent=tr(
        "Android-Gerätestatus momentan nicht erreichbar", "Android device status currently unavailable");
    } finally {deviceLoading=false;}
  }
  async function setNativeMode(next) {
    if (nativeBusy || !["mute","wake","continuous"].includes(next)) return;
    const selected=devices.find(item=>item.device_id===deviceSelect.value);
    if (!selected || !selected.online) return;
    nativeBusy=true;
    showDevice();
    el("voice-native-status").textContent=tr("Mikrofon-Einstellung wird gespeichert", "Saving microphone setting");
    try {
      const updated=await postForm("voice_device_mode",{device_id:selected.device_id,mode:next});
      renderDevices(updated);
      el("voice-native-status").textContent=tr(
        "Gespeichert · warte auf Android-Bestätigung",
        "Saved · waiting for Android acknowledgment");
    } catch(_) {
      el("voice-native-status").textContent=tr(
        "Änderung fehlgeschlagen · bisherige Einstellung bleibt aktiv",
        "Update failed · previous setting remains active");
    } finally {nativeBusy=false;showDevice();}
  }
  async function saveFollowups(){
    if(nativeBusy)return;
    const device=devices.find(item=>item.device_id===deviceSelect.value);
    if(!device||!device.online)return;
    const value=Number(el("voice-followups-select").value);
    if(!Number.isInteger(value)||value < -1||value >100)return;
    nativeBusy=true;
    try{
      const updated=await postForm("voice_device_followups",{
        device_id:device.device_id,limit:String(value)});
      delete el("voice-followups-select").dataset.dirty;
      renderDevices(updated);
    }catch(error){
      el("voice-native-status").textContent=tr("Anschlussfragen konnten nicht gespeichert werden",
        "Could not save follow-up setting");
    }finally{nativeBusy=false;showDevice();}
  }
  function downsample(chunks, sampleRate) {
    const sourceLength = chunks.reduce((count, chunk) => count + chunk.length, 0);
    if (!sourceLength) return new Uint8Array(0);
    const joined = new Float32Array(sourceLength);
    let written = 0;
    for (const chunk of chunks) { joined.set(chunk, written); written += chunk.length; }
    const count = Math.min(480000, Math.floor(sourceLength * 16000 / sampleRate));
    const bytes = new Uint8Array(count * 2);
    const view = new DataView(bytes.buffer);
    for (let i=0; i<count; i++) {
      const pos = i * sampleRate / 16000;
      const lo = Math.floor(pos);
      const part = pos-lo;
      const value = joined[Math.min(lo,sourceLength-1)]*(1-part) +
                    joined[Math.min(lo+1,sourceLength-1)]*part;
      const sample = Math.round(Math.max(-1,Math.min(1,value))*32767);
      view.setInt16(i*2,sample,true);
    }
    return bytes;
  }
  async function recordOne(current) {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      throw Error(tr("Mikrofon benötigt HTTPS und Browserfreigabe.", "Microphone requires HTTPS and browser permission."));
    }
    if (document.hidden) return null;
    const stream = await navigator.mediaDevices.getUserMedia({audio:{
      channelCount:{ideal:1},echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
    if (current !== generation || document.hidden) {
      stream.getTracks().forEach(t => t.stop()); return null;
    }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) {stream.getTracks().forEach(t=>t.stop()); throw Error("AudioContext unavailable");}
    const context = new AC();
    let source, node, sink, timer, settled = false, start = performance.now();
    let chunks = [], heard = false, silence = 0, speechFrames = 0;
    const rate = context.sampleRate;
    indicator(tr("Mikrofon aktiv", "Mic active"),true);
    mark(tr("Hört zu · Bitte sprechen", "Listening · Speak now"), tr("Hört zu", "Listening"));
    return new Promise(async (resolve, reject) => {
      function finish(result, error) {
        if (settled) return;
        settled = true; clearTimeout(timer);
        try {node && node.disconnect();source && source.disconnect();sink && sink.disconnect();} catch (_) {}
        stream.getTracks().forEach(t => t.stop());
        context.close().catch(()=>{});
        if (recording?.finish === finish) recording = null;
        indicator(tr("Mikrofon aus", "Mic off"),false);
        if (error) reject(error); else resolve(result);
      }
      recording = {finish};
      try {
        await context.resume();
        if (settled || current !== generation) {finish(null);return;}
        source=context.createMediaStreamSource(stream);
        node=context.createScriptProcessor(4096,1,1);
        sink=context.createGain();sink.gain.value=0;
        node.onaudioprocess = event => {
          if (settled || current !== generation || document.hidden) {finish(null);return;}
          const frame = event.inputBuffer.getChannelData(0);
          let squared = 0;
          for(let i=0;i<frame.length;i++) squared += frame[i]*frame[i];
          const rms=Math.sqrt(squared/frame.length);
          const seconds=frame.length/rate;
          if (rms > 0.018) {heard=true;silence=0;speechFrames++;}
          else if (heard) silence += seconds;
          if (heard) chunks.push(new Float32Array(frame));
          const duration=performance.now()-start;
          if (heard && speechFrames>=2 && silence>=1.1) {
            const bytes=downsample(chunks,rate);
            finish(bytes.length>=16000?{pcm:bytes,durationMs:Math.round(duration)}:null);
          } else if (duration > 23000) {
            if (heard) {
              const bytes=downsample(chunks,rate);
              finish(bytes.length>=16000?{pcm:bytes,durationMs:Math.round(duration)}:null);
            } else finish(null);
          }
        };
        source.connect(node);node.connect(sink);sink.connect(context.destination);
        timer=setTimeout(()=>finish(null),24000);
      } catch (error) {finish(null,error);}
    });
  }
  async function runAudio(captured, current) {
    if (!captured || current!==generation) return null;
    controller = new AbortController();
    mark(tr("Audio wird in TAFA verarbeitet", "Audio processing in TAFA"), tr("Verarbeitet", "Processing"));
    const url="./voice/run?kind=turn"+
      (conversationId?"&conversation_id="+encodeURIComponent(conversationId):"");
    const response=await fetch(url,{method:"POST", credentials:"same-origin",
      headers:{"Content-Type":"application/octet-stream","X-TAFA-CSRF":csrf},
      body:captured.pcm,signal:controller.signal,cache:"no-store"});
    const data=await response.json();
    if (!response.ok) throw Error(data.error||tr("Assist-Anfrage fehlgeschlagen","Assist request failed"));
    return data;
  }
  async function runText(value,current) {
    controller = new AbortController();
    mark(tr("Text wird von TAFA beantwortet", "TAFA is answering"), tr("Verarbeitet","Processing"));
    return await postForm("voice_text",{text:value,conversation_id:conversationId},controller.signal);
  }
  function timing(data, captured) {
    const times = data.timings || {};
    el("voice-time-capture").textContent = ms(captured?.durationMs);
    el("voice-time-stt").textContent = ms(times.stt_ms);
    el("voice-time-audio").textContent =
      ms(Number.isFinite(captured?.durationMs)&&Number.isFinite(times.stt_ms)
       ? captured.durationMs+times.stt_ms : null);
    el("voice-time-intent").textContent = ms(times.intent_ms);
    el("voice-time-tts").textContent = ms(times.tts_ms);
    el("voice-time-total").textContent = ms(times.total_ms);
    if (Number.isFinite(times.total_ms)) totals.push(times.total_ms);
    if (totals.length > 5) totals.shift();
    el("voice-time-average").textContent =
      totals.length ? ms(totals.reduce((a,b)=>a+b,0)/totals.length) : "—";
  }
  function entry(data, captured, question) {
    const stamp = new Date().toLocaleTimeString(en?"en-GB":"de-DE");
    const row=document.createElement("article");
    row.className="voice-turn";
    const head=document.createElement("div");
    head.className="voice-turn-head";
    const a=document.createElement("strong");a.textContent=stamp;
    const b=document.createElement("span");
    b.textContent=(data.pipeline||"TAFA Lokal")+" · "+ms(data.timings?.total_ms);
    head.append(a,b);
    const user=document.createElement("p");
    user.textContent=tr("Du: ","You: ")+(question||data.transcript||"—");
    const answer=document.createElement("p");
    answer.textContent="TAFA: "+(data.reply||data.error||"—");
    const meta=document.createElement("small");
    meta.textContent=tr("STT: ","STT: ")+(lastStatus?.entities?.stt?.backend||"—")+
      " · TTS: "+(lastStatus?.entities?.tts?.backend||"—");
    row.append(head,user,answer,meta);
    el("voice-history-empty")?.remove();
    history.prepend(row);
    while(history.children.length>20)history.lastChild.remove();
  }
  async function playback(id, waitForEnd=false) {
    if (!id) return;
    audio.pause();audio.src="./voice/audio/"+encodeURIComponent(id);
    try {
      await audio.play();
      if (waitForEnd) await new Promise(resolve=>{
        const done=()=>{audio.removeEventListener("ended",done);audio.removeEventListener("error",done);resolve();};
        audio.addEventListener("ended",done,{once:true});
        audio.addEventListener("error",done,{once:true});
        setTimeout(done,30000);
      });
    } catch (_) {
      mark(tr("Audio bereit · Mit „Letzte Audioantwort abspielen“ starten",
              "Audio ready · Use Replay latest audio to listen"), tr("Antwort","Response"));
    }
  }
  async function handleResult(data,captured,current,question,autoplay=false) {
    if (current!==generation) return;
    conversationId = data.conversation_id || conversationId;
    if (data.error) setError(data.error); else {
      latestError=""; el("voice-error").textContent="—";
      mark(tr("Antwort empfangen","Answer received"),tr("Antwort","Response"));
    }
    timing(data,captured);
    lastAudioId=data.audio_id||"";
    el("voice-replay").disabled=!lastAudioId;
    await refresh();
    entry(data,captured,question);
    if (lastAudioId && autoplay && current===generation) await playback(lastAudioId,true);
  }
  async function runOnce() {
    if (running) return;
    stopLoop();
    // Manual browser capture never changes native Android settings.
    const current=generation;
    try {
      running=true;
      const captured=await recordOne(current,false);
      if (!captured||current!==generation) return;
      const data=await runAudio(captured,current);
      await handleResult(data,captured,current,null,false);
    } catch(error) {
      if (current===generation) setError(error.message);
    } finally {running=false;}
  }
  nativeModes.forEach(button=>button.addEventListener("click",()=>setNativeMode(button.dataset.nativeMode)));
  deviceSelect.addEventListener("change",()=>{
    delete el("voice-followups-select").dataset.dirty;
    showDevice();
  });
  el("voice-followups-select").addEventListener("change",e=>{e.target.dataset.dirty="true";});
  el("voice-followups-save").addEventListener("click",()=>void saveFollowups());
  el("voice-once").addEventListener("click",()=>{runOnce();});
  el("voice-stop").addEventListener("click",()=>stopLoop(tr("Browser-Aufnahme beendet", "Browser recording stopped")));
  el("voice-refresh").addEventListener("click",()=>{void refresh();void loadDevices();});
  el("voice-clear").addEventListener("click",()=>{
    history.replaceChildren();
    const empty=document.createElement("p");
    empty.className="subtle";empty.id="voice-history-empty";
    empty.textContent=tr("Noch keine Testgespräche.","No test conversations yet.");
    history.append(empty);totals.length=0;conversationId="";
    el("voice-time-average").textContent="—";
  });
  el("voice-text-form").addEventListener("submit",async event=>{
    event.preventDefault(); if(running) return;
    const input=el("voice-text-input"), question=input.value.trim();
    if(!question)return;
    stopLoop();const current=generation;running=true;
    try {
      const data=await runText(question,current);
      await handleResult(data,null,current,question,false);
      input.value="";
    }catch(error){if(current===generation)setError(error.message);}
    finally{running=false;}
  });
  el("voice-replay").addEventListener("click",()=>playback(lastAudioId));
  document.addEventListener("visibilitychange",()=>{
    if(document.hidden){stopLoop();audio.pause();}
    else if(activePage()){void refresh();void loadDevices();}
  });
  if (voicePanel) {
    new MutationObserver(()=>{
      if (voicePanel.hidden){stopLoop();audio.pause();}
      else {void refresh();void loadDevices();}
    }).observe(voicePanel,{attributes:true,attributeFilter:["hidden"]});
  }
  window.addEventListener("hashchange",()=>{
    if(window.location.hash!=="#voice"){stopLoop();audio.pause();}
    else {void refresh();void loadDevices();}
  });
  // Status polling never starts the browser microphone or a second wakeword
  // recognizer. Suppress it when the page is hidden or another tab is selected.
  setInterval(()=>{if(activePage())void loadDevices();},1000);
  setInterval(()=>{if(activePage())void refresh();},20000);
  if(window.location.hash==="#voice"){void refresh();void loadDevices();}
})();
