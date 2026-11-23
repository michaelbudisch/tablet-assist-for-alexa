# Ring multi-frame recordings for Jarvis / TAFA (developer preview)

Ring's `camera.haustur_letzte_aufnahme` and `camera.vorderseite_letzte_aufnahme` entities expose signed, short-lived MP4 URLs. Existing `describe_camera` calls using `mode: scene` still inspect **one still image**. The new `mode: ring_video` inspects up to four time points in the latest recording.

## Flow
1. The existing HA Ring automation checks that the activity timestamp matches the latest recording timestamp.
2. Both cameras already share the serial `script.ring_ki_bildanalyse_seriell` vision queue.
3. For `ring_video`, Jarvis fetches the current signed Ring MP4 (max 20 MiB) from a vetted Ring download host.
4. A local `ffmpeg` executable extracts approximately +3, +8, +13, and +18 seconds (fewer if the clip is short).
5. The worker receives a labeled 2×2 storyboard JPEG using its existing `scene` endpoint. This is **multi-frame still-image analysis**, not continuous video understanding.
6. The result flows into `jarvis_infobox_update`, the existing package-detection text rule, and TAFA's recognition history.

## Deployment
- Back up and update the Python integration files under `/config/custom_components/jarvis_tablet_audio/`. Do not mix versions from incompatible builds.
- `ffmpeg` must be available in the Home Assistant Core runtime's PATH; an ffmpeg binary installed elsewhere is not sufficient.
- Restart Home Assistant for the updated Python service to load.
- **Only after deployment**, change the existing `script.ring_ki_bildanalyse_seriell` service action to `mode: ring_video` instead of `mode: scene`. All other queue logic stays unchanged.
- Test `jarvis_tablet_audio.describe_camera` with `source: door` and `source: outside`, both with `mode: ring_video`. The response should include `frames_analyzed` and `limitation`.
- Finally trigger a genuine Ring event and review *TAFA → Cameras → AI recognition history*.

## Boundaries
- Cloud event notifications and expiring MP4 URLs can still cause delays or failed downloads.
- Recording URLs are taken from the configured Ring camera entity, not caller input. Clips have bounded sizes and downloads use no redirects.
- The MP4 is written only to a private temporary file for decoding and removed immediately; extracted images are not stored. Do not log signed download URLs.
- Four sampled frames can still miss a person or parcel. The model's description is an uncertain visual estimate, not identity recognition.
- Respect the privacy of everyone in the camera's field of view.

## Rollback
If MP4 retrieval or ffmpeg fails, the request reports an error rather than falsely claiming a successful multi-frame analysis. Switch the action back to `mode: scene` for the previous still-image behavior. The existing 30-minute cooldown and the disabled Echo announcement are unchanged.
