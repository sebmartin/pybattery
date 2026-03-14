from __future__ import annotations
import adafruit_dht
import board
from datetime import datetime
from typing import Any, Dict, Literal, Optional, Protocol, runtime_checkable

from pybattery.models.config import DeviceConfig
from pybattery.models.device import Device
from pybattery.rpi import fake_devices_allowed, is_raspberry_pi


@runtime_checkable
class DhtSensor(Protocol):
    """Protocol for a DHT sensor object (real adafruit_dht or fake)."""

    @property
    def temperature(self) -> Optional[float]: ...
    @property
    def humidity(self) -> Optional[float]: ...
    def exit(self) -> None: ...


class AdafruitHardware:
    """DHT hardware using adafruit_dht (no daemon required).

    Accepts a sensor (real or fake) for dependency injection.
    """

    def __init__(self, sensor: DhtSensor):
        self._sensor = sensor

    def read(self) -> Optional[Dict[str, float]]:
        """Return {"temperature": float, "humidity": float} or None on failure."""
        temperature = self._sensor.temperature
        humidity = self._sensor.humidity
        if temperature is None or humidity is None:
            return None
        return {"temperature": temperature, "humidity": humidity}


class DhtDevice(Device):
    """Read temperature and humidity from a DHT11/DHTXX sensor."""

    def __init__(
        self, config: DeviceConfig, hardware: Optional[AdafruitHardware] = None
    ) -> None:
        super().__init__(config)
        self.gpio = config.args.get("gpio", 13)
        self.model: Literal["DHT11", "DHTXX"] = config.args.get("model", "DHT11")
        if hardware is not None:
            self._hardware = hardware
        elif is_raspberry_pi():
            pin = getattr(board, f"D{self.gpio}")
            sensor = (
                adafruit_dht.DHT22(pin)
                if self.model == "DHTXX"
                else adafruit_dht.DHT11(pin)
            )
            self._hardware = AdafruitHardware(sensor=sensor)
        elif fake_devices_allowed():
            from pybattery.device_drivers.dht.fakes import FakeDht

            self._hardware = AdafruitHardware(sensor=FakeDht())
        else:
            raise RuntimeError("DHT requires a Raspberry Pi or ALLOW_FAKE_DEVICES=1")

    def read(self) -> Dict[str, Any]:
        """Read temperature and humidity from the DHT sensor."""
        try:
            result = self._hardware.read()
            if result is None:
                return {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "temperature": None,
                    "humidity": None,
                }
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                **result,
            }
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "temperature": None,
                "humidity": None,
                "error": str(e),
            }


Device = DhtDevice

__all__ = ["Device", "DhtDevice", "AdafruitHardware", "DhtSensor"]
