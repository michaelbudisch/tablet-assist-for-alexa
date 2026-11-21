"""Jarvis conversation router: bounded, selectable follow-up and local fallback."""
import asyncio
import logging
import re
from time import monotonic

from homeassistant.components import conversation
from homeassistant.helpers import intent

_LOGGER = logging.getLogger(__name__)
LLM_AGENT = "__JARVIS_LLM_AGENT__"
START = {"gespräch starten", "gespraech starten", "gesprächsmodus starten", "lass uns reden", "gespräch beginnen"}
STOP = {"gespräch beenden", "gespraech beenden", "gesprächsmodus beenden", "stop", "stopp", "auf wiedersehen", "danke das war alles", "danke das reicht"}
TIMEOUT = 90
MAX_SESSIONS = 50
MODE_HELPER = "input_select.jarvis_gesprachsmodus"
QUESTION = re.compile(r"^(wer|was|wie|warum|weshalb|wieso|wann|wo|woher|wohin|welch\w*|woraus|wofür|woran|womit|kannst du (?:mir )?(?:erklären|sagen|erzählen)|erklär\w*|erzähl\w*|beschreib\w*)\b")
AUTO_TIMEOUT = 90
CLOSED_TIMEOUT = 600


ANN_ROOMS = ("Büro", "Wohnzimmer", "Badezimmer", "Schlafzimmer", "Kinderzimmer")
ANN_ALIASES = {"büro":"Büro", "buero":"Büro", "buro":"Büro", "wohnzimmer":"Wohnzimmer", "badezimmer":"Badezimmer", "bad":"Badezimmer", "schlafzimmer":"Schlafzimmer", "kinderzimmer":"Kinderzimmer"}
ANN_ALL = {"alle", "allen", "alles", "überall", "ueberall", "uberall", "hausweit"}
ANN_FILLER = set("ja nein bitte doch nur sende send schicke schick sag sage spiele spiel es sie das die den dem der nachricht durchsage benachrichtigung an ans am im ins in für fuer fürs fuers zum zur und sowie auch noch lieber lautsprecher gerät geräte geraet geraete alexa alexas echo echos raum räume raeume haus ganzen gesamte gesamtes".split())
ANN_START = re.compile(r"^\s*(?:(?:hey\s+)?jarvis[\s,.:]+)?(?:(?:mach(?:e)?|erstelle(?:n|t)?|er\s+stell(?:e|t)?|stell(?:e)?|starte|send(?:e)?|schick(?:e)?|möchte|will|machst\s+du|kannst\s+du)\s+(?:bitte\s+)?)?(?:eine\s+)?(?:durchsage|benachrichtigung|ansage|ankündigung|ankuendigung|ankundigung|mitteilung)\b\s*(.*)$", re.I | re.S)
ANN_COMMAND_LIKE = re.compile(r"^(?:(?:hey )?jarvis )?(?:bitte |ich möchte |ich will |kannst du |würdest du )?(?:mach\w*|erstell\w*|er stellt|stell\w*|sende\w*|schick\w*|starte\w*|sag\w*|ankündig\w*)\b.{0,45}\b(?:durchsage|benachrichtigung|ansage|ankündigung|ankuendigung|ankundigung|mitteilung)\b", re.I)
ANN_YES = {"ja", "ja bitte", "ja mach das", "ja sende sie", "ja sende", "mach das", "senden", "absenden", "bestätigen", "durchsage bestätigen", "nachricht senden"}
ANN_CANCEL = {"abbrechen", "abbruch", "doch nicht", "nein danke", "nicht senden", "durchsage abbrechen", "nachricht abbrechen", "vergiss es", "stopp", "stop"}
ANN_NOISE = {"danke", "vielen dank", "danke schön", "gerne geschehen", "gern geschehen", "okay", "ok", "ja", "nein", "hallo", "hey jarvis"}

def ann_normal(text):
    phrase = re.sub(r"[^\wäöüß]+", " ", text.casefold()).strip()
    if re.fullmatch(r"ja(?: ja| bitte)*", phrase):
        return "ja"
    if re.fullmatch(r"nein(?: nein)*", phrase):
        return "nein"
    return phrase

def ann_rooms(text, base=ANN_ROOMS):
    """Only recognized room grammar; reject unknown tokens rather than guessing."""
    phrase = ann_normal(text)
    if not phrase:
        return None
    # Whisper sometimes renders "ins Büro" as "ein Büro". Correct only before a known room.
    phrase = re.sub(r"\b(?:ein|eins|einem|einen|eine)\s+(?=(?:" + "|".join(map(re.escape, ANN_ALIASES)) + r")\b)", "in ", phrase)
    phrase = re.sub(r"^nein\s+nicht\s+an\s+alle\s+(?:sondern\s+)?nur\s+", "nur ", phrase)
    pieces = re.split(r"\b(?:außer|ausser|ohne|aber nicht|nicht)\b", phrase)
    if len(pieces) > 2:
        return None
    def parse(part):
        tokens = part.split()
        if any(t not in ANN_ALIASES and t not in ANN_ALL and t not in ANN_FILLER for t in tokens):
            return None, False
        found = {ANN_ALIASES[t] for t in tokens if t in ANN_ALIASES}
        all_rooms = any(t in ANN_ALL for t in tokens)
        return found, all_rooms
    wanted, all_rooms = parse(pieces[0])
    if wanted is None or (all_rooms and wanted):
        return None
    if len(pieces) == 2:
        excluded, excluded_all = parse(pieces[1])
        if excluded is None or excluded_all or not excluded:
            return None
        if not wanted and not all_rooms:
            wanted = set(base)
        elif all_rooms:
            wanted = set(ANN_ROOMS)
        wanted -= excluded
    elif all_rooms:
        wanted = set(ANN_ROOMS)
    if not wanted:
        return None
    return tuple(room for room in ANN_ROOMS if room in wanted)

def ann_request(text):
    match = ANN_START.fullmatch(text.strip())
    if not match:
        return None
    tail = match.group(1).strip(" .?!")
    parts = re.split(r"\s+(?:mit (?:dem text|der nachricht)|nachricht lautet)\s*[:,.]?\s+|\s*:\s*", tail, maxsplit=1, flags=re.I)
    target = parts[0].strip(" ,.!?")
    if target == "bitte":
        target = ""
    message = parts[1].strip() if len(parts) == 2 else None
    return target, message

def ann_label(rooms):
    if tuple(rooms) == ANN_ROOMS:
        return "alle Lautsprecher"
    return " und ".join(rooms) if len(rooms) <= 2 else ", ".join(rooms[:-1]) + " und " + rooms[-1]



async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([JarvisConversation(entry.entry_id)])


class JarvisConversation(conversation.ConversationEntity):
    _attr_name = "Jarvis Gesprächsrouter"
    _attr_should_poll = False

    def __init__(self, entry_id):
        self._attr_unique_id = entry_id + "_conversation_router"
        self._sessions = {}
        self._closed = {}
        self._announcements = {}

    @property
    def supported_languages(self):
        return ["de", "de-DE"]

    def _reply(self, user_input, chat_log, message, keep=False):
        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech(message)
        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(agent_id=self.entity_id, content=message)
        )
        return conversation.ConversationResult(
            response=response, conversation_id=chat_log.conversation_id,
            continue_conversation=keep,
        )

    def _key(self, user_input, chat_log):
        return (user_input.context.user_id, user_input.device_id, chat_log.conversation_id)

    def _mode(self):
        state = self.hass.states.get(MODE_HELPER)
        return state.state if state and state.state in {"Manuell", "Intelligent", "Automatisch"} else "Manuell"

    def _remember_closed(self, key, now):
        if len(self._closed) >= MAX_SESSIONS and key not in self._closed:
            self._closed.pop(next(iter(self._closed)))
        self._closed[key] = now + CLOSED_TIMEOUT

    def _store_session(self, key, session):
        if len(self._sessions) >= MAX_SESSIONS and key not in self._sessions:
            evicted = next(iter(self._sessions))
            self._sessions.pop(evicted)
            self._remember_closed(evicted, monotonic())
        self._sessions[key] = session

    def _continue(self, key, active, mode, eligible):
        now = monotonic()
        if active is not None:
            # Changing the setting to manual also stops automatically opened sessions.
            expiry, remaining, explicit = active
            if (remaining > 1 and now < expiry and (explicit or mode != "Manuell")):
                self._store_session(key, (expiry, remaining - 1, explicit))
                return True
            self._remember_closed(key, now)
            return False
        if eligible and mode != "Manuell" and key not in self._closed:
            self._store_session(key, (now + AUTO_TIMEOUT, 3, False))
            return True
        return False


    def _ann_wait(self, key, pending, now, user_input, chat_log, message):
        if now >= pending["deadline"] or pending["turns"] >= 5:
            return self._reply(user_input, chat_log, "Die Durchsage wurde wegen Zeitüberschreitung beendet. Bitte starte sie erneut.")
        pending["expires"] = min(pending["deadline"], now + 35)
        pending["turns"] += 1
        if len(self._announcements) >= MAX_SESSIONS and key not in self._announcements:
            self._announcements.pop(next(iter(self._announcements)))
        self._announcements[key] = pending
        return self._reply(user_input, chat_log, message, True)

    async def _ann_send(self, user_input, chat_log, message, rooms):
        if not message or len(message) > 500 or not rooms or not all(room in ANN_ROOMS for room in rooms):
            return self._reply(user_input, chat_log, "Die Durchsage konnte nicht erstellt werden. Bitte starte erneut.")
        if not self.hass.services.has_service("script", "jarvis_durchsage"):
            return self._reply(user_input, chat_log, "Die Durchsagefunktion steht momentan nicht zur Verfügung.")
        try:
            await self.hass.services.async_call("script", "turn_on", {"entity_id": "script.jarvis_durchsage", "variables": {"text": message, "raeume": list(rooms)}}, blocking=False, context=user_input.context)
        except Exception:
            _LOGGER.debug("Jarvis announcement could not be scheduled")
            return self._reply(user_input, chat_log, "Die Durchsage konnte nicht gestartet werden.")
        return self._reply(user_input, chat_log, "Ich erstelle die Durchsage für " + ann_label(rooms) + ".")

    async def _ann_dialog(self, key, now, phrase, user_input, chat_log):
        self._announcements = {k: v for k, v in self._announcements.items() if v["expires"] > now}
        pending = self._announcements.pop(key, None)
        if pending:
            self._sessions.pop(key, None)
            if phrase in STOP or phrase in ANN_CANCEL:
                return self._reply(user_input, chat_log, "Durchsage abgebrochen.")
            if pending["message"] is None:
                if pending["need_target"]:
                    rooms = ann_rooms(phrase)
                    if rooms is None:
                        return self._ann_wait(key, pending, now, user_input, chat_log, "Welche Räume meinst du? Büro, Wohnzimmer, Badezimmer, Schlafzimmer, Kinderzimmer oder alle.")
                    pending["rooms"] = rooms
                    pending["need_target"] = False
                    return self._ann_wait(key, pending, now, user_input, chat_log, "Was soll ich für " + ann_label(rooms) + " durchsagen?")
                msg = re.sub(r"^\s*nachricht lautet[\s:,.–-]+", "", user_input.text.strip(), count=1, flags=re.I).strip()
                explicit = bool(re.match(r"^\s*nachricht lautet\b", user_input.text, re.I))
                if not msg or len(msg) > 500 or (not explicit and (phrase in ANN_NOISE or phrase in ANN_YES)):
                    return self._ann_wait(key, pending, now, user_input, chat_log, "Bitte sage den Nachrichtentext. Mit Abbrechen beendest du die Durchsage.")
                pending["message"] = msg
                return self._ann_wait(key, pending, now, user_input, chat_log, "Soll ich die Nachricht an " + ann_label(pending["rooms"]) + " senden?")
            # The message is now fixed. A target correction is also explicit permission to send.
            edit = re.match(r"^\s*(?:ändere|aendere|ändere bitte|aendere bitte)\s+(?:den\s+)?(?:text|nachricht)\s+(?:auf|zu)\s+(.+)$", user_input.text.strip(), re.I | re.S)
            if edit:
                msg = edit.group(1).strip()
                if not 0 < len(msg) <= 500:
                    return self._ann_wait(key, pending, now, user_input, chat_log, "Die Nachricht darf höchstens 500 Zeichen lang sein. Bitte wiederhole die Korrektur.")
                pending["message"] = msg
                if pending["need_target"]:
                    return self._ann_wait(key, pending, now, user_input, chat_log, "An welche Räume soll ich die Nachricht senden?")
                return self._ann_wait(key, pending, now, user_input, chat_log, "Text geändert. Soll ich die Nachricht an " + ann_label(pending["rooms"]) + " senden?")
            if phrase in ANN_YES and not pending["need_target"]:
                return await self._ann_send(user_input, chat_log, pending["message"], pending["rooms"])
            rooms = ann_rooms(phrase, pending["rooms"] or ANN_ROOMS)
            if rooms is not None:
                return await self._ann_send(user_input, chat_log, pending["message"], rooms)
            return self._ann_wait(key, pending, now, user_input, chat_log, "An welche Lautsprecher soll ich senden? Nenne die Räume, sage Ja für die vorgeschlagene Auswahl oder Abbrechen." if not pending["need_target"] else "Bitte nenne die gewünschten Räume oder sage Abbrechen.")
        req = ann_request(user_input.text)
        if req is None:
            if ANN_COMMAND_LIKE.match(phrase):
                self._sessions.pop(key, None)
                return self._reply(user_input, chat_log, "Ich habe eine Durchsage erkannt, aber den Befehl nicht sicher verstanden. Bitte wiederhole, an wen ich senden soll.")
            return None
        target, msg = req
        self._sessions.pop(key, None)
        rooms = ann_rooms(target) if target else ANN_ROOMS
        if msg is not None and not 0 < len(msg) <= 500:
            return self._reply(user_input, chat_log, "Bitte nenne einen Nachrichtentext mit höchstens 500 Zeichen.")
        # Complete one-sentence commands have both an explicit recipient and message.
        if target and rooms and msg:
            # A misrecognized third-person command needs explicit confirmation.
            if not re.match(r"^er\s+stellt\b", phrase):
                return await self._ann_send(user_input, chat_log, msg, rooms)
            pending = {"deadline": now + 90, "turns": 0, "rooms": rooms, "message": msg, "need_target": False}
            return self._ann_wait(key, pending, now, user_input, chat_log, "Soll ich die Nachricht an " + ann_label(rooms) + " senden?")
        pending = {"deadline": now + 90, "turns": 0, "rooms": rooms, "message": msg, "need_target": rooms is None}
        if rooms is None or msg is not None:
            return self._ann_wait(key, pending, now, user_input, chat_log, "An welche Räume soll ich die Durchsage senden? Nenne die Räume oder sage alle.")
        return self._ann_wait(key, pending, now, user_input, chat_log, "Was soll ich durchsagen?" if not target else "Was soll ich für " + ann_label(rooms) + " durchsagen?")

    async def _async_handle_message(self, user_input, chat_log):
        now = monotonic()
        self._closed = {k: v for k, v in self._closed.items() if v > now}
        for expired in [k for k, v in self._sessions.items() if v[0] <= now]:
            self._sessions.pop(expired)
            self._remember_closed(expired, now)
        key = self._key(user_input, chat_log)
        mode = self._mode()
        phrase = ann_normal(user_input.text)
        announcement = await self._ann_dialog(key, now, phrase, user_input, chat_log)
        if announcement is not None:
            return announcement
        if phrase in STOP:
            self._sessions.pop(key, None)
            self._remember_closed(key, now)
            return self._reply(user_input, chat_log, "Gespräch beendet.")
        if phrase in START:
            self._closed.pop(key, None)
            self._store_session(key, (now + TIMEOUT, 3, True))
            return self._reply(user_input, chat_log, "Gesprächsmodus aktiv. Du kannst bis zu drei Fragen stellen. Was möchtest du wissen?", True)

        active = self._sessions.pop(key, None)
        if active and mode == "Manuell" and not active[2]:
            active = None
            self._remember_closed(key, now)
        # Preserve local sentence handling if Assist forwards a request to this agent.
        # The ordinary pipeline still handles its local intents before invoking us.
        try:
            handler = getattr(conversation, "async_handle_sentence_triggers", None)
            if handler is not None:
                local = await handler(self.hass, user_input, chat_log)
                if isinstance(local, str):
                    keep = self._continue(key, active, mode, mode == "Automatisch")
                    return self._reply(user_input, chat_log, local, keep)
        except Exception:
            self._remember_closed(key, monotonic())
            _LOGGER.debug("Jarvis local sentence failed")
            return self._reply(user_input, chat_log, "Die lokale Abfrage konnte nicht abgeschlossen werden. Bitte versuche es erneut.")

        profile = self.hass.states.get("input_select.jarvis_stt_profil")
        state = self.hass.states.get(LLM_AGENT)
        if (profile and profile.state == "Homeserver") or state is None or state.state == "unavailable":
            self._remember_closed(key, monotonic())
            return self._reply(user_input, chat_log, "Meine lokale KI ist gerade nicht verfügbar. Hausdaten und bekannte Befehle funktionieren weiterhin.")
        try:
            async with asyncio.timeout(15):
                result = await conversation.async_converse(
                    hass=self.hass, text=user_input.text,
                    conversation_id=chat_log.conversation_id, context=user_input.context,
                    language=user_input.language, agent_id=LLM_AGENT,
                    device_id=user_input.device_id, satellite_id=user_input.satellite_id,
                )
            if result.response.as_dict().get("response_type") == "error":
                raise ValueError("LLM error")
        except Exception:
            self._remember_closed(key, monotonic())
            _LOGGER.debug("Jarvis AI unavailable")
            return self._reply(user_input, chat_log, "Meine lokale KI ist gerade nicht erreichbar. Hausdaten und bekannte Befehle funktionieren weiterhin.")

        eligible = mode == "Automatisch" or (mode == "Intelligent" and bool(QUESTION.match(phrase)))
        keep = self._continue(key, active, mode, eligible)
        # Native clients may reopen a short, visible listening window.
        # No microphone capture is initiated from this server integration.
        return conversation.ConversationResult(
            response=result.response, conversation_id=chat_log.conversation_id,
            continue_conversation=keep,
        )
