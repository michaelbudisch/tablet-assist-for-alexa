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
INFERENCE_SIZE = (960, 540)
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


async def _decode(hass, video, *, fractions=None, resolution=INFERENCE_SIZE, max_output=MAX_OUTPUT_BYTES):
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
        positions = [round((min(duration, 120.0) if fractions is not None else duration) * fraction, 3)
                     for fraction in (fractions if fractions is not None else (0.1, 0.35, 0.6, 0.85))]
        target_w, target_h = resolution
        samples = []
        total_size = 0
        for position in positions:
            proc = await asyncio.create_subprocess_exec(
                binary, "-hide_banner", "-loglevel", "error", "-nostdin",
                "-ss", str(position), "-i", video_path, "-frames:v", "1",
                "-vf", f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2",
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
            if proc.returncode != 0 or len(frame) < 100 or total_size > max_output:
                raise ServiceValidationError("Ring frame extraction failed")
            samples.append((frame, position))
        return samples
    finally:
        await asyncio.to_thread(os.unlink, video_path)


def _contact_sheet(samples):
    """Create a timestamped debug storyboard for four or twelve sampled frames."""
    selected = samples[:12]
    cols = 4 if len(selected) > 4 else 2
    tile_w = 1280 // cols
    tile_h = tile_w * 9 // 16
    rows = (len(selected) + cols - 1) // cols
    if not rows:
        raise ValueError("No decodable frames")
    canvas = Image.new("RGB", (1280, rows * (tile_h + 20)), (16, 24, 34))
    draw = ImageDraw.Draw(canvas)
    for i, (chunk, position) in enumerate(selected):
        with Image.open(io.BytesIO(chunk)) as source:
            if source.width * source.height > 1280 * 720:
                raise ValueError("Frame too large")
            frame = ImageOps.exif_transpose(source).convert("RGB")
            frame.thumbnail((tile_w, tile_h))
            x, y = (i % cols) * tile_w, (i // cols) * (tile_h + 20)
            canvas.paste(frame, (x, y + 20))
            draw.text((x + 8, y + 4), f"+{position:.1f}s", fill=(255, 255, 255))
    target = io.BytesIO()
    canvas.save(target, "JPEG", quality=80, optimize=True)
    if target.tell() > 2 * 1024 * 1024:
        raise ValueError("Contact sheet too large")
    return target.getvalue(), len(selected)


def _person_focus_region(frame):
    """Magnify the right-side driveway area; used only after full-frame detection misses."""
    with Image.open(io.BytesIO(frame)) as picture:
        picture.load()
        picture = picture.convert("RGB")
        w, h = picture.size
        if w > 1280 or h > 720:
            raise ValueError("Invalid frame resolution")
        # On the outside camera the far end of the driveway is at the right.
        # This ROI is a secondary check, never a substitute for the full frame.
        roi = picture.crop((round(w * 0.52), round(h * 0.07), w, round(h * 0.95)))
        # Upscale the distant right-edge subject for the vision worker; a
        # thumbnail call would leave the cropped person tiny.
        target_w = 960
        target_h = min(1280, round(roi.height * target_w / roi.width))
        roi = roi.resize((target_w, target_h), Image.Resampling.LANCZOS)
        result = io.BytesIO()
        roi.save(result, "JPEG", quality=88)
        return result.getvalue()


async def ring_person_focus(hass, frame):
    return await hass.async_add_executor_job(_person_focus_region, frame)


async def ring_recording(hass, camera_entity):
    """Download one approved Ring recording for joint inference and fallback."""
    state = hass.states.get(camera_entity)
    url = state.attributes.get("video_url") if state is not None else None
    if not _ring_download_url(url):
        raise ServiceValidationError("No approved Ring MP4 URL on this camera")
    return await _download(hass, url)


async def ring_fallback_frames(hass, video):
    """Four original high-resolution samples from the same downloaded clip."""
    return await _decode(hass, video)


async def ring_frames(hass, camera_entity, *, include_video=False):
    """Compatibility: four separate samples from one approved Ring recording."""
    video = await ring_recording(hass, camera_entity)
    frames = await ring_fallback_frames(hass, video)
    return (frames, video) if include_video else frames


async def ring_sequence_frames(hass, video):
    """Sample twelve chronological timestamps for joint inference."""
    fractions = (0.04, 0.10, 0.18, 0.26, 0.35, 0.44,
                 0.52, 0.60, 0.69, 0.77, 0.85, 0.95)
    return await _decode(hass, video, fractions=fractions,
                         resolution=(768, 432), max_output=7 * 1024 * 1024)


async def ring_detail_frames(hass, video):
    """Four higher-resolution samples for an uncertain structured result."""
    return await _decode(hass, video, fractions=(0.10, 0.35, 0.60, 0.85),
                         resolution=(1024, 576), max_output=5 * 1024 * 1024)


async def ring_benchmark_frames(hass, video):
    """Compatibility alias for the optional diagnostic benchmark."""
    return await ring_sequence_frames(hass, video)


async def ring_storyboard(hass, camera_entity):
    """Return (JPEG storyboard, frame count); kept for compatibility."""
    return await ring_contact_sheet(hass, await ring_frames(hass, camera_entity))


async def ring_contact_sheet(hass, frames):
    """Generate a debug-only storyboard; never used as a model input."""
    try:
        return await hass.async_add_executor_job(_contact_sheet, frames)
    except (ValueError, OSError, Image.DecompressionBombError) as exc:
        raise ServiceValidationError("Could not construct Ring video storyboard") from exc
