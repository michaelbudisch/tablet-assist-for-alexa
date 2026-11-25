"""Return actual WAV audio to native Assist, never invoke Alexa notify.

The Android media output device (including a paired Bluetooth speaker)
is chosen by Android. Existing Alexa push pipelines remain independent.
"""
import asyncio
import io
import logging
import wave
from time import monotonic
from datetime import timedelta
from uuid import uuid4

import aiohttp
from homeassistant.components.tts import TextToSpeechEntity, TTSAudioResponse
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .const import MAX_WAV, settings
from .audio_dsp import PCMFilter, PROFILES, filter_wav

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    session = async_get_clientsession(hass)
    cfg = settings(entry)
    token = ""  # GPU worker is restricted to the private network.
    entities = [JarvisNativeTTS(entry.entry_id, session, "piper", "Tablet Assist Piper", "", cfg)]
    if cfg.get("gpu_base"):
        entities.append(JarvisNativeTTS(entry.entry_id, session, "qwen", "Tablet Assist Qwen", token, cfg))
    entities.append(JarvisStreamingTTS(entry.entry_id, session, "stream", "Tablet Assist Stream", token, cfg))
    async_add_entities(entities)


def valid_wav(data):
    try:
        with wave.open(io.BytesIO(data), "rb") as audio:
            return (
                0 < audio.getnframes()
                and audio.getnchannels() in (1, 2)
                and 8000 <= audio.getframerate() <= 48000
                and audio.getsampwidth() == 2
            )
    except (EOFError, wave.Error, ValueError):
        return False


class JarvisNativeTTS(TextToSpeechEntity):
    _attr_default_language = "de"
    _attr_supported_languages = ["de", "de-DE"]
    _attr_supported_options = []

    def __init__(self, entry_id, session, backend, name, token, cfg):
        self._cfg = cfg
        self._piper_url = cfg["piper_base"] + "/synthesize"
        self._gpu_base = cfg.get("gpu_base", "")
        self._attr_unique_id = entry_id + "_" + backend
        self._attr_name = name
        self._session = session
        self._backend = backend
        self._token = token
        self._retry_after = 0.0
        self._lock = asyncio.Lock()

    async def _fetch(self, url, text, timeout, token="", voice_variant=None):
        headers = {"X-API-Key": token} if token else {}
        async with self._session.post(
            url, json={"text": text, **({"voice_variant": voice_variant} if voice_variant else {})}, headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout),
            allow_redirects=False,
        ) as response:
            response.raise_for_status()
            if response.status != 200:
                raise ValueError("unexpected status")
            if response.content_length is not None and response.content_length > MAX_WAV:
                raise ValueError("oversized audio")
            data = bytearray()
            async for chunk in response.content.iter_chunked(65536):
                data.extend(chunk)
                if len(data) > MAX_WAV:
                    raise ValueError("oversized audio")
            if not valid_wav(data):
                raise ValueError("invalid audio")
            if voice_variant:
                self._voice_metadata = self._read_voice_headers(response.headers)
            return bytes(data)

    async def _qwen_ready(self):
        async with self._session.get(
            self._gpu_base + "/health",
            timeout=aiohttp.ClientTimeout(total=1.5),
            allow_redirects=False,
        ) as response:
            if response.status != 200:
                return False
            data = await response.json()
            return isinstance(data, dict) and data.get("ready") is True and not data.get("busy")

    async def async_get_tts_audio(self, message, language, options):
        text = message.strip()
        if not text or len(text) > 500:
            return None, None

        # Only one outstanding synthesis per entity. Piper and Qwen remain separate.
        async with self._lock:
            start = monotonic()
            if self._backend == "qwen" and self._gpu_base and self._cfg.get("hardware_profile") != "Homeserver" and monotonic() >= self._retry_after:
                try:
                    if await self._qwen_ready():
                        audio = await self._fetch(self._gpu_base + "/synthesize", text, 20, self._token)
                        _LOGGER.debug("Tablet TTS: Qwen in %.2fs", monotonic() - start)
                        return "wav", audio
                except (aiohttp.ClientError, TimeoutError, ValueError):
                    self._retry_after = monotonic() + 30
                    _LOGGER.debug("Tablet TTS: Qwen unavailable; Piper fallback.")
            try:
                audio = await self._fetch(self._piper_url, text, 30)
                _LOGGER.debug("Tablet TTS: Piper in %.2fs", monotonic() - start)
                return "wav", audio
            except (aiohttp.ClientError, TimeoutError, ValueError):
                _LOGGER.warning("Tablet TTS: Piper unavailable.")
                return None, None


# Separate provider: the known-working Piper and Alexa pipelines are untouched.


def streaming_header(rate):
    # The native Wyoming TTS implementation also uses a zero-length WAV
    # header for incremental PCM. Home Assistant converts it for playback.
    out = io.BytesIO()
    with wave.open(out, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
    return out.getvalue()


class JarvisStreamingTTS(JarvisNativeTTS):
    """Stream PCM from Faster Qwen; fall back only before audio is emitted."""

    _attr_supported_options = ["jarvis_cache_voice", "jarvis_cache_profile", "jarvis_cache_epoch", "jarvis_cache_sound"]

    def __init__(self, *args):
        super().__init__(*args)
        self._health = None
        self._cache_generation = 0
        self._cache_boot = uuid4().hex[:8]

    def _profile(self):
        return self._cfg.get("hardware_profile", "Automatisch")

    def _sound_profile(self):
        return self._cfg.get("live_profile", "Natürlich")

    def _requested_sound(self, options):
        value = (options or {}).get("jarvis_cache_sound", self._sound_profile())
        return value if value in PROFILES else "Natürlich"

    @property
    def default_options(self):
        # HA includes these options in its native audio-cache hash.
        return {
            "jarvis_cache_voice": self._voice_variant(),
            "jarvis_cache_profile": self._profile(),
            "jarvis_cache_sound": self._sound_profile(),
            "jarvis_cache_epoch": f"{self._cache_boot}-{self._cache_generation}",
        }

    def _set_health(self, ready):
        if ready != self._health:
            self._health = ready
            self._cache_generation += 1
            if ready:
                self._retry_after = 0.0

    async def _poll_health(self, _now=None):
        if not self._gpu_base:
            return
        try:
            async with self._session.get(
                self._gpu_base + "/health",
                timeout=aiohttp.ClientTimeout(total=0.8),
                allow_redirects=False,
            ) as response:
                payload = await response.json() if response.status == 200 else {}
                ready = isinstance(payload, dict) and payload.get("ready") is True
        except (aiohttp.ClientError, TimeoutError, ValueError):
            ready = False
        self._set_health(ready)

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(async_track_time_interval(self.hass, self._poll_health, timedelta(seconds=5)))
        await self._poll_health()

    def _requested_variant(self, options):
        value = (options or {}).get("jarvis_cache_voice", self._voice_variant())
        return value if value in {"default", *map(str, range(1, 10))} else "default"

    def _gpu_allowed(self):
        return bool(self._gpu_base and self._profile() != "Homeserver"
                    and monotonic() >= self._retry_after)

    def _voice_variant(self):
        return self._cfg.get("voice_variant", "default")

    @staticmethod
    def _read_voice_headers(headers):
        effective = headers.get("X-Jarvis-Voice-Variant", "default")
        status = headers.get("X-Jarvis-Voice-Status", "unknown")
        if effective not in {"default", *map(str, range(1, 10))}:
            effective = "default"
        meanings = {"selected": "Gespeicherte Variante", "default": "Standard (.env)",
                    "not-prepared": "Variante fehlt - Standard",
                    "mode-not-fixed": "Worker nicht im Fixed-Modus",
                    "invalid-variant": "Ungültige Variante - Standard"}
        return {"aktive_stimme": "Variante " + effective if effective != "default" else "Standard (.env)",
                "stimmstatus": meanings.get(status, "Worker ohne Varianten-Rückmeldung")}

    async def _stream_ready(self):
        async with self._session.get(
            self._gpu_base + "/health",
            timeout=aiohttp.ClientTimeout(total=1.5),
            allow_redirects=False,
        ) as response:
            if response.status != 200:
                return False
            payload = await response.json()
            return isinstance(payload, dict) and payload.get("ready") is True and not payload.get("busy")

    async def _stream_chunks(self, text, voice_variant, sound_profile):
        started = monotonic()
        dsp = None if sound_profile == 'Natürlich' else PCMFilter(sound_profile)
        if self._gpu_allowed():
            sent = False
            try:
                if not await self._stream_ready():
                    raise ValueError("GPU stream not ready")
                async with self._session.post(
                    self._gpu_base + "/stream",
                    json={"text": text, "voice_variant": voice_variant},
                    headers={},
                    timeout=aiohttp.ClientTimeout(total=90, connect=2, sock_read=15),
                    allow_redirects=False,
                ) as response:
                    response.raise_for_status()
                    if response.status != 200 or response.headers.get("X-Audio-Rate") != "24000" or response.headers.get("X-Audio-Format") != "s16le-mono":
                        raise ValueError("Invalid stream format")
                    count = 0
                    # Do not send the header until we actually receive audio.
                    async for chunk in response.content.iter_chunked(8192):
                        if not chunk:
                            continue
                        count += len(chunk)
                        if count > MAX_WAV:
                            raise ValueError("Audio limit exceeded")
                        if dsp is not None:
                            chunk = await self.hass.async_add_executor_job(dsp.process, chunk)
                            if not chunk:
                                continue
                        if not sent:
                            sent = True
                            self._attr_extra_state_attributes = {"letztes_backend": "Faster Qwen", "erste_audio_ms": round((monotonic()-started)*1000), "klangprofil": sound_profile, **self._read_voice_headers(response.headers)}
                            self.async_write_ha_state()
                            yield streaming_header(24000)
                        yield chunk
                    if not sent or count % 2:
                        raise ValueError("Empty or malformed PCM")
                    _LOGGER.debug("Tablet streaming complete after %.2fs", monotonic()-started)
                    return
            except (aiohttp.ClientError, TimeoutError, ValueError):
                self._retry_after = monotonic() + 5
                self._set_health(False)
                if sent:
                    # Never replay the entire answer in another voice mid-stream.
                    _LOGGER.warning("Tablet stream interrupted after audio began")
                    return
                _LOGGER.debug("Faster Qwen unavailable, falling back before playback")

        # Piper fallback remains a complete WAV. No duplicate spoken answer.
        try:
            audio = await self._fetch(self._piper_url, text, 30)
            if sound_profile != "Natürlich":
                audio = await self.hass.async_add_executor_job(filter_wav, audio, sound_profile)
            self._attr_extra_state_attributes = {"letztes_backend": "Piper", "erste_audio_ms": round((monotonic()-started)*1000), "klangprofil": sound_profile, "aktive_stimme": "Thorsten", "stimmstatus": "Homeserver / Reserve"}
            self.async_write_ha_state()
            yield audio
        except (aiohttp.ClientError, TimeoutError, ValueError):
            _LOGGER.warning("Tablet streaming: Piper fallback unavailable")

    async def async_stream_tts_audio(self, request):
        # Built-in Assist produces completed text. Audio itself is streamed;
        # incremental LLM text synthesis is deliberately not enabled yet.
        async def data_gen():
            parts = []
            length = 0
            async for part in request.message_gen:
                length += len(part)
                if length > 500:
                    # Drain no additional text beyond the existing size limit.
                    _LOGGER.warning("Tablet streaming: response too long")
                    return
                parts.append(part)
            text = "".join(parts).strip()
            if not text:
                return
            async with self._lock:
                async for chunk in self._stream_chunks(text, self._requested_variant(request.options), self._requested_sound(request.options)):
                    yield chunk
        return TTSAudioResponse("wav", data_gen())

    async def async_get_tts_audio(self, message, language, options):
        # Clients that need a complete file still use the accelerated engine.
        sound_profile = self._requested_sound(options)
        text = message.strip()
        if not text or len(text) > 500:
            return None, None
        async with self._lock:
            start = monotonic()
            if self._gpu_allowed():
                try:
                    if not await self._stream_ready():
                        raise ValueError("GPU stream not ready")
                    audio = await self._fetch(self._gpu_base + "/synthesize", text, 20, self._token, self._requested_variant(options))
                    if sound_profile != "Natürlich":
                        audio = await self.hass.async_add_executor_job(filter_wav, audio, sound_profile)
                    self._attr_extra_state_attributes = {"letztes_backend": "Faster Qwen (Datei)", "erste_audio_ms": round((monotonic()-start)*1000), "klangprofil": sound_profile, **getattr(self, "_voice_metadata", {})}
                    self.async_write_ha_state()
                    return "wav", audio
                except (aiohttp.ClientError, TimeoutError, ValueError):
                    self._retry_after = monotonic() + 5
                    self._set_health(False)
            try:
                audio = await self._fetch(self._piper_url, text, 30)
                if sound_profile != "Natürlich":
                    audio = await self.hass.async_add_executor_job(filter_wav, audio, sound_profile)
                self._attr_extra_state_attributes = {"letztes_backend": "Piper", "erste_audio_ms": round((monotonic()-start)*1000), "klangprofil": sound_profile, "aktive_stimme": "Thorsten", "stimmstatus": "Homeserver / Reserve"}
                self.async_write_ha_state()
                return "wav", audio
            except (aiohttp.ClientError, TimeoutError, ValueError):
                return None, None
