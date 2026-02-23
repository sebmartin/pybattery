from __future__ import annotations

from typing import Callable, List, Literal, Optional


class FakeCallback:
    """Cancelable callback handle returned by FakePi.callback()."""
    def cancel(self) -> None:
        pass


def _dht11_bitstring(temp: float, humidity: float, checksum: Optional[int] = None) -> int:
    """Encode DHT11 values as a 40-bit integer (MSB-first: byte4..byte0).

    Byte layout (MSB to LSB in the integer):
      byte4=humidity_int, byte3=humidity_dec, byte2=temp_int, byte1=temp_dec, byte0=checksum
    """
    b1 = int(round((temp - int(temp)) * 10))
    b2 = int(temp)
    b3 = int(round((humidity - int(humidity)) * 10))
    b4 = int(humidity)
    b0 = checksum if checksum is not None else (b1 + b2 + b3 + b4) & 0xFF
    return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24) | (b4 << 32)


def _dhtxx_bitstring(temp: float, humidity: float, checksum: Optional[int] = None) -> int:
    """Encode DHTXX values as a 40-bit integer (MSB-first: byte4..byte0).

    Byte layout (MSB to LSB in the integer):
      byte4=hum_MSB, byte3=hum_LSB, byte2=temp_MSB, byte1=temp_LSB, byte0=checksum
    """
    sign_bit = 0x80 if temp < 0 else 0x00
    temp_raw = int(round(abs(temp) * 10))
    hum_raw = int(round(humidity * 10))

    b1 = temp_raw & 0xFF
    b2 = ((temp_raw >> 8) & 0x7F) | sign_bit
    b3 = hum_raw & 0xFF
    b4 = (hum_raw >> 8) & 0xFF
    b0 = checksum if checksum is not None else (b1 + b2 + b3 + b4) & 0xFF
    return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24) | (b4 << 32)


class FakePi:
    """Fake pigpio.pi() that simulates DHT sensor responses.

    When write(gpio, 0) is called (the trigger), it fires the registered
    callback with realistic tick timings for the configured data, exercising
    the real PigpioHardware.read_bits() timing logic.
    """

    def __init__(
        self,
        temperature: float = 0.0,
        humidity: float = 0.0,
        model: Literal["DHT11", "DHTXX"] = "DHT11",
        checksum: Optional[int] = None,
        error: Optional[Exception] = None,
    ):
        if model == "DHTXX":
            self.data: Optional[int] = _dhtxx_bitstring(temperature, humidity, checksum)
        else:
            self.data = _dht11_bitstring(temperature, humidity, checksum)
        self._error = error
        self._callback: Optional[Callable[[int, int, int], None]] = None
        self._gpio = 0
        self._tick = 20_000
        self.triggered_gpios: List[int] = []

    def set_mode(self, gpio: int, mode: int) -> None:
        pass

    def write(self, gpio: int, level: int) -> None:
        """Simulate the DHT response when the host pulls the line low."""
        if self._error:
            raise self._error
        self.triggered_gpios.append(gpio)
        if self._callback is None or level != 0 or self.data is None:
            return
        # Response pulse: ~80µs high (skipped by _edges_to_bits)
        self._tick += 80
        self._callback(self._gpio, 1, self._tick)
        self._tick += 80
        self._callback(self._gpio, 0, self._tick)

        # 40 data bits, MSB first
        bitmask = 1 << 39
        while bitmask:
            bit = 1 if self.data & bitmask else 0
            # Low period before each bit (~50µs)
            self._tick += 50
            self._callback(self._gpio, 1, self._tick)
            # High period: ~26µs for 0-bit, ~70µs for 1-bit
            self._tick += 70 if bit == 1 else 26
            self._callback(self._gpio, 0, self._tick)
            bitmask >>= 1

    def callback(self, gpio: int, edge: int, func: Callable[[int, int, int], None]) -> FakeCallback:
        self._gpio = gpio
        self._callback = func
        return FakeCallback()
