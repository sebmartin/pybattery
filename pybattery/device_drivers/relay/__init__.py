from pybattery.models.config import DeviceConfig
from pybattery.models.device import Device


class RelayDevice(Device):
    """Control a relay switch."""

    def __init__(self, config: DeviceConfig) -> None:
        super().__init__(config)

    def write(self, value: str) -> None:
        """Write a value to the relay (on/off)."""
        pass


Device = RelayDevice

__all__ = ["Device", "RelayDevice"]
