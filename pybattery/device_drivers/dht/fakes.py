from typing import List, Optional


class FakePigpio:
    """Controllable fake for PigpioHardware. Pre-load bits to return."""

    def __init__(self, bits: Optional[List[int]] = None, error: Optional[Exception] = None):
        self._bits = bits or []
        self._error = error
        self.triggered_gpios: List[int] = []

    def trigger(self, gpio: int) -> None:
        if self._error:
            raise self._error
        self.triggered_gpios.append(gpio)

    def read_bits(self, gpio: int) -> List[int]:
        return list(self._bits)
