"""Bounded Ring MP4 frame sampling for the optional local vision workflow.

Ring's camera "Last recording" exposes a signed, short-lived video_url.
Only that Ring-owned URL is accepted, never a caller-supplied URL.
The signed clip is held briefly in a private temporary file, then deleted.
No extracted frames are stored.
Uses Home Assistant\'s configured ffmpeg binary.
"""
import asyncio
import io
import os
import re
import tempfile
from urllib.parse import urlsplit

import aiohttp
from PIL import Image, ImageDraw, ImageOps
from homeassistant.components import ffmpeg
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

MAX_VIDEO_BYTES = 20 * 1024 * 1024
MAX_FRAMES = 4
FRAME_SIZE = (640, 360)
MAX_OUTPUT_BYTES = 3 * 1024 * 1024


def _ring_download_url(url):
    """Accept only a Ring-created HTTPS recording URL, never arbitrary hosts."""
    if not isinstance(url, str) or len(url) > 8192:
        return False
    try:
        p = urlsplit(url)
        host = (p.hostname or "").lower()
        return (
            p.scheme == "https" and p.username is None and p.password is None
            and p.port in (None, 443) and not p.fragment
            and host.startswith("download-")
            and host.endswith(".prod.phoenix.devices.amazon.dev")
            and p.path.startswith("/v1/download/") and p.path.endswith(".mp4")
        )
    except ValueError:
        return False


def _approved_redirect(url):
    """Ring may redirect signed clips to trusted Amazon storage/CDN hosts."""
    if not isinstance(url, str) or len(url) > 8192:
        return False
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        suffixes = ("amazonaws.com", "cloudfront.net", "ring.com",
                    "ring-video.com", "devices.amazon.dev")
        return (
            parsed.scheme == "https" and parsed.port in (None, 443)
            and parsed.username is None and parsed.password is None
            and not parsed.fragment
            and any(host == suffix or host.endswith("." + suffix)
                    for suffix in suffixes)
        )
    except ValueError:
        return False


async def _download(hass, url):
    from urllib.parse import urljoin

    session = async_get_clientsession(hass)
    for redirect in range(4):
        try:
            async with session.get(
                url, allow_redirects=False,
                timeout=aiohttp.ClientTimeout(total=25, sock_read=12)
            ) as response:
                if response.status in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location", "")
                    next_url = urljoin(url, location)
                    if not location or not _approved_redirect(next_url):
                        raise ServiceValidationError("Ring recording redirect was blocked")
                    url = next_url
                    continue
                if response.status != 200:
                    raise ServiceValidationError(
                        f"Ring recording HTTP {response.status}"
                    )
                if (response.content_length is not None
                        and response.content_length > MAX_VIDEO_BYTES):
                    raise ServiceValidationError("Ring recording exceeds size limit")
                data = bytearray()
                async for chunk in response.content.iter_chunked(65536):
                    data.extend(chunk)
                    if len(data) > MAX_VIDEO_BYTES:
                        raise ServiceValidationError("Ring recording exceeds size limit")
                if len(data) < 200 or b"ftyp" not in data[:64]:
                    raise ServiceValidationError("Ring recording is not a supported MP4")
                return bytes(data)
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise ServiceValidationError("Ring recording download failed") from exc
    raise ServiceValidationError("Ring recording has too many redirects")


def _write_private_clip(video):
    # MP4 atoms can be at the end of a file, which ffmpeg cannot seek on stdin.
    # NamedTemporaryFile uses mode 0600; the clip is unlinked immediately after use.
    with tempfile.NamedTemporaryFile(prefix="ring-vision-", suffix=".mp4", delete=False) as tmp:
        try:
            tmp.write(video)
            return tmp.name
        except BaseException:
            os.unlink(tmp.name)
            raise


async def _decode(hass, video):
    """Sample across the actual clip length, including short Ring clips."""
    binary = ffmpeg.get_ffmpeg_manager(hass).binary
    if not binary:
        raise ServiceValidationError("Home Assistant ffmpeg binary is unavailable")
    video_path = await asyncio.to_thread(_write_private_clip, video)
    try:
        info = await asyncio.create_subprocess_exec(
            binary, "-hide_banner", "-i", video_path,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, details = await asyncio.wait_for(info.communicate(), timeout=8)
        except asyncio.TimeoutError as exc:
            info.kill()
            await info.communicate()
            raise ServiceValidationError("Ring clip duration lookup timed out") from exc
        match = re.search(rb"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", details[:32768])
        if not match:
            raise ServiceValidationError("Ring clip duration unavailable")
        duration = int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3])
        if not 0.2 <= duration <= 300:
            raise ServiceValidationError("Ring clip duration outside safe limits")
        # Four locations distributed through the clip. For a 6s Ring event,
        # approx. +0.6, +2.1, +3.6, +5.1s instead of only +3s.
        positions = [round(duration * fraction, 3)
                     for fraction in (0.1, 0.35, 0.6, 0.85)]
        samples = []
        total_size = 0
        for position in positions:
            proc = await asyncio.create_subprocess_exec(
                binary, "-hide_banner", "-loglevel", "error", "-nostdin",
                "-ss", str(position), "-i", video_path, "-frames:v", "1",
                "-vf", "scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2",
                "-f", "image2pipe", "-vcodec", "mjpeg", "pipe:1",
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                frame, _ = await asyncio.wait_for(proc.communicate(), timeout=9)
            except asyncio.TimeoutError as exc:
                proc.kill()
                await proc.communicate()
                raise ServiceValidationError("Ring frame extraction timed out") from exc
            total_size += len(frame)
            if proc.returncode != 0 or len(frame) < 100 or total_size > MAX_OUTPUT_BYTES:
                raise ServiceValidationError("Ring frame extraction failed")
            samples.append((frame, position))
        return samples
    finally:
        await asyncio.to_thread(os.unlink, video_path)


def _contact_sheet(samples):
    """Re-encode only bounded images into a timestamped 2x2 storyboard."""
    frames = []
    for chunk, position in samples[:MAX_FRAMES]:
        with Image.open(io.BytesIO(chunk)) as source:
            if source.width * source.height > 640 * 480:
                raise ValueError("Frame too large")
            frame = ImageOps.exif_transpose(source).convert("RGB")
            frame.thumbnail(FRAME_SIZE)
            frames.append((frame.copy(), position))
    if not frames:
        raise ValueError("No decodable frames")
    canvas = Image.new("RGB", (1280, 760), (16, 24, 34))
    draw = ImageDraw.Draw(canvas)
    for i, (frame, position) in enumerate(frames):
        x, y = (i % 2) * 640, (i // 2) * 380
        canvas.paste(frame, (x, y + 20))
        draw.text((x + 10, y + 4), f"Ring video: +{position:.1f}s", fill=(255, 255, 255))
    target = io.BytesIO()
    canvas.save(target, "JPEG", quality=80, optimize=True)
    if target.tell() > 2 * 1024 * 1024:
        raise ValueError("Contact sheet too large")
    return target.getvalue(), len(frames)


async def ring_storyboard(hass, camera_entity):
    """Return (JPEG storyboard, frame count), or raise a bounded error."""
    state = hass.states.get(camera_entity)
    url = state.attributes.get("video_url") if state is not None else None
    if not _ring_download_url(url):
        raise ServiceValidationError("No approved Ring MP4 URL on this camera")
    video = await _download(hass, url)
    frames = await _decode(hass, video)
    try:
        return await hass.async_add_executor_job(_contact_sheet, frames)
    except (ValueError, OSError, Image.DecompressionBombError) as exc:
        raise ServiceValidationError("Could not construct Ring video storyboard") from exc
