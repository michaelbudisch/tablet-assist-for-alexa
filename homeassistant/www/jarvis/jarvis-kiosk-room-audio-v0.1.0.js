/* Room-scoped transport; no private configuration. */
const fmt=x=>String(x??"");
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const visible=()=>!document.hidden;
const de=h=>String(h?.language||"de").startsWith("de");
const methods={
nativeAudioReady(){return this._roomStatus?.ready===true&&Date.now()-(this._roomStatusAt||0)<7000;},
    roomRpc(data){return this.h.callApi("POST","jarvis_echo_relay/room_audio",data);},
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
    },
    cancelNativeAudio(){
      const id=this._nativeRequest;this._nativeRequest=null;
      if(id)void this.roomRpc({action:"cancel",id}).catch(()=>{});
    },
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
};
export function attachRoomAudio(voice){
 if(voice._roomAttached)return;
 const subscribe=voice.subscribe.bind(voice),destroy=voice.destroy.bind(voice);
 Object.assign(voice,methods);
 voice._roomAttached=true;voice.mode="dashboard";voice.output="native_audio";
 voice._roomStatus=null;voice._roomStatusTimer=setInterval(()=>void voice.refreshRoom(),3000);
 voice.subscribe=async function(s,opts){
  if(!this._roomStatus)await this.refreshRoom();
  if(!this._roomStatus)throw Error(this._roomError||"Raumkonto nicht eingerichtet");
  await this.roomRpc({action:"activity",busy:true});
  if(!this.alive(s))return;
  return subscribe(s,{...opts,...(this._roomStatus.device_id?{device_id:this._roomStatus.device_id}:{})});
 };
 voice.destroy=function(){clearInterval(this._roomStatusTimer);return destroy();};
 void voice.refreshRoom();
}
