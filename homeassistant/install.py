"""Render a new portable HA install, never edit existing configuration.yaml or secrets."""
import argparse, json, re, shutil, ast
from pathlib import Path
from urllib.parse import urlparse
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
cfg=json.loads(a.config.read_text(encoding='utf-8'))

def host(k):
    v=cfg.get(k,'')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,252}',v):raise SystemExit('Invalid host: '+k)
    return v

def entity(v,domain=None):
    if not isinstance(v,str) or not re.fullmatch(r'[a-z0-9_]+\.[a-z0-9_]+',v) or domain and not v.startswith(domain+'.'):raise SystemExit('Invalid entity ID: '+str(v))
    return v

pipeline=cfg.get('pipeline_id','')
if not re.fullmatch(r'[A-Za-z0-9_-]{0,80}',pipeline):raise SystemExit('Invalid pipeline ID')
url=cfg.get('audio_public_base','https://audio.example.invalid').rstrip('/')
if not re.fullmatch(r'https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?',url):raise SystemExit('HTTPS base without path required')
repl={'__JARVIS_CPU_HOST__':host('cpu_host'),'__JARVIS_GPU_HOST__':host('gpu_host'),'__JARVIS_CPU_STT__':entity(cfg['cpu_stt'],'stt'),'__JARVIS_GPU_STT__':entity(cfg['gpu_stt'],'stt'),'__JARVIS_LLM_AGENT__':entity(cfg['llm_agent'],'conversation'),'__JARVIS_PIPELINE_ID__':pipeline,'https://audio.example.invalid':url}
for slug,room in cfg.get('rooms',{}).items():
    if slug not in ('buero','wohnzimmer','badezimmer','schlafzimmer','kinderzimmer'):raise SystemExit('Unknown room key')
    for field,original,domain in [('media_player',f'media_player.jarvis_{slug}','media_player'),('notify',f'notify.jarvis_{slug}_sprechen','notify'),('dnd',f'switch.jarvis_{slug}_bitte_nicht_storen','switch')]:
        repl[original]=entity(room[field],domain)
# Explicit DND map, as the installed panel formerly inferred switch IDs from player IDs.
dnd={repl.get('media_player.jarvis_'+s,'media_player.jarvis_'+s):repl.get('switch.jarvis_'+s+'_bitte_nicht_storen','switch.jarvis_'+s+'_bitte_nicht_storen') for s in ['buero','wohnzimmer','badezimmer','schlafzimmer','kinderzimmer']}

def render(s):
    for k,v in sorted(repl.items(),key=lambda kv:-len(kv[0])):s=s.replace(k,v)
    if '__JARVIS_' in s:raise SystemExit('Unresolved placeholder')
    return s

if not (HERE/'templates/package.json').is_file():raise SystemExit('Missing bundled HA template. Clone the full repository.')
if a.output.exists() and any(a.output.iterdir()):raise SystemExit('Output must be empty; install into a staging directory first.')
a.output.mkdir(parents=True,exist_ok=True)
for root in ['custom_components','www']:
    for f in (HERE/root).rglob('*'):
        if not f.is_file() or f.suffix not in ('.py','.json','.js','.yaml'):continue
        out=a.output/f.relative_to(HERE);out.parent.mkdir(parents=True,exist_ok=True)
        txt=render(f.read_text(encoding='utf-8'))
        if f.name=='const.py' and f.parent.name=='jarvis_tablet_audio':txt=txt.replace(':10501',':10502')
        if f.name=='jarvis-dashboard-assist-v1.4.0.js':txt=txt.replace('pipeline_id:pipeline,start_listening:true','...(pipeline?{pipeline_id:pipeline}:{}),start_listening:true')
        if f.name=='jarvis-control-panel-v1.5.js':txt=txt.replace('class J extends HTMLElement {','class J extends HTMLElement {\nsetConfig(config){this._config=config||{};}\ngetCardSize(){return 6;}\ngetGridOptions(){return {columns:12,rows:"auto"};}').replace('entities[name].replace("media_player.","switch.")+"_bitte_nicht_storen"',f'({json.dumps(dnd,ensure_ascii=False)})[entities[name]]')
        if f.name=='jarvis-control-panel-v1.6.0.js':txt=txt.replace('entities[name].replace("media_player.","switch.")+"_bitte_nicht_storen"',f'({json.dumps(dnd,ensure_ascii=False)})[entities[name]]')
        if f.suffix=='.py':ast.parse(txt)
        out.write_text(txt,encoding='utf-8')
pack=json.loads(render((HERE/'templates/package.json').read_text(encoding='utf-8')))
# Restore persistent rule settings, initialize only unset helpers on first boot.
init=[]
for key,helper in pack.get('input_text',{}).items():
    default=helper.pop('initial',None)
    if default is not None:init.append({'if':[{'condition':'template','value_template':"{{ states('input_text."+key+"') in ['unknown','unavailable',''] }}"}],'then':[{'action':'input_text.set_value','target':{'entity_id':'input_text.'+key},'data':{'value':default}}]})
init.append({'if':[{'condition':'template','value_template':"{{ states('input_text.jarvis_stt_zusatzrechner') in ['unknown','unavailable',''] }}"}],'then':[{'action':'input_text.set_value','target':{'entity_id':'input_text.jarvis_stt_zusatzrechner'},'data':{'value':cfg['gpu_stt']}}]})
pack['automation'].append({'id':'jarvis_initialize_defaults','alias':'Jarvis initialize unset settings','triggers':[{'trigger':'homeassistant','event':'start'}],'actions':init,'mode':'single'})
allowed_event={'sensor.jarvis_example_dishwasher_status','sensor.jarvis_example_grid_power','sensor.jarvis_example_wallbox_status','input_text.jarvis_example_washer_status','sensor.jarvis_example_waste_bio','sensor.jarvis_example_waste_paper','sensor.jarvis_example_waste_residual','sensor.jarvis_example_waste_recycling','weather.jarvis_example_home'}
for k,v in cfg.get('event_sources',{}).items():
    if k not in allowed_event:raise SystemExit('Unknown event-source placeholder '+k)
    repl[k]=entity(v,k.split('.')[0])
for rule in json.loads(render((HERE/'templates/event-automations.json').read_text(encoding='utf-8'))):
    if 'jarvis_example_' in json.dumps(rule):continue
    pack['automation'].append(rule)
# YAML accepts JSON flow syntax. Keep !secret as native YAML outside these values.
output='\n'.join(f'{k}: '+json.dumps(v,ensure_ascii=False) for k,v in pack.items())+'\n'+render((HERE/'templates/rest-command.yaml').read_text(encoding='utf-8'))
(a.output/'packages').mkdir();(a.output/'packages/jarvis.yaml').write_text(output,encoding='utf-8')
(a.output/'jarvis-dashboard.yaml').write_text('title: Jarvis\nviews:\n  - title: Jarvis\n    path: main\n    type: sections\n    max_columns: 1\n    sections:\n      - type: grid\n        cards:\n          - type: custom:echo-relay-assist-card\n            title: HA Jarvis Echo Relay\n'+('            pipeline_id: '+pipeline+'\n' if pipeline else '')+'          - type: custom:jarvis-control-panel\n',encoding='utf-8')
print('Prepared',a.output,'Review and copy only new files to HA /config. See docs/home-assistant.md.')
