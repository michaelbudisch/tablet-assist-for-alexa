/* TAFA custom dashboard compatibility: route an assigned room account through
 * the existing room-scoped Echo Relay transport, including legacy admins.
 * No private dashboard configuration, tokens or household entities.
 */
export function maybeEnableProvisionedRoomAudio(card, voice, remount) {
  if (!voice || voice.roomMode || voice._tafaRoomProbeStarted ||
      !card?.isConnected || typeof card.h?.callApi !== "function") return;
  voice._tafaRoomProbeStarted = true;
  Promise.resolve()
    .then(() => card.h.callApi("POST", "jarvis_echo_relay/room_audio", { action: "status" }))
    .then(status => {
      if (!status?.room || !card.isConnected ||
          card._jarvisIntegratedVoice !== voice) return;
      voice.roomMode = true;
      voice.cfg = { ...(voice.cfg || {}), room_audio: true };
      voice.mode = "dashboard";
      voice.output = "native_audio";
      remount(card);
    })
    .catch(() => {
      // No provisioned room, unavailable endpoint, or authorization denied:
      // preserve the legacy output path. Never create or reassign rooms.
    });
}
