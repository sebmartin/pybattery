import pigpio
from enum import IntEnum
from typing import Any, Protocol, Literal


class DhtModel(IntEnum):
    DHT11 = 1
    DHTXX = 2


class DhtStatus(IntEnum):
    DHT_GOOD = 0
    DHT_BAD_CHECKSUM = 1
    DHT_BAD_DATA = 2
    DHT_TIMEOUT = 3


class CallbackProtocol(Protocol):
    def cancel(self) -> None: ...


class PiProtocol(Protocol):
    def write(self, gpio: int, level: Literal[0, 1]) -> Any: ...
    def get_current_tick(self) -> int: ...
    def set_mode(self, gpio: int, mode: int) -> None: ...
    def callback(
        self, user_gpio, edge=pigpio.RISING_EDGE, func=None
    ) -> CallbackProtocol: ...
