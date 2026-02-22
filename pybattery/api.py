import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pybattery.device_drivers import list_device_drivers
from pybattery.models.config import Config
from pybattery.protocols import ReadableDriver, WritableDriver


class ReadFormat(Enum):
    """Enum for read formats."""

    JSON = "json"
    YAML = "yaml"


class Api:
    def __init__(self, config: Config):
        self._config = config
        self._device_drivers = None
        self._read_devices, self._write_devices = self._parse_devices()

    @property
    def config(self) -> Config:
        """Get the configuration."""
        return self._config

    @property
    def read_devices(self) -> Dict[str, ReadableDriver]:
        """Get the readable devices."""
        return self._read_devices

    @property
    def write_devices(self) -> Dict[str, WritableDriver]:
        """Get the writable devices."""
        return self._write_devices

    @property
    def all_devices(self) -> Dict[str, Union[ReadableDriver, WritableDriver]]:
        """Get all devices."""
        return {**self._read_devices, **self._write_devices}

    @property
    def device_drivers(self) -> Dict[str, type]:
        """Get all device drivers."""
        if self._device_drivers is None:
            self._device_drivers = list_device_drivers()
        return self._device_drivers

    def read(
        self,
        device_names: List[str],
    ) -> Optional[Dict[str, Any]]:
        """Read component data."""
        unknown_devices = set(device_names) - set(self.read_devices.keys())
        if unknown_devices:
            print(f"Unknown devices: {', '.join(unknown_devices)}", file=sys.stderr)
            return None

        output = {
            device_name: device.read()
            for device_name in device_names
            if (device := self.read_devices.get(device_name))
        }
        if len(device_names) == 1:
            output = output.get(device_names[0])
        return output

    def write(self, device: WritableDriver, value: str) -> None:
        """Write component data."""
        device.write(value)

    def _parse_devices(self) -> Tuple[Dict[str, ReadableDriver], Dict[str, WritableDriver]]:
        """Parse devices from the configuration."""
        all_devices = {
            name: driver_cls(device_config)
            for name, device_config in self._config.devices.items()
            if (driver_cls := self.device_drivers.get(device_config.driver))
            and isinstance(driver_cls, (ReadableDriver, WritableDriver))
        }
        if unknown_devices := set(self.config.devices.keys()) - set(all_devices.keys()):
            print(f"Unknown devices found in config: {', '.join(unknown_devices)}", file=sys.stderr)
            print("Devices were not recognized as either a readable or writable device.", file=sys.stderr)

        read_devices = {name: device for name, device in all_devices.items() if isinstance(device, ReadableDriver)}
        write_devices = {name: device for name, device in all_devices.items() if isinstance(device, WritableDriver)}

        return read_devices, write_devices
