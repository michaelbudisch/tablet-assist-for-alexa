"""Local single-image vision; fixed camera mapping, authorization, bounded requests and no redirects."""
import asyncio
import base64
import ipaddress
import json
import re
from urllib.parse import urlsplit

import aiohttp
from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.components.camera import async_get_image
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er

from .const import QWEN_BASE

DOOR_PLACE = r"(?:(?:haus ?|eingangs ?)?t(?:ür|uer)|klingel)"
CAMERA_REFERENCES = {
    "door": rf"(?:{DOOR_PLACE}(?: ?kamera)?|kamera {DOOR_PLACE})(?: live ansicht)?",
    "outside": r"(?:vorderseite(?:n? ?kamera)?|vorder ?kamera|außen ?kamera|aussen ?kamera|außenseite|aussenseite|vorne|kamera (?:vorderseite|vorne|außen|aussen))(?: live ansicht)?",
    "tablet": r"(?:(?:tablet|tablett) ?kamera|kamera (?:tablet|tablett))(?: live ansicht)?",
}


def classify(text):
    """Return (source, view/scene/object_in_hand); only explicit questions infer an image."""
    if not isinstance(text, str) or len(text) > 500:
        return None
    phrase = re.sub(r"[^\wäöüß]+", " ", text.casefold()).strip()
    phrase = re.sub(r"^(?:(?:hey )?jarvis |bitte )+", "", phrase)
    phrase = re.sub(r"^kannst du (?:mir )?(?:bitte )?zeigen ", "zeige ", phrase)
    phrase = re.sub(r"^(?:kannst du (?:mir )?(?:bitte )?sagen |sag mir (?:bitte )?)+", "", phrase)
    phrase = re.sub(r" bitte$", "", phrase)
    show = r"(?:(?:zeige|zeig) (?:mir )?(?:bitte )?)?"
    article = r"(?:(?:die|das|unsere|meine) )?"
    if re.fullmatch(show + r"(?:(?:alle|die|unsere|meine) )?(?:kameras|kameraübersicht|kamera übersicht)(?: anzeigen)?", phrase):
        return ("all", "view")
    if phrase in {"schau nach draußen", "schau nach draussen", "show outdoor camera"}:
        return ("outside", "view")
    for source, reference in CAMERA_REFERENCES.items():
        if re.fullmatch(show + article + reference + r"(?: anzeigen)?", phrase):
            return (source, "view")
        if (re.fullmatch(r"was (?:siehst|erkennst) du(?: (?:gerade|jetzt|denn|da))* (?:(?:auf|in|an|bei|vor|durch) (?:(?:der|die|das|unserer|meiner) )?)?" + reference + r"(?: (?:gerade|jetzt|denn|da))*", phrase)
            or re.fullmatch(r"was (?:sieht|zeigt) (?:(?:die|unsere|meine) )?" + reference, phrase)
            or re.fullmatch(r"beschreib(?:e)? (?:mir )?" + article + reference, phrase)
            or re.fullmatch(r"(?:wer|was) (?:ist|steht|sitzt|wartet|passiert|befindet sich)(?: (?:gerade|jetzt|denn|da))* (?:an|vor|auf|in|bei) (?:(?:der|unserer|meiner) )?" + reference + r"(?: (?:gerade|jetzt|denn|da|los|zu sehen))*", phrase)):
            return (source, "scene")
    groups = {
        ("tablet", "object_in_hand"): ("was halte ich in der hand", "was habe ich in der hand", "what am i holding"),
        ("tablet", "scene"): ("was siehst du", "beschreibe das kamerabild", "what do you see"),
        ("outside", "scene"): ("was ist draußen los", "was ist draussen los", "was siehst du draußen", "was siehst du draussen", "was siehst du vorne", "was ist vorne los", "was ist vor dem haus los", "what is happening outside"),
        ("door", "scene"): ("who is at the door", "who is at the front door", "what is at the front door", "what is happening at the front door"),
    }
    return next((key for key, values in groups.items() if phrase in values), None)


async def resolve_camera(relay, source, context):
    """One mapping and permission check shared by descriptions and the requesting UI."""
    entity_id = relay.camera_id() if source == "tablet" else relay.entry.options.get("vision_outside_camera" if source == "outside" else "vision_door_camera", "")
    if not entity_id or not re.fullmatch(r"camera\.[a-z0-9_]+", entity_id):
        raise ServiceValidationError("Select this camera in Jarvis integration options")
    if context.user_id:
        user = await relay.hass.auth.async_get_user(context.user_id)
        if user is None or not user.permissions.check_entity(entity_id, POLICY_READ):
            raise Unauthorized()
    return entity_id


async def resolve_camera_request(relay, selection, context):
    """Resolve only authorized configured cameras, without capturing or inferring images."""
    source, mode = selection
    sources = ("door", "outside", "tablet") if source == "all" else (source,)
    entities = []
    denied = False
    for selected in sources:
        try:
            entity_id = await resolve_camera(relay, selected, context)
        except Unauthorized:
            if source != "all":
                raise
            denied = True
            continue
        except ServiceValidationError:
            if source != "all":
                raise
            continue
        state = relay.hass.states.get(entity_id)
        if source == "all" and (state is None or selected == "tablet" and not relay.frames.fresh):
            continue
        if entity_id not in entities:
            entities.append(entity_id)
    if not entities:
        if denied:
            raise Unauthorized()
        raise ServiceValidationError("No configured camera is available")
    return {"camera_entity_id": entities[0] if len(entities) == 1 else None,
        "camera_entity_ids": entities, "source": source,
        "action": "view" if mode == "view" else "describe"}

def worker_url(entry):
    configured = entry.options.get("vision_url", "").strip()
    if not configured:
        parsed = urlsplit(QWEN_BASE)
        configured = f"http://{parsed.hostname}:10503"
    parsed = urlsplit(configured)
    try:
        address = ipaddress.ip_address(parsed.hostname)
        local = (address.is_private or address.is_loopback) and not address.is_unspecified and not address.is_multicast
        port = parsed.port
    except ValueError:
        local, port = False, None
    if parsed.scheme not in ("http", "https") or not local or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/") or port is None:
        raise ServiceValidationError("Vision URL must be an explicit local IP address and port")
    return configured.rstrip("/")

async def request(relay, path, payload=None):
    token = relay.entry.data.get("qwen_token", "")
    if len(token) < 32:
        raise ServiceValidationError("Worker token is missing")
    client = async_get_clientsession(relay.hass)
    try:
        async with client.request("POST" if payload is not None else "GET", worker_url(relay.entry) + path,
                headers={"X-API-Key": token}, json=payload, allow_redirects=False,
                timeout=aiohttp.ClientTimeout(total=15 if path == "/detect" else 110 if payload else 10)) as response:
            if response.status != 200:
                raise ServiceValidationError("Local vision worker unavailable")
            data = bytearray()
            async for block in response.content.iter_chunked(8192):
                data.extend(block)
                if len(data) > 65536:
                    raise ServiceValidationError("Vision reply too large")
            result = json.loads(data)
            if not isinstance(result, dict):
                raise ValueError()
            return result
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as error:
        raise ServiceValidationError("Local vision request failed") from error

async def health(relay):
    result = await request(relay, "/health")
    return {"ready": result.get("ready") is True, "model": str(result.get("model", ""))[:100], "busy": result.get("busy") is True,
            "tablet_available": relay.frames.fresh, "outside_camera": relay.entry.options.get("vision_outside_camera", ""),
            "door_camera": relay.entry.options.get("vision_door_camera", "")}

async def describe(relay, source, mode, context):
    if relay.vision_lock.locked():
        raise ServiceValidationError("Vision is already busy")
    async with relay.vision_lock:
        entity_id = await resolve_camera(relay, source, context)
        if mode == "ring_video" and source == "tablet":
            raise ServiceValidationError("Video analysis requires a configured Ring recording camera")
        frame_count = 1
        if source == "tablet":
            if not relay.frames.fresh:
                raise ServiceValidationError("Tablet camera has no fresh image")
            image = relay.frames.image
            captured_at = relay.frames.captured_at
        elif mode == "ring_video":
            # Independent high-resolution frames; the contact sheet is for UI only.
            from .relay_ring_video import ring_frames, ring_contact_sheet, ring_person_focus
            samples = await ring_frames(relay.hass, entity_id)
            montage, extracted = await ring_contact_sheet(relay.hass, samples)
            relay.save_ring_storyboard(source, montage, extracted)
            reports = []
            successful = []
            last_model = ""
            model_options = {
                "model": relay.entry.options.get("vision_model", "qwen3-vl:4b-instruct"),
                "keep_alive": relay.entry.options.get("model_keep_alive", 0),
                "num_ctx": relay.entry.options.get("model_num_ctx", 4096),
            }
            for index, (frame, second) in enumerate(samples, 1):
                if len(frame) > 2 * 1024 * 1024:
                    raise ServiceValidationError("Ring frame too large")
                encoded = base64.b64encode(frame).decode("ascii")
                confirmed, possible, counted, checked = False, False, 0, False
                detected_with = ""
                description = ""
                # The worker's 'objects' prompt ignored people. Use its dedicated
                # structured people detector, not the object listing, and keep a
                # non-identifying scene description for the dashboard.
                try:
                    result = await request(relay, "/detect", {"image": encoded, **model_options})
                    detection = result.get("detection", {})
                    if isinstance(detection, dict):
                        counted = detection.get("person_count", 0)
                        if type(counted) is not int or not 0 <= counted <= 10:
                            counted = 0
                        uncertain = detection.get("uncertain") is True
                        confirmed = counted > 0 and not uncertain
                        possible = counted > 0 and uncertain
                        detected_with = "whole_frame" if counted > 0 else ""
                except ServiceValidationError:
                    pass
                # Search the distant/right driveway at native resolution if the
                # full-frame detector missed people. Do not turn a vague visual
                # possibility into a confirmed detection.
                if source == "outside" and not confirmed:
                    try:
                        focus = await ring_person_focus(relay.hass, frame)
                        checked = True
                        roi = await request(relay, "/detect", {
                            "image": base64.b64encode(focus).decode("ascii"),
                            **model_options,
                        })
                        crop_result = roi.get("detection", {})
                        if isinstance(crop_result, dict):
                            crop_count = crop_result.get("person_count", 0)
                            if type(crop_count) is int and 0 < crop_count <= 10:
                                if crop_result.get("uncertain") is True:
                                    possible = True
                                else:
                                    confirmed, counted = True, max(counted, crop_count)
                                    detected_with = "right_side"
                    except (ServiceValidationError, ValueError):
                        pass
                success = False
                try:
                    result = await request(relay, "/describe", {
                        "image": encoded, "mode": "scene", **model_options,
                    })
                    answer = result.get("description")
                    if isinstance(answer, str) and answer.strip():
                        description = answer.strip()[:350]
                        last_model = str(result.get("model", ""))[:100]
                        success = True
                except ServiceValidationError:
                    pass
                if not description:
                    description = "Szenenbeschreibung nicht verfügbar"
                # The dedicated detector can return an uncertain count even
                # when the separate scene description explicitly sees someone.
                # Keep the evidence source visible; never count negated phrases.
                described_person = False
                described_uncertain = False
                word = r"\\b(?:person(?:en)?|mann|frau|mensch(?:en)?|passant(?:in|en)?|zusteller(?:in)?|postbot(?:e|in))\\b"
                for sentence in re.split(r"[.!?]+", description.casefold()):
                    if not re.search(word, sentence):
                        continue
                    if (re.search(r"\\b(?:kein(?:e|en|er|es)?|niemand|ohne)\\b.{0,55}" + word, sentence)
                            or re.search(word + r".{0,45}\\b(?:nicht|unsichtbar|unerkennbar)\\b", sentence)):
                        continue
                    if re.search(r"\\b(?:vielleicht|möglicherweise|eventuell|könnte|koennte|ähnlich|vermutlich)\\b", sentence):
                        described_uncertain = True
                    else:
                        described_person = True
                if described_person and not confirmed:
                    confirmed = True
                    detected_with = "scene_description"
                elif described_uncertain and not confirmed:
                    possible = True
                status = ("Person laut KI-Szenenbeschreibung sichtbar"
                          if confirmed and detected_with == "scene_description"
                          else "Person erkannt" if confirmed
                          else "Person möglicherweise sichtbar" if possible
                          else "Keine Person eindeutig erkannt")
                reports.append({
                    "frame": index, "second": round(second, 1),
                    "description": description,
                    "person_detected": confirmed,
                    "person_possible": possible and not confirmed,
                    "person_count": counted if detected_with != "scene_description" and confirmed else None,
                    "person_status": status,
                    "detection_source": detected_with or ("uncertain" if possible else "none"),
                    "focus_checked": checked,
                    "success": success or confirmed or possible,
                })
                if success or confirmed or possible:
                    successful.append((index, second, description))
            relay.save_ring_storyboard(source, montage, extracted, reports)
            if not successful:
                raise ServiceValidationError("No Ring frame inference succeeded")
            confirmed_frames = [str(r["frame"]) for r in reports if r["person_detected"]]
            possible_frames = [str(r["frame"]) for r in reports if r["person_possible"]]
            if confirmed_frames:
                summary = "Person erkannt in Bild " + ", ".join(confirmed_frames) + ". "
            elif possible_frames:
                summary = "Mögliche Person in Bild " + ", ".join(possible_frames) + " (unsicher). "
            else:
                summary = "Keine Person eindeutig erkannt. "
            details = " ".join(
                f"Bild {r['frame']} (+{r['second']:.1f}s): {r['person_status']}. {r['description'][:125].rstrip('.')}."
                for r in reports
            )
            combined = f"Ring-Video ({len(successful)}/{extracted} Einzelprüfungen). " + summary + details
            return {
                "description": combined[:950], "camera_entity_id": entity_id,
                "captured_at": None, "model": last_model,
                "frame_results": reports, "frames_analyzed": len(successful),
                "frames_extracted": extracted,
                "person_detected": bool(confirmed_frames),
                "person_possible": bool(possible_frames),
                "person_frames": [int(x) for x in confirmed_frames],
                "limitation": "four independent scene descriptions and structured person checks; estimates may be inaccurate",
            }
        else:
            state = relay.hass.states.get(entity_id)
            if state is None or state.state in ("unknown", "unavailable"):
                raise ServiceValidationError("Camera unavailable")
            async with asyncio.timeout(15):
                picture = await async_get_image(relay.hass, entity_id, timeout=12)
            image = picture.content
            # Normalize external camera images off-loop and bound the worker input.
            from .relay_camera import normalize
            image = await relay.hass.async_add_executor_job(normalize, image, True)
            captured_at = None
        if len(image) > 2 * 1024 * 1024:
            raise ServiceValidationError("Image too large")
        result = await request(relay, "/describe", {"image": base64.b64encode(image).decode("ascii"), "mode": "scene" if mode == "ring_video" else mode,
            "model": relay.entry.options.get("vision_model", "qwen3-vl:4b-instruct"),
            "keep_alive": relay.entry.options.get("model_keep_alive", 0),
            "num_ctx": relay.entry.options.get("model_num_ctx", 4096)})
        description = result.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ServiceValidationError("Empty vision reply")
        text = description.strip()
        if mode == "ring_video":
            text = f"Ring-Video ({frame_count} über die Aufnahmelänge verteilte Zeitpunkte): " + text
        return {"description": text[:700], "camera_entity_id": entity_id, "captured_at": captured_at,
                "model": str(result.get("model", ""))[:100], "metrics": result.get("metrics", {}),
                "frames_analyzed": frame_count,
                "limitation": "multi-frame contact sheet; may be inaccurate" if mode == "ring_video" else "single image; may be inaccurate"}
