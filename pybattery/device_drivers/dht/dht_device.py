from typing import Any, Dict
import pygpio

from pybattery.models.config import DeviceConfig
from pybattery.models.device_driver import DeviceDriver
from pybattery.device_drivers.dht.dht_pigpio import DhtSensor

DEFAULT_GPIO = 13


class Dht11Device(DeviceDriver):
    """
    Read temperature and humidity data from a DHT11 sensor.
    """

    gpio: str

    def __init__(self, config: DeviceConfig) -> None:
        super().__init__(config)
        self._pi = pygpio.pi()
        self.gpio = config.args.get("gpio", DEFAULT_GPIO)

    def read(self) -> Dict[str, Any]:
        """
        Read the temperature and humidity data from the DHT11 sensor.
        """

        humidity, temperature = read_sensor(DHT11, self.gpio)
        try:
            return {
                "temperature": temperature,
                "humidity": humidity,
            }
        except RuntimeError as e:
            print(f"Error reading DHT11 sensor: {e}")
            return {}


DeviceDriver = Dht11Device

__all__ = ["DeviceDriver", "Dht11Device"]
