/* Jarvis Room Assist Card | experimental, isolated native room audio */
(() => {
  "use strict";
  const storageKey=(cfg,key)=>"jarvis-room-assist.v1."+(cfg.instance_id||cfg.command_entity)+"."+key;
  const get=(cfg,key,fallback)=>{try{return localStorage.getItem(storageKey(cfg,key))||fallback;}catch{return fallback;}};
  const save=(cfg,key,value)=>{try{localStorage.setItem(storageKey(cfg,key),value);}catch{}};
  const preferenceDefaults={captions:true,history:false,followMode:"auto",pause:1700,sensitivity:100,turns:3,dialogSeconds:90,infoSeconds:30,captionSeconds:10,autoFallback:false};
  const de=h=>String(h?.language||navigator.language||"en").toLowerCase().startsWith("de");
  const labels={
    "Bereit":"Ready","Audio prüfen":"Audio issue","Prüfen":"Check","Mikrofon aus":"Microphone off","Modus wechseln":"Switching mode",
    "Rufwort aktiv · Dauerbetrieb aktivieren":"Wake word on · enable continuous mode","Mikrofon aus · Rufwort aktivieren":"Microphone off · enable wake word","Dauerbetrieb aktiv · ausschalten":"Continuous mode on · switch off",
    "Wakeword startet":"Starting wake word","Dauerbetrieb startet":"Starting continuous mode","Mikrofon nur im sichtbaren Dashboard aktiv":"Microphone active only while dashboard is visible",
    "Warte auf Wakeword":"Waiting for wake word","Warte wieder auf Wakeword":"Waiting for wake word again","Wakeword erkannt":"Wake word detected","Hört zu":"Listening",
    "Mikrofon startet":"Starting microphone","Verarbeitet":"Processing","Antwort":"Response","Sprachausgabe":"Speech output","Echo Relay · verbindet":"Echo Relay · connecting","Echo Relay · puffert":"Echo Relay · buffering",
    "Spricht · Echo Relay":"Speaking · Echo Relay","Spricht · Tablet":"Speaking · tablet","Spricht · Alexa":"Speaking · Alexa",
    "Anschlussfrage":"Follow-up question","Dauerbetrieb · nächste Aufnahme":"Continuous mode · next capture","Rufwort · nächste Aufnahme":"Wake word · next capture",
    "Assistent":"Assistant","Audioausgabe":"Audio output","Dashboard Assist":"In-dashboard assistant","Android-Assistent (Reserve)":"Android assistant (fallback)","Echo Relay · empfohlen":"Echo Relay · recommended",
    "Tablet / Bluetooth":"Tablet / Bluetooth","Alexa direkt (Qwen / Piper)":"Direct Alexa (optional)","Android-Assistent öffnen":"Open native Assist","Einmal sprechen":"Speak once",
    "Antwort wiederholen":"Replay answer","Tablet-Reserve":"Tablet fallback","Alexa direkt aktivieren":"Enable direct Alexa","Abbrechen":"Cancel",
    "Jarvis · Assistent und Audio":"Assistant and audio settings","Mikrofon oben rechts: Rufwort → Dauerbetrieb → Aus. Nur bei sichtbarem Dashboard aktiv. Informiere Anwesende.":"Microphone: wake word → continuous → off. Active only while the dashboard is visible. Inform people nearby.",
    "Alexa direkt nutzt einen zeitlich begrenzt öffentlichen Audio-Link. Nur für nicht vertrauliche Antworten.":"Direct Alexa may use a temporary public audio link. Use only for non-confidential answers.",
    "Echo Relay · verbunden":"Echo Relay · connected","Echo Relay · nicht bereit (App und Bluetooth prüfen)":"Echo Relay · not ready (check app and Bluetooth)",
    "Native Audio App nicht bereit · App starten und Alexa per Bluetooth verbinden":"Echo Relay not ready · start app and connect Bluetooth",
    "Native Audio App starten und Bluetooth verbinden.":"Start Echo Relay and connect Bluetooth.","Keine Audioantwort erhalten":"No audio response received",
    "Warte auf die Android-App":"Waiting for Android app","Warte auf Audiopuffer":"Waiting for audio buffer","Bluetooth-Wiedergabe bestätigt":"Bluetooth playback confirmed",
    "App hat Auftrag nicht angenommen":"App did not accept request","Player-Zeitüberschreitung":"Player timeout","Mikrofon benötigt HTTPS und eine erteilte Berechtigung.":"Microphone needs HTTPS and permission.",
    "Keine weitere Frage · Mikrofon aus":"No follow-up · microphone off","Warte auf Audiofreigabe":"Waiting for microphone access","Jetzt sprechen · kurze Pause vor der Frage":"Speak now","Sprich jetzt · Mikrofon aktiv":"Speak now · microphone active",
    "Mikrofon aus · Dashboard nicht sichtbar":"Microphone off · dashboard not visible","Im Dashboard · Mikrofon aus":"In dashboard · microphone off","Nativer Android-Assistent":"Native Android assistant"
  };
  const tr=(h,s)=>de(h)?s:(labels[s]||s);
  function outputMode(cfg){const v=get(cfg,"output",cfg.output||"native_audio");return ["bluetooth","native_audio",...(cfg.alexa_script?["alexa"]:[])].includes(v)?v:"native_audio";}
  function audioSession(type){try{if(navigator.audioSession)navigator.audioSession.type=type;}catch{}}
  const getMode=cfg=>get(cfg,"mode","dashboard")==="native"?"native":"dashboard";
  const visible=()=>!document.hidden;
  const android=()=>/Android/i.test(navigator.userAgent+" "+(navigator.userAgentData?.platform||""));
  const fmt=x=>String(x??"");
  const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  function element(tag, label, styles){const n=document.createElement(tag);if(label!=null)n.textContent=label;if(styles)n.style.cssText=styles;return n;}
  function native(el,voice){const id=voice.cfg.pipeline_id||"last_used",ext=voice.h?.auth?.external;if(ext?.config?.hasAssist&&typeof ext.fireMessage==="function"){ext.fireMessage({type:"assist/show",payload:{pipeline_id:id,start_listening:true}});return;}el.dispatchEvent(new CustomEvent("hass-action",{bubbles:true,composed:true,detail:{config:{tap_action:{action:"assist",...(voice.cfg.pipeline_id?{pipeline_id:id}:{}),start_listening:true}},action:"tap"}}));}
  // Continuous averaging resampler: no block-boundary sample loss; output exactly 16 kHz mono PCM.
  class PCM16 {
    constructor(rate,cb){this.rate=rate;this.step=rate/16000;this.cb=cb;this.phase=0;this.sum=0;this.weight=0;this.buf=new Int16Array(320);this.i=0;}
    push(data){for(let j=0;j<data.length;j++){let left=1,v=Number.isFinite(data[j])?data[j]:0;while(left>1e-8){const take=Math.min(left,this.step-this.phase);this.sum+=v*take;this.weight+=take;this.phase+=take;left-=take;if(this.phase>=this.step-1e-8){const x=Math.max(-1,Math.min(1,this.sum/this.weight));this.buf[this.i++]=Math.round(x*(x<0?32768:32767));this.phase=0;this.sum=0;this.weight=0;if(this.i===320){this.cb(this.buf);this.buf=new Int16Array(320);this.i=0;}}}}}
  }
  // Audio is forwarded continuously, but client-side endpointing replaces HA's early VAD end.
  // Suppress residual wakeword frames; require several voiced frames, then allow thinking pauses.
  class Endpointer {
    constructor(wake,p=preferenceDefaults){this.silenceFrames=Math.round(p.pause/20);this.sensitivity=p.sensitivity/100;this.frames=0;this.guard=wake?20:0;this.noise=0.003;this.recent=[];this.started=false;this.voiced=0;this.silent=0;this.leading=0;this.threshold=0.008;}
    step(rms){
      this.frames++;
      if(this.frames<=this.guard)return {gate:true,end:false,empty:false};
      this.threshold=Math.max(0.004,Math.min(0.055,Math.max(0.008,Math.min(0.035,this.noise*2.5))/this.sensitivity));
      const voice=rms>=this.threshold;
      if(!this.started&&!voice)this.noise=this.noise*.97+rms*.03;
      this.recent.push(voice);if(this.recent.length>8)this.recent.shift();
      if(!this.started){
        this.leading++;
        if(this.recent.filter(Boolean).length>=5){this.started=true;this.voiced=this.recent.filter(Boolean).length;this.silent=0;}
        return {gate:false,end:false,empty:!this.started&&this.leading>=450};
      }
      if(voice){this.voiced++;this.silent=0;}else this.silent++;
      return {gate:false,end:this.voiced>=12&&this.silent>=this.silenceFrames,empty:this.voiced<12&&this.silent>=this.silenceFrames};
    }
  }
  class Voice {
    constructor(card){
      this.card=card;this.cfg=card.voiceConfig;this.mode="dashboard";this.wake=false;this.continuous=false;this.session=null;this.phase=tr(card.h,"Bereit");this.detail="";this.follow=false;this.dialogId=null;this.lastAudio=null;this.level=0;this.retry=0;this.generation=0;this.playing=false;this.processing=false;this.turnsLeft=0;this.dialogUntil=0;this.output="native_audio";this.lastReply="";this.pref=this.loadPreferences();this.history=[];this.historySeq=0;this.caption=null;
      this.audio=new Audio();this.audio.preload="none";this.audio.playsInline=true;
      this.onHidden=()=>{if(document.hidden)this.stop("Mikrofon aus · Dashboard nicht sichtbar");};
      document.addEventListener("visibilitychange",this.onHidden);
      this._roomStatus=null;
      this._roomStatusTimer=setInterval(()=>void this.refreshRoom(),3000);
      void this.refreshRoom();
      this.onPageHide=()=>this.stop("Mikrofon aus");window.addEventListener("pagehide",this.onPageHide);
    }
    get h(){return this.card.h;}
    get busy(){return !!this.session||this.wake||this.continuous||this.playing||this.processing||this.retryTimer!=null;}
    alive(s){return this.session===s&&this.card.isConnected&&visible();}
    state(phase,detail=""){this.phase=tr(this.h,phase);this.detail=tr(this.h,detail);this.update();}
    report(value){try{Promise.resolve(this.cfg.status_entity&&this.h?.callService("input_text","set_value",{entity_id:this.cfg.status_entity,value:fmt(value).slice(0,255)})).catch(()=>{});}catch{}}
    async setNativeWake(enabled){
      if(!android()||!this.h||!this.cfg.native_notify_service)return;
      try{await this.h.callService("notify",this.cfg.native_notify_service,{message:"command_wake_word_detection",data:{command:enabled?"turn_on":"turn_off",ttl:0,priority:"high"}});this.report("native-wake|"+(enabled?"on":"off")+"|sent");}
      catch(e){this.state("Prüfen","Android-Wakeword: "+fmt(e.message||e));}
    }
    setMode(mode){if(mode!=="dashboard")return;if(mode===this.mode||!["native","dashboard"].includes(mode))return;this.stop("Bereit");this.mode=mode;save(this.cfg,"mode",mode);this.state("Bereit",mode==="dashboard"?"Im Dashboard · Mikrofon aus":"Nativer Android-Assistent");this.report("mode|"+mode);this.setNativeWake(false);}
    nativeAudioReady(){return this._roomStatus?.ready===true&&Date.now()-(this._roomStatusAt||0)<7000;}
    roomRpc(data){return this.h.callApi("POST","jarvis_echo_relay/room_audio",data);}
    async refreshRoom(){
      if(!this.card.isConnected)return;
      if(this._roomRefreshPromise)return this._roomRefreshPromise;
      this._roomRefreshPromise=(async()=>{
        try{
          this._roomStatus=await this.roomRpc({action:"status"});this._roomStatusAt=Date.now();this._roomError="";
          await this.roomRpc({action:"activity",busy:!!(this.session||this.processing||this.playing)}).catch(()=>{});
        }catch(e){
          this._roomStatus=null;
          const status=Number(e?.status_code??e?.status??e?.statusCode??0);
          this._roomError=status===401||status===403?(de(this.h)?"Raumkonto nicht autorisiert (HTTP "+status+")":"Room account not authorized (HTTP "+status+")"):status?(de(this.h)?"Statusabfrage fehlgeschlagen (HTTP "+status+")":"Status request failed (HTTP "+status+")"):(de(this.h)?"Statusabfrage fehlgeschlagen":"Status request failed");
        }
        if(this.card.isConnected)this.update();
      })();
      try{await this._roomRefreshPromise;}finally{this._roomRefreshPromise=null;}
    }
    cancelNativeAudio(){
      const id=this._nativeRequest;this._nativeRequest=null;
      if(id)void this.roomRpc({action:"cancel",id}).catch(()=>{});
    }
    async playNativeAudio(url,keep=false){
      if(!visible()||this.mode!=="dashboard"||!this.card.isConnected)return;
      let target;try{target=new URL(url,location.href);if(target.origin!==location.origin||!/^\/api\/tts_proxy\/[A-Za-z0-9_.~-]{1,200}$/.test(target.pathname)||target.search||target.hash)throw Error("Invalid local audio address");}catch(e){this.playError(fmt(e.message||e));return;}
      const gen=this.generation;
      this._playbackRoute="native_audio";this.playing=true;this.state("Echo Relay · verbindet","Warte auf die Android-App");
      try{
        const result=await this.roomRpc({action:"submit",path:target.pathname});
        const id=result?.id;
        if(!result?.accepted||!/^[a-f0-9]{32}$/.test(id||""))throw Error(de(this.h)?"Raum-Player nicht bereit":"Room player not ready");
        if(gen!==this.generation||!visible()){void this.roomRpc({action:"cancel",id}).catch(()=>{});return;}
        this._nativeRequest=id;
        const start=Date.now();let received=false,last="";
        while(gen===this.generation&&this._nativeRequest===id&&Date.now()-start<150000){
          const r=await this.roomRpc({action:"status",id}),stage=r?.stage||"unknown";
          if(stage==="playing"||stage==="buffering")received=true;
          if(stage!==last){last=stage;if(stage==="buffering")this.state("Echo Relay · puffert","Warte auf Audiopuffer");if(stage==="playing")this.state("Spricht · Echo Relay","Bluetooth-Wiedergabe bestätigt");}
          if(stage==="done"){this._nativeRequest=null;this.finishPlayback(keep);return;}
          if(["cancelled","error","expired","unknown"].includes(stage)){this._nativeRequest=null;this.playError("Room audio · "+stage);return;}
          if(!received&&Date.now()-start>18000)throw Error("App did not accept room audio");
          await wait(500);
        }
        if(gen===this.generation&&this._nativeRequest===id)throw Error("Player timeout");
      }catch(e){if(gen===this.generation){this.cancelNativeAudio();this.playError(fmt(e.message||e));}}
    }

    setOutput(value,confirmed=false){if(value!=="native_audio")return;if(this.busy||!["alexa","bluetooth","native_audio"].includes(value)||value==="alexa"&&!this.cfg.alexa_script)return;if(value==="native_audio"&&!this.nativeAudioReady()){this.state("Audio prüfen","Native Audio App starten und Bluetooth verbinden.");return;}if(value==="alexa"&&this.output!=="alexa"&&!confirmed){this._jarvisMenu="alexa-confirm";this.update();return;}this.output=value;save(this.cfg,"output",value);this.update();}
    beginDialog(){this.turnsLeft=this.pref.turns;this.dialogUntil=Date.now()+this.pref.dialogSeconds*1000;}
    shouldFollow(s){return this.canFollow()&&(!!s.keep||this.pref.followMode==="auto"||(this.pref.followMode==="smart"&&/\?\s*$/.test(s.reply||"")));}
    endDialog(){this.turnsLeft=0;this.dialogUntil=0;this.dialogId=null;this.follow=false;}
    canFollow(){return this.turnsLeft>0&&Date.now()<this.dialogUntil;}
    finishSilent(s){this.finish(s);this.endDialog();this.state("Bereit",this.wake?"Warte wieder auf Wakeword":this.continuous?"Dauerbetrieb · nächste Aufnahme":"Keine weitere Frage · Mikrofon aus");if(this.wake||this.continuous)this.rearm(800);}
    unlock(){
      // Run on an explicit click. The same audio element is reused for later answers.
      if(this.output!=="bluetooth"||this.audio.src||this.unlocked)return;
      const raw=new Uint8Array(44+1600),v=new DataView(raw.buffer);
      const ascii=(off,str)=>{for(let i=0;i<str.length;i++)raw[off+i]=str.charCodeAt(i);};
      ascii(0,"RIFF");v.setUint32(4,raw.length-8,true);ascii(8,"WAVEfmt ");v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,16000,true);v.setUint32(28,32000,true);v.setUint16(32,2,true);v.setUint16(34,16,true);ascii(36,"data");v.setUint32(40,1600,true);
      const url=URL.createObjectURL(new Blob([raw],{type:"audio/wav"}));this.audio.src=url;
      const clear=()=>{URL.revokeObjectURL(url);};this.audio.addEventListener("ended",clear,{once:true});
      this.audio.play().then(()=>{this.unlocked=true;}).catch(()=>{clear();});
    }
    async tap(button){
      if(this.mode==="native"){native(button,this);return;}
      if(this.busy){this.stop("Mikrofon aus");return;}
      this.unlock();this.dialogId=null;this.follow=false;this.beginDialog();this.setNativeWake(false);await this.capture(false);
    }
    async toggleWake(){
      if(this.wake){this.stop("Freisprechen aus");return;}
      if(this.mode!=="dashboard"||this.busy)return;
      this.unlock();this.wake=true;this.endDialog();this.retry=0;this.setNativeWake(false);
      this.state("Wakeword startet","Mikrofon aktiv nur im sichtbaren Dashboard");
      await this.capture(true);
    }
    async cycle(){
      if(this.continuous){this.stop("Mikrofon aus");return;}
      const next=this.wake?"continuous":"wake";
      if(this.mode!=="dashboard")this.setMode("dashboard");
      const prev=this.session;this.stop("Modus wechseln");this.unlock();
      this.wake=next==="wake";this.continuous=next==="continuous";this.retry=0;
      if(this.continuous)this.beginDialog();
      const generation=this.generation;
      this.state(this.wake?"Wakeword startet":"Dauerbetrieb startet","Mikrofon nur im sichtbaren Dashboard aktiv");
      this.setNativeWake(false);
      if(prev?.closePromise)await prev.closePromise;
      if(generation!==this.generation)return;
      await this.capture(this.wake);
    }
    makeSession(wake,kind){const s={wake,kind,handler:null,unsub:null,ended:false,stage:"start",speechMs:0,peak:0,peakRms:0,frames:0,follow:false,text:"",tts:null,runEnded:false};this.session=s;return s;}
    async capture(wake,follow=false){
      if(this.session||this.mode!=="dashboard"||!visible()||!this.card.isConnected)return;
      if(!window.isSecureContext||!navigator.mediaDevices?.getUserMedia){this.fail(null,"Mikrofon benötigt HTTPS und eine erteilte Berechtigung.");return;}
      const s=this.makeSession(wake,"stt");s.follow=follow;
      this.state(wake?"Wakeword startet":"Mikrofon startet","Warte auf Audiofreigabe");this.report("capture|"+(wake?"wake":"stt"));
      s.timeout=setTimeout(()=>this.fail(s,"Audio-Zeitüberschreitung"),wake?80000:30000);
      try{
        const AC=window.AudioContext||window.webkitAudioContext;
        if(!AC)throw Error("AudioContext fehlt");
        audioSession("play-and-record");s.ctx=new AC();
        const resumed=s.ctx.resume();resumed.catch(()=>{});
        s.stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:{ideal:1},echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
        if(!this.alive(s)){s.stream.getTracks().forEach(t=>t.stop());return;}
        await resumed;if(!this.alive(s))return;
        s.source=s.ctx.createMediaStreamSource(s.stream);s.zero=s.ctx.createGain();s.zero.gain.value=0;
        const pcm=new PCM16(s.ctx.sampleRate,frame=>this.frame(s,frame));
        // AudioWorklet preferred; fallback for older Android WebViews.
        if(s.ctx.audioWorklet && typeof AudioWorkletNode!=="undefined"){
          const url=URL.createObjectURL(new Blob(["class JRecorder extends AudioWorkletProcessor {process(inputs){const c=inputs[0]?.[0];if(c)this.port.postMessage(new Float32Array(c));return true;}} registerProcessor('jarvis-recorder-v2',JRecorder);"],{type:"application/javascript"}));
          try{await s.ctx.audioWorklet.addModule(url);if(!this.alive(s))return;s.node=new AudioWorkletNode(s.ctx,"jarvis-recorder-v2");s.node.port.onmessage=e=>{if(this.alive(s)&&!s.ended)pcm.push(e.data);};s.recorder="worklet";}catch{if(!this.alive(s))return;}finally{URL.revokeObjectURL(url);}
        }
        if(!s.node){s.node=s.ctx.createScriptProcessor(2048,1,1);s.node.onaudioprocess=e=>{if(this.alive(s)&&!s.ended)pcm.push(e.inputBuffer.getChannelData(0));};s.recorder="legacy";}
        if(!this.alive(s))return;
        // Wait for server channel before forwarding audio.
        s.zero.connect(s.ctx.destination);s.source.connect(s.node);s.node.connect(s.zero);
        await this.subscribe(s,{pipeline:wake?(this.cfg.wake_pipeline_id||this.cfg.pipeline_id):this.cfg.pipeline_id,start_stage:wake?"wake_word":"stt",end_stage:"stt",input:wake?{sample_rate:16000,timeout:60,audio_seconds_to_buffer:0,no_vad:true}:{sample_rate:16000,no_vad:true}});
      }catch(e){if(this.alive(s))this.fail(s,e?.name==="NotAllowedError"?"Mikrofon nicht freigegeben. Android-/WebView-Berechtigung prüfen.":fmt(e?.message||e));}
    }
    async subscribe(s,opts){
      if(!this._roomStatus)await this.refreshRoom();
      if(!this._roomStatus)throw Error(this._roomError||(de(this.h)?"Raumkonto nicht eingerichtet":"Room account not provisioned"));
      await this.roomRpc({action:"activity",busy:true});
      const conn=this.h?.connection;
      if(!conn?.socket||conn.socket.readyState!==1)throw Error("Home Assistant nicht verbunden");
      s.socket=conn.socket;
      const unsub=await conn.subscribeMessage(e=>{if(this.alive(s))this.event(s,e);},{type:"assist_pipeline/run",...opts,...(this._roomStatus?.device_id?{device_id:this._roomStatus.device_id}:{})},false);
      if(!this.alive(s)){try{await unsub();}catch{}return;}
      s.unsub=unsub;
    }
    frame(s,pcm){
      if(!this.alive(s)||s.ended||!Number.isInteger(s.handler)||!["wake","listen"].includes(s.stage))return;
      let sq=0,peak=0;for(const v of pcm){const a=Math.abs(v)/32768;sq+=a*a;peak=Math.max(peak,a);}
      const rms=Math.sqrt(sq/pcm.length);s.frames++;s.peak=Math.max(s.peak,peak);
      let endpoint=null;
      if(s.stage==="listen"){s.peakRms=Math.max(s.peakRms,rms);s.endpoint??=new Endpointer(s.wake,this.pref);endpoint=s.endpoint.step(rms);s.speechMs=s.endpoint.voiced*20;
        if(endpoint.empty){this.finishSilent(s);return;}
      }
      if(s.frames%10===0){this.level=Math.min(100,Math.round(rms*550));this.update();}
      try{
        if(s.socket.readyState!==1||s.socket.bufferedAmount>512000)throw Error("Audio-Verbindung überlastet");
        const b=new Uint8Array(1+pcm.length*2);b[0]=s.handler;const dv=new DataView(b.buffer);for(let i=0;i<pcm.length;i++)dv.setInt16(1+i*2,endpoint?.gate?0:pcm[i],true);s.socket.send(b);
        if(endpoint?.end){this.report("endpoint|speech_ms="+s.speechMs+"|silence_ms="+(s.endpoint.silent*20));this.endMic(s,true);this.state("Verarbeitet","Whisper · Mikrofon aus");}
      }catch(e){this.fail(s,fmt(e.message||e));}
    }
    endMic(s,signal=false){
      if(!s||s.ended)return;s.ended=true;clearTimeout(s.recordTimer);
      if(signal&&Number.isInteger(s.handler)&&s.socket?.readyState===1){try{s.socket.send(Uint8Array.of(s.handler));}catch{}}
      s.stream?.getTracks().forEach(t=>t.stop());
      if(s.node?.port)s.node.port.onmessage=null;if(s.node&&"onaudioprocess" in s.node)s.node.onaudioprocess=null;
      try{s.source?.disconnect();s.node?.disconnect();s.zero?.disconnect();}catch{}
      if(s.ctx&&s.ctx.state!=="closed")s.closePromise=s.ctx.close().catch(()=>{});
      this.level=0;
    }
    event(s,event){
      const d=event.data||{};
      try{
        switch(event.type){
          case "run-start":s.handler=d.runner_data?.stt_binary_handler_id??null;break;
          case "wake_word-start":s.stage="wake";this.state("Warte auf Wakeword","Mikrofon aktiv · local wakeword");break;
          case "wake_word-end":s.wakeDetected=true;s.stage="listen";s.speechMs=0;s.peakRms=0;s.endpoint=new Endpointer(true,this.pref);this.beginDialog();this.state("Wakeword erkannt","Jetzt sprechen · kurze Pause vor der Frage");break;
          case "stt-start":s.stage="listen";s.endpoint??=new Endpointer(s.wake,this.pref);this.state("Hört zu","Sprich jetzt · Mikrofon aktiv");clearTimeout(s.timeout);s.timeout=setTimeout(()=>this.fail(s,"Spracherkennung-Zeitüberschreitung"),30000);s.recordTimer=setTimeout(()=>{if(this.alive(s)){if(s.speechMs<240){this.finishSilent(s);return;}this.endMic(s,true);this.state("Verarbeitet","Whisper · Mikrofon aus");}},22000);break;
          case "stt-vad-end":this.report("server-vad|unexpected");break;
          case "stt-end":{
            this.endMic(s,false);s.text=fmt(d.stt_output?.text).trim();
            this.report("stt|"+s.recorder+"|"+(s.ctx?.sampleRate||0)+"Hz|speech_ms="+s.speechMs+"|rms="+s.peakRms.toFixed(4)+"|chars="+s.text.length);
            break;
          }
          case "intent-start":this.state("Verarbeitet","Jarvis · Mikrofon aus");break;
          case "intent-end":s.question??=s.text;s.reply=fmt(d.intent_output?.response?.speech?.plain?.speech).trim();s.keep=!!d.intent_output?.continue_conversation;this.dialogId=d.intent_output?.conversation_id||null;this.lastReply=s.reply;this.state("Antwort","");break;
          case "tts-start":this.state("Sprachausgabe","Piper/Qwen · Mikrofon aus");break;
          case "tts-end":s.tts=d.tts_output?.url;break;
          case "run-end":if(s.runEnded)break;s.runEnded=true;if(s.kind==="stt")this.afterSTT(s);else this.afterReply(s);break;
          case "error":{
            const code=fmt(d.code);
            if(s.kind==="stt"&&(s.wake||s.follow||this.continuous)&&/wake.?word.?timeout|stt.?no.?text|no.?speech|stt.?stream.?failed/i.test(code)){this.finishSilent(s);return;}
            this.fail(s,fmt(d.message||code||"Pipeline-Fehler"));break;
          }
        }
      }catch(e){this.fail(s,fmt(e.message||e));}
    }
    async afterSTT(s){
      this.endMic(s,false);const text=s.text?.trim()||"";
      const normalized=text.toLocaleLowerCase(this.h?.language||"en").replace(/[.!?,]/g,"").trim();
      const noCommand=!text||s.speechMs<240||/^(untertitel(ung)? (des |von )?(zdf|ard)|untertitel der amara)/.test(normalized)||((s.wake||s.follow)&&s.speechMs<650&&/^(danke( schön)?|gern(e)? geschehen|vielen dank|okay|ok|hallo)$/.test(normalized));
      if(noCommand){this.finishSilent(s);return;}
      if(/^(mikrofon aus|microphone off|stopp?|gespräch beenden|end conversation|danke das reicht|danke das war alles)$/.test(normalized)){this.finish(s);if(normalized==="mikrofon aus"||normalized==="microphone off"||/^stopp?$/.test(normalized)){this.stop("Mikrofon aus");return;}this.endDialog();this.state("Bereit","Gespräch beendet");if(this.wake||this.continuous)this.rearm(800);return;}
      if(this.turnsLeft>0)this.turnsLeft--;
      const close=s.closePromise;const follow=s.follow;const generation=this.generation;this.finish(s);this.processing=true;
      this.state("Verarbeitet","");
      // Let Android release microphone routing before requesting TTS.
      if(close)await close;if(this.output==="bluetooth"){audioSession("playback");await wait(1200);}else if(this.output==="alexa"){audioSession("playback");await wait(1200);}else audioSession("auto");
      if(generation!==this.generation||!this.card.isConnected||!visible()||this.mode!=="dashboard"||this.session||this.phase!==tr(this.h,"Verarbeitet")){if(generation===this.generation){this.processing=false;this.update();}return;}
      this.processing=false;await this.intent(text,follow);
    }
    async intent(text,follow){
      if(this.session||!visible()||this.mode!=="dashboard")return;
      this.closeInfo();const s=this.makeSession(false,"intent");s.question=text;s.timeout=setTimeout(()=>this.fail(s,"Antwort-Zeitüberschreitung"),45000);
      try{if(!this.alive(s))return;await this.subscribe(s,{pipeline:this.cfg.pipeline_id,start_stage:"intent",end_stage:this.output==="alexa"?"intent":"tts",input:{text},...(follow&&this.dialogId?{conversation_id:this.dialogId}:{})});}catch(e){if(this.alive(s))this.fail(s,fmt(e.message||e));}
    }
    async afterReply(s){
      this.rememberTurn(s);this.showCaption(s.question,s.reply);const url=s.tts,keep=s.keep,reply=s.reply;this.info?.cameraView?.setReply(reply);this.finish(s);
      if(!reply){this.fail(null,"Keine Antwort erhalten");return;}
      if(this.output==="alexa"){this.follow=this.shouldFollow(s);await this.playAlexa(reply,this.follow);return;}
      if(!url){this.playError("Keine Audioantwort erhalten");return;}
      let target;try{target=new URL(url,location.href);if(target.origin!==location.origin)throw Error("Fremde Audio-Adresse abgelehnt");}catch(e){this.fail(null,fmt(e.message));return;}
      this.lastAudio=target.href;this.follow=this.shouldFollow(s);if(this.output==="native_audio"){await this.playNativeAudio(this.lastAudio,this.follow);return;}await this.play(this.lastAudio,this.follow);
    }
    finishPlayback(keep){
      this.playing=false;this.scheduleInfo(true);this.scheduleCaption();clearTimeout(this.playbackTimer);this.audio.onended=null;this.audio.onerror=null;
      this.report("tts|finished|"+(this._playbackRoute||this.output));
      if(keep){this.follow=false;this.state("Anschlussfrage","Sprich nach der Antwort weiter · Mikrofon öffnet sich gleich");this.rearm(1200,true);}
      else{this.endDialog();this.state("Bereit",this.continuous?"Dauerbetrieb · nächste Aufnahme":this.wake?"Rufwort · nächste Aufnahme":"Mikrofon aus");if(this.wake||this.continuous)this.rearm(1600);}
    }
    async playAlexa(reply,keep=false){
      if(!visible()||this.mode!=="dashboard"||!this.card.isConnected)return;
      const speaker=this.cfg.alexa_notify,room=speaker;
      if(!speaker||!this.h?.states?.[speaker]||this.h.states[speaker].state==="unavailable"){this.playError("Alexa-Ziel nicht verfügbar. Lautsprecher in Jarvis auswählen.");return;}
      const text=reply.trim().slice(0,500);
      if(!text){this.playError("Antwort fehlt");return;}
      this._playbackRoute="alexa";this.playing=true;const gen=this.generation;this.state("Spricht · Alexa",room);this.lastReply=text;
      try{
        await this.h.callService("script",this.cfg.alexa_script,{text,lautsprecher:speaker});
        if(gen!==this.generation)return;
        this.report("tts|alexa|sent");
        // Alexa notify acknowledges submission, not end of playback. Conservative estimated pause.
        const duration=Math.min(65000,Math.max(6500,Math.ceil(text.length/8)*1000+3500));
        this.playbackTimer=setTimeout(()=>{if(gen===this.generation)this.finishPlayback(keep);},duration);
      }catch(e){if(gen===this.generation)this.playError("Alexa-Ausgabe fehlgeschlagen · "+fmt(e.message||e));}
    }
    async play(url,keep=false){
      if(!visible()||this.mode!=="dashboard"||!this.card.isConnected)return;
      audioSession("playback");this._playbackRoute="bluetooth";this.playing=true;const generation=this.generation;this.state("Spricht · Tablet","Sprachausgabe");
      this.audio.pause();this.audio.src=url;this.audio.load();
      this.audio.onended=()=>this.finishPlayback(keep);
      this.audio.onerror=()=>this.playError("Audiodatei konnte nicht abgespielt werden.");
      clearTimeout(this.playbackTimer);this.playbackTimer=setTimeout(()=>{this.audio.pause();this.playError("Wiedergabe-Zeitüberschreitung");},90000);
      try{await this.audio.play();if(generation===this.generation){this.unlocked=true;this.report("tts|started");}}catch(e){if(generation===this.generation)this.playError("Android hat die automatische Wiedergabe blockiert. Tippe auf ▶.");}
    }
    playError(msg){this.playing=false;this.scheduleInfo(true);this.scheduleCaption();clearTimeout(this.playbackTimer);this.audio.onended=null;this.audio.onerror=null;this.wake=false;this.continuous=false;this.endDialog();this.state("Audio prüfen",msg);this.report("tts|blocked|"+fmt(msg).slice(0,185));}
    finish(s){if(!s)return;if(this.session===s)this.session=null;clearTimeout(s.timeout);this.endMic(s,false);if(s.unsub)Promise.resolve().then(()=>s.unsub()).catch(()=>{});}
    rearm(ms,follow=false){clearTimeout(this.retryTimer);if(!visible()||this.mode!=="dashboard"||(!this.wake&&!this.continuous&&!follow))return;
      this.retryTimer=setTimeout(()=>{this.retryTimer=null;if(!this.session&&visible()&&this.mode==="dashboard"&&(this.wake||this.continuous||follow)){if(this.continuous&&!follow)this.beginDialog();this.capture(!follow&&this.wake&&!this.continuous,follow);}},ms);this.update();}
    closeInfo(){this.info?.cameraView?.dispose();this.info=null;}
    scheduleInfo(ended=false){this.info?.cameraView?.schedule(ended);}
    stop(reason="Mikrofon aus"){this.generation++;this.closeInfo();this.cancelNativeAudio();this.playing=false;this.processing=false;this.wake=false;this.continuous=false;this.endDialog();clearTimeout(this.retryTimer);this.retryTimer=null;clearTimeout(this.playbackTimer);if(this.session)this.finish(this.session);this.audio.onended=null;this.audio.onerror=null;this.audio.pause();audioSession("auto");this.level=0;this.state("Bereit",reason);this.report("idle");}
    fail(s,message){if(s&&this.session!==s)return;this.stop();this.state("Prüfen",message);this.report("error|"+message);}
    destroy(){clearInterval(this._roomStatusTimer);this.clearCaption();this.stop();document.removeEventListener("visibilitychange",this.onHidden);window.removeEventListener("pagehide",this.onPageHide);}
    mount(){
      const shadow=this.card.shadowRoot,actions=shadow?.querySelector(".relay-actions");if(!actions)return;
      let b=actions.querySelector("[data-jarvis-mic]");
      if(!b){b=element("button");b.type="button";b.className="relay-mic";b.dataset.jarvisMic="1";b.style.position="relative";
        const icon=element("ha-icon");icon.dataset.role="mic-icon";
        const mark=element("span",null,"position:absolute;right:-3px;bottom:-3px;width:17px;height:17px;border-radius:50%;display:grid;place-items:center;pointer-events:none;box-shadow:0 0 0 2px var(--card-background-color);");mark.dataset.role="activity-icon";
        const small=element("ha-icon");small.style.setProperty("--mdc-icon-size","12px");small.style.color="#13232e";mark.append(small);b.append(icon,mark);
        b.onclick=e=>{e.stopPropagation();this.cycle();};actions.append(b);}
      this.micButton=b;
      const details=shadow.querySelector("details");let root=details.querySelector("[data-jarvis-integrated]");
      if(!root){root=this.buildSettings();details.append(root);}this.ui=root;
      this.update();
    }
    buildSettings(){
      const root=element("section",null,"display:grid;gap:12px;box-sizing:border-box;width:100%;margin:0 0 16px;padding:16px;border:1px solid var(--hz-line,var(--divider-color,#456));border-radius:14px;background:var(--hz-surface,var(--card-background-color,#192526));color:inherit;");
      root.dataset.jarvisIntegrated="1";
      root.append(element("strong",tr(this.h,"Jarvis · Assistent und Audio"),"font-size:16px;"));
      root.append(element("span",tr(this.h,"Mikrofon oben rechts: Rufwort → Dauerbetrieb → Aus. Nur bei sichtbarem Dashboard aktiv. Informiere Anwesende."),"font-size:12px;opacity:.75;"));
      const btn=(role,label,fn)=>{const b=element("button",tr(this.h,label),"font:inherit;font-size:13px;min-height:40px;border:1px solid var(--divider-color,#456);border-radius:10px;padding:8px 12px;background:var(--secondary-background-color,#26364a);color:inherit;cursor:pointer;touch-action:manipulation;");b.type="button";b.dataset.role=role;b.onclick=e=>{e.stopPropagation();fn(b);};return b;};
      const group=(name,choices,kind)=>{root.append(element("strong",tr(this.h,name),"font-size:13px;"));const row=element("div",null,"display:flex;flex-wrap:wrap;gap:8px;");for(const [value,label] of choices){
        const b=btn("choice-"+kind+"-"+value,label,()=>{
          if(this.busy)return;
          if(kind==="mode")this.setMode(value);
          else if(value==="alexa"&&this.output!=="alexa"){this._jarvisMenu="alexa-confirm";this.update();}
          else this.setOutput(value);
        });b.dataset.kind=kind;b.dataset.choice=value;row.append(b);
      }root.append(row);};
      group("Assistent",[["dashboard","Dashboard Assist"]],"mode");
      group("Audioausgabe",[["native_audio","Echo Relay · empfohlen"]],"output");
      const confirm=element("div",null,"display:none;gap:8px;flex-wrap:wrap;align-items:center;");confirm.dataset.role="confirm";
      confirm.append(element("span",tr(this.h,"Alexa direkt nutzt einen zeitlich begrenzt öffentlichen Audio-Link. Nur für nicht vertrauliche Antworten."),"font-size:12px;width:100%;"),btn("approve","Alexa direkt aktivieren",()=>{this._jarvisMenu=null;this.setOutput("alexa",true);this.update();}),btn("cancel","Abbrechen",()=>{this._jarvisMenu=null;this.update();}));root.append(confirm);
      const row=element("div",null,"display:flex;gap:8px;flex-wrap:wrap;align-items:center;");
      row.append(btn("native","Android-Assistent öffnen",b=>{this.stop();native(b,this);}),btn("test","Einmal sprechen",b=>{if(this.busy)return;if(this.mode!=="dashboard")this.setMode("dashboard");this.tap(b);}),btn("replay","Antwort wiederholen",()=>{if(this.busy)return;if(this.output==="alexa"&&this.lastReply)this.playAlexa(this.lastReply,false);else if(this.output==="native_audio"&&this.lastAudio)this.playNativeAudio(this.lastAudio,false);else if(this.lastAudio)this.play(this.lastAudio,false);}),btn("tabletReplay","Tablet-Reserve",()=>{if(!this.busy&&this.lastAudio)this.play(this.lastAudio,false);}));
      row.querySelector("[data-role=native]").hidden=true;row.querySelector("[data-role=tabletReplay]").hidden=true;
      root.append(row);
      const status=element("span","Bereit","font-size:13px;overflow-wrap:anywhere;");status.dataset.role="status";status.setAttribute("role","status");root.append(status);
      const relay=element("span","","font-size:12px;opacity:.8;");relay.dataset.role="relay";root.append(relay);const captions=element("label",null,"display:flex;gap:8px;align-items:center;");const toggle=element("input");toggle.type="checkbox";toggle.checked=this.pref.captions;toggle.onchange=()=>this.setPref("captions",toggle.checked);captions.append(toggle,document.createTextNode(de(this.h)?"Untertitel":"Captions"));root.append(captions);
      const follow=element("label",null,"display:flex;gap:8px;align-items:center;");const select=element("select");for(const [v,l] of [["auto",de(this.h)?"Automatisch":"Automatic"],["smart",de(this.h)?"Bei Rückfrage":"On follow-up"],["server",de(this.h)?"Nur Server":"Server only"]]){const option=element("option",l);option.value=v;select.append(option);}select.value=this.pref.followMode;select.onchange=()=>this.setPref("followMode",select.value);follow.append(document.createTextNode(de(this.h)?"Anschlussfragen":"Follow-up"),select);root.append(follow);
      return root;
    }
    loadPreferences(){
      let stored={};try{stored=JSON.parse(get(this.cfg,"preferences","{}"));}catch{}
      const p={...preferenceDefaults,infoSeconds:Math.max(15,Math.min(90,Number(this.cfg.camera_info_seconds)||30))};
      for(const key of ["captions","history","autoFallback"])if(typeof stored?.[key]==="boolean")p[key]=stored[key];
      for(const [key,min,max] of [["pause",1000,3200],["sensitivity",75,150],["turns",1,8],["dialogSeconds",30,180],["infoSeconds",15,90],["captionSeconds",5,30]])if(Number.isFinite(stored?.[key]))p[key]=Math.round(Math.max(min,Math.min(max,stored[key])));
      if(["auto","smart","server"].includes(stored?.followMode))p.followMode=stored.followMode;return p;
    }
    setPref(key,value){this.pref={...this.pref,[key]:value};save(this.cfg,"preferences",JSON.stringify(this.pref));if(key==="history"&&!value){this.history=[];this.historySeq++;}if(key==="captions"&&!value)this.clearCaption();this.renderHistory();this.update();}
    resetPreferences(){if(this.busy)return;save(this.cfg,"preferences","{}");this.pref=this.loadPreferences();this.history=[];this.historySeq++;this.clearCaption();this.ui?.remove();this.ui=null;this.mount();}
    rememberTurn(s){if(!this.pref.history||!s?.reply)return;this.history.unshift({q:fmt(s.question).slice(0,300),a:fmt(s.reply).slice(0,1200)});this.history=this.history.slice(0,15);this.historySeq++;this.renderHistory();}
    renderHistory(){const root=this.ui?.querySelector("[data-jv-history]");if(!root)return;root.hidden=!this.pref.history;const items=root.querySelector("[data-jv-history-items]");if(!this.pref.history){items.replaceChildren();return;}if(items.dataset.seq===String(this.historySeq))return;items.dataset.seq=String(this.historySeq);items.replaceChildren();if(!this.history.length)items.append(element("p",de(this.h)?"Noch keine Fragen in dieser Sitzung.":"No questions in this session."));for(const item of this.history){const row=element("div",null,"display:grid;gap:6px;padding:12px 0;overflow-wrap:anywhere;");row.append(element("strong",item.q),element("p",item.a,"white-space:pre-wrap;"));items.append(row);}}
    showCaption(q,a){if(!this.pref.captions||!a)return;this.clearCaption();const box=element("section",null,"margin:12px 0;padding:12px;border:1px solid var(--divider-color);border-radius:10px;font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere;");box.dataset.jvCaptions="1";box.setAttribute("aria-live","polite");if(q)box.append(element("strong",fmt(q).slice(0,400)));box.append(element("p",fmt(a).slice(0,1000)));this.card.shadowRoot.querySelector("header").after(box);this.caption=box;this.captionTimer=setTimeout(()=>this.clearCaption(),150000);}
    scheduleCaption(){if(!this.caption)return;clearTimeout(this.captionTimer);this.captionTimer=setTimeout(()=>this.clearCaption(),this.pref.captionSeconds*1000);}
    clearCaption(){clearTimeout(this.captionTimer);this.caption?.remove();this.caption=null;}
    activity(){
      const s=this.session, l=(a,b)=>de(this.h)?a:b;
      if([tr(this.h,"Prüfen"),tr(this.h,"Audio prüfen")].includes(this.phase))return ["error",l("Fehler","Error"),"mdi:alert-circle-outline","#fb923c"];
      if(this.playing)return /^(Spricht|Speaking)/.test(this.phase)?["playing",l("Spricht","Speaking"),"mdi:volume-high","#38bdf8"]:["buffer",l("Lädt","Buffering"),"mdi:progress-clock","#fbbf24"];
      if(this.processing||s?.kind==="intent"||s?.ended)return ["processing",l("Verarbeitet","Processing"),"mdi:dots-horizontal","#fbbf24"];
      if(s?.stage==="listen"){
        if(s.endpoint?.started)return ["speech",l("Stimme erkannt","Speech detected"),"mdi:waveform","#4ade80"];
        if(s.wakeDetected)return ["wake",l("Rufwort erkannt","Wake word detected"),"mdi:check-bold","#4ade80"];
        return ["listen",l("Hört zu","Listening"),"mdi:waveform","#60a5fa"];
      }
      if(this.wake)return ["waiting",l("Rufwort","Wake word"),"mdi:ear-hearing","#36bb9a"];
      if(this.continuous||s)return ["listen",l("Hört zu","Listening"),"mdi:waveform","#60a5fa"];
      return ["off",l("Aus","Off"),"mdi:microphone-off","#94a3b8"];
    }
    update(){
      this.info?.cameraView?.update();
      const b=this.micButton, active=this.continuous?"continuous":this.wake?"wake":"off";
      if(b?.isConnected){
        b.querySelector("[data-role=mic-icon]")?.setAttribute("icon",active==="off"?"mdi:microphone-off":active==="wake"?"mdi:microphone-outline":"mdi:microphone");
        b.style.color=active==="continuous"?"#60a5fa":active==="wake"?"#36bb9a":"";
        b.style.boxShadow=active==="off"?"":"inset 0 0 0 1px currentColor";
        const label=active==="off"?"Mikrofon aus · Rufwort aktivieren":active==="wake"?"Rufwort aktiv · Dauerbetrieb aktivieren":"Dauerbetrieb aktiv · ausschalten";
        const [activity,description,icon,color]=this.activity();const mark=b.querySelector("[data-role=activity-icon]");if(b.dataset.activity!==activity){b.dataset.activity=activity;mark.style.display=activity==="off"?"none":"grid";mark.style.background=color;mark.querySelector("ha-icon").setAttribute("icon",icon);}b.title=tr(this.h,label)+" · "+description;b.setAttribute("aria-label",tr(this.h,label)+" · "+description);b.setAttribute("data-mic-mode",active);
      }
      const summary=this.card.shadowRoot?.querySelector(".relay-state");if(summary){const [,label]=this.activity();if(summary.textContent!==label)summary.textContent=label;summary.setAttribute("aria-live","polite");}const u=this.ui;if(!u?.isConnected)return;const q=r=>u.querySelector('[data-role="'+r+'"]');
      const running=this.busy,ready=this.nativeAudioReady();
      for(const b of u.querySelectorAll("[data-choice]")){
        const kind=b.dataset.kind,v=b.dataset.choice,selected=(kind==="mode"?this.mode:this.output)===v;
        b.disabled=running;b.setAttribute("aria-pressed",String(selected));b.style.borderColor=selected?"#36bb9a":"var(--divider-color,#456)";b.style.background=selected?"rgba(54,187,154,.18)":"var(--secondary-background-color,#26364a)";
      }
      q("confirm").style.display=this._jarvisMenu==="alexa-confirm"&&!running?"flex":"none";
      q("native").disabled=running;q("test").disabled=running;
      q("replay").disabled=running||this.mode!=="dashboard"||!(this.output==="alexa"?this.lastReply:this.lastAudio);
      q("tabletReplay").disabled=running||this.mode!=="dashboard"||!this.lastAudio;
      q("status").textContent=this.phase+(this.detail?" · "+this.detail:"");q("relay").textContent=(this._roomStatus?.room?this._roomStatus.room+" · ":"")+"Echo Relay · "+(ready?(de(this.h)?"verbunden":"connected"):this._roomError?this._roomError+" · "+(this.h?.user?.name||""):this._roomStatus?.online?(de(this.h)?"Player verbunden, aber beschäftigt/nicht bereit":"Player connected, busy/not ready"):(de(this.h)?"Player offline oder Status noch nicht geladen":"Player offline or status not yet loaded"));
      q("relay").style.color=ready?"var(--hz-active,var(--success-color,#167867))":"var(--hz-heat,var(--warning-color,#9a6700))";
    }
  }

  class EchoRelayAssistCard extends HTMLElement{
    constructor(){super();this.attachShadow({mode:"open"});}
    setConfig(c){
      if(!c||typeof c!=="object")throw Error("Configuration required");
      const cfg={command_entity:"input_text.jarvis_native_audio_command",relay_status_entity:"input_text.jarvis_native_audio_status",...c,room_audio:true,output:"native_audio",alexa_script:null,alexa_notify:null,native_notify_service:null,status_entity:null};
      for(const k of ["command_entity","relay_status_entity","status_entity"])if(cfg[k]&&!/^input_text\.[a-z0-9_]+$/.test(cfg[k]))throw Error("Invalid "+k);
      if(cfg.command_entity===cfg.relay_status_entity)throw Error("Command and status helpers must differ");
      if(cfg.alexa_script&&!/^[a-z0-9_]+$/.test(cfg.alexa_script))throw Error("alexa_script must be a script service name without script.");
      if(cfg.alexa_script&&!/^notify\.[a-z0-9_]+$/.test(cfg.alexa_notify||""))throw Error("Configure alexa_notify with alexa_script");
      if(cfg.native_notify_service&&!/^mobile_app_[a-z0-9_]+$/.test(cfg.native_notify_service))throw Error("Invalid native_notify_service");
      if(cfg.output&&!["native_audio","bluetooth","alexa"].includes(cfg.output))throw Error("Invalid output");
      if(this.voice){this.voice.destroy();this.voice=null;}
      this.voiceConfig=cfg;this.shadowRoot.replaceChildren();this.ensure();
    }
    set hass(h){this.h=h;this.ensure();}
    connectedCallback(){this.ensure();}
    disconnectedCallback(){this.voice?.destroy();this.voice=null;this.shadowRoot.replaceChildren();}
    getCardSize(){return 2;}
    ensure(){
      if(!this.isConnected||!this.h||!this.voiceConfig)return;
      if(!this.voice){
        this.shadowRoot.innerHTML='<style>:host{display:block;color:var(--primary-text-color)}ha-card{padding:14px}header{display:flex;align-items:center;justify-content:space-between;gap:12px}header strong{display:block;font-size:16px}.relay-state{font-size:12px;color:var(--secondary-text-color)}.relay-actions{display:flex;gap:8px}.relay-mic{display:grid;place-items:center;width:44px;height:44px;border:1px solid var(--divider-color);border-radius:12px;background:var(--secondary-background-color);color:var(--primary-text-color);cursor:pointer}.relay-mic ha-icon{--mdc-icon-size:24px}details{margin-top:12px}summary{cursor:pointer;font-size:13px;color:var(--secondary-text-color);padding:8px 0}</style><ha-card><header><div><strong></strong><span class="relay-state"></span></div><div class="relay-actions"></div></header><details><summary></summary></details></ha-card>';
        this.shadowRoot.querySelector("header strong").textContent=this.voiceConfig.title||"Echo Relay";
        this.shadowRoot.querySelector("summary").textContent=de(this.h)?"Assistent und Audio · Einstellungen":"Assistant and audio · settings";
        this.voice=new Voice(this);
      }
      this.voice.mount();
    }
  }
  if(!customElements.get("jarvis-room-assist-card"))customElements.define("jarvis-room-assist-card",EchoRelayAssistCard);
  window.customCards=window.customCards||[];
  if(!window.customCards.some(c=>c.type==="jarvis-room-assist-card"))window.customCards.push({type:"jarvis-room-assist-card",name:"Jarvis Room Assist",description:"Experimental authenticated room-scoped audio relay."});
})();
