/* TAFA Control Center speech-test: browser-only mic modes and local Assist runs.
   No audio or history persists; no HA/Android settings are mutated. */
(() => {
  "use strict";
  const root = document.getElementById("tafa-voice-test");
  if (!root) return;
  const en = root.dataset.lang === "en";
  const tr = (de, eng) => en ? eng : de;
  const el = id => document.getElementById(id);
  const csrf = root.dataset.csrf || "";
  const modes = root.querySelectorAll("[data-voice-mode]");
  const history = el("voice-history-list");
  const audio = new Audio();
  audio.preload = "none";
  let mode = "mute", generation = 0, recording = null, controller = null;
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
  function chooseMode(selected) {
    if (!["mute","wake","continuous"].includes(selected)) return;
    stopLoop();
    mode = selected;
    modes.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.voiceMode === mode)));
    if (mode === "mute") {
      mark(tr("Stumm · Nur durch „Einmal sprechen“ wird das Mikrofon kurz aktiviert.",
              "Muted · Only Speak once activates the microphone briefly."), tr("Bereit", "Ready"));
    } else {
      const current = generation;
      runLoop(current).catch(error => {
        if (current === generation) { mode = "mute"; chooseMode("mute"); setError(error.message); }
      });
    }
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
  async function recordOne(current, wake = false) {
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
    mark(wake ? tr("Warte auf „Jarvis“ / „Hey Jarvis“ / „Alexa“", "Listening for Jarvis / Hey Jarvis / Alexa") :
      tr("Hört zu · Bitte sprechen", "Listening · Speak now"), tr("Hört zu", "Listening"));
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
          } else if (duration > (wake?18000:23000)) {
            if (heard) {
              const bytes=downsample(chunks,rate);
              finish(bytes.length>=16000?{pcm:bytes,durationMs:Math.round(duration)}:null);
            } else finish(null);
          }
        };
        source.connect(node);node.connect(sink);sink.connect(context.destination);
        timer=setTimeout(()=>finish(null), wake?19000:24000);
      } catch (error) {finish(null,error);}
    });
  }
  async function runAudio(captured, wake, current) {
    if (!captured || current!==generation) return null;
    controller = new AbortController();
    mark(tr("Audio wird in TAFA verarbeitet", "Audio processing in TAFA"), tr("Verarbeitet", "Processing"));
    const url="./voice/run?kind="+(wake?"wake":"turn")+
      (conversationId && !wake?"&conversation_id="+encodeURIComponent(conversationId):"");
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
  async function runLoop(current) {
    if (running) return;
    running=true;
    try {
      while(current===generation && mode!=="mute" && !document.hidden) {
        const wake=mode==="wake";
        const captured=await recordOne(current,wake);
        if (current!==generation||document.hidden) break;
        if (!captured) continue;
        let data=await runAudio(captured,wake,current);
        if (current!==generation) break;
        if (wake) {
          const phrase=(data.transcript||"").trim();
          const match=phrase.match(/^(?:hey\s+)?(?:jarvis|alexa)\b[\s.,!?;:]*(.*)$/i);
          if (!match) {
            mark(tr("Kein Rufwort erkannt · Warte weiter", "No wake phrase · listening again"),tr("Rufwort","Wake word"));
            continue;
          }
          mark(tr("Rufwort erkannt","Wake phrase detected"),tr("Rufwort","Wake word"));
          let question=match[1]?.trim();
          let next=null;
          if (!question) {
            next=await recordOne(current,false);
            if (current!==generation||!next) continue;
            question=null;
          }
          data=question?await runText(question,current):await runAudio(next,false,current);
          await handleResult(data,next,current,question,true);
        } else await handleResult(data,captured,current,null,true);
        if(current!==generation)break;
      }
    } catch(error) {
      if (current===generation) {
        mode="mute";stopLoop();
        modes.forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.voiceMode==="mute")));
        setError(error.name==="NotAllowedError"?tr("Mikrofonberechtigung verweigert","Microphone permission denied"):error.message);
      }
    } finally {running=false;}
  }
  async function runOnce() {
    if (running) return;
    chooseMode("mute");
    // Manual push-to-talk remains available even when background listening is muted.
    const current=generation;
    try {
      running=true;
      const captured=await recordOne(current,false);
      if (!captured||current!==generation) return;
      const data=await runAudio(captured,false,current);
      await handleResult(data,captured,current,null,false);
    } catch(error) {
      if (current===generation) setError(error.message);
    } finally {running=false;}
  }
  modes.forEach(button=>button.addEventListener("click",()=>chooseMode(button.dataset.voiceMode)));
  el("voice-once").addEventListener("click",()=>{runOnce();});
  el("voice-stop").addEventListener("click",()=>chooseMode("mute"));
  el("voice-refresh").addEventListener("click",()=>refresh());
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
    chooseMode("mute");const current=generation;running=true;
    try {
      const data=await runText(question,current);
      await handleResult(data,null,current,question,false);
      input.value="";
    }catch(error){if(current===generation)setError(error.message);}
    finally{running=false;}
  });
  el("voice-replay").addEventListener("click",()=>playback(lastAudioId));
  document.addEventListener("visibilitychange",()=>{
    if(document.hidden){chooseMode("mute");audio.pause();}
    else if(window.location.hash==="#voice")refresh();
  });
  window.addEventListener("hashchange",()=>{
    if(window.location.hash!=="#voice"){chooseMode("mute");audio.pause();}
    else refresh();
  });
  if(window.location.hash==="#voice")refresh();
})();
