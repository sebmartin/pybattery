from typing import Any, Dict

from pybattery.models.config import DeviceConfig
from pybattery.models.device import Device


class Ds12b20Device(Device):
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


Device = Ds12b20Device

__all__ = ["Device", "Ds12b20Device"]
