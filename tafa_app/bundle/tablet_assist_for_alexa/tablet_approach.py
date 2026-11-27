"""Independent local face-size presence; never starts a wake or greeting automation."""
from datetime import timedelta
from homeassistant.core import callback
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.event import async_track_time_interval
from .tablet_entities import TabletMixin, setup_tablets
from .const import DOMAIN


class TabletApproach(TabletMixin, BinarySensorEntity):
    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(self, controller, identifier):
        super().__init__(controller, identifier, "approach", "Annäherung")

    @property
    def available(self):
        value = self.controller.fresh_approach(self.device_id)
        return super().available and value is not None and value["near"] is not None

    @property
    def is_on(self):
        value = self.controller.fresh_approach(self.device_id)
        return value["near"] if value else None

    @property
    def extra_state_attributes(self):
        value = self.controller.fresh_approach(self.device_id)
        return ({"face_size_percent": value["face_percent"],
                 "threshold_percent": value["threshold_percent"],
                 "source": "local_front_camera"} if value else {})


def setup_approach(hass, entry, add_entities):
    controller = hass.data[DOMAIN]["wake_devices_dynamic"]
    setup_tablets(hass, entry, add_entities,
                  lambda c, identifier: [TabletApproach(c, identifier)])
    @callback
    def expire(now):
        controller.expire_approach(now)
    entry.async_on_unload(async_track_time_interval(
        hass, expire, timedelta(seconds=2)))
