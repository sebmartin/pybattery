from typing import Any, Dict
import pigpio

from pydantic import BaseModel

from pybattery.device_drivers.dht.dht_pigpio import DhtModel, DhtSensor
from pybattery.device_drivers.dht.models import DhtStatus
from pybattery.models.config import DeviceConfig
from pybattery.models.device_driver import DeviceDriver
from pybattery.models.protocols import ReadableDeviceDriver

DEFAULT_GPIO = 13


class DhtConfig(BaseModel):
    gpio: int = DEFAULT_GPIO
    model: DhtModel


class Dht11Driver(DeviceDriver, ReadableDeviceDriver):
    """
    Read temperature and humidity data from a DHT11 sensor.
    """

    gpio: str

    def __init__(self, config: DeviceConfig, pi: pigpio.pi | None = None) -> None:
        super().__init__(config)

        dht_config = DhtConfig(**config.args)

        self._pi = pi or pigpio.pi()
        self.sensor = DhtSensor(
            gpio=dht_config.gpio,
            model=dht_config.model,
            pi=pi,
        )

    def read(self) -> Dict[str, Any]:  # TODO: Use a type, BaseModel?
        """
        Read the temperature and humidity data from the DHT11 sensor.
        """

        try:
            timestamp, _, status, temperature, humidity = self.sensor.read()
            return {
                "timestamp": timestamp,
                "status": status,
                "temperature": temperature,
                "humidity": humidity,
            }
        except Exception as e:
            print(f"Error reading DHT11 sensor: {e}")
            return {
                "timestamp": 0,
                "status": DhtStatus.DHT_BAD_DATA,
                "temperature": 0.0,
                "humidity": 0.0,
            }
