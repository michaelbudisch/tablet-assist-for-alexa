"""Optional local Wyoming STT routing with a CPU fallback.

Only audio from a running Assist request is processed. No recordings or
transcripts are persisted or logged by this router.
"""
import asyncio
import io
import wave
import aiohttp
from collections.abc import AsyncIterable
import logging
from time import monotonic

from homeassistant.components import stt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)
from .const import settings
MAX_AUDIO_BYTES = 2 * 1024 * 1024
FAILOVER_SECONDS = 5


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    async_add_entities([JarvisSpeechRouter(entry.entry_id, settings(entry))])


class JarvisSpeechRouter(stt.SpeechToTextEntity):
    _attr_name = "Tablet Assist Sprachrouter"
    _attr_should_poll = False

    def __init__(self, entry_id, cfg):
        self._cfg = cfg
        self._attr_unique_id = entry_id + "_stt_router"
        self._retry_after = {}
        self._counts = {"homeserver": 0, "zusatzrechner": 0, "fallback": 0, "fehler": 0}
        self._attr_extra_state_attributes = {"letztes_backend": None, "letzte_dauer_ms": None}

    @property
    def supported_languages(self):
        return ["de"]

    @property
    def supported_formats(self):
        return [stt.AudioFormats.WAV]

    @property
    def supported_codecs(self):
        return [stt.AudioCodecs.PCM]

    @property
    def supported_bit_rates(self):
        return [stt.AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self):
        return [stt.AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self):
        return [stt.AudioChannels.CHANNEL_MONO]

    def _engine(self, entity_id, metadata):
        if not entity_id or not entity_id.startswith("stt.") or entity_id == self.entity_id:
            return None
        record = er.async_get(self.hass).async_get(entity_id)
        if record is None or record.platform != "wyoming":
            return None
        engine = stt.async_get_speech_to_text_entity(self.hass, entity_id)
        if engine is None or not engine.available or not engine.check_metadata(metadata):
            return None
        return engine

    async def _gpu_reachable(self):
        # Only the explicitly configured GPU endpoint; no scanning or audio.
        host = self._cfg.get("gpu_stt_host")
        if not host:
            return True
        try:
            async with asyncio.timeout(0.8):
                _, writer = await asyncio.open_connection(host, self._cfg.get("gpu_stt_port", 10300))
                writer.close()
                await writer.wait_closed()
            return True
        except (OSError, TimeoutError):
            return False

    @staticmethod
    def _ok(result):
        return bool(result and result.result == stt.SpeechResultState.SUCCESS
                    and isinstance(result.text, str) and result.text.strip())

    async def _call(self, engine, metadata, stream, seconds):
        if engine is None:
            return None
        try:
            async with asyncio.timeout(seconds):
                return await engine.internal_async_process_audio_stream(metadata, stream)
        except Exception:
            # Never log audio, transcripts or exception payloads.
            return None

    async def _built_in_stt(self, stream):
        """Use the bundled TAFA App CPU recognizer when no Wyoming STT is configured."""
        endpoint = self._cfg.get("piper_base", "").rstrip("/")
        if not endpoint:
            return None
        chunks = []
        length = 0
        try:
            async with asyncio.timeout(55):
                async for chunk in stream:
                    length += len(chunk)
                    if length > MAX_AUDIO_BYTES:
                        return None
                    chunks.append(bytes(chunk))
            if not chunks:
                return None
            data = b"".join(chunks)
            if not data.startswith(b"RIFF"):
                buf = io.BytesIO()
                with wave.open(buf, "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(16000)
                    wav.writeframes(data)
                data = buf.getvalue()
            session = async_get_clientsession(self.hass)
            async with session.post(endpoint + "/stt", data=data,
                    headers={"Content-Type": "audio/wav"},
                    timeout=aiohttp.ClientTimeout(total=55),
                    allow_redirects=False) as response:
                if response.status != 200:
                    return None
                result = await response.json()
                if isinstance(result, dict) and isinstance(result.get("text"), str) and result["text"].strip():
                    return stt.SpeechResult(result["text"].strip(), stt.SpeechResultState.SUCCESS)
        except (aiohttp.ClientError, TimeoutError, ValueError, OSError):
            pass
        return None

    def _finish(self, name, start, result, fallback=False):
        self._counts[name] += 1
        if fallback:
            self._counts["fallback"] += 1
        if not self._ok(result):
            self._counts["fehler"] += 1
        self._attr_extra_state_attributes = {
            "letztes_backend": name,
            "letzte_dauer_ms": round((monotonic() - start) * 1000),
            **self._counts,
        }
        self.async_write_ha_state()
        if self._ok(result):
            return result
        return stt.SpeechResult(None, stt.SpeechResultState.ERROR)

    async def async_process_audio_stream(self, metadata, stream: AsyncIterable[bytes]):
        start = monotonic()
        base_id = self._cfg.get("cpu_stt", "")
        base = self._engine(base_id, metadata)
        mode = self._cfg.get("hardware_profile", "Automatisch")
        target_id = self._cfg.get("gpu_stt", "")
        enhanced = None
        if (mode == "Automatisch" and target_id and target_id != base_id
                and monotonic() >= self._retry_after.get(target_id, 0)):
            enhanced = self._engine(target_id, metadata)

        # Probe the known GPU socket before buffering or waiting for ASR.
        unavailable = False
        if enhanced is not None and not await self._gpu_reachable():
            enhanced = None
            unavailable = True
            self._retry_after[target_id] = monotonic() + FAILOVER_SECONDS

        # Fast path: original streaming behavior on the homeserver.
        if enhanced is None:
            result = await self._call(base, metadata, stream, 60) if base is not None else await self._built_in_stt(stream)
            return self._finish("homeserver", start, result, fallback=unavailable)

        # Buffer only the bounded active request in RAM, so a failure can
        # replay that request to the base engine without asking the user again.
        chunks = []
        size = 0
        try:
            async with asyncio.timeout(45):
                async for chunk in stream:
                    size += len(chunk)
                    if size > MAX_AUDIO_BYTES:
                        break
                    chunks.append(bytes(chunk))
        except TimeoutError:
            return self._finish("zusatzrechner", start, None)
        if size > MAX_AUDIO_BYTES or not chunks:
            return self._finish("zusatzrechner", start, None)

        async def replay():
            for chunk in chunks:
                yield chunk

        result = await self._call(enhanced, metadata, replay(), 8)
        if self._ok(result):
            self._retry_after.pop(target_id, None)
            return self._finish("zusatzrechner", start, result)
        self._retry_after[target_id] = monotonic() + FAILOVER_SECONDS
        _LOGGER.debug("Jarvis STT: Zusatzrechner nicht erfolgreich, CPU-Fallback.")
        result = await self._call(base, metadata, replay(), 25) if base is not None else await self._built_in_stt(replay())
        return self._finish("homeserver", start, result, fallback=True)
