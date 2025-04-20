from typing import Any, Dict

from pybattery.models.config import DeviceConfig


class Dht11Device:
    """
    Read temperature and humidity data from a DHT11 sensor.
    """

    def __init__(self, config: DeviceConfig) -> None:
        pass

    def read(self) -> Dict[str, Any]:
        """
        Read the temperature and humidity data from the DHT11 sensor.
        """
        import board
        import adafruit_dht

        dht_device = adafruit_dht.DHT11(board.D13)
        try:
            temperature = dht_device.temperature
            humidity = dht_device.humidity
            return {"temperature": temperature, "humidity": humidity}
        except RuntimeError as e:
            print(f"Error reading DHT11 sensor: {e}")
            return {}

        # dht = adafruit_dht.DHT11(board.D13)
        # return {
        #     "temperature": dht.temperature,
        #     "humidity": dht.humidity
        # }


Device = Dht11Device

__all__ = ["Device", "Dht11Device"]
