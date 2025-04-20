from typing import Any, Dict

from pybattery.models.config import DeviceConfig


class Ds12b20Device:
    """
    Read temperature data from a DS12B20 thermometer sensor.
    """

    def __init__(self, config: DeviceConfig) -> None:
        pass

    def read(self) -> Dict[str, Any]:
        """
        Read the component's value.
        """
        return {}


Device = Ds12b20Device

__all__ = ["Device", "Ds12b20Device"]
