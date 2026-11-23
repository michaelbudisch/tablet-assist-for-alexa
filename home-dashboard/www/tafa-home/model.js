// TAFA Home Dashboard — portable configuration and data model (MIT).
function createModel(){
 const role=(key,en,de,domains,kind="state",multiple=true,terms=[])=>({key,en,de,domains,kind,multiple,terms});
 const modules=[
 {id:"lights",en:"Lights & rooms",de:"Licht & Räume",icon:"mdi:lightbulb-group-outline",roles:[role("lights","Lights","Leuchten",["light"]),role("room_temperature","Room temperatures","Raumtemperaturen",["sensor"],"temperature")]},
 {id:"energy",en:"Energy & solar",de:"Energie & Solar",icon:"mdi:solar-power",roles:[role("grid_power","Grid power","Netzleistung",["sensor"],"power",false,["grid","netz","power meter"]),role("home_power","Household consumption","Hausverbrauch",["sensor"],"power",false,["consumption","verbrauch","load"]),role("solar_power","PV production power","PV-Erzeugungsleistung",["sensor"],"power",true,["solar","pv","photovoltaik"]),role("solar_today","PV energy today","PV-Ertrag heute",["sensor"],"energy",true,["today","heute","daily","tages"]),role("grid_import","Grid import energy","Netzbezug Energie",["sensor"],"energy",false,["import","bezug"]),role("grid_export","Grid export energy","Netzeinspeisung Energie",["sensor"],"energy",false,["export","einspeis"]),role("price","Electricity tariff","Stromtarif",["sensor"],"rate",false,["price","preis","tariff"])]},
 {id:"battery",en:"Battery storage",de:"Batteriespeicher",icon:"mdi:battery-high",roles:[role("battery_level","State of charge","Ladezustand",["sensor"],"percent",true,["battery","batterie","soc","storage"]),role("battery_charge","Charging power","Ladeleistung",["sensor"],"power",true,["charg","lad"]),role("battery_discharge","Discharging power","Entladeleistung",["sensor"],"power",true,["discharg","entlad"])]},
 {id:"ev",en:"EV charging",de:"E-Auto & Wallbox",icon:"mdi:ev-station",roles:[role("charger_power","Charging power","Ladeleistung",["sensor"],"power",true,["wallbox","charger","ev"]),role("charger_energy","Session energy","Energie je Ladevorgang",["sensor"],"energy",true,["session","ladung","sitzung"]),role("charger_status","Charging status","Ladestatus",["sensor","binary_sensor"],"state",true,["charger","wallbox","charging","lade"])]},
 {id:"heating",en:"Heating",de:"Heizung",icon:"mdi:radiator",roles:[role("climate","Climate devices","Klimageräte",["climate"]),role("heating_temperature","Heating temperatures","Heizungstemperaturen",["sensor"],"temperature",true,["heating","heizung","vorlauf","rücklauf"]),role("heating_status","Heating status","Heizungsstatus",["sensor","binary_sensor"],"state",true,["heating","heizung","brenner"])]},
 {id:"heatpump",en:"Heat pump",de:"Wärmepumpe",icon:"mdi:heat-pump-outline",roles:[role("heatpump_power","Power","Leistung",["sensor"],"power",true,["heatpump","heat pump","wärmepumpe","warmepumpe"]),role("heatpump_temperature","Tank & water temperatures","Speicher- & Wassertemperaturen",["sensor"],"temperature",true,["water","wasser","speicher","tank"]),role("heatpump_status","Operating state","Betriebszustand",["sensor","binary_sensor","water_heater"],"state",true,["heatpump","wärmepumpe","warmepumpe"])]},
 {id:"fuel",en:"Fuel & tank monitoring",de:"Heizöl & Tank",icon:"mdi:gauge",roles:[role("fuel_percent","Tank fill level","Tankfüllstand",["sensor"],"percent",true,["fuel","oil","heizöl","heizol","tank"]),role("fuel_volume","Stored volume","Vorrat",["sensor"],"volume",true,["fuel","oil","heizöl","heizol","tank"]),role("fuel_usage","Reported fuel use","Gemeldeter Verbrauch",["sensor"],"volume",true,["usage","verbrauch"])]},
 {id:"appliances",en:"Appliances",de:"Haushaltsgeräte",icon:"mdi:washing-machine",roles:[role("appliance_power","Appliance power","Geräteleistung",["sensor"],"power",true,["washer","dryer","dishwasher","wasch","spül","spul","trockner"]),role("appliance_status","Appliance status","Gerätestatus",["sensor","binary_sensor"],"state",true,["washer","dryer","dishwasher","wasch","spül","spul","trockner"]),role("appliance_progress","Progress","Fortschritt",["sensor"],"percent",true,["progress","fortschritt"])]},
 {id:"cameras",en:"Cameras",de:"Kameras",icon:"mdi:cctv",roles:[role("cameras","Selected cameras","Ausgewählte Kameras",["camera"])]},
 {id:"waste",en:"Waste collection",de:"Abfallkalender",icon:"mdi:trash-can-outline",roles:[role("waste_dates","Collection date sensors","Abholtermine",["sensor"],"state",true,["waste","abfall","müll","muell","collection"]),role("waste_calendars","Calendars","Kalender",["calendar"])]},
 {id:"shopping",en:"Shopping",de:"Einkauf",icon:"mdi:cart-outline",roles:[role("shopping_lists","To-do lists","Einkaufslisten",["todo"])]},
 {id:"weather",en:"Weather",de:"Wetter",icon:"mdi:weather-partly-cloudy",roles:[role("weather","Weather sources","Wetterdienste",["weather"])]},
 {id:"assist",en:"Voice assistant",de:"Sprachassistent",icon:"mdi:microphone-outline",roles:[]},
 {id:"custom",en:"Custom tiles",de:"Eigene Kacheln",icon:"mdi:view-grid-plus-outline",roles:[role("custom","Selected read-only tiles","Ausgewählte Anzeigekacheln",["sensor","binary_sensor","light","switch","climate","weather","media_player","calendar","todo","number","select","input_boolean","input_number","input_text"])]}
 ];
 const byId=new Map(modules.map(m=>[m.id,m])),roles=modules.flatMap(m=>m.roles),byRole=new Map(roles.map(r=>[r.key,r]));
 const ENTITY=/^[a-z][a-z0-9_]*\.[a-z0-9_]+$/;
 const units={power:{"W":1,"kW":1000,"MW":1e6,"mW":.001},energy:{"Wh":.001,"kWh":1,"MWh":1000},percent:{"%":1},volume:{"L":1,"l":1,"m³":1000},temperature:{"°C":1,"°F":1,"K":1}};
 const eligible=(r,id,s)=>{if(!r||!ENTITY.test(id)||!r.domains.includes(id.split(".")[0]))return false;if(!s)return false;const u=s.attributes?.unit_of_measurement||"";if(r.kind==="rate")return /^(?:[A-Z]{3}|€|ct|¢)\/(?:kWh|MWh)$/i.test(u);return r.kind==="state"||Object.hasOwn(units[r.kind]||{},u);};
 function normalize(raw={}){
  raw=raw&&typeof raw==="object"?raw:{};
  const enabled=[...new Set(Array.isArray(raw.modules)?raw.modules.filter(x=>typeof x==="string"&&byId.has(x)):[])];
  const out={type:"custom:tafa-home-dashboard",version:1,modules:enabled,bindings:{},language:["auto","en","de"].includes(raw.language)?raw.language:"auto",theme:["dark","light","ha"].includes(raw.theme)?raw.theme:"dark",density:["comfortable","compact"].includes(raw.density)?raw.density:"comfortable",accent:["teal","blue","violet"].includes(raw.accent)?raw.accent:"teal",assist:{},title:typeof raw.title==="string"?raw.title.trim().slice(0,60):""};
  for(const r of roles){const b=raw.bindings&&typeof raw.bindings==="object"&&Object.hasOwn(raw.bindings,r.key)?raw.bindings[r.key]:[];out.bindings[r.key]=[...new Set((Array.isArray(b)?b:typeof b==="string"?[b]:[]).filter(x=>typeof x==="string"&&ENTITY.test(x)&&r.domains.includes(x.split(".")[0])))].slice(0,r.multiple?100:1);}
  for(const k of ["pipeline_id","wake_pipeline_id"])if(typeof raw.assist?.[k]==="string"&&/^[A-Za-z0-9_-]{1,100}$/.test(raw.assist[k]))out.assist[k]=raw.assist[k];
  return out;
 }
 const language=(cfg,hass)=>cfg.language==="auto"?(String(hass?.locale?.language||hass?.language||"en").toLowerCase().startsWith("de")?"de":"en"):cfg.language;
 const name=(s,id)=>String(s?.attributes?.friendly_name||id);
 const label=(x,lang)=>x[lang]||x.en;
 function candidates(r,states={}){
  return Object.entries(states).filter(([id,s])=>eligible(r,id,s)).map(([id,s])=>{const n=name(s,id),t=(id+" "+n).toLowerCase();return {id,name:n,score:r.terms.filter(k=>t.includes(k)).length};}).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name)||a.id.localeCompare(b.id));
 }
 function value(states,id){const s=states?.[id];return s&&typeof s.state==="string"&&!["unavailable","unknown",""].includes(s.state)?s:null;}
 function sum(states,ids,kind){const factors=units[kind];if(!factors)return null;const unique=[...new Set(ids)];if(!unique.length)return null;let result=0;for(const id of unique){const s=value(states,id),unit=s?.attributes?.unit_of_measurement;if(!s||!Object.hasOwn(factors,unit)||!Number.isFinite(Number(s.state)))return null;const n=Number(s.state)*factors[unit];if(n<0)return null;result+=n;}return Number.isFinite(result)?result:null;}
 function area(hass,id){const reg=hass?.entities?.[id],device=reg?.device_id?hass?.devices?.[reg.device_id]:null,aid=reg?.area_id||device?.area_id;return aid?String(hass?.areas?.[aid]?.name||""):"";}
 const escape=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
 return {modules,roles,byId,byRole,normalize,eligible,candidates,value,sum,area,escape,label,name,language};
}
export const model = createModel();
