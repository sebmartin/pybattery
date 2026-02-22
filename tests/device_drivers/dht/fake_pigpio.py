from typing import Any, Literal
from pybattery.device_drivers.dht.models import (
    CallbackProtocol,
    DhtModel,
    PiProtocol,
)


class FakeCallback(CallbackProtocol):
    called = False

    def cancel(self) -> None:
        self.called = True


class FakePi(PiProtocol):
    def __init__(
        self,
        temperature: float,
        humidity: float,
        model: DhtModel,
        checksum: int | None = None,
    ):
        if model == DhtModel.DHT11:
            self.data = dht11_bitstring(temperature, humidity, checksum)
        else:
            self.data = dhtxx_bitstring(temperature, humidity, checksum)
        self.last_tick = 20_000

        self.mode_gpio = None
        self.mode = None

    def write(self, gpio: int, level: Literal[0, 1]) -> Any:
        if not self._callback:
            return
        if level == 0:
            # Add the header bits
            data = (0b01 << 40) | self.data
            # Start bitmask on first header bit
            bitmask = 1 << 42
            while bitmask:
                bitmask = bitmask >> 1
                bit = 1 if data & bitmask else 0
                if bit == 1:
                    self.last_tick += 110
                else:
                    self.last_tick += 75
                self._callback(self.gpio, level, self.last_tick)

    def get_current_tick(self) -> int:
        return self.last_tick

    def set_mode(self, gpio: int, mode: int) -> None:
        self.mode_gpio = gpio
        self.mode = mode

    def callback(self, user_gpio, edge=None, func=None) -> CallbackProtocol:
        self.gpio = user_gpio
        self.edge = edge
        self._callback = func

        return FakeCallback()


def binstring(number: int, signed: bool) -> str:
    result = ("000000000" + bin(number).removeprefix("-").removeprefix("0b"))[-8:]

    if signed:
        result = ("1" if number < 0 else "0") + result[-7:]

    return result


def dht11_bitstring(temp: float, humidity: float, checksum: int | None = None) -> int:
    b1 = int((temp - int(temp)) * 10)
    b2 = int(temp)
    b3 = int((humidity - int(humidity)) * 10)
    b4 = int(humidity)
    b0 = checksum if checksum is not None else (b1 + b2 + b3 + b4) & 0xFF

    return b0 | b1 << 8 | b2 << 16 | b3 << 24 | b4 << 32


def dhtxx_bitstring(temp: float, humidity: float, checksum: int | None = None) -> int:
    temp_sign_bit = 0x80 if temp < 0 else 0x00

    temp = int(abs(temp) * 10)
    humidity = int(humidity * 10)

    b1 = temp & 0xFF
    b2 = (temp >> 8) & 0x7F | temp_sign_bit  # first bit is sign
    b3 = humidity & 0xFF
    b4 = (humidity >> 8) & 0xFF
    b0 = checksum if checksum is not None else (b1 + b2 + b3 + b4) & 0xFF

    return b0 | b1 << 8 | b2 << 16 | b3 << 24 | b4 << 32
