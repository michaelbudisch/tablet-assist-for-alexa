"""Opt-in automatic Ring A/B test after normal Ring inference.

Uses the SAME signed Ring clip already downloaded for normal analysis.
Runs in the background with bounded, sequential calls to the existing
local vision worker. No extra container, public upload or announcements.
"""
import asyncio
import base64
from datetime import datetime, timezone
from time import monotonic

from homeassistant.exceptions import ServiceValidationError

ACTIVE = "input_boolean.jarvis_ring_a_b_test_aktiv"
COUNTER = "input_number.jarvis_ring_a_b_testlaufe"
STATUS = "input_text.jarvis_ring_a_b_status"
MAX_RUNS = 4
COOLDOWN_SECONDS = 20 * 60
SAMPLES_FOUR = (1, 4, 7, 10)
SAMPLES_EIGHT = (0, 1, 3, 4, 6, 7, 9, 10)


def schedule(relay, *, source, camera_entity_id, video, production_ms):
    """Schedule only one non-urgent benchmark at a time; never delay Ring UI."""
    if not relay.hass.states.is_state(ACTIVE, "on"):
        return False
    if getattr(relay, "ring_ab_running", False):
        return False
    count = relay.hass.states.get(COUNTER)
    if count is None or count.state in ("unknown", "unavailable"):
        return False
    try:
        if int(float(count.state)) >= MAX_RUNS:
            return False
    except ValueError:
        return False
    last_start = getattr(relay, "ring_ab_last_started", 0.0)
    if last_start and monotonic() - last_start < COOLDOWN_SECONDS:
        return False
    if source not in ("outside", "door") or type(video) is not bytes:
        return False

    relay.ring_ab_running = True
    relay.ring_ab_last_started = monotonic()
    try:
        relay.hass.async_create_task(_run(
            relay, source=source, entity=camera_entity_id,
            video=video, production_ms=production_ms,
        ))
    except Exception:
        relay.ring_ab_running = False
        return False
    return True


async def _set_status(relay, text):
    try:
        await relay.hass.services.async_call(
            "input_text", "set_value",
            {"entity_id": STATUS, "value": str(text)[:255]},
            blocking=True,
        )
    except Exception:
        # Missing status helper must never disrupt a Ring notification.
        pass


async def _run(relay, *, source, entity, video, production_ms):
    from .relay_ring_video import ring_benchmark_frames
    from .relay_vision import request

    report = {
        "source": source, "camera": entity,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "production_ms": production_ms,
        "tests": [],
        "status": "running",
    }
    try:
        # In-memory video is held only until extra frames are extracted.
        await _set_status(relay, f"Ring A/B {source}: entnehme 12 Frames aus vorhandener Aufnahme")
        samples = await ring_benchmark_frames(relay.hass, video)
        del video
        if len(samples) != 12:
            raise ServiceValidationError("Ring benchmark did not extract 12 frames")
        groups = (
            ("4 einzeln", "independent", SAMPLES_FOUR),
            ("4 gemeinsam", "joint", SAMPLES_FOUR),
            ("8 gemeinsam", "joint", SAMPLES_EIGHT),
            ("12 gemeinsam", "joint", tuple(range(12))),
        )
        options = relay.entry.options
        model = options.get("vision_model", "qwen3-vl:4b-instruct")
        # Keep the same 4096-token context across all four alternatives.
        for label, mode, indices in groups:
            if not relay.hass.states.is_state(ACTIVE, "on"):
                report["status"] = "cancelled"
                break
            await _set_status(relay, f"Ring A/B {source}: prüfe {label}")
            frames = [{
                "second": round(samples[i][1], 2),
                "image": base64.b64encode(samples[i][0]).decode("ascii"),
            } for i in indices]
            started = monotonic()
            try:
                result = await request(
                    relay, "/benchmark/sequence", {
                        "frames": frames, "mode": mode,
                        "model": model,
                        "keep_alive": options.get("model_keep_alive", 300),
                        "num_ctx": options.get("model_num_ctx", 4096),
                        "priority": "background",
                        "wait_ms": 0,
                    }, timeout=490 if mode == "independent" else 170,
                )
                values = result.get("metrics", {})
                if result.get("mode") != mode or result.get("frames") != len(indices):
                    raise ServiceValidationError("Invalid benchmark result")
                descriptions = result.get("descriptions", [])
                report["tests"].append({
                    "name": label, "mode": mode,
                    "frames": len(indices), "ok": True,
                    "wall_ms": round((monotonic() - started) * 1000, 1),
                    "worker_ms": values.get("total_ms"),
                    "inference_ms": values.get("inference_ms"),
                    "descriptions": [
                        str(x)[:450] for x in descriptions if isinstance(x, str)
                    ][:4],
                })
            except (ServiceValidationError, asyncio.TimeoutError):
                report["tests"].append({
                    "name": label, "mode": mode,
                    "frames": len(indices), "ok": False,
                    "wall_ms": round((monotonic() - started) * 1000, 1),
                    "error": "Vision worker unavailable or busy",
                })
                # One failed mode means skip remaining modes rather than
                # repeatedly hammering a busy production GPU.
                report["status"] = "partial"
                break
        if report["status"] == "running":
            report["status"] = ("complete" if len(report["tests"]) == 4
                                and all(row["ok"] for row in report["tests"])
                                else "partial")
    except Exception:
        report["status"] = "error"
        # Don't expose signed Ring URLs or lower-level worker exceptions.
        report["error"] = "Frames konnten nicht für den Benchmark verarbeitet werden"
    finally:
        relay.ring_ab_running = False
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        history = getattr(relay, "ring_ab_reports", None)
        if history is None:
            history = relay.ring_ab_reports = []
        history.append(report)
        del history[:-5]
        completed = relay.hass.states.get(COUNTER)
        try:
            new_count = min(MAX_RUNS, int(float(completed.state)) + 1)
            await relay.hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": COUNTER, "value": new_count},
                blocking=True,
            )
            if new_count >= MAX_RUNS:
                await relay.hass.services.async_call(
                    "input_boolean", "turn_off",
                    {"entity_id": ACTIVE}, blocking=True,
                )
        except (ValueError, AttributeError, ServiceValidationError):
            new_count = None
        lines = [row for row in report["tests"] if row.get("ok")]
        speeds = " / ".join(
            f"{row['frames']}{'e' if row['mode'] == 'independent' else 'g'}: "
            f"{row['wall_ms'] / 1000:.1f}s"
            for row in lines
        )
        summary = (
            f"Ring A/B {source}: {report['status']}, Produktion "
            f"{production_ms / 1000:.1f}s; {speeds or 'kein gültiger Lauf'}"
            + (f"; {new_count}/{MAX_RUNS}" if new_count is not None else "")
        )
        await _set_status(relay, summary)
        relay.hass.bus.async_fire("jarvis_ring_ab_result", {
            "camera_source": source, "status": report["status"],
            "production_ms": production_ms, "times": [{
                "frames": row["frames"], "mode": row["mode"],
                "wall_ms": row["wall_ms"],
            } for row in lines],
        })


def status(relay):
    """Read-only in-memory report; no recording or stills are ever returned."""
    value = relay.hass.states.get(COUNTER)
    return {
        "active": relay.hass.states.is_state(ACTIVE, "on"),
        "running": getattr(relay, "ring_ab_running", False),
        "runs": value.state if value else None,
        "max_runs": MAX_RUNS,
        "results": list(reversed(getattr(relay, "ring_ab_reports", []))),
    }
