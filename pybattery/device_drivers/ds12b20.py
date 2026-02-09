from typing import Any, Dict

from pybattery.models.config import DeviceConfig
from pybattery.models.device_driver import DeviceDriver


class Ds12b20Device(DeviceDriver):
    """
    Read temperature data from a DS12B20 thermometer sensor.
    """

    def __init__(self, config: DeviceConfig) -> None:
        super().__init__(config)

    def read(self) -> Dict[str, Any]:
        """
        Read the component's value.
        """
        return {}


DeviceDriver = Ds12b20Device

__all__ = ["DeviceDriver", "Ds12b20Device"]
