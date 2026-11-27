"""Choose whether a spoken reply invites another user turn.

Only the Android client actually opens a microphone; this function controls
Home Assistant's ConversationResult.continue_conversation flag.
"""
import re

_PROMPT = re.compile(
    r"(?:^|[.!?]\s+)(?:bitte\s+)?(?:sage|sag|nenne|nenn|wähle|waehle|"
    r"antworte|entscheide)\b[^.!?]{0,130}[.!]?$",
    re.IGNORECASE,
)
_GENERIC = re.compile(
    r"(?:hast du noch (?:weitere )?fragen|"
    r"kann ich (?:dir|ihnen) sonst noch helfen)\s*\?$",
    re.IGNORECASE,
)

def reply_expects_answer(speech):
    """Require an actual closing question or an explicit answer request."""
    if not isinstance(speech, str):
        return False
    text = " ".join(speech.strip().split())
    if not text:
        return False
    tail = text[-240:]
    if tail.endswith(("?", "？")):
        return not bool(_GENERIC.search(tail))
    return bool(_PROMPT.search(tail))

def wants_followup(mode, speech, delegated=False):
    """Manual never starts generic auto-dialog; Intelligent waits for a prompt."""
    if mode == "Automatisch":
        return True
    if mode != "Intelligent":
        return False
    return bool(delegated) or reply_expects_answer(speech)
