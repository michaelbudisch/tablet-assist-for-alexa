"""Admin-only device and multiroom controls in the TAFA Supervisor Ingress UI.

The Home Assistant integration owns every device's settings and state.
This layer only renders sanitized values and validates explicit form actions.
No new Home Assistant dashboard, helper, or automation is created.
"""
import html
import re
import urllib.error
from auto_setup import device_admin_rpc as ws_call

DEVICE_ID = re.compile(r"[a-f0-9]{32}\Z")
ROOM = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")
FIELDS = {
    "strict": (int, 1, 3), "cooldown": (int, 3, 30),
    "hold": (int, 10, 90), "pause_ms": (int, 900, 3200),
    "followup_limit": (int, -1, 100),
    "mic_gain": (int, 50, 200), "brightness": (int, 1, 100),
    "muted": (bool,), "voice_mode": (str,), "audio_output_mode": (str,), "screen_awake": (bool,),
    "display_control_enabled": (bool,), "room": (str,),
    "word": (str,),
}
WORDS = ("Hey Jarvis", "Jarvis", "Alexa", "Alle drei")


def read_device_data():
    """Load devices, audio rooms and new HA users using one admin WebSocket."""
    try:
        result = ws_call("list")
        if not isinstance(result, dict):
            raise ValueError("Invalid TAFA device response")
        for key in ("devices", "rooms", "users"):
            if not isinstance(result.get(key), list):
                raise ValueError("Invalid TAFA " + key)
        if not isinstance(result.get("areas"), list):
            result["areas"] = []
        return {**result, "error": "", "room_error": ""}
    except Exception as exc:
        # Do not leak tokens, URLs or server exception messages into the UI.
        detail = (str(exc) if isinstance(exc, RuntimeError)
                  and str(exc).startswith("TAFA WebSocket: ")
                  else type(exc).__name__)
        return {"devices": [], "rooms": [], "users": [], "areas": [],
                "error": detail, "room_error": detail}


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
        if not re.fullmatch(r"-?[0-9]{1,4}" if key == "followup_limit" else r"[0-9]{1,4}", raw):
            raise ValueError("Invalid numeric setting")
        value = int(raw)
        if not FIELDS[key][1] <= value <= FIELDS[key][2]:
            raise ValueError("Setting outside allowed range")
    else:
        value = raw.strip()
        if key == "voice_mode" and value not in ("wake","continuous"):
            raise ValueError("Unknown native speech mode")
        if key == "audio_output_mode" and value not in ("auto", "bluetooth", "tablet"):
            raise ValueError("Unknown audio output mode")
        if key == "word" and value not in WORDS:
            raise ValueError("Unknown wake phrase")
        if key == "room" and not 0 < len(value) <= 48:
            raise ValueError("Room name must be 1–48 characters")
    ws_call("configure", device_id=identifier, settings={key: value})
    return "Tablet setting saved."


def set_native_microphone_mode(identifier, mode):
    """Set native mode atomically through the existing per-device HA store."""
    if not DEVICE_ID.fullmatch(identifier) or mode not in ("mute","wake","continuous"):
        raise ValueError("Invalid microphone mode")
    settings = {"muted": mode == "mute"}
    if mode != "mute":
        settings["voice_mode"] = mode
    ws_call("configure", device_id=identifier, settings=settings)
    return "Native microphone mode saved."


def set_native_followup_limit(identifier, limit):
    """Restrict an enrolled tablet's follow-ups; -1 defers to the app."""
    if not DEVICE_ID.fullmatch(identifier) or type(limit) is not int or not -1 <= limit <= 100:
        raise ValueError("Invalid follow-up ceiling")
    ws_call("configure", device_id=identifier, settings={"followup_limit": limit})
    return "Follow-up ceiling saved."


def assign_to_ha_area(fields):
    """One action: bind an already enrolled tablet to an existing HA area.

    The backend derives the device's non-admin principal, provisions the
    private audio room and syncs the HA device registry automatically.
    """
    identifier = fields.get("device_id", [""])[0]
    area_id = fields.get("area_id", [""])[0].strip()
    if not DEVICE_ID.fullmatch(identifier) or not ROOM.fullmatch(area_id):
        raise ValueError("Invalid TAFA tablet or HA area")
    confirmed = fields.get("confirm_move", ["0"])[0]
    if confirmed not in ("0", "1"):
        raise ValueError("Invalid move confirmation")
    response = ws_call("assign_area", device_id=identifier, area_id=area_id,
                       confirm_move=confirmed == "1")
    return ("Tablet einem Home-Assistant-Raum zugeordnet."
            if isinstance(response, dict) else "Zuordnung gespeichert.")


def create_room(fields):
    """Create an audio room before any tablet is enrolled."""
    room = fields.get("room", [""])[0].strip()
    user_id = fields.get("user_id", [""])[0]
    if (not ROOM.fullmatch(room) or not isinstance(user_id, str)
            or not 1 <= len(user_id) <= 128):
        raise ValueError("Ungültige Raum-ID oder Benutzer-ID / Invalid room or user")
    ws_call("create", room=room, user_id=user_id)
    return "Raum angelegt / Room created."


def pair_device(fields):
    identifier = fields.get("device_id", [""])[0]
    room = fields.get("room", [""])[0].strip()
    user_id = fields.get("user_id", [""])[0]
    if (not DEVICE_ID.fullmatch(identifier) or not ROOM.fullmatch(room)
            or not 1 <= len(user_id) <= 128):
        raise ValueError("Invalid multiroom assignment")
    transfer = fields.get("transfer_device", ["0"])[0]
    if transfer not in ("0", "1"):
        raise ValueError("Invalid device transfer choice")
    ws_call("pair", device_id=identifier, room=room,
            user_id=user_id, transfer_device=transfer == "1")
    return "Multiroom pairing saved."


def set_room_camera(fields):
    """Require a real room, matching owner and explicit enable/disable value."""
    room = fields.get("room", [""])[0].strip()
    user_id = fields.get("user_id", [""])[0]
    raw = fields.get("camera_enabled", [""])[0]
    if (not ROOM.fullmatch(room) or not isinstance(user_id, str)
            or not 1 <= len(user_id) <= 128 or raw not in ("true", "false")):
        raise ValueError("Invalid camera room or permission")
    enabled = raw == "true"
    ws_call("camera", room=room, user_id=user_id, camera_enabled=enabled)
    return "Kamera für Raum aktiviert." if enabled else "Kamera für Raum deaktiviert."


def remove_device(fields):
    identifier = fields.get("device_id", [""])[0]
    if not DEVICE_ID.fullmatch(identifier) or fields.get("confirm", [""])[0] != "1":
        raise ValueError("Confirm the registered tablet before removal")
    ws_call("delete_device", device_id=identifier, confirmed=True)
    return "Tablet entfernt / Tablet removed."


def unpair_device(fields):
    identifier = fields.get("device_id", [""])[0]
    room, user_id = fields.get("room", [""])[0], fields.get("user_id", [""])[0]
    if (not DEVICE_ID.fullmatch(identifier) or not ROOM.fullmatch(room)
            or not 1 <= len(user_id) <= 128 or fields.get("confirm", [""])[0] != "1"):
        raise ValueError("Confirm the current tablet pairing")
    ws_call("unpair", room=room, user_id=user_id, device_id=identifier, confirmed=True)
    return "Tablet vom Raum gelöst / Tablet unpaired."


def delete_room(fields):
    room, user_id = fields.get("room", [""])[0], fields.get("user_id", [""])[0]
    if (not ROOM.fullmatch(room) or not 1 <= len(user_id) <= 128
            or fields.get("confirm", [""])[0] != "1"):
        raise ValueError("Confirm room deletion")
    ws_call("delete_room", room=room, user_id=user_id, confirmed=True)
    return "Raum entfernt / Room deleted. HA-Benutzer bleibt erhalten."


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
                     "display_control_enabled": False, "audio_output_mode": "auto"}.get(key, "")
        if choices is not None:
            options = "".join(
                f'<option value="{h(item)}"{" selected" if item == value else ""}>{h({"auto": t("Automatisch", "Automatic"), "bluetooth": t("Nur Bluetooth", "Bluetooth only"), "tablet": t("Nur Tablet", "Tablet only")}.get(item, item) if key == "audio_output_mode" else item)}</option>'
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
        delete_form = (
            '<details class="device-removal">'
            f'<summary>{t("Tablet aus TAFA entfernen","Remove tablet from TAFA")}</summary>'
            f'<p class="subtle">{t("Stoppe zuerst TAFA Device Bridge auf dem Tablet (Rufwort und Player), sonst meldet es sich automatisch erneut an. Nur die TAFA-Geräteregistrierung und ihre Entitäten werden entfernt; der HA-Benutzer bleibt erhalten.","Stop wakeword and player on the tablet first, otherwise it will automatically enroll again. Only the TAFA registration and its entities are removed; the HA user is preserved.")}</p>'
            f'<form method="post" action="./" class="pair-form">{hidden("device_delete", did)}'
            f'<label class="pair-consent"><input name="confirm" type="checkbox" value="1" required> {t("Ich möchte dieses Tablet zurücksetzen.","I want to reset this tablet.")}</label>'
            f'<button class="btn btn-outline" type="submit">{t("Tablet entfernen","Remove tablet")}</button>'
            '</form></details>'
        )
        parts.append(f'<article class="work-card tablet-card">'
                     f'<header><h3>{h(device.get("room") or "Tablet")}</h3>'
                     f'<span class="status-pill status-{"good" if connected else "neutral"}">'
                     f'{t("Online","Online") if connected else t("Offline","Offline")}</span></header>'
                     f'<p class="subtle">{h(did)}</p><p class="subtle">{telemetry}</p>'
                     '<details open><summary>'+t("Audioausgabe","Audio output")+'</summary><div class="device-settings">'+
                     setting(device,"audio_output_mode",t("Audioausgabe","Audio output"),choices=("auto","bluetooth","tablet"))+
                     '</div></details><details><summary>'+t("Rufwort & Mikrofon","Wakeword & microphone")+'</summary>'
                     '<div class="device-settings">'+
                     setting(device,"muted",t("Mikrofon stumm","Mute microphone"),kind="boolean")+
                     setting(device,"voice_mode",t("Nativer Sprachmodus","Native speech mode"),choices=("wake","continuous"))+
                     setting(device,"followup_limit",t("Anschlussfragen (HA-Grenze: -1 = App)","Follow-up ceiling (-1 = app setting)"),choices=(-1,0,1,2,3,5,10,20,50,100))+
                     setting(device,"word",t("Rufwort","Wake phrase"),choices=WORDS)+
                     setting(device,"strict",t("Rufwort-Bestätigung","Wake confirmation"),lo=1,hi=3)+
                     setting(device,"cooldown",t("Rufwort-Sperrzeit (s)","Wake cooldown (s)"),lo=3,hi=30)+
                     setting(device,"hold",t("Rufwort-Haltezeit (s)","Wake handoff (s)"),lo=10,hi=90)+
                     setting(device,"pause_ms",t("Sprechpause (ms)","Speech endpoint pause (ms)"),lo=900,hi=3200)+
                     setting(device,"mic_gain",t("Digitale Mikrofonverstärkung (%)","Digital mic gain (%)"),lo=50,hi=200)+
                     '</div></details><details><summary>'+t("Anzeige","Display")+'</summary>'
                     '<p class="subtle">'+t(
                       "Display-Steuerung ist optional und benötigt die Android-Freigabe „Systemeinstellungen ändern“. Die Einstellung dimmt nur, sie sperrt oder weckt den Bildschirm nicht.",
                       "Display control requires optional Android Modify system settings permission. It only dims, without locking or waking the screen."
                     )+'</p><div class="device-settings">'+
                     setting(device,"display_control_enabled",t("Displaysteuerung erlauben","Enable brightness control"),kind="boolean")+
                     setting(device,"screen_awake",t("Display hell statt gedimmt","Bright instead of dim"),kind="boolean")+
                     setting(device,"brightness",t("Helligkeit (%)","Brightness (%)"),lo=1,hi=100)+
                     '</div></details>'+delete_form+'</article>')
    device_section = '<div class="device-grid">'+"".join(parts)+'</div>' if parts else (
        f'<div class="work-card"><p>{t("Noch kein Tablet angemeldet. Starte TAFA Device Bridge auf einem Tablet und verbinde es mit HA.","No tablets enrolled. Start TAFA Device Bridge and connect it to HA.")}</p></div>')

    # One authority: Home Assistant's area registry. Do not offer a
    # second TAFA-specific room creation/assignment wizard.
    areas = state.get("areas") if isinstance(state.get("areas"), list) else []
    area_names = {
        area["area_id"]: area["name"]
        for area in areas if isinstance(area, dict)
        and isinstance(area.get("area_id"), str)
        and isinstance(area.get("name"), str)
        and ROOM.fullmatch(area["area_id"])
    }
    bound = {
        room.get("wake_device_id"): room.get("room")
        for room in rooms if isinstance(room, dict)
        and isinstance(room.get("wake_device_id"), str)
    }
    rows = []
    for device in devices:
        if not isinstance(device, dict):
            continue
        did = device.get("device_id")
        if not isinstance(did, str) or not DEVICE_ID.fullmatch(did):
            continue
        active = bound.get(did, "")
        options = "".join(
            f'<option value="{h(area_id)}"{" selected" if area_id == active else ""}>{h(name)}</option>'
            for area_id, name in sorted(area_names.items(), key=lambda a: a[1].casefold())
        )
        label = device.get("room") or "TAFA Tablet"
        online = bool(device.get("online"))
        status = (t("Verbunden","Connected") if online else t("Offline","Offline"))
        current = (t("Zugeordnet","Assigned") if active in area_names else
                   t("Noch keinem HA-Raum zugeordnet","Not assigned to an HA area"))
        if active and active not in area_names:
            current = t("Alte TAFA-Zuordnung","Legacy TAFA assignment") + ": " + active
        rows.append(
            '<div class="tafa-area-row">'
            '<div class="tafa-area-identity">'
            f'<strong>{h(label)}</strong> '
            f'<span class="status-pill status-{"good" if online else "neutral"}">{status}</span>'
            f'<small>{t("Geräte-ID","Device ID")}: <code>{h(did)}</code></small>'
            f'<small>{t("Aktueller Raum","Current area")}: {h(current)}</small>'
            '</div>'
            f'<form class="tafa-area-form" data-current-area="{h(active)}" method="post" action="./">{hidden("area_assign", did)}'
            '<input type="hidden" name="confirm_move" value="0">'
            f'<label for="area-{h(did)}">{t("Home-Assistant-Raum","Home Assistant area")}</label>'
            f'<select id="area-{h(did)}" name="area_id" required{" disabled" if not options else ""}>'
            f'<option value=""{" selected" if not active or active not in area_names else ""} disabled>'
            f'{t("Raum auswählen","Choose area")}</option>{options}</select>'
            f'<button class="btn btn-primary" type="submit"{" disabled" if not options else ""}>'
            f'{t("Raum zuweisen","Assign area")}</button></form></div>'
        )
    if rows:
        content = "".join(rows)
    else:
        content = ('<p class="subtle">' +
                   t("Noch kein TAFA-Tablet registriert. Verbinde TAFA Device Bridge in Android mit Home Assistant; die App registriert ihre eindeutige Kennung automatisch.",
                     "No TAFA tablet enrolled. Connect Device Bridge to Home Assistant; the app enrolls its own unique ID automatically.") +
                   '</p>')
    area_hint = ('<p class="subtle">' +
                 t("Noch keine Home-Assistant-Räume verfügbar. Lege sie zuerst unter Einstellungen → Bereiche an.",
                   "No Home Assistant areas available. Create one in Settings → Areas first.") +
                 '</p>' if not area_names else "")
    guide = (
        '<p class="subtle">' +
        t("1. Raum in Home Assistant erstellen. 2. TAFA Device Bridge verbinden. 3. Hier das Tablet dem Raum zuweisen. Die technische Audio-/Kamerazuordnung erledigt TAFA automatisch. Für getrennte Audiokanäle benötigt jedes Tablet weiterhin ein eigenes Nicht-Admin-HA-Konto.",
          "1. Create an area in Home Assistant. 2. Connect Device Bridge. 3. Assign this tablet to its area. TAFA handles internal audio/camera routing. Each tablet still requires its own non-admin HA account for isolated audio.") +
        '</p>'
    )
    assignment_panel = (
        '<section class="work-card multiroom-panel tafa-area-panel">'
        f'<h3>{t("Tablets und Home-Assistant-Räume","Tablets and Home Assistant areas")}</h3>'
        + guide
        + '<p><a href="/config/areas/dashboard" target="_top" rel="noopener">'
        + t("Home-Assistant-Räume verwalten","Manage Home Assistant areas") + '</a></p>'
        + '<div class="tafa-area-rows">' + content + '</div>' + area_hint + '</section>'
    )

    # Settings and destructive actions remain available, but do not create
    # another visible pairing flow or a duplicate listing of each room.
    camera_controls = []
    reset_controls = []
    for item in rooms:
        if not isinstance(item, dict):
            continue
        rid, uid = item.get("room"), item.get("user_id")
        if (not isinstance(rid, str) or not ROOM.fullmatch(rid)
                or not isinstance(uid, str) or not 1 <= len(uid) <= 128):
            continue
        has_device = isinstance(item.get("wake_device_id"), str) and DEVICE_ID.fullmatch(item["wake_device_id"])
        if has_device:
            enabled = item.get("camera_enabled") is True
            camera_controls.append(
                f'<form class="pair-form" method="post" action="./">{hidden("room_camera")}'
                f'<input type="hidden" name="room" value="{h(rid)}">'
                f'<input type="hidden" name="user_id" value="{h(uid)}">'
                f'<label>{h(area_names.get(rid, rid))} – {t("Tablet-Kamera","Tablet camera")}'
                '<select name="camera_enabled">'
                f'<option value="false"{" selected" if not enabled else ""}>{t("Aus","Off")}</option>'
                f'<option value="true"{" selected" if enabled else ""}>{t("An (nach manuellem Start in der App)","On (after manual app start)")}</option>'
                '</select></label>'
                f'<button class="btn btn-outline" type="submit">{t("Kamera speichern","Save camera")}</button>'
                '</form>'
            )
            reset_controls.append(
                f'<form class="pair-form" method="post" action="./">{hidden("room_unpair", item["wake_device_id"])}'
                f'<input type="hidden" name="room" value="{h(rid)}">'
                f'<input type="hidden" name="user_id" value="{h(uid)}">'
                f'<strong>{h(area_names.get(rid,rid))}: {t("Tablet lösen","Unpair tablet")}</strong>'
                f'<label class="pair-consent"><input type="checkbox" name="confirm" value="1" required>'
                f'{t("TAFA-Gerätezuordnung wirklich lösen","Confirm unpairing")}</label>'
                f'<button class="btn btn-outline" type="submit">{t("Tablet lösen","Unpair")}</button>'
                '</form>'
            )
        reset_controls.append(
            f'<form class="pair-form" method="post" action="./">{hidden("room_delete")}'
            f'<input type="hidden" name="room" value="{h(rid)}">'
            f'<input type="hidden" name="user_id" value="{h(uid)}">'
            f'<strong>{h(area_names.get(rid,rid))}: {t("TAFA-Routing zurücksetzen","Reset TAFA routing")}</strong>'
            f'<label class="pair-consent"><input type="checkbox" name="confirm" value="1" required>'
            f'{t("Nur TAFA-Routing löschen (HA-Raum bleibt erhalten)","Delete only TAFA routing (HA area remains)")}</label>'
            f'<button class="btn btn-outline" type="submit">{t("TAFA-Routing entfernen","Remove TAFA routing")}</button>'
            '</form>'
        )
    advanced = (
        '<details class="work-card multiroom-panel tafa-area-advanced">'
        f'<summary>{t("Erweitert: Tablet-Einstellungen, Kamera und Zurücksetzen","Advanced: device settings, camera and reset")}</summary>'
        f'<h3>{t("Tablet-Einstellungen","Tablet settings")}</h3>'
        + device_section
        + f'<h3>{t("Kamerafreigabe (optional)","Camera access (optional)")}</h3>'
        + '<p class="subtle">' +
          t("Kamerabilder werden nur nach ausdrücklichem Start auf dem Tablet übertragen.",
            "Camera images are shared only after explicit activation on the tablet.") +
          '</p>'
        + "".join(camera_controls)
        + f'<h3>{t("TAFA-Zuordnung zurücksetzen","Reset TAFA pairing")}</h3>'
        + '<p class="subtle">' +
          t("Diese Aktionen verändern weder Home-Assistant-Bereiche noch Benutzer. Automationen mit Kamera-Entitäten können danach eine neue Zuordnung benötigen.",
            "These actions never delete Home Assistant areas or users. Automations using camera entities may require reassignment.") +
          '</p>'
        + "".join(reset_controls) + '</details>'
    )
    return notice + assignment_panel + advanced
