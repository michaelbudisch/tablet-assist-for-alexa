"""Two-room synthetic camera HTTP and entity lifecycle checks."""
import asyncio
import io
from PIL import Image
from homeassistant.core import Context
from homeassistant.components import camera
from homeassistant.exceptions import ServiceValidationError
from custom_components.jarvis_tablet_audio.relay_room_camera import hub
from custom_components.jarvis_tablet_audio.relay_vision import resolve_camera
from custom_components.jarvis_tablet_audio.relay_camera import runtime

async def check_room_camera(hass, client, base, admin, guest, guest_bearer, jpeg, check):
    second = await hass.auth.async_create_user("Room camera fixture", group_ids=["system-users"])
    token = hass.auth.async_create_access_token(await hass.auth.async_create_refresh_token(second, client_id="https://room-camera.invalid"))
    async def service(data):
        return await hass.services.async_call("jarvis_tablet_audio","room_audio",data,blocking=True,return_response=True,context=Context(user_id=admin.id))
    async def register(bearer,device,expected):
        async with client.post(base+"/room_camera/register",json={"device_id":device},headers={"Authorization":"Bearer "+bearer}) as response:
            check(response.status==expected,"room camera pairing HTTP "+str(expected))
            return (await response.json())["session"] if expected==200 else None
    async def frame(bearer,device,session,jpg,motion,interval,expected):
        headers={"Authorization":"Bearer "+bearer,"Content-Type":"image/jpeg","X-Relay-Device":device,"X-Relay-Session":session,"X-Relay-Sequence":"1","X-Relay-Captured-At":"1795390000000","X-Relay-Motion":motion,"X-Relay-Interval":str(interval)}
        async with client.post(base+"/room_camera/frame",data=jpg,headers=headers) as response:
            check(response.status==expected,"room camera upload HTTP "+str(expected))
    await service({"action":"provision","room":"fixture_cam_a","user_id":guest.id})
    await service({"action":"provision","room":"fixture_cam_b","user_id":second.id,"camera_enabled":True})
    try:
        a,b="a"*32,"b"*32
        await register(guest_bearer,a,403)
        await service({"action":"configure","room":"fixture_cam_a","camera_enabled":True})
        sa,sb=await register(guest_bearer,a,200),await register(token,b,200)
        await register(guest_bearer,b,409)
        await frame(token,a,sa,jpeg,"1",2,409)
        second_image=io.BytesIO();Image.new("RGB",(320,240),"blue").save(second_image,"JPEG")
        await frame(guest_bearer,a,sa,jpeg,"1",1,204)
        await frame(token,b,sb,second_image.getvalue(),"0",10,204)
        current=hub(hass)
        async with asyncio.timeout(15):
            while not all(current.entity_id(r,k) and hass.states.get(current.entity_id(r,k)) for r in ("fixture_cam_a","fixture_cam_b") for k in ("camera","motion")):
                await asyncio.sleep(.1)
        await hass.async_block_till_done()
        ca,cb=(current.entity_id(r,"camera") for r in ("fixture_cam_a","fixture_cam_b"))
        ma,mb=(current.entity_id(r,"motion") for r in ("fixture_cam_a","fixture_cam_b"))
        check(ca!=cb and ma!=mb,"independent room entities")
        check(hass.states.is_state(ma,"on") and hass.states.is_state(mb,"off"),"independent room motion")
        check((await camera.async_get_image(hass,ca)).content != (await camera.async_get_image(hass,cb)).content,"independent room camera images")
        check(await resolve_camera(runtime(hass),"tablet",Context(user_id=guest.id))==ca,"room A vision mapping")
        check(await resolve_camera(runtime(hass),"tablet",Context(user_id=second.id))==cb,"room B vision mapping")
        await service({"action":"configure","room":"fixture_cam_a","camera_enabled":False})
        check(not current.store.fresh("fixture_cam_a") and current.store.fresh("fixture_cam_b"),"disable clears only chosen room")
        try:
            await resolve_camera(runtime(hass),"tablet",Context(user_id=guest.id))
        except ServiceValidationError:
            check(True,"disabled room cannot fall back to legacy camera")
        else:
            raise AssertionError("disabled room fell back")
        await frame(guest_bearer,a,sa,jpeg,"1",1,403)
    finally:
        await service({"action":"revoke","room":"fixture_cam_a"})
        await service({"action":"revoke","room":"fixture_cam_b"})
