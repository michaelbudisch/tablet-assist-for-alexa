"""Pure, testable announcement routing and MP3 URL validation."""
import re

def audio_url(base, body):
    if not isinstance(body, dict) or body.get("success") is not True:
        raise ValueError("Invalid audio response")
    path = body.get("path", "")
    if not isinstance(path, str) or not re.fullmatch(r"/[a-f0-9]{32}\.mp3", path):
        raise ValueError("Invalid audio path")
    if not isinstance(base,str) or not re.fullmatch(r"https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?", base):
        raise ValueError("Invalid HTTPS base")
    return base + path

def allowed_targets(config, rooms, get_state):
    targets = []
    for room in rooms:
        entry = config.get(room)
        if not entry:
            continue
        blocked = False
        for field in ("dnd", "quiet"):
            if entry.get(field):
                state = get_state(entry[field])
                if state is None or state.state != "off":
                    blocked = True
        target = entry.get("notify")
        state = get_state(target) if target else None
        if not blocked and state is not None and state.state != "unavailable" and target not in targets:
            targets.append(target)
    return targets
