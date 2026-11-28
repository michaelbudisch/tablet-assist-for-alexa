"""TAFA conversation router: bounded, selectable follow-up and local fallback."""
import asyncio
import logging
import re
from time import monotonic

from homeassistant.components import conversation
from homeassistant.helpers import intent

_LOGGER = logging.getLogger(__name__)
from .const import DOMAIN, settings
from .local_intents import classify, SEARCH_PATTERN, FOLLOW_PATTERN
from .followup_decision import wants_followup
SEARCH_CONTINUATION = re.compile(r"^(?:zurück|zurueck|zeige|zeig|lies|lese|erzähl|erzaehl|erkläre|erklaere|fass|fasse)\b", re.I)
START = {"gespräch starten", "gespraech starten", "gesprächsmodus starten", "lass uns reden", "gespräch beginnen"}
STOP = {"gespräch beenden", "gespraech beenden", "gesprächsmodus beenden", "stop", "stopp", "auf wiedersehen", "danke das war alles", "danke das reicht"}
TIMEOUT = 90
MAX_SESSIONS = 50
AUTO_TIMEOUT = 90
CLOSED_TIMEOUT = 600


ANN_ROOMS = ("Büro", "Wohnzimmer", "Badezimmer", "Schlafzimmer", "Kinderzimmer")
ANN_ALIASES = {"büro":"Büro", "buero":"Büro", "buro":"Büro", "wohnzimmer":"Wohnzimmer", "badezimmer":"Badezimmer", "bad":"Badezimmer", "schlafzimmer":"Schlafzimmer", "kinderzimmer":"Kinderzimmer"}
ANN_ALL = {"alle", "allen", "alles", "überall", "ueberall", "uberall", "hausweit"}
ANN_FILLER = set("ja nein bitte doch nur sende send schicke schick sag sage spiele spiel es sie das die den dem der nachricht durchsage benachrichtigung an ans am im ins in für fuer fürs fuers zum zur und sowie auch noch lieber lautsprecher gerät geräte geraet geraete alexa alexas echo echos raum räume raeume haus ganzen gesamte gesamtes".split())
ANN_START = re.compile(r"^\s*(?:(?:hey\s+)?(?:jarvis|tafa)[\s,.:]+)?(?:(?:mach(?:e)?|erstelle(?:n|t)?|er\s+stell(?:e|t)?|stell(?:e)?|starte|send(?:e)?|schick(?:e)?|möchte|will|machst\s+du|kannst\s+du)\s+(?:bitte\s+)?)?(?:eine\s+)?(?:durchsage|benachrichtigung|ansage|ankündigung|ankuendigung|ankundigung|mitteilung)\b\s*(.*)$", re.I | re.S)
ANN_COMMAND_LIKE = re.compile(r"^(?:(?:hey )?(?:jarvis|tafa) )?(?:bitte |ich möchte |ich will |kannst du |würdest du )?(?:mach\w*|erstell\w*|er stellt|stell\w*|sende\w*|schick\w*|starte\w*|sag\w*|ankündig\w*)\b.{0,45}\b(?:durchsage|benachrichtigung|ansage|ankündigung|ankuendigung|ankundigung|mitteilung)\b", re.I)
ANN_YES = {"ja", "ja bitte", "ja mach das", "ja sende sie", "ja sende", "mach das", "senden", "absenden", "bestätigen", "durchsage bestätigen", "nachricht senden"}
ANN_CANCEL = {"abbrechen", "abbruch", "doch nicht", "nein danke", "nicht senden", "durchsage abbrechen", "nachricht abbrechen", "vergiss es", "stopp", "stop"}
ANN_NOISE = {"danke", "vielen dank", "danke schön", "gerne geschehen", "gern geschehen", "okay", "ok", "ja", "nein", "hallo", "hey jarvis", "hey tafa"}

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



def _agent_is_usable(agent, state, own_entity_id):
    """Unknown means a conversation entity has not handled its first message.

    HA's ConversationEntity state is the last-message timestamp; its normal
    initial state is 'unknown'. Only a missing or explicitly unavailable
    agent must prevent forwarding to its conversation handler.
    """
    return bool(agent and agent != own_entity_id and
                state is not None and state.state != "unavailable")


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([TafaConversation(entry.entry_id, settings(entry), hass.data[DOMAIN][entry.entry_id])])


class TafaConversation(conversation.ConversationEntity):
    _attr_name = "Tablet Assist Gesprächsrouter"
    _attr_should_poll = False

    def __init__(self, entry_id, cfg, data):
        self._local_data = data
        self._cfg = cfg
        self._attr_unique_id = entry_id + "_conversation_router"
        self._sessions = {}
        self._closed = {}
        self._announcements = {}

    @property
    def supported_languages(self):
        return ["de", "de-DE"]

    def _announce_response(self, user_input, message, chat_log=None):
        """Short-lived HA event for authorized dashboards, including native Android Assist.

        The entity mapping is shared with voice queries. No household IDs are
        hard-coded into the distributable dashboard; the frontend only reads
        configured, permission-checked Home Assistant states.
        """
        if not isinstance(message, str) or not message.strip():
            return
        try:
            text = str(user_input.text or "")[:240]
            topic = classify(text)
            category = topic if topic not in (None, "ambiguous", "bring_list") else "knowledge"
            sources = dict(self._local_data.sources)
            event = {"question": text, "reply": message[:1800], "topic": category,
                     "user_id": getattr(user_input.context, "user_id", None),
                     "device_id": user_input.device_id or "", "sources": sources}
            search_request = bool(SEARCH_PATTERN.match(text.strip()))
            follow_request = bool(FOLLOW_PATTERN.match(text.strip()))
            more_search = bool(SEARCH_CONTINUATION.match(text.strip()))
            if search_request or follow_request or more_search:
                search = self._local_data.search_context(
                    (getattr(user_input.context, "user_id", None), user_input.device_id,
                     chat_log.conversation_id if chat_log is not None else None))
                if search_request or search:
                    event["topic"] = "search"
                    event["results"] = search.get("results", [])[:10] if search else []
                    if search and (follow_request or more_search):
                        event["selected_index"] = search.get("selected", -1)
                        if more_search and search.get("article"):
                            event["article"] = search["article"]
            self.hass.bus.async_fire("tafa_assist_response", event,
                                     context=user_input.context)
        except Exception:
            _LOGGER.debug("TAFA dashboard response event could not be emitted", exc_info=True)

    def _reply(self, user_input, chat_log, message, keep=False):
        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech(message)
        self._announce_response(user_input, message, chat_log)
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
        return self._cfg.get("conversation_mode", "Manuell")

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
            if (remaining > 1 and now < expiry
                    and (explicit or (mode != "Manuell" and eligible))):
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
        if not self._cfg.get("public_audio_base") or not self._cfg.get("rooms") or not self.hass.services.has_service(DOMAIN, "announce"):
            return self._reply(user_input, chat_log, "Die Durchsagefunktion steht momentan nicht zur Verfügung.")
        try:
            await self.hass.services.async_call(DOMAIN, "announce", {"text": message, "rooms": list(rooms)}, blocking=True, context=user_input.context)
        except Exception:
            _LOGGER.debug("TAFA announcement could not be scheduled")
            return self._reply(user_input, chat_log, "Die Durchsage konnte nicht gestartet werden.")
        return self._reply(user_input, chat_log, "Ich habe die Durchsage an die freigegebenen Lautsprecher übergeben.")

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
            self._local_data.followups.clear(key)
            self._local_data.reminders.pending.pop(key, None)
            return announcement
        try:
            reminder = await self._local_data.reminders.handle(key, user_input.text, phrase)
            if reminder is not None:
                self._local_data.followups.clear(key)
                self._sessions.pop(key, None)
                return self._reply(user_input, chat_log, *reminder)
        except Exception:
            _LOGGER.debug("Tablet Assist reminder operation failed")
            return self._reply(user_input, chat_log, "Die Erinnerung konnte nicht bestätigt werden.")
        if phrase in STOP:
            self._local_data.followups.clear(key)
            self._sessions.pop(key, None)
            self._remember_closed(key, now)
            return self._reply(user_input, chat_log, "Gespräch beendet.")
        if phrase in START:
            self._local_data.followups.clear(key)
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
            # A legacy HA conversation trigger may still refer to an obsolete
            # oil tank sensor. For an explicitly configured, read-only TAFA oil
            # source, let the native local-data router answer first. Never
            # disable or modify the user's existing HA automations.
            prefer_tafa_oil = (
                classify(user_input.text) == "heizoel"
                and bool(self._local_data.sources.get("heizoel"))
            )
            # Read-only search and its numbered follow-ups take precedence
            # over legacy sentence automations while the search context exists.
            prefer_tafa_search = bool(SEARCH_PATTERN.match(user_input.text.strip()))
            if not prefer_tafa_search and self._local_data.search_context(key):
                prefer_tafa_search = bool(FOLLOW_PATTERN.match(user_input.text.strip())
                                          or SEARCH_CONTINUATION.match(user_input.text.strip()))
            if handler is not None and not prefer_tafa_oil and not prefer_tafa_search:
                local = await handler(self.hass, user_input, chat_log)
                if isinstance(local, str):
                    self._local_data.followups.clear(key)
                    keep = self._continue(key, active, mode, mode == "Automatisch")
                    return self._reply(user_input, chat_log, local, keep)
        except Exception:
            self._remember_closed(key, monotonic())
            _LOGGER.debug("TAFA local sentence failed")
            return self._reply(user_input, chat_log, "Die lokale Abfrage konnte nicht abgeschlossen werden. Bitte versuche es erneut.")

        try:
            async with asyncio.timeout(15):
                result = await self._local_data.handle(key, user_input.text, user_input.context)
            if result is not None:
                message, keep = result
                eligible = wants_followup(mode, message)
                if not keep:
                    keep = self._continue(key, active, mode, eligible)
                if not keep:self._local_data.followups.clear(key)
                return self._reply(user_input, chat_log, message, keep)
        except Exception:
            self._local_data.followups.clear(key)
            _LOGGER.debug("Tablet Assist local data operation failed")
            return self._reply(user_input, chat_log, "Die lokale Abfrage konnte nicht bestätigt werden. Bitte überprüfe die Datenquelle.")

        agent = self._cfg.get("llm_agent")
        if not agent:
            self._remember_closed(key, monotonic())
            return self._reply(
                user_input, chat_log,
                "Der KI-Gesprächsassistent ist in TAFA noch nicht eingerichtet. "
                "Unter Apps, TAFA, Konfiguration kannst du den Ollama-Agenten auswählen."
            )
        state = self.hass.states.get(agent)
        # Hardware profile controls TTS routing (Qwen/Piper), not whether
        # a configured HA conversation agent may handle a question.
        # 'unknown' is the normal state of an unused ConversationEntity.
        if not _agent_is_usable(agent, state, self.entity_id):
            self._remember_closed(key, monotonic())
            return self._reply(
                user_input, chat_log,
                "Der ausgewählte KI-Gesprächsassistent ist momentan nicht verfügbar. "
                "Bitte prüfe den Ollama-Agenten und das Hardwareprofil in TAFA."
            )
        try:
            async with asyncio.timeout(15):
                result = await conversation.async_converse(
                    hass=self.hass, text=user_input.text,
                    conversation_id=chat_log.conversation_id, context=user_input.context,
                    language=user_input.language, agent_id=agent,
                    device_id=user_input.device_id, satellite_id=user_input.satellite_id,
                )
            if result.response.as_dict().get("response_type") == "error":
                raise ValueError("LLM error")
        except Exception:
            self._remember_closed(key, monotonic())
            _LOGGER.debug("TAFA AI unavailable")
            return self._reply(user_input, chat_log, "Meine lokale KI ist gerade nicht erreichbar. Hausdaten und bekannte Befehle funktionieren weiterhin.")

        # Intelligent mode must follow the assistant's invitation, not
        # whether the user's original sentence happened to be a question.
        try:
            speech = result.response.as_dict().get("speech", {}).get("plain", {}).get("speech", "")
        except Exception:
            speech = ""
        eligible = wants_followup(mode, speech, getattr(result, "continue_conversation", False))
        keep = self._continue(key, active, mode, eligible)
        try:
            if isinstance(speech, str):
                self._announce_response(user_input, speech, chat_log)
        except Exception:
            _LOGGER.debug("TAFA LLM visual response unavailable", exc_info=True)
        return conversation.ConversationResult(
            response=result.response, conversation_id=chat_log.conversation_id,
            continue_conversation=keep,
        )
