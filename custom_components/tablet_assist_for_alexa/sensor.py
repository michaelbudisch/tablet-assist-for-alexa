"""Diagnostic HA sensors for each enrolled TAFA tablet."""
from datetime import datetime, timezone
import time
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
from .tablet_entities import TabletMixin, setup_tablets

SENSORS = {
    "online": ("Verbindung", "mdi:lan-connect"),
    "wake_status": ("Rufwortstatus", "mdi:microphone"),
    "microphone": ("Mikrofonstatus", "mdi:microphone-settings"),
    "audio": ("Audioausgabe", "mdi:bluetooth-audio"),
    "bluetooth": ("Bluetooth", "mdi:bluetooth-connect"),
    "battery": ("Akku", "mdi:battery"),
    "app_version": ("App-Version", "mdi:cellphone"),
    "last_seen": ("Zuletzt gesehen", "mdi:clock-outline"),
    "last_wake": ("Letztes Rufwort", "mdi:history"),
    "display": ("Displaystatus", "mdi:tablet"),
}
class TabletSensor(TabletMixin, SensorEntity):
    def __init__(self, controller, device_id, key):
        super().__init__(controller, device_id, key, SENSORS[key][0])
        self._attr_icon = SENSORS[key][1]
        if key == "battery":
            self._attr_device_class = SensorDeviceClass.BATTERY
            self._attr_native_unit_of_measurement = "%"
        if key in ("last_seen", "last_wake"):
            self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        runtime = self.controller.telemetry.get(self.device_id, {})
        if self.key == "online":
            return "online" if runtime.get("seen", 0) and time.time() - runtime["seen"] < 45 else "offline"
        if self.key in ("last_seen", "last_wake"):
            value = runtime.get("seen" if self.key == "last_seen" else self.key)
            return datetime.fromtimestamp(value, timezone.utc) if value else None
        return runtime.get(self.key)

async def async_setup_entry(hass, entry, async_add_entities):
    setup_tablets(hass, entry, async_add_entities,
                  lambda controller, device: [TabletSensor(controller, device, key) for key in SENSORS])
    from .const import DOMAIN
    from .relay.relay_wake_devices import KEY, SIGNAL
    from homeassistant.helpers.dispatcher import async_dispatcher_send
    @callback
    def refresh_stale(now):
        async_dispatcher_send(hass, SIGNAL, None)

    entry.async_on_unload(async_track_time_interval(
        hass, refresh_stale, timedelta(seconds=30)))
