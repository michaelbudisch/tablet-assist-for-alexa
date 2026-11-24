"""Real authenticated HA room API test with synthetic audio paths only."""
from types import SimpleNamespace
from unittest.mock import patch
from homeassistant.core import Context
from homeassistant.exceptions import Unauthorized

async def check_room_audio(hass, client, base, admin, guest, guest_bearer, check):
    second = await hass.auth.async_create_user("Second room fixture", group_ids=["system-users"])
    token = hass.auth.async_create_access_token(await hass.auth.async_create_refresh_token(second, client_id="https://room-fixture.invalid"))
    async def service(data, actor=admin):
        return await hass.services.async_call("jarvis_tablet_audio", "room_audio", data, blocking=True, return_response=True, context=Context(user_id=actor.id))
    async def rpc(data, bearer=guest_bearer, expected=200):
        headers = {"Authorization": "Bearer " + bearer} if bearer else {}
        async with client.post(base + "/room_audio", json=data, headers=headers) as response:
            check(response.status == expected, "room API " + data["action"] + " expected HTTP " + str(expected))
            return await response.json() if expected == 200 else {}
    try:
        await service({"action": "list"}, guest)
    except Unauthorized:
        check(True, "room management requires admin")
    else:
        raise AssertionError("guest could list all rooms")
    await rpc({"action": "status"}, None, 401)
    await rpc({"action": "connect"}, guest_bearer, 403)
    await service({"action": "provision", "room": "fixture_a", "user_id": guest.id})
    await service({"action": "provision", "room": "fixture_b", "user_id": second.id})
    try:
        a = (await rpc({"action": "connect"}))["session"]
        b = (await rpc({"action": "connect"}, token))["session"]
        await rpc({"action": "connect"}, guest_bearer, 409)
        await rpc({"action": "poll", "session": a, "ready": True}, token, 403)
        await rpc({"action": "poll", "session": a, "ready": True})
        await rpc({"action": "poll", "session": b, "ready": True}, token)
        path = "/api/tts_proxy/room-fixture.mp3"
        job = (await rpc({"action": "submit", "path": path}))["id"]
        check(job and (await rpc({"action": "poll", "session": b, "ready": True}, token)) == {}, "other room never receives private reply")
        check((await rpc({"action": "status", "id": job}, token))["stage"] == "unknown", "other room cannot inspect reply status")
        check((await rpc({"action": "poll", "session": a, "ready": True})) == {"id": job, "path": path}, "origin room receives path exactly once")
        await rpc({"action": "report", "session": a, "id": job, "stage": "playing"})
        check((await rpc({"action": "status", "id": job}))["stage"] == "playing", "playback acknowledgement")
        await rpc({"action": "report", "session": a, "id": job, "stage": "done"})
        await rpc({"action": "poll", "session": a, "ready": True})
        with patch("custom_components.jarvis_tablet_audio.relay_room_adapter.async_create_stream", return_value=SimpleNamespace(url=path, async_set_message=lambda message: None)):
            await rpc({"action": "activity", "busy": True})
            result = await service({"action": "announce", "rooms": ["fixture_a", "fixture_b"], "message": "Synthetic room test"})
            check(result["results"]["fixture_a"]["status"] == "not_ready" and result["results"]["fixture_b"]["accepted"], "explicit multiroom announcement avoids busy room")
            await rpc({"action": "activity", "busy": False})
        await rpc({"action": "disconnect", "session": a})
        await rpc({"action": "poll", "session": a, "ready": True}, guest_bearer, 403)
    finally:
        await service({"action": "revoke", "room": "fixture_a"})
        await service({"action": "revoke", "room": "fixture_b"})
