/* node --test tests/test_tafa_room_routing.mjs */
import test from "node:test";
import assert from "node:assert/strict";
import { maybeEnableProvisionedRoomAudio } from "../homeassistant/www/jarvis/tafa-room-routing-v0.1.0.mjs";

async function flush() {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
  await new Promise(resolve => setImmediate(resolve));
}
function setup({ admin = true, status = { room: "office", ready: true }, reject = false } = {}) {
  const calls = [];
  const voice = { roomMode: !admin, cfg: { room_audio: !admin }, mode: "dashboard", output: "native_audio" };
  const card = {
    isConnected: true,
    _jarvisIntegratedVoice: voice,
    h: { callApi: (...args) => { calls.push(args); return reject ? Promise.reject(new Error("403")) : Promise.resolve(status); } }
  };
  let mounts = 0;
  const remount = () => { mounts++; };
  return { card, voice, calls, remount, get mounts() { return mounts; } };
}

test("upgraded admin with a provisioned room uses the room player", async () => {
  const a = setup();
  maybeEnableProvisionedRoomAudio(a.card, a.voice, a.remount);
  await flush();
  assert.equal(a.calls.length, 1);
  assert.deepEqual(a.calls[0], ["POST", "jarvis_echo_relay/room_audio", { action: "status" }]);
  assert.equal(a.voice.roomMode, true);
  assert.equal(a.voice.cfg.room_audio, true);
  assert.equal(a.mounts, 1);
});

test("unassigned admin stays on the legacy route", async () => {
  const a = setup({ status: { online: false } });
  maybeEnableProvisionedRoomAudio(a.card, a.voice, a.remount);
  await flush();
  assert.equal(a.voice.roomMode, false);
  assert.equal(a.mounts, 0);
});

test("authorization error preserves legacy route without crashing", async () => {
  const a = setup({ reject: true });
  maybeEnableProvisionedRoomAudio(a.card, a.voice, a.remount);
  await flush();
  assert.equal(a.voice.roomMode, false);
  assert.equal(a.mounts, 0);
});

test("non-admin room account uses existing room logic without probing", async () => {
  const a = setup({ admin: false });
  maybeEnableProvisionedRoomAudio(a.card, a.voice, a.remount);
  await flush();
  assert.equal(a.calls.length, 0);
  assert.equal(a.mounts, 0);
});

test("does not remount a disconnected or replaced dashboard", async () => {
  let resolve;
  const a = setup();
  a.card.h.callApi = (...args) => { a.calls.push(args); return new Promise(r => { resolve = r; }); };
  maybeEnableProvisionedRoomAudio(a.card, a.voice, a.remount);
  await Promise.resolve();
  a.card.isConnected = false;
  resolve({ room: "office" });
  await flush();
  assert.equal(a.voice.roomMode, false);
  assert.equal(a.mounts, 0);
});

test("repeated renders do not schedule duplicate status probes", async () => {
  const a = setup();
  maybeEnableProvisionedRoomAudio(a.card, a.voice, a.remount);
  maybeEnableProvisionedRoomAudio(a.card, a.voice, a.remount);
  await flush();
  assert.equal(a.calls.length, 1);
  assert.equal(a.mounts, 1);
});
