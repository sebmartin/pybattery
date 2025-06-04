from typing import Any, Dict

from pybattery.models.config import DeviceConfig
from pybattery.models.device import Device
from Adafruit_DHT import read as read_sensor, DHT11

DEFAULT_GPIO = 13

class Dht11Device(Device):
    """
    Read temperature and humidity data from a DHT11 sensor.
    """

    gpio: str

    def __init__(self, config: DeviceConfig) -> None:
        super().__init__(config)
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


Device = Dht11Device

__all__ = ["Device", "Dht11Device"]
