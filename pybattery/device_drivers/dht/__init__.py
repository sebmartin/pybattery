from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional, Protocol, runtime_checkable

from pybattery.models.config import DeviceConfig
from pybattery.models.device import Device
from pybattery.rpi import fake_devices_allowed

DHT_TIMEOUT_BITS = 40


class DhtConfig:
    def __init__(self, gpio: int, model: Literal["DHT11", "DHTXX"] = "DHT11"):
        self.gpio = gpio
        self.model = model


class CancelableCallback(Protocol):
    def cancel(self) -> None: ...


class PiProtocol(Protocol):
    """Protocol matching the subset of pigpio.pi() we use."""
    def set_mode(self, gpio: int, mode: int) -> None: ...
    def write(self, gpio: int, level: int) -> None: ...
    def callback(self, gpio: int, edge: int, func: Callable[[int, int, int], None]) -> CancelableCallback: ...


EDGE_EITHER = 2  # pigpio.EITHER_EDGE
MODE_INPUT = 0   # pigpio.INPUT
MODE_OUTPUT = 1  # pigpio.OUTPUT


def _edges_to_bits(edges: List[tuple[int, int]]) -> List[int]:
    """Convert a list of (level, tick) edge events into decoded DHT data bits.

    The DHT protocol sends a response pulse (~80µs low + ~80µs high) followed
    by 40 data bits. Each data bit starts with ~50µs low, then high for ~26µs
    (0-bit) or ~70µs (1-bit).

    We measure the duration of each high pulse: <50µs -> 0, >=50µs -> 1.
    The first high->low transition is the response pulse and is skipped.
    """
    bits: List[int] = []
    last_rise_tick = 0
    in_data = False

    for level, tick in edges:
        if level == 1:
            last_rise_tick = tick
        elif level == 0 and last_rise_tick != 0:
            dt = tick - last_rise_tick
            if not in_data:
                in_data = True
            else:
                bits.append(0 if dt < 50 else 1)
                if len(bits) >= DHT_TIMEOUT_BITS:
                    break
    return bits


class PigpioHardware:
    """Hardware implementation using a pigpio pi instance.

    Accepts a pi (real or fake) for dependency injection, making the
    trigger/read_bits logic testable without real hardware.
    """

    def __init__(self, pi: Optional[PiProtocol] = None):
        if pi is not None:
            self._pi = pi
        else:
            try:
                import pigpio
                self._pi = pigpio.pi()
                if not self._pi.connected:
                    raise RuntimeError("pigpio daemon is not running")
            except ImportError as e:
                raise RuntimeError("pigpio is not installed") from e

    def read(self, gpio: int) -> List[int]:
        """Trigger the DHT sensor and read 40 decoded bits.

        Registers an edge callback first, then triggers the sensor by pulling
        the line low. This ensures we capture the sensor's response edges.
        Returns a list of 40 integer values (0 or 1).
        """
        import threading

        edges: List[tuple[int, int]] = []
        done = threading.Event()

        def _cb(_gpio_pin: int, level: int, tick: int) -> None:
            edges.append((level, tick))
            # Response pulse (2 edges) + 40 data bits (2 edges each) = 82 edges
            if len(edges) >= 82:
                done.set()

        cb = self._pi.callback(gpio, EDGE_EITHER, _cb)
        try:
            # Trigger: pull line low for ~20ms, then release to input
            self._pi.set_mode(gpio, MODE_OUTPUT)
            self._pi.write(gpio, 0)
            time.sleep(0.02)
            self._pi.set_mode(gpio, MODE_INPUT)
            done.wait(timeout=0.1)
        finally:
            cb.cancel()
        return _edges_to_bits(edges)


def _decode_dht11(bits: List[int]) -> Optional[Dict[str, float]]:
    """Decode 40 bits into DHT11 temperature and humidity.

    DHT11 data format (40 bits = 5 bytes):
      byte 0: humidity integer part
      byte 1: humidity decimal part (always 0 for DHT11)
      byte 2: temperature integer part
      byte 3: temperature decimal part
      byte 4: checksum (sum of bytes 0-3 & 0xFF)
    """
    if len(bits) < DHT_TIMEOUT_BITS:
        return None

    bytes_ = []
    for i in range(5):
        val = 0
        for j in range(8):
            val = (val << 1) | bits[i * 8 + j]
        bytes_.append(val)

    checksum = (bytes_[0] + bytes_[1] + bytes_[2] + bytes_[3]) & 0xFF
    if checksum != bytes_[4]:
        return None

    humidity = bytes_[0] + bytes_[1] * 0.1
    temperature = bytes_[2] + bytes_[3] * 0.1

    if not (0 <= temperature <= 60) or not (9 <= humidity <= 100):
        return None

    return {"temperature": temperature, "humidity": humidity}


def _decode_dhtxx(bits: List[int]) -> Optional[Dict[str, float]]:
    """Decode 40 bits into DHT22/DHTXX temperature and humidity.

    DHTXX data format (40 bits = 5 bytes):
      bytes 0-1: humidity x 10 as 16-bit unsigned
      bytes 2-3: temperature x 10 as 16-bit value (bit 15 = sign)
      byte 4:    checksum (sum of bytes 0-3 & 0xFF)
    """
    if len(bits) < DHT_TIMEOUT_BITS:
        return None

    bytes_ = []
    for i in range(5):
        val = 0
        for j in range(8):
            val = (val << 1) | bits[i * 8 + j]
        bytes_.append(val)

    checksum = (bytes_[0] + bytes_[1] + bytes_[2] + bytes_[3]) & 0xFF
    if checksum != bytes_[4]:
        return None

    humidity = ((bytes_[0] << 8) | bytes_[1]) * 0.1

    raw_temp = (bytes_[2] << 8) | bytes_[3]
    sign = 1
    if raw_temp & 0x8000:
        sign = -1
        raw_temp &= 0x7FFF
    temperature = sign * raw_temp * 0.1

    if not (-50 <= temperature <= 135) or not (0 <= humidity <= 110):
        return None

    return {"temperature": temperature, "humidity": humidity}


class DhtDevice(Device):
    """Read temperature and humidity from a DHT11/DHTXX sensor via pigpio."""

    def __init__(self, config: DeviceConfig, hardware: Optional[PigpioHardware] = None) -> None:
        super().__init__(config)
        self.gpio = config.args.get("gpio", 13)
        self.model: Literal["DHT11", "DHTXX"] = config.args.get("model", "DHT11")
        if hardware is not None:
            self._hardware = hardware
        elif fake_devices_allowed():
            from pybattery.device_drivers.dht.fakes import FakePi  # noqa: F811
            self._hardware = PigpioHardware(pi=FakePi())
        else:
            self._hardware = PigpioHardware()

    def read(self) -> Dict[str, Any]:
        """Read temperature and humidity from the DHT sensor."""
        try:
            bits = self._hardware.read(self.gpio)
            if self.model == "DHTXX":
                result = _decode_dhtxx(bits)
            else:
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

__all__ = [
    "Device", "DhtDevice", "DhtConfig",
    "PigpioHardware", "PiProtocol",
    "_edges_to_bits", "_decode_dht11", "_decode_dhtxx",
]
