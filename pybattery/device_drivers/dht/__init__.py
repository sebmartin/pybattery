from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Protocol, runtime_checkable

from pybattery.models.config import DeviceConfig
from pybattery.models.device import Device
from pybattery.rpi import fake_devices_allowed

DHT_TIMEOUT_BITS = 40 * 2  # 40 bits, 2 edges each


class DhtConfig:
    def __init__(self, gpio: int, model: Literal["DHT11", "DHTXX"] = "DHT11"):
        self.gpio = gpio
        self.model = model


@runtime_checkable
class PigpioHardware(Protocol):
    def trigger(self, gpio: int) -> None: ...
    def read_bits(self, gpio: int) -> List[int]: ...


class PigpioImpl:
    """Real pigpio-based hardware implementation."""

    def __init__(self):
        try:
            import pigpio
            self._pi = pigpio.pi()
            if not self._pi.connected:
                raise RuntimeError("pigpio daemon is not running")
        except ImportError as e:
            raise RuntimeError("pigpio is not installed") from e

    def trigger(self, gpio: int) -> None:
        import pigpio
        self._pi.set_mode(gpio, pigpio.OUTPUT)
        self._pi.write(gpio, 0)
        import time
        time.sleep(0.02)
        self._pi.set_mode(gpio, pigpio.INPUT)

    def read_bits(self, gpio: int) -> List[int]:
        import pigpio
        import time
        bits = []
        self._pi.set_mode(gpio, pigpio.INPUT)
        last = self._pi.read(gpio)
        deadline = time.monotonic() + 0.1
        while len(bits) < DHT_TIMEOUT_BITS and time.monotonic() < deadline:
            current = self._pi.read(gpio)
            if current != last:
                bits.append(current)
                last = current
        return bits


def _decode_dht11(bits: List[int]) -> Optional[Dict[str, float]]:
    """Decode raw bit edges into temperature and humidity."""
    if len(bits) < DHT_TIMEOUT_BITS:
        return None
    # Simplified decode: in a real implementation this would parse the
    # 40-bit DHT11 protocol from the edge timings captured by pigpio.
    # Here we return None to indicate a decode failure in the stub path.
    return None


class DhtDevice(Device):
    """Read temperature and humidity from a DHT11/DHTXX sensor via pigpio."""

    def __init__(self, config: DeviceConfig, hardware: Optional[PigpioHardware] = None) -> None:
        super().__init__(config)
        self.gpio = config.args.get("gpio", 13)
        self.model: Literal["DHT11", "DHTXX"] = config.args.get("model", "DHT11")
        if hardware is not None:
            self._hardware: PigpioHardware = hardware
        elif fake_devices_allowed():
            from pybattery.device_drivers.dht.fakes import FakePigpio
            self._hardware = FakePigpio()
        else:
            self._hardware = PigpioImpl()

    def read(self) -> Dict[str, Any]:
        """Read temperature and humidity from the DHT sensor."""
        try:
            self._hardware.trigger(self.gpio)
            bits = self._hardware.read_bits(self.gpio)
            result = _decode_dht11(bits)
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

__all__ = ["Device", "DhtDevice", "DhtConfig", "PigpioHardware", "PigpioImpl"]
