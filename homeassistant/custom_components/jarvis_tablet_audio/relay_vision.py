"""Local single-image vision; fixed camera mapping, authorization, bounded requests and no redirects."""
import asyncio
import base64
import ipaddress
import json
import logging
import re
from urllib.parse import urlsplit

import aiohttp
from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.components.camera import async_get_image
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er

from .const import QWEN_BASE

_LOGGER = logging.getLogger(__name__)

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


def room_camera_context(relay, context):
    from .relay_room_camera import hub
    current = hub(relay.hass)
    if current and context.user_id:
        try:
            room = current.transport.room_for(context.user_id)
        except PermissionError:
            return None, None
        return current, room
    return None, None


async def resolve_camera(relay, source, context):
    """One mapping and permission check shared by descriptions and the requesting UI."""
    entity_id = relay.camera_id() if source == "tablet" else relay.entry.options.get("vision_outside_camera" if source == "outside" else "vision_door_camera", "")
    if source == "tablet":
        current, room = room_camera_context(relay, context)
        if current:
            entity_id = current.entity_id(room, "camera") if current.store.enabled(room) else None
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
        if source == "all" and (state is None or state.state in ("unknown", "unavailable")):
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

async def _benchmark_http_error(response):
    """Report HTTP status and safe diagnostic categories, never raw worker bodies."""
    status = response.status
    tags = []
    try:
        raw = await response.content.read(8192)
        body = json.loads(raw)
        if isinstance(body, dict):
            messages = [body.get(k) for k in ("error", "detail", "message", "code", "reason")]
            details = body.get("detail")
            if isinstance(details, list):
                messages.extend(row.get(k) for row in details[:5] if isinstance(row, dict) for k in ("msg", "type"))
            for message in list(messages):
                if isinstance(message, dict):
                    messages.extend(message.get(k) for k in ("message", "code", "type", "error"))
            normalized = " ".join(v[:1000].lower() for v in messages if isinstance(v, str))
            categories = (
                ("busy/queue", ("busy", "queue", "capacity", "try again")),
                ("context limit", ("context", "num_ctx", "too many tokens", "token limit")),
                ("image input", ("image", "multimodal", "vision input", "frame")),
                ("multiple images unsupported", ("multiple images", "only one image", "single image", "one image")),
                ("model", ("model", "ollama")),
                ("memory", ("out of memory", "oom", "vram", "cuda")),
                ("validation", ("validation", "invalid", "missing", "required", "unprocessable")),
                ("timeout", ("timeout", "timed out")),
                ("payload limit", ("too large", "payload", "request size")),
            )
            tags = [label for label, terms in categories if any(term in normalized for term in terms)]
    except (ValueError, aiohttp.ClientError, asyncio.TimeoutError):
        pass
    return f"Benchmark HTTP {status}" + (": " + ", ".join(tags) if tags else "")


async def request(relay, path, payload=None, *, timeout=None):
    token = relay.entry.data.get("qwen_token", "")
    if len(token) < 32:
        raise ServiceValidationError("Worker token is missing")
    client = async_get_clientsession(relay.hass)
    try:
        async with client.request("POST" if payload is not None else "GET", worker_url(relay.entry) + path,
                headers={"X-API-Key": token}, json=payload, allow_redirects=False,
                timeout=aiohttp.ClientTimeout(total=timeout if timeout is not None else
                    (15 if path == "/detect" else 110 if payload else 10))) as response:
            if response.status != 200:
                if path == "/benchmark/sequence":
                    raise ServiceValidationError(await _benchmark_http_error(response))
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
        if path == "/benchmark/sequence":
            raise ServiceValidationError(f"Benchmark transport/response: {type(error).__name__}") from None
        raise ServiceValidationError("Local vision request failed") from error

async def health(relay):
    result = await request(relay, "/health")
    capabilities = {}
    try:
        capabilities = await request(relay, "/capabilities", timeout=5)
    except ServiceValidationError:
        pass
    return {"ready": result.get("ready") is True, "model": str(result.get("model", ""))[:100], "busy": result.get("busy") is True,
            "worker_version": str(capabilities.get("worker_version", ""))[:30],
            "sequence_api": capabilities.get("sequence_api", 0),
            "tablet_available": relay.frames.fresh, "outside_camera": relay.entry.options.get("vision_outside_camera", ""),
            "door_camera": relay.entry.options.get("vision_door_camera", "")}


_SEQUENCE_FIELDS = ("person", "vehicle", "parcel_carried", "parcel_placed", "delivery_vehicle", "delivery_clothing")


async def structured_sequence(relay, samples, options, profile):
    count = 12 if profile == "standard" else 4
    result = await request(relay, "/describe/sequence", {
        "frames": [{"second": round(second, 2), "image": base64.b64encode(frame).decode("ascii")}
                   for frame, second in samples],
        "profile": profile, "priority": "interactive", "wait_ms": 20000,
        **options,
    }, timeout=130)
    evidence, metrics, description = result.get("evidence"), result.get("metrics"), result.get("description")
    if (result.get("sequence_api") != 1 or result.get("profile") != profile
            or result.get("frames") != count or not isinstance(description, str)
            or not description.strip() or len(description) > 600
            or not isinstance(evidence, dict) or set(evidence) != set(_SEQUENCE_FIELDS)
            or any(value not in ("yes", "no", "uncertain") for value in evidence.values())
            or result.get("delivery_assessment") not in ("likely", "uncertain", "no_evidence")
            or not isinstance(metrics, dict) or metrics.get("effective_num_ctx") != 16384):
        raise ServiceValidationError("Invalid structured sequence response")
    return result


async def describe(relay, source, mode, context):
    if relay.vision_lock.locked():
        raise ServiceValidationError("Vision is already busy")
    async with relay.vision_lock:
        entity_id = await resolve_camera(relay, source, context)
        if mode == "ring_video" and source == "tablet":
            raise ServiceValidationError("Video analysis requires a configured Ring recording camera")
        frame_count = 1
        if source == "tablet":
            current, room = room_camera_context(relay, context)
            if current and not current.store.fresh(room):
                raise ServiceValidationError("Room camera has no fresh image")
            frames = current.store.frames[room] if current else relay.frames
            if not frames.fresh:
                raise ServiceValidationError("Tablet camera has no fresh image")
            image = frames.image
            captured_at = frames.captured_at
        elif mode == "ring_video":
            # Download once; joint chronological inference is the production path.
            from .relay_ring_video import (ring_recording, ring_sequence_frames,
                ring_fallback_frames, ring_contact_sheet, ring_person_focus)
            model_options = {
                "model": relay.entry.options.get("vision_model", "qwen3-vl:4b-instruct"),
                "keep_alive": relay.entry.options.get("model_keep_alive", 0),
                "num_ctx": relay.entry.options.get("model_num_ctx", 4096),
            }
            video = await ring_recording(relay.hass, entity_id)
            try:
                samples = await ring_sequence_frames(relay.hass, video)
                if len(samples) != 12:
                    raise ServiceValidationError("Expected twelve Ring frames")
                # Prefer the production structured API; keep the previously tested
                # twelve-frame endpoint as a compatibility fallback.
                try:
                    standard = await structured_sequence(relay, samples, model_options, "standard")
                    evidence = dict(standard["evidence"])
                    assessment = standard["delivery_assessment"]
                    summary = " ".join(standard["description"].split())
                    metrics = dict(standard["metrics"])
                    detail_status = "not_needed"
                    if assessment == "uncertain":
                        try:
                            from .relay_ring_video import ring_detail_frames
                            detail_samples = await ring_detail_frames(relay.hass, video)
                            detail = await structured_sequence(relay, detail_samples, model_options, "detail")
                            detail_status = "completed"
                            metrics["detail"] = detail["metrics"]
                            # Only corroborate an uncertain positive with a clear
                            # observed delivery cue. Never negate a standard
                            # observation because a smaller sample omitted it.
                            strong = ("parcel_carried", "parcel_placed", "delivery_vehicle")
                            if detail["delivery_assessment"] == "likely" and any(
                                    detail["evidence"][key] == "yes" and evidence[key] == "uncertain"
                                    for key in strong):
                                assessment = "likely"
                                for key in _SEQUENCE_FIELDS:
                                    if evidence[key] == "uncertain" and detail["evidence"][key] == "yes":
                                        evidence[key] = "yes"
                                extra = " ".join(detail["description"].split())
                                if extra != summary:
                                    summary = (summary + " Detailprüfung: " + extra)[:900]
                        except (ServiceValidationError, asyncio.TimeoutError, ValueError):
                            detail_status = "unavailable"
                    montage, extracted = await ring_contact_sheet(relay.hass, samples)
                    relay.save_ring_storyboard(source, montage, extracted, analyzed=12,
                        summary=summary, analysis_mode="structured_12")
                    return {"description": summary, "camera_entity_id": entity_id,
                            "captured_at": None, "model": standard.get("model", ""),
                            "metrics": metrics, "frame_results": [], "frames_analyzed": 12,
                            "frames_extracted": extracted, "analysis_mode": "structured_12",
                            "sequence_api": 1, "evidence": evidence,
                            "delivery_assessment": assessment, "detail_status": detail_status,
                            "limitation": "sampled images; not proof of delivery"}
                except (ServiceValidationError, asyncio.TimeoutError, ValueError) as error:
                    _LOGGER.warning("Ring structured sequence unavailable (%s); using legacy joint endpoint",
                                    type(error).__name__)
                result = await request(relay, "/benchmark/sequence", {
                    "frames": [{"second": round(second, 2),
                                "image": base64.b64encode(frame).decode("ascii")}
                               for frame, second in samples],
                    "mode": "joint", "priority": "interactive", "wait_ms": 20000,
                    **model_options,
                }, timeout=170)
                descriptions = result.get("descriptions")
                metrics = result.get("metrics")
                if (result.get("mode") != "joint" or result.get("frames") != 12
                        or not isinstance(descriptions, list) or len(descriptions) != 1
                        or not isinstance(descriptions[0], str) or not descriptions[0].strip()
                        or not isinstance(metrics, dict) or metrics.get("effective_num_ctx") != 16384):
                    raise ServiceValidationError("Invalid twelve-frame joint response")
                summary = " ".join(descriptions[0].split())[:900]
                montage, extracted = await ring_contact_sheet(relay.hass, samples)
                relay.save_ring_storyboard(source, montage, extracted, analyzed=12,
                    summary=summary, analysis_mode="joint_12")
                return {
                    "description": summary, "camera_entity_id": entity_id,
                    "captured_at": None, "model": str(result.get("model", ""))[:100],
                    "metrics": metrics, "frame_results": [],
                    "frames_analyzed": 12, "frames_extracted": extracted,
                    "analysis_mode": "joint_12",
                    "limitation": "joint description of twelve sampled frames; events between frames may be missed",
                }
            except (ServiceValidationError, asyncio.TimeoutError, ValueError) as error:
                _LOGGER.warning("Ring joint inference failed (%s); using four independent frames",
                                type(error).__name__)
            # Preserve the existing high-resolution detector/ROI fallback;
            # no second download and no additional A/B run.
            samples = await ring_fallback_frames(relay.hass, video)
            del video
            montage, extracted = await ring_contact_sheet(relay.hass, samples)
            relay.save_ring_storyboard(source, montage, extracted)
            reports = []
            successful = []
            last_model = ""
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
                word = r"\b(?:person(?:en)?|mann|frau|mensch(?:en)?|passant(?:in|en)?|zusteller(?:in)?|postbot(?:e|in))\b"
                for sentence in re.split(r"[.!?]+", description.casefold()):
                    if not re.search(word, sentence):
                        continue
                    if (re.search(r"\b(?:kein(?:e|en|er|es)?|niemand|ohne)\b.{0,55}" + word, sentence)
                            or re.search(word + r".{0,45}\b(?:nicht|unsichtbar|unerkennbar)\b", sentence)):
                        continue
                    if re.search(r"\b(?:vielleicht|möglicherweise|eventuell|könnte|koennte|ähnlich|vermutlich)\b", sentence):
                        described_uncertain = True
                    else:
                        described_person = True
                if described_person and not confirmed:
                    confirmed = True
                    detected_with = "scene_description"
                elif described_uncertain and not confirmed:
                    possible = True
                if source == "outside" and not confirmed:
                    # A focused scene description can spot a small distant
                    # person that the structured count misses in this camera.
                    try:
                        focus_image = await ring_person_focus(relay.hass, frame)
                        focus_result = await request(relay, "/describe", {
                            "image": base64.b64encode(focus_image).decode("ascii"),
                            "mode": "scene", **model_options,
                        })
                        focus_text = focus_result.get("description", "")
                        if isinstance(focus_text, str):
                            for sentence in re.split(r"[.!?]+", focus_text.casefold()):
                                if not re.search(word, sentence):
                                    continue
                                if (re.search(r"\b(?:kein(?:e|en|er|es)?|niemand|ohne)\b.{0,55}" + word, sentence)
                                        or re.search(word + r".{0,45}\b(?:nicht|unsichtbar|unerkennbar)\b", sentence)):
                                    continue
                                if re.search(r"\b(?:vielleicht|möglicherweise|eventuell|könnte|koennte|ähnlich|vermutlich)\b", sentence):
                                    possible = True
                                else:
                                    confirmed = True
                                    detected_with = "focus_description"
                                    break
                            if confirmed:
                                description = (description[:200] + " | Rechts vergrößert: " + focus_text[:220])[:350]
                    except (ServiceValidationError, ValueError):
                        pass
                status = ("Person laut KI-Szenenbeschreibung sichtbar"
                          if confirmed and detected_with == "scene_description"
                          else "Person im rechten Bildbereich beschrieben" if confirmed and detected_with == "focus_description"
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
            if not successful:
                raise ServiceValidationError("No Ring frame inference succeeded")
            confirmed_frames = [r["frame"] for r in reports if r["person_detected"]]
            possible_frames = [r["frame"] for r in reports if r["person_possible"]]
            # A compact extractive fallback: prioritize delivery evidence, then
            # people/actions, then the scene. Never invent a temporal sequence.
            sentences = {}
            for r in reports:
                if r["description"] == "Szenenbeschreibung nicht verfügbar":
                    continue
                for sentence in re.split(r"(?<=[.!?])\s+|\s+\|\s+", r["description"]):
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    folded = sentence.casefold()
                    score = (6 if re.search(r"\b(?:paket\w*|karton\w*|päckchen\w*|post\w*|dhl|lieferwagen\w*)\b", folded)
                             else 4 if re.search(r"\b(?:person\w*|mann|frau|mensch\w*|trägt|geht|hält|fährt)\b", folded)
                             else 1)
                    sentences.setdefault(folded, (score, sentence))
            selected = sorted(sentences.values(), key=lambda item: -item[0])[:3]
            combined = " ".join(s if s.endswith((".", "!", "?")) else s + "." for _, s in selected)
            if not combined:
                combined = ("Eine Person ist erkennbar." if confirmed_frames else
                            "Eine Person ist möglicherweise sichtbar." if possible_frames else
                            "Eine eindeutige Szenenbeschreibung ist nicht verfügbar.")
            relay.save_ring_storyboard(source, montage, extracted, reports,
                analyzed=len(successful), summary=combined[:700], analysis_mode="independent_4")
            return {
                "description": combined[:700], "camera_entity_id": entity_id,
                "captured_at": None, "model": last_model,
                "frame_results": reports, "frames_analyzed": len(successful),
                "frames_extracted": extracted, "analysis_mode": "independent_4",
                "person_detected": bool(confirmed_frames),
                "person_possible": bool(possible_frames),
                "person_frames": confirmed_frames,
                "limitation": "compact extract of independent scenes; no verified temporal sequence",
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
