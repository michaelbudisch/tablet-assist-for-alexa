/* Camera preview v1.0.0: server-selected entity, only on the requesting visible dashboard. */
export async function previewCamera(voice, text, session) {
  const generation = voice.generation;
  const active = () => voice.generation === generation && voice.session === session &&
    voice.mode === "dashboard" && voice.card.isConnected && !document.hidden;
  if (!active()) return false;
  try {
    const result = await voice.h.callApi("POST", "jarvis_echo_relay/resolve_camera", {text});
    if (!active() || !/^camera\.[a-z0-9_]+$/.test(result?.camera_entity_id || "")) return false;
    session.cameraEntity = result.camera_entity_id;
    voice.lastKnowledge = null;
    voice.closeInfo?.();
    voice.card.dispatchEvent(new CustomEvent("hass-more-info", {
      detail: {entityId: result.camera_entity_id}, bubbles: true, composed: true
    }));
    return true;
  } catch {
    // A missing integration, missing camera or denied access must not interrupt the voice response.
    return false;
  }
}
