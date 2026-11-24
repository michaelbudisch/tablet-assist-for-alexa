"""Isolated synthetic proactive checks; no microphone, speakers or real images."""
from types import SimpleNamespace
from unittest.mock import patch
from homeassistant.core import Context, SupportsResponse
from homeassistant.exceptions import Unauthorized, ServiceValidationError
from homeassistant.util import dt as dt_util


async def check_proactive(hass, relay, jpeg, device, nonce, admin, guest, worker_state, check):
    from custom_components.jarvis_tablet_audio.relay_proactive import DEFAULTS, validate_settings, validate_detection, EVENT, DETECTION_EVENT
    p = relay.proactive
    async def call(data, user=admin):
        return await hass.services.async_call('jarvis_tablet_audio','proactive',data,blocking=True,return_response=True,
            context=Context(user_id=user.id) if user else Context())
    async def save(**updates):
        current=await call({'action':'get'})
        values={key:current[key] for key in DEFAULTS}
        return await call({'action':'set','revision':current['revision'],'settings':{**values,**updates}})
    def fresh():
        relay.frames.put(device,nonce,relay.frames.sequence+1,jpeg,1795390000000,True)
        p.last_attempt=None
    try:
        await call({'action':'get'},guest)
    except Unauthorized:
        check(True,'proactive settings require administrator')
    else:raise AssertionError('Guest can edit proactive settings')
    check((await call({'action':'check'}))['status']=='disabled','proactive defaults off')
    for values in ({**DEFAULTS,'name':'<script>'},{**DEFAULTS,'classes':['unsupported_class']},{**DEFAULTS,'cooldown':True},{**DEFAULTS,'script_entity':'light.fixture'}):
        try:validate_settings(values)
        except ServiceValidationError:pass
        else:raise AssertionError('Invalid proactive settings accepted')
    check(validate_detection({'person_count':1,'dog_count':0,'age_groups':['adult'],'uncertain':True})==[], 'uncertain detection cannot trigger')
    await save(enabled=True,test_mode=True,greeting=False)
    check(relay is hass.data['jarvis_tablet_audio']['relay_camera'],'proactive settings preserve camera runtime')
    events=[]
    unsub=hass.bus.async_listen(DETECTION_EVENT,lambda event:events.append(event.data))
    prompts=[]
    unsub2=hass.bus.async_listen(EVENT,lambda event:prompts.append(event.data))
    try:
        fresh();result=await call({'action':'check'})
        check(result['status']=='detected' and result['labels']==['person','adult'],'validated detector fires configured categories')
        await hass.async_block_till_done()
        check(len(events)==1 and not prompts,'event-only checks do not speak')
        check((await call({'action':'check'}))['status']=='cooldown','motion spam is throttled')
        await p.mark_action();fresh()
        check((await call({'action':'check'}))['status']=='detected','test mode repeats even after daily action')
        await save(test_mode=False,start='00:00',end='00:00');fresh()
        check((await call({'action':'check'}))['status']=='already_today','normal mode blocks second daily action')
        await save(test_mode=True,greeting=True);fresh()
        check((await call({'action':'check'}))['status']=='no_idle_dashboard','no unattended greeting inference')
        await call({'action':'heartbeat','client_id':'fixture-client','busy':True},guest);fresh()
        check((await call({'action':'check'}))['status']=='no_idle_dashboard','active speech prevents proactive inference')
        await call({'action':'heartbeat','client_id':'fixture-client','busy':False},guest)
        fresh();worker_state['busy']=True
        check((await call({'action':'check'}))['status']=='busy','worker busy skipped without queue')
        worker_state['busy']=False;worker_state['uncertain']=True;fresh()
        check((await call({'action':'check'}))['status']=='uncertain','uncertain worker output does not act')
        worker_state['uncertain']=False
        hass.states.async_set('weather.proactive_fixture','cloudy',{'supported_features':2})
        async def forecast(call):
            return {'weather.proactive_fixture':{'forecast':[{'datetime':dt_util.utcnow().isoformat(),'condition':'rainy'}]}}
        hass.services.async_register('weather','get_forecasts',forecast,supports_response=SupportsResponse.ONLY)
        await save(name='Fixture',weather_entity='weather.proactive_fixture');fresh()
        check((await call({'action':'check'}))['status']=='detected','greeting candidate produced')
        await hass.async_block_till_done()
        check(len(prompts)==1 and set(prompts[0])=={'request_id','camera_entity_id'},'broadcast contains no speech or identity data')
        message=p.pending['message']
        check('Fixture' in message and 'Regenschirm' in message and 'Tagesüberblick' in message,'fixed greeting uses actual forecast and offers overview')
        stream=SimpleNamespace(url='/api/tts_proxy/fixture',async_set_message=lambda message:None)
        with patch('homeassistant.components.tts.async_create_stream',return_value=stream):
            claim=await call({'action':'claim','client_id':'fixture-client','request_id':p.pending['id']},guest)
            check(claim['accepted'] and claim['audio_path']==stream.url,'authorized client claims native stream')
            await call({'action':'heartbeat','client_id':'other-client','busy':False},guest)
            second=await call({'action':'claim','client_id':'other-client','request_id':p.pending['id']},guest)
            check(not second['accepted'],'multiple dashboards cannot double speak')
            ack=await call({'action':'ack','client_id':'fixture-client','request_id':p.pending['id'],'started':True},guest)
            check(ack['accepted'] and p.greeted_date==dt_util.now().date().isoformat(),'confirmed playback records daily guard')
        worker_state['offline']=True;fresh()
        check((await call({'action':'check'}))['status']=='worker_unavailable','offline worker does not wake or act')
        worker_state['offline']=False
        await save(enabled=False);fresh()
        check((await call({'action':'check'}))['status']=='disabled','master switch stops new checks')
    finally:
        unsub();unsub2();await save(enabled=False)
