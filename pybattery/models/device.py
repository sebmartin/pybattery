from pybattery.models.config import DeviceConfig


class Device:
    def __init__(self, config: DeviceConfig):
        self._config = config

    @property
    def description(self) -> str:
        """Get the device description."""
        return self._config.description