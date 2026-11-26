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
    "mic_gain": (int, 50, 200), "brightness": (int, 1, 100),
    "muted": (bool,), "screen_awake": (bool,),
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
        return {**result, "error": "", "room_error": ""}
    except Exception as exc:
        # Do not leak tokens, URLs or server exception messages into the UI.
        detail = (str(exc) if isinstance(exc, RuntimeError)
                  and str(exc).startswith("TAFA WebSocket: ")
                  else type(exc).__name__)
        return {"devices": [], "rooms": [], "users": [],
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
    ws_call("configure", device_id=identifier, settings={key: value})
    return "Tablet setting saved."


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
                     '</div></details>'+delete_form+'</article>')
    device_section = '<div class="device-grid">'+"".join(parts)+'</div>' if parts else (
        f'<div class="work-card"><p>{t("Noch kein Tablet angemeldet. Starte TAFA Device Bridge auf einem Tablet und verbinde es mit HA.","No tablets enrolled. Start TAFA Device Bridge and connect it to HA.")}</p></div>')

    roomrows = []
    for item in rooms:
        if isinstance(item, dict):
            roomrows.append(
                f'<div class="room-row"><strong>{h(item.get("room"))}</strong>'
                f'<span>{t("bereit","ready") if item.get("ready") else t("nicht bereit","not ready")}</span>'
                f'<small>{h(item.get("wake_device_id"))}</small></div>')
    room_management_forms = []
    if not state.get("room_error"):
        for item in rooms:
            if not isinstance(item, dict):
                continue
            rid, uid = item.get("room"), item.get("user_id")
            paired = item.get("wake_device_id")
            if (not isinstance(rid, str) or not ROOM.fullmatch(rid)
                    or not isinstance(uid, str) or not 1 <= len(uid) <= 128):
                continue
            if isinstance(paired, str) and DEVICE_ID.fullmatch(paired):
                room_management_forms.append(
                    f'<form class="pair-form" method="post" action="./">{hidden("room_unpair", paired)}'
                    f'<input type="hidden" name="room" value="{h(rid)}">'
                    f'<input type="hidden" name="user_id" value="{h(uid)}">'
                    f'<strong>{h(rid)} – {t("Tablet lösen","Unpair tablet")}</strong>'
                    f'<p class="subtle">{t("Trennt die Gerätezuordnung und beendet die aktive Raum-Audio-/Kamerasitzung. Der Raum und das Tablet bleiben gespeichert.","Clears the assignment and stops active room audio/camera sessions. The room and tablet remain registered.")}</p>'
                    f'<label class="pair-consent"><input type="checkbox" name="confirm" value="1" required> {t("Zuordnung zurücksetzen","Reset assignment")}</label>'
                    f'<button type="submit" class="btn btn-outline">{t("Tablet lösen","Unpair tablet")}</button></form>'
                )
            room_management_forms.append(
                f'<form class="pair-form" method="post" action="./">{hidden("room_delete")}'
                f'<input type="hidden" name="room" value="{h(rid)}">'
                f'<input type="hidden" name="user_id" value="{h(uid)}">'
                f'<strong>{h(rid)} – {t("Raum löschen","Delete room")}</strong>'
                f'<p class="subtle">{t("Löscht den TAFA-Raum und seine Kamera-/Bewegungsentitäten, aber nicht den HA-Benutzer oder Automatisierungen. Der Raumnutzer kann danach neu zugeordnet werden.","Deletes the TAFA room and its camera/motion entities, not the HA user or automations. The room user can then be reassigned.")}</p>'
                f'<label class="pair-consent"><input type="checkbox" name="confirm" value="1" required> {t("Raum wirklich löschen","Confirm room deletion")}</label>'
                f'<button type="submit" class="btn btn-outline">{t("Raum löschen","Delete room")}</button></form>'
            )
    room_management = (
        f'<section class="work-card multiroom-panel"><h3>{t("Räume und Zuordnungen zurücksetzen","Reset rooms and assignments")}</h3>'
        f'<p class="subtle">{t("Keine Home-Assistant-Benutzer oder Automatisierungen werden gelöscht. Bereits darauf verweisende Automatisierungen können nach dem Entfernen einer Kamera-/Geräteentität eine erneute Zuordnung benötigen.","No HA users or automations are deleted. Automations referring to removed camera/device entities may need to be reconfigured.")}</p>'
        + "".join(room_management_forms)
        + (f'<p class="subtle">{t("Noch keine Räume angelegt.","No rooms created.")}</p>' if not room_management_forms else "")
        + '</section>'
    )
    # The first room can be created before there is any registered tablet.
    # A fresh install must not hide its creation form behind device enrollment.
    useropts = "".join(
        f'<option value="{h(u.get("id"))}">{h(u.get("name") or u.get("id"))}</option>'
        for u in users if isinstance(u, dict)
        and isinstance(u.get("id"), str) and 1 <= len(u["id"]) <= 128
    )
    deviceopts = "".join(
        f'<option value="{h(d.get("device_id"))}">{h(d.get("room") or "Tablet")}'
        f' ({h(str(d.get("device_id"))[:8])})</option>'
        for d in devices if isinstance(d, dict)
        and DEVICE_ID.fullmatch(str(d.get("device_id", "")))
    )

    guide = (
        f'<div class="work-card first-room-guide">'
        f'<h3>{t("Erste Einrichtung","First-time setup")}</h3>'
        f'<p><strong>1.</strong> {t("In Home Assistant unter Einstellungen → Personen → Benutzer einen eigenen Nicht-Admin-Benutzer für den Raum anlegen.","Create a dedicated non-admin HA user for this room under Settings → People → Users.")}</p>'
        f'<p><strong>2.</strong> {t("Hier einen Raum erstellen – auch wenn noch kein Tablet angemeldet ist.","Create the room here, even before a tablet is enrolled.")}</p>'
        f'<p><strong>3.</strong> {t("Die native App mit der Adresse des Testservers und dem Token dieses Benutzers verbinden. Rufworterkennung starten, damit das Tablet registriert wird.","Connect the native app to the test-server address with this users token. Start wakeword detection to enroll the tablet.")}</p>'
        f'<p><strong>4.</strong> {t("Das angemeldete Tablet dem erstellten Raum zuordnen und danach den Bluetooth-Player starten.","Pair the enrolled tablet with the new room, then start Bluetooth playback.")}</p>'
        '</div>'
    )

    ready = bool(useropts) and not state.get("room_error")
    userhint = (
        f'<p class="subtle">{t("Noch kein Nicht-Admin-Benutzer vorhanden. Lege zuerst einen in Home Assistant an und aktualisiere diese Seite.","No non-admin HA user yet. Create one in Home Assistant first and refresh this page.")}</p>'
        if not useropts else ""
    )
    api_hint = (
        f'<p class="subtle">{t("TAFA-Raum-API nicht erreichbar. Prüfe, ob die neue Integration auf diesem Testserver geladen ist und der Zugriff autorisiert ist.","TAFA room API unavailable. Check that the updated integration is loaded and authorized on this test server.")}</p>'
        if state.get("room_error") else ""
    )
    disabled = " disabled" if not ready else ""
    room_create = (
        f'<section class="work-card multiroom-panel">'
        f'<h3>{t("Neuen Raum anlegen","Create a new room")}</h3>'
        f'<p class="subtle">{t("Dafür muss noch kein Tablet registriert sein.","No enrolled tablet is required.")}</p>'
        f'<form class="pair-form" action="./" method="post">{hidden("room_create")}'
        f'<label>{t("Raum-ID (z. B. buero)","Room ID (e.g. office)")}'
        '<input name="room" type="text" pattern="[a-z0-9][a-z0-9_-]*" maxlength="64" required></label>'
        f'<label>{t("Home-Assistant-Raumnutzer","Home Assistant room user")}'
        f'<select name="user_id" required{disabled}>{useropts}</select></label>'
        f'<button class="btn btn-primary" type="submit"{disabled}>{t("Raum anlegen","Create room")}</button>'
        '</form>' + userhint + api_hint + '</section>'
    )

    pair_forms = []
    if not state.get("room_error") and deviceopts:
        for room in rooms:
            if not isinstance(room, dict):
                continue
            rid, uid = room.get("room"), room.get("user_id")
            if (not isinstance(rid, str) or not ROOM.fullmatch(rid)
                    or not isinstance(uid, str) or not 1 <= len(uid) <= 128):
                continue
            pair_forms.append(
                f'<form class="pair-form" action="./" method="post">{hidden("room_pair")}'
                f'<input type="hidden" name="room" value="{h(rid)}">'
                f'<input type="hidden" name="user_id" value="{h(uid)}">'
                f'<strong>{h(rid)}</strong>'
                f'<label>{t("Tablet auswählen","Select tablet")}'
                f'<select name="device_id" required>{deviceopts}</select></label>'
                f'<label class="pair-consent"><input type="checkbox" name="transfer_device" value="1"> '
                f'{t("Gerätebesitz ausdrücklich übertragen (nur wenn das Tablet unter einem anderen HA-Benutzer registriert wurde). Danach in Android das Token des Raumnutzers verwenden.","Explicitly transfer device ownership only if enrolled under a different user. Then use the room users token in Android.")}</label>'
                f'<button class="btn btn-primary" type="submit">{t("Tablet zuordnen","Pair tablet")}</button>'
                '</form>'
            )
    camera_forms = []
    if not state.get("room_error"):
        for item in rooms:
            if not isinstance(item, dict):
                continue
            rid, uid = item.get("room"), item.get("user_id")
            if (not isinstance(rid, str) or not ROOM.fullmatch(rid)
                    or not isinstance(uid, str) or not 1 <= len(uid) <= 128):
                continue
            enabled = item.get("camera_enabled") is True
            selector = (
                f'<select name="camera_enabled" aria-label="{t("Kamera für Raum","Camera for room")} {h(rid)}">'
                f'<option value="false"{" selected" if not enabled else ""}>{t("Aus – keine Bilder","Off – no images")}</option>'
                f'<option value="true"{" selected" if enabled else ""}>{t("An – Bilder bei manuellem Kamerastart","On – images on manual camera start")}</option>'
                '</select>'
            )
            camera_forms.append(
                f'<form class="pair-form" action="./" method="post">{hidden("room_camera")}'
                f'<input type="hidden" name="room" value="{h(rid)}">'
                f'<input type="hidden" name="user_id" value="{h(uid)}">'
                f'<strong>{h(rid)}</strong>'
                + selector
                + f'<button class="btn btn-outline" type="submit">{t("Kamerafreigabe speichern","Save camera permission")}</button>'
                '</form>'
            )
    camera_panel = (
        f'<section class="work-card multiroom-panel">'
        f'<h3>{t("Tablet-Kameras je Raum","Tablet cameras per room")}</h3>'
        f'<p class="subtle">{t("Kameraübertragung ist standardmäßig aus. Erlaube sie hier für einen Raum und starte die Kamera anschließend ausdrücklich auf dem Tablet. Es werden nur aktuelle Bilder im HA-Arbeitsspeicher gehalten.","Camera uploads are off by default. Enable them for a room here and explicitly start the tablet camera afterwards. Only recent images are held in HA memory.")}</p>'
        + "".join(camera_forms)
        + (f'<p class="subtle">{t("Lege zuerst einen Raum an.","Create a room first.")}</p>' if not camera_forms else "")
        + '</section>'
    )
    pairing_note = (
        f'<p class="subtle">{t("Nach der Anmeldung des Tablets über die Rufworterkennung erscheint hier die Zuordnung.","After enrolling a tablet with wakeword recognition, pairing appears here.")}</p>'
        if not pair_forms else ""
    )
    pairing = (
        f'<section class="work-card multiroom-panel">'
        f'<h3>{t("Tablet einem Raum zuordnen","Pair a tablet with a room")}</h3>'
        '<div class="room-list">' + "".join(roomrows) + '</div>'
        + "".join(pair_forms) + pairing_note + '</section>'
    )
    return notice + device_section + guide + room_create + camera_panel + pairing + room_management
