"""Pure, bounded target extraction for TAFA's native Assist switch notices.

No phrase guessing and no control actions: only explicit Home Assistant entity
targets after a paired, authenticated TAFA wake-up are eligible.
"""
import re
from collections.abc import Mapping

ENTITY = re.compile(r"^(light|switch|input_boolean)\.[a-z0-9_]+$")
DOMAINS = {"light", "switch", "input_boolean", "homeassistant"}
SERVICES = {"turn_on", "turn_off", "toggle"}
MAX_TARGETS = 6
WAKE_SECONDS = 25.0


def extract_targets(domain, service, service_data):
    if domain not in DOMAINS or service not in SERVICES or not isinstance(service_data, Mapping):
        return ()
    raw = service_data.get("entity_id")
    if not raw and isinstance(service_data.get("target"), Mapping):
        raw = service_data["target"].get("entity_id")
    if isinstance(raw, str):
        ids = [part.strip() for part in raw.split(",")]
    elif isinstance(raw, (list, tuple)):
        ids = list(raw)
    else:
        return ()
    if not 0 < len(ids) <= MAX_TARGETS:
        return ()
    result = []
    for entity_id in ids:
        if not isinstance(entity_id, str) or ENTITY.fullmatch(entity_id) is None:
            return ()
        if domain != "homeassistant" and not entity_id.startswith(domain + "."):
            return ()
        if entity_id not in result:
            result.append(entity_id)
    return tuple(result)


def expected_state(service, previous):
    if previous not in ("on", "off") or service not in SERVICES:
        return None
    if service == "turn_on":
        return "on"
    if service == "turn_off":
        return "off"
    return "off" if previous == "on" else "on"


def eligible_wake(wake, user_id, when, context_id):
    """Bind the first direct service context from a single recent paired wake."""
    if not wake or not user_id or wake.get("user_id") != user_id:
        return False
    elapsed = when - wake.get("at", -1000)
    if not 0 <= elapsed <= WAKE_SECONDS:
        return False
    owner = wake.get("context_id")
    return owner is None or owner == context_id


def confirmed_transition(entity_id, previous, current):
    """Only direct on/off changes from an existing controllable HA entity."""
    return (isinstance(entity_id, str) and ENTITY.fullmatch(entity_id) is not None
            and previous in ("on", "off") and current in ("on", "off")
            and previous != current)

def reported_native_wake(status, selected):
    """Accept only a real Android detector edge matching its HA configuration.

    The native Android Assist route reports 'detected: <word>' and does
    not invoke the old /wake API. Never infer a wake from standby phases.
    """
    if not isinstance(status, str) or not status.startswith("detected: "):
        return None
    word = status[len("detected: "):].strip()
    if word not in ("Hey Jarvis", "Jarvis", "Alexa"):
        return None
    if selected == "Alle drei" or selected == word:
        return word
    if selected == "Jarvis" and word == "Hey Jarvis":
        return word
    return None

