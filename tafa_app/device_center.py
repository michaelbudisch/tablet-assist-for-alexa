"""Admin-only device and multiroom controls in the TAFA Supervisor Ingress UI.

The Home Assistant integration owns every device's settings and state.
This layer only renders sanitized values and validates explicit form actions.
No new Home Assistant dashboard, helper, or automation is created.
"""
import html
import re
import urllib.error
from auto_setup import call as ha_call

DEVICE_ID = re.compile(r"[a-f0-9]{32}\Z")
ROOM = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")
FIELDS = {
    "strict": (int, 1, 3), "cooldown": (int, 3, 30),
    "hold": (int, 10, 90), "pause_ms": (int, 900, 3200),
    "mic_gain": (int, 50, 200), "brightness": (int, 1, 100),
    "muted": (bool,), "screen_awake": (bool,),
    "display_control_enabled": (bool,), "room": (str,),
    "word": (str,),
}
WORDS = ("Hey Jarvis", "Jarvis", "Alexa", "Alle drei")


def _read_endpoint(endpoint):
    """Request one privileged HA endpoint without hiding other healthy sections.

    The error is a fixed type name or numeric HTTP code only. Never include
    HA's exception body, endpoint URL or bearer token in the user interface.
    """
    try:
        reply = ha_call("tablet_assist_for_alexa/" + endpoint, {"action": "list"})
        if not isinstance(reply, dict):
            raise ValueError("Invalid API response")
        return reply, ""
    except urllib.error.HTTPError as exc:
        return {}, "HTTP " + str(exc.code)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, RuntimeError, TypeError) as exc:
        return {}, type(exc).__name__


def read_device_data():
    """Read authenticated tablet data and room administration independently."""
    devices, device_error = _read_endpoint("wake_devices")
    multiroom, room_error = _read_endpoint("room_admin")
    return {"devices": devices.get("devices", []),
            "rooms": multiroom.get("rooms", []),
            "users": multiroom.get("users", []),
            "error": device_error, "room_error": room_error}


def update_device(fields):
    identifier = fields.get("device_id", [""])[0]
    key = fields.get("setting", [""])[0]
    raw = fields.get("value", [""])[0]
    if not DEVICE_ID.fullmatch(identifier) or key not in FIELDS:
        raise ValueError("Invalid device or setting")
    kind = FIELDS[key][0]
    if kind is bool:
        if raw not in ("true", "false"):
            raise ValueError("Invalid switch value")
        value = raw == "true"
    elif kind is int:
        if not re.fullmatch(r"[0-9]{1,4}", raw):
            raise ValueError("Invalid numeric setting")
        value = int(raw)
        if not FIELDS[key][1] <= value <= FIELDS[key][2]:
            raise ValueError("Setting outside allowed range")
    else:
        value = raw.strip()
        if key == "word" and value not in WORDS:
            raise ValueError("Unknown wake phrase")
        if key == "room" and not 0 < len(value) <= 48:
            raise ValueError("Room name must be 1–48 characters")
    ha_call("tablet_assist_for_alexa/wake_devices", {
        "action": "configure", "device_id": identifier,
        "settings": {key: value}})
    return "Tablet setting saved."


def pair_device(fields):
    identifier = fields.get("device_id", [""])[0]
    room = fields.get("room", [""])[0].strip()
    user_id = fields.get("user_id", [""])[0]
    if (not DEVICE_ID.fullmatch(identifier) or not ROOM.fullmatch(room)
            or not 1 <= len(user_id) <= 128):
        raise ValueError("Invalid multiroom assignment")
    # The backend enforces ownership. No implicit transfer or replacement.
    ha_call("tablet_assist_for_alexa/room_admin", {
        "action": "pair", "device_id": identifier,
        "room": room, "user_id": user_id,
        "replace": False, "transfer_device": False})
    return "Multiroom pairing saved."


def render_device_center(lang, csrf, state):
    en = lang == "en"
    t = lambda de, eng: eng if en else de
    h = lambda value: html.escape(str(value if value is not None else ""), quote=True)

    def hidden(action, identifier=""):
        return (f'<input type="hidden" name="csrf" value="{h(csrf)}">'
                f'<input type="hidden" name="lang" value="{h(lang)}">'
                f'<input type="hidden" name="tab" value="devices">'
                +(f'<input type="hidden" name="device_id" value="{h(identifier)}">' if identifier else "")
                +f'<input type="hidden" name="action" value="{h(action)}">')

    def setting(device, key, label, kind="number", lo=1, hi=100, choices=None):
        value = device.get(key)
        if value is None:
            value = {"muted": False, "screen_awake": True,
                     "display_control_enabled": False}.get(key, "")
        if choices is not None:
            options = "".join(
                f'<option value="{h(item)}"{" selected" if item == value else ""}>{h(item)}</option>'
                for item in choices)
            control = f'<select name="value" id="{h(device["device_id"]+key)}">{options}</select>'
        elif kind == "boolean":
            choices_bool = ((False, t("Aus","Off")), (True, t("An","On")))
            options = "".join(
                f'<option value="{str(v).lower()}"{" selected" if v == value else ""}>{h(label)}</option>'
                for v,label in choices_bool)
            control = f'<select name="value" id="{h(device["device_id"]+key)}">{options}</select>'
        elif kind == "text":
            control = (f'<input type="text" name="value" id="{h(device["device_id"]+key)}" '
                       f'value="{h(value)}" maxlength="48" required>')
        else:
            control = (f'<input type="number" name="value" id="{h(device["device_id"]+key)}" '
                       f'value="{h(value)}" min="{lo}" max="{hi}" step="1" required>')
        return (f'<form class="device-setting" method="post" action="./">'
                f'{hidden("device_update", device["device_id"])}'
                f'<input type="hidden" name="setting" value="{h(key)}">'
                f'<label for="{h(device["device_id"]+key)}">{h(label)}</label>'
                f'{control}<button class="btn btn-outline" type="submit">'
                f'{t("Speichern","Save")}</button></form>')

    devices = state.get("devices")
    rooms = state.get("rooms")
    users = state.get("users")
    if not isinstance(devices, list):
        devices = []
    if not isinstance(rooms, list):
        rooms = []
    if not isinstance(users, list):
        users = []
    notice = ""
    if state.get("error"):
        notice += (f'<div class="info-note" role="status"><strong>'
                   f'{t("Tablet-Verbindung zu HA fehlgeschlagen","Tablet API unavailable")}</strong>'
                   f'<p>{t("Tablet-Abfrage","Tablet request")}: {h(state["error"])}. '
                   f'{t("Die übrigen Bereiche bleiben verfügbar.","Other sections remain available.")}'
                   '</p></div>')
    if state.get("room_error"):
        notice += (f'<div class="info-note" role="status"><strong>'
                   f'{t("Multiroom-Verwaltung nicht erreichbar","Multiroom API unavailable")}</strong>'
                   f'<p>{t("Raum-Abfrage","Room request")}: {h(state["room_error"])}. '
                   f'{t("Die Tablet-Einstellungen sind weiterhin nutzbar.","Tablet controls remain available.")}'
                   '</p></div>')

    parts = []
    for device in devices:
        if not isinstance(device, dict) or not DEVICE_ID.fullmatch(str(device.get("device_id", ""))):
            continue
        did = str(device["device_id"])
        connected = bool(device.get("online"))
        tele = device.get("telemetry") if isinstance(device.get("telemetry"), dict) else {}
        telemetry = " · ".join(
            f'{h(label)}: {h(tele.get(key,"—"))}'
            for key,label in (("microphone",t("Mikrofon","Microphone")),
                              ("bluetooth","Bluetooth"), ("audio","Audio"),
                              ("battery",t("Akku","Battery")), ("app_version","App"))
        )
        parts.append(f'<article class="work-card tablet-card">'
                     f'<header><h3>{h(device.get("room") or "Tablet")}</h3>'
                     f'<span class="status-pill status-{"good" if connected else "neutral"}">'
                     f'{t("Online","Online") if connected else t("Offline","Offline")}</span></header>'
                     f'<p class="subtle">{h(did)}</p><p class="subtle">{telemetry}</p>'
                     '<details open><summary>'+t("Rufwort & Mikrofon","Wakeword & microphone")+'</summary>'
                     '<div class="device-settings">'+
                     setting(device,"muted",t("Mikrofon stumm","Mute microphone"),kind="boolean")+
                     setting(device,"word",t("Rufwort","Wake phrase"),choices=WORDS)+
                     setting(device,"strict",t("Rufwort-Bestätigung","Wake confirmation"),lo=1,hi=3)+
                     setting(device,"cooldown",t("Rufwort-Sperrzeit (s)","Wake cooldown (s)"),lo=3,hi=30)+
                     setting(device,"hold",t("Rufwort-Haltezeit (s)","Wake handoff (s)"),lo=10,hi=90)+
                     setting(device,"pause_ms",t("Sprechpause (ms)","Speech endpoint pause (ms)"),lo=900,hi=3200)+
                     setting(device,"mic_gain",t("Digitale Mikrofonverstärkung (%)","Digital mic gain (%)"),lo=50,hi=200)+
                     '</div></details><details><summary>'+t("Anzeige & Raum","Display & room")+'</summary>'
                     '<p class="subtle">'+t(
                       "Display-Steuerung ist optional und benötigt die Android-Freigabe „Systemeinstellungen ändern“. Die Einstellung dimmt nur, sie sperrt oder weckt den Bildschirm nicht.",
                       "Display control requires optional Android Modify system settings permission. It only dims, without locking or waking the screen."
                     )+'</p><div class="device-settings">'+
                     setting(device,"room",t("Raumname","Room name"),kind="text")+
                     setting(device,"display_control_enabled",t("Displaysteuerung erlauben","Enable brightness control"),kind="boolean")+
                     setting(device,"screen_awake",t("Display hell statt gedimmt","Bright instead of dim"),kind="boolean")+
                     setting(device,"brightness",t("Helligkeit (%)","Brightness (%)"),lo=1,hi=100)+
                     '</div></details></article>')
    device_section = '<div class="device-grid">'+"".join(parts)+'</div>' if parts else (
        f'<div class="work-card"><p>{t("Noch kein Tablet angemeldet. Starte TAFA Device Bridge auf einem Tablet und verbinde es mit HA.","No tablets enrolled. Start TAFA Device Bridge and connect it to HA.")}</p></div>')

    roomrows = []
    for item in rooms:
        if isinstance(item, dict):
            roomrows.append(
                f'<div class="room-row"><strong>{h(item.get("room"))}</strong>'
                f'<span>{t("bereit","ready") if item.get("ready") else t("nicht bereit","not ready")}</span>'
                f'<small>{h(item.get("wake_device_id"))}</small></div>')
    useropts = "".join(
        f'<option value="{h(x.get("id"))}">{h(x.get("name") or x.get("id"))}</option>'
        for x in users if isinstance(x, dict))
    deviceopts = "".join(
        f'<option value="{h(x.get("device_id"))}">{h(x.get("room") or "Tablet")}'
        f' ({h(str(x.get("device_id",""))[:8])})</option>'
        for x in devices if isinstance(x, dict) and DEVICE_ID.fullmatch(str(x.get("device_id",""))))
    pairing = (f'<form class="pair-form" action="./" method="post">{hidden("room_pair")}'
               f'<label>{t("Raum-ID (z. B. buero)","Room ID (e.g. office)")}'
               '<input type="text" name="room" pattern="[a-z0-9][a-z0-9_-]*" maxlength="64" required></label>'
               f'<label>{t("Tablet","Tablet")}<select name="device_id" required>{deviceopts}</select></label>'
               f'<label>{t("Dedizierter Home-Assistant-Benutzer","Dedicated Home Assistant user")}'
               f'<select name="user_id" required>{useropts}</select></label>'
               f'<button class="btn btn-primary" type="submit">{t("Multiroom koppeln","Pair multiroom")}</button>'
               '</form>' if useropts and deviceopts else
               f'<p class="subtle">{t("Für jeden Raum einen eigenen Nicht-Admin-HA-Benutzer anlegen und die App damit anmelden.","Create a dedicated non-admin HA user for each room and sign the tablet in with it.")}</p>')
    if state.get("room_error"):
        pairing = f'<p class="subtle">{t("Raumkopplung derzeit nicht verfügbar.","Room pairing temporarily unavailable.")}</p>'
    return (notice + device_section
            +f'<section class="work-card multiroom-panel"><h3>{t("Multiroom · Bluetooth-Ausgabe","Multiroom · Bluetooth playback")}</h3>'
            f'<p class="subtle">{t("Jedes Tablet ist einem eigenen Home-Assistant-Benutzer und Raum zugeordnet. Antworten werden über den nativen Audio-Player auf dem gekoppelten Bluetooth-Lautsprecher ausgegeben.","Each tablet is paired with its own HA user and room. Native playback routes answers to its Bluetooth speaker.")}</p>'
            +'<div class="room-list">'+"".join(roomrows)+'</div>'+pairing+'</section>')
