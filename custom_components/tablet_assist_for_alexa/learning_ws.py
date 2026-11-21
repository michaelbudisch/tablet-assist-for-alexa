"""Authenticated admin-only configuration API."""
import voluptuous as vol
from homeassistant.components import websocket_api
from .const import DOMAIN

@websocket_api.websocket_command({vol.Required("type"): DOMAIN+"/learning",vol.Required("action"):vol.In(("list","approve","dismiss","delete","clear")),vol.Optional("phrase",default=""):vol.All(str,vol.Length(max=140)),vol.Optional("target",default=""):vol.All(str,vol.Length(max=64))})
@websocket_api.require_admin
@websocket_api.async_response
async def learning_command(hass,connection,msg):
    entries=hass.data.get(DOMAIN,{})
    data=next(iter(entries.values()),None)
    if not data or not data.learning:
        connection.send_error(msg["id"],"not_ready","Tablet Assist is not configured.");return
    try:
        result=data.learning.snapshot() if msg["action"]=="list" else await data.learning.edit(msg["action"],msg["phrase"],msg["target"])
    except (ValueError,TypeError):
        connection.send_error(msg["id"],"invalid_input","Invalid learning configuration.");return
    connection.send_result(msg["id"],result)
