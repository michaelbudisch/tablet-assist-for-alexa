/* TAFA shared visual response layer. No browser microphone. */
const HEAT=["vorlauf","ruecklauf","spreizung"], ENERGY=["netz","solar","preis","netzheute","solarheute"], HEATPUMP=["waermepumpe","wpheute","wpkosten"];
const LABELS={vorlauf:"Vorlauf",ruecklauf:"Rücklauf",spreizung:"Spreizung",preis:"Strompreis",guenstig:"Günstigster Tarif",netz:"Netzleistung",solar:"PV-Leistung",prognose:"PV-Prognose",solarheute:"PV heute",netzheute:"Netzbezug heute",einspeisungheute:"Einspeisung heute",waermepumpe:"Wärmepumpe",wpheute:"Wärmepumpe heute",wpkosten:"Wärmepumpenkosten",heizoel:"Heizöl",oelverbrauch:"Heizölverbrauch",waschmaschine:"Waschmaschine",waschenergie:"Waschverbrauch",waschkosten:"Waschkosten",kuehlschrank:"Kühlschrank",kuehlschrankheute:"Kühlschrank heute",weather:"Wetter",shopping:"Einkaufsliste"};
const TITLES={vorlauf:"Heizung",ruecklauf:"Heizung",spreizung:"Heizung",netz:"Energie",solar:"Energie",preis:"Strompreis",waermepumpe:"Wärmepumpe",shopping:"Einkaufsliste",weather:"Wetter",search:"Internetsuche",knowledge:"Wissen"};
const DEFAULT={captions:true,houseCards:true,knowledge:true,knowledgeMedia:false,contextNav:true,returnTarget:"previous",returnSeconds:20,infoSeconds:30,search:true};
function el(tag,text,klass){const n=document.createElement(tag);if(klass)n.className=klass;if(text!==undefined&&text!==null)n.textContent=String(text);return n;}
function validLink(raw){try{const u=new URL(raw);if(u.protocol!=="https:"||u.username||u.password)return null;return u.href;}catch{return null;}}
function numberText(st){if(!st||["unknown","unavailable","none",""].includes(String(st.state)))return null;const n=Number(st.state);const v=Number.isFinite(n)?new Intl.NumberFormat("de-DE",{maximumFractionDigits:2}).format(n):String(st.state);return v+(st.attributes?.unit_of_measurement?" "+st.attributes.unit_of_measurement:"");}
function publicSubject(question){
  const q=String(question||"").trim().replace(/^(?:hey\s+)?(?:jarvis|tafa)[,:\s]+/i,"");
  if(/\b(?:mein|meine|meiner|unsere|unser|zuhause|adresse|telefon|passwort|konto|kind|familie)\b/i.test(q))return "";
  const m=/^(?:wer|was)\s+(?:ist|war|sind)\s+(?:(?:ein|eine|der|die|das)\s+)?(.{3,75}?)[?.!]?$/i.exec(q);
  return m?m[1].trim().replace(/[?.!]+$/,""):"";
}
export class TafaResponseOverlay extends HTMLElement {
  constructor(){
    super();this.attachShadow({mode:"open"});this.settings={...DEFAULT};this._hass=null;this._unsubscribe=null;this._generation=0;this._timer=null;this._last=null;this._options={};this._searchBusy=false;
  }
  connectedCallback(){this.subscribe();}
  disconnectedCallback(){this._unsubscribe?.();this._unsubscribe=null;clearTimeout(this._timer);}
  set hass(value){this._hass=value;this.subscribe();if(this._last)this.updateValues();}
  get hass(){return this._hass;}
  set options(value){this._options=value||{};this.settings={...DEFAULT,...(value?.presentation||value?.settings||{})};}
  subscribe(){
    if(this._unsubscribe||!this.isConnected||!this._hass?.connection?.subscribeEvents)return;
    this._hass.connection.subscribeEvents(ev=>this.receive(ev?.data||ev),"tafa_assist_response")
      .then(unsubscribe=>{if(this.isConnected)this._unsubscribe=unsubscribe;else unsubscribe();})
      .catch(()=>{this._unsubscribe=null;});
  }
  receive(data){
    if(!data||typeof data!=="object")return;
    const wanted=data.user_id,owner=this._hass?.user?.id;
    if(wanted&&owner&&wanted!==owner)return;
    if(!String(data.reply||"").trim())return;
    const topic=String(data.topic||"knowledge");
    const metric=(data.sources&&Object.hasOwn(data.sources,topic))||["vorlauf","ruecklauf","spreizung"].includes(topic);
    this._last={...data,topic:metric?topic:topic};
    this.show();
    if(this.settings.contextNav&&metric&&typeof this._options.onNavigate==="function"){
      try{this._options.onNavigate(topic);}catch{}
    }
    if(this.settings.knowledgeMedia&&topic==="knowledge")void this.wiki(data.question);
  }
  show(){this._generation++;this.render();clearTimeout(this._timer);const ms=Number(this.settings.infoSeconds)||30;this._timer=setTimeout(()=>this.close(),Math.max(15,Math.min(180,ms))*1000);}
  close(){this._last=null;this._generation++;clearTimeout(this._timer);this.shadowRoot.replaceChildren();}
  setLive(hass){this._hass=hass;if(this._last)this.updateValues();}
  updateValues(){
    const d=this._last;if(!d||!this._hass)return;
    for(const item of this.shadowRoot.querySelectorAll("[data-source]")){
      const id=d.sources?.[item.dataset.source]||this.sourceFromBindings(item.dataset.source);
      const val=numberText(this._hass.states?.[id]);item.textContent=val||"Keine Daten";
    }
  }
  sourceFromBindings(key){
    const b=this._options.bindings||{};
    const role={vorlauf:"heating_temperature",ruecklauf:"heating_temperature",spreizung:"heating_temperature",preis:"price",netz:"grid_power",solar:"solar_power",waermepumpe:"heatpump_power",heizoel:"fuel_volume",waschmaschine:"appliance_power",shopping:"shopping_lists"}[key];
    const rows=b[role]||[];return Array.isArray(rows)?rows[key==="ruecklauf"?1:key==="spreizung"?2:0]:null;
  }
  presentationCategory(topic){return TITLES[topic]||LABELS[topic]||"TAFA Antwort";}
  metrics(topic){
    const group=HEAT.includes(topic)?HEAT:ENERGY.includes(topic)?ENERGY:HEATPUMP.includes(topic)?HEATPUMP:[topic];
    const sources=this._last?.sources||{};
    return group.filter(k=>sources[k]||this.sourceFromBindings(k)).slice(0,6);
  }
  async wiki(question){
    const subject=publicSubject(question);if(!subject)return;
    const stamp=this._generation;
    try{
      const u=new URL("https://de.wikipedia.org/w/api.php");
      u.search=new URLSearchParams({action:"query",format:"json",formatversion:"2",origin:"*",prop:"extracts|pageimages|info|pageprops",inprop:"url",exintro:"1",explaintext:"1",exchars:"550",piprop:"thumbnail",pithumbsize:"420",titles:subject,redirects:"1"}).toString();
      const response=await fetch(u.href,{credentials:"omit",referrerPolicy:"no-referrer"});
      if(!response.ok)return;
      const json=await response.json();const p=json?.query?.pages?.[0];
      if(stamp!==this._generation||p?.missing||p?.pageprops?.disambiguation!==undefined||!p?.extract)return;
      this._last.wiki={title:String(p.title).slice(0,100),extract:String(p.extract).slice(0,550),url:validLink(p.fullurl),image:validLink(p.thumbnail?.source)};
      this.render();
    }catch{}
  }
  async search(query){
    if(!this._hass?.callWS||this._searchBusy)return;
    const term=String(query||"").trim().slice(0,160);
    if(!term)return;
    this._searchBusy=true;this._last={question:term,reply:"Suche läuft …",topic:"search",sources:{}};this.show();
    try{
      const results=await this._hass.callWS({type:"tablet_assist_for_alexa/search",query:term});
      this._last={question:term,reply:results?.message||"Suchergebnisse",topic:"search",results:results?.results||[],sources:{}};
      this.show();
    }catch{this._last={question:term,reply:"Internetsuche nicht eingerichtet oder momentan nicht erreichbar. SearXNG ist eine optionale Erweiterung.",topic:"search",sources:{}};this.show();}
    finally{this._searchBusy=false;}
  }
  render(){
    const data=this._last;if(!data||!this.isConnected)return;
    const root=this.shadowRoot;root.replaceChildren();
    const css=el("style");css.textContent=":host{position:fixed;inset:0;z-index:10020;display:grid;place-items:center;padding:16px;box-sizing:border-box;pointer-events:none;color:#edf7fa;font:14px/1.45 Inter,Roboto,Arial,sans-serif}.veil{position:absolute;inset:0;background:#020a14a6;pointer-events:auto}.dialog{position:relative;z-index:1;width:min(650px,100%);max-height:min(85vh,790px);overflow:auto;pointer-events:auto;background:#142031;border:1px solid #36566c;border-radius:18px;padding:22px;box-shadow:0 20px 70px #000b}.head{display:flex;align-items:center;justify-content:space-between;gap:12px}.pill{font-size:11px;letter-spacing:.09em;color:#66dfcf;font-weight:750}.title{font-size:22px;font-weight:700;margin:6px 0 12px}.reply{font-size:15px;line-height:1.5;white-space:pre-wrap}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:9px;margin-top:16px}.metric{background:#1c3145;border:1px solid #36566c;border-radius:12px;padding:13px}.metric small{color:#b5cbd7;display:block}.metric strong{font-size:19px;display:block;margin-top:4px}.actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:18px}.actions button,.actions a,form button{border:1px solid #3a786e;background:#23584f;color:#f0fffc;border-radius:10px;padding:9px 12px;font:inherit;text-decoration:none;cursor:pointer}.muted{color:#a8c2cc;font-size:12px;margin-top:14px}.result{padding:12px 0;border-bottom:1px solid #2e495a}.result a{color:#8debdc;font-weight:700;overflow-wrap:anywhere}.result p{margin:5px 0;font-size:12px;color:#b5cbd7}.wiki{display:flex;gap:14px;margin-top:15px}.wiki img{max-width:36%;max-height:185px;object-fit:contain;border-radius:10px}.search{display:flex;gap:8px;margin-top:12px}.search input{flex:1;min-width:0;padding:10px;background:#101a28;color:#fff;border:1px solid #527381;border-radius:9px}@media(max-width:540px){.dialog{padding:15px}.wiki{display:block}.wiki img{max-width:100%;max-height:155px}}";
    const veil=el("div",null,"veil");veil.onclick=()=>this.close();root.append(css,veil);
    const dialog=el("section",null,"dialog");dialog.setAttribute("role","dialog");dialog.setAttribute("aria-label","TAFA Antwort");const head=el("div",null,"head");head.append(el("span","TAFA · "+(this.metrics(data.topic).length?"LIVE · HOME ASSISTANT":data.topic==="search"?"INTERNET":"WISSEN"),"pill"));
    const close=el("button","✕");close.type="button";close.title="Schließen";close.onclick=()=>this.close();head.append(close);dialog.append(head,el("h2",this.presentationCategory(data.topic),"title"));
    if(this.settings.captions)dialog.append(el("p",data.question,"muted"));
    dialog.append(el("div",data.reply,"reply"));
    if(this.settings.houseCards){
      const metrics=this.metrics(data.topic);if(metrics.length){const grid=el("div",null,"metrics");for(const key of metrics){const item=el("div",null,"metric");item.append(el("small",LABELS[key]||key));const strong=el("strong","Keine Daten");strong.dataset.source=key;item.append(strong);grid.append(item);}dialog.append(grid);}
    }
    if(data.topic==="search"&&Array.isArray(data.results)){
      const results=el("div");for(const entry of data.results.slice(0,10)){const url=validLink(entry.url);if(!url)continue;const item=el("div",null,"result");const a=el("a",String(entry.title||url).slice(0,170));a.href=url;a.rel="noopener noreferrer";a.target="_blank";item.append(a);if(entry.snippet)item.append(el("p",String(entry.snippet).slice(0,300)));results.append(item);}dialog.append(results);
    }
    if(data.wiki&&this.settings.knowledge){const card=el("section",null,"wiki");if(data.wiki.image){const img=el("img");img.src=data.wiki.image;img.alt=data.wiki.title;card.append(img);}const p=el("div");p.append(el("strong",data.wiki.title),el("p",data.wiki.extract,"muted"));if(data.wiki.url){const a=el("a","Wikipedia-Artikel");a.href=data.wiki.url;a.target="_blank";a.rel="noopener noreferrer";p.append(a);}card.append(p);dialog.append(card);}
    const actions=el("div",null,"actions");
    if(this.metrics(data.topic).length&&typeof this._options.onNavigate==="function"){const b=el("button","Passende Hausansicht öffnen");b.onclick=()=>{this._options.onNavigate(data.topic);this.close();};actions.append(b);}
    if(data.topic==="search"&&this.settings.search){const form=el("form",null,"search");const input=el("input");input.type="search";input.placeholder="Im Internet suchen";input.maxLength=160;const btn=el("button","Suchen");form.append(input,btn);form.onsubmit=e=>{e.preventDefault();void this.search(input.value)};dialog.append(form);}
    const more=el("button","Länger anzeigen");more.onclick=()=>{clearTimeout(this._timer);this._timer=setTimeout(()=>this.close(),60000);};actions.append(more);
    dialog.append(actions,el("p","Datenquelle: Home Assistant. Inhalte aus externen Quellen können Fehler enthalten.","muted"));root.append(dialog);this.updateValues();
  }
}
if(!customElements.get("tafa-response-overlay"))customElements.define("tafa-response-overlay",TafaResponseOverlay);
export function installTafaResponseOverlay(host,hass,options={}){
  if(!document.body)return null;
  let overlay=document.querySelector("tafa-response-overlay");
  if(!overlay){overlay=document.createElement("tafa-response-overlay");document.body.append(overlay);}
  overlay.options=options;overlay.hass=hass;
  return overlay;
}
