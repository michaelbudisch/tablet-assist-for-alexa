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


async def _download(hass, url):
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            url, allow_redirects=False,
            timeout=aiohttp.ClientTimeout(total=25, sock_read=12)
        ) as response:
            if response.status != 200:
                raise ServiceValidationError("Ring recording download unavailable")
            if response.content_length is not None and response.content_length > MAX_VIDEO_BYTES:
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
    binary = ffmpeg.get_ffmpeg_manager(hass).binary
    if not binary:
        raise ServiceValidationError("Home Assistant ffmpeg binary is unavailable")
    video_path = await asyncio.to_thread(_write_private_clip, video)
    proc = None
    try:
        # Sample about +3/+8/+13/+18 seconds, even for ordinary non-faststart MP4.
        proc = await asyncio.create_subprocess_exec(
            binary, "-hide_banner", "-loglevel", "error", "-nostdin",
            "-ss", "3", "-i", video_path,
            "-vf", "fps=1/5,scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2",
            "-frames:v", str(MAX_FRAMES),
            "-f", "image2pipe", "-vcodec", "mjpeg", "pipe:1",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, _stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError as exc:
            proc.kill()
            await proc.communicate()
            raise ServiceValidationError("Ring video decoding timed out") from exc
        if proc.returncode != 0 or not stdout or len(stdout) > MAX_OUTPUT_BYTES:
            raise ServiceValidationError("Ring video decoding failed")
        return stdout
    finally:
        await asyncio.to_thread(os.unlink, video_path)


def _contact_sheet(jpegs):
    """Re-encode only clean, bounded images into a labeled 2x2 storyboard."""
    frames = []
    for chunk in jpegs[:MAX_FRAMES]:
        with Image.open(io.BytesIO(chunk)) as source:
            if source.width * source.height > 640 * 480:
                raise ValueError("Frame too large")
            frame = ImageOps.exif_transpose(source).convert("RGB")
            frame.thumbnail(FRAME_SIZE)
            frames.append(frame.copy())
    if not frames:
        raise ValueError("No decodable frames")
    canvas = Image.new("RGB", (1280, 760), (16, 24, 34))
    draw = ImageDraw.Draw(canvas)
    for i, frame in enumerate(frames):
        x, y = (i % 2) * 640, (i // 2) * 380
        canvas.paste(frame, (x, y + 20))
        draw.text((x + 10, y + 4), f"Ring clip: approx. +{3 + 5*i}s", fill=(255, 255, 255))
    target = io.BytesIO()
    canvas.save(target, "JPEG", quality=80, optimize=True)
    if target.tell() > 2 * 1024 * 1024:
        raise ValueError("Contact sheet too large")
    return target.getvalue(), len(frames)


def _split_mjpeg(blob):
    results, index = [], 0
    while len(results) < MAX_FRAMES:
        start = blob.find(b"\xff\xd8", index)
        if start < 0:
            break
        end = blob.find(b"\xff\xd9", start + 2)
        if end < 0:
            break
        results.append(blob[start:end + 2])
        index = end + 2
    return results


async def ring_storyboard(hass, camera_entity):
    """Return (JPEG storyboard, frame count), or raise a bounded error."""
    state = hass.states.get(camera_entity)
    url = state.attributes.get("video_url") if state is not None else None
    if not _ring_download_url(url):
        raise ServiceValidationError("No approved Ring MP4 URL on this camera")
    video = await _download(hass, url)
    frames = await _decode(hass, video)
    try:
        return await hass.async_add_executor_job(_contact_sheet, _split_mjpeg(frames))
    except (ValueError, OSError, Image.DecompressionBombError) as exc:
        raise ServiceValidationError("Could not construct Ring video storyboard") from exc
