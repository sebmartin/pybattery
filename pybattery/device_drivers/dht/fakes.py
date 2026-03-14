from typing import Optional


class FakeDht:
    """Fake DHT sensor implementing DhtSensor protocol."""

    def __init__(
        self,
        temperature: Optional[float] = 20.0,
        humidity: Optional[float] = 50.0,
        error: Optional[Exception] = None,
    ):
        self._temperature = temperature
        self._humidity = humidity
        self._error = error

    @property
    def temperature(self) -> Optional[float]:
        if self._error:
            raise self._error
        return self._temperature

    @property
    def humidity(self) -> Optional[float]:
        return self._humidity

    def exit(self) -> None:
        pass
