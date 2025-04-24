from typing import Any, Dict

from pybattery.models.config import DeviceConfig
from adafruit_dht import DHT11


class Dht11Device:
    """
    Read temperature and humidity data from a DHT11 sensor.
    """

    gpio: str

    def __init__(self, config: DeviceConfig) -> None:
        self.gpio = config.args.get("gpio", "D13")
        self._sensor = None

    @property
    def sensor(self) -> DHT11:
        import board

        if not self._sensor:
            pin = getattr(board, self.gpio, None)
            self._sensor = DHT11(pin)
        return self._sensor

    def read(self) -> Dict[str, Any]:
        """
        Read the temperature and humidity data from the DHT11 sensor.
        """

        dht_device = self.sensor
        try:
            return {
                "temperature": dht_device.temperature,
                "humidity": dht_device.humidity,
            }
        except RuntimeError as e:
            print(f"Error reading DHT11 sensor: {e}")
            return {}


Device = Dht11Device

__all__ = ["Device", "Dht11Device"]
