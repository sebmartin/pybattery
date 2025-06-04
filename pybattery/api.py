import json
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from pybattery.device_types import list_device_types
from pybattery.models.config import Config
from pybattery.protocols import ReadableDeviceType, WritableDeviceType


class ReadFormat(Enum):
    """Enum for read formats."""

    JSON = "json"
    YAML = "yaml"


class Api:
    def __init__(self, config: Config):
        self._config = config
        self._device_types = None
        self._read_devices, self._write_devices = self._parse_devices()

    @property
    def config(self) -> Config:
        """Get the configuration."""
        return self._config

    @property
    def read_devices(self) -> Dict[str, ReadableDeviceType]:
        """Get the readable devices."""
        return self._read_devices

    @property
    def write_devices(self) -> Dict[str, WritableDeviceType]:
        """Get the writable devices."""
        return self._write_devices

    @property
    def all_devices(self) -> Dict[str, Union[ReadableDeviceType, WritableDeviceType]]:
        """Get all devices."""
        return {**self._read_devices, **self._write_devices}

    @property
    def device_types(self) -> Dict[str, type]:
        """Get all device types."""
        if self._device_types is None:
            self._device_types = list_device_types()
        return self._device_types

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
            device_name: device.read() for device_name in device_names if (device := self.read_devices.get(device_name))
        }
        if len(device_names) == 1:
            output = output.get(device_names[0])
        return output

    def write(self, device: WritableDeviceType, value: str, **kwargs):
        """Write component data."""
        print(f"Writing {value} to {device}")

    def list_gpio(self, **kwargs):
        """List all available GPIO pins on the board."""
        try:
            # import board

            def parse_gpio(gpio: Union[str, List[str]]):
                return gpio if isinstance(gpio, list) else [gpio]

            configured_gpios = {
                gpio: device
                for device, device_config in self.config.devices.items()
                for gpio in parse_gpio(device_config.args.get("gpio", []))
            }

            # print("Board identified as:", str(board.board_id))

            gpio_pins = [pin for pin in dir(board) if not pin.startswith("_")]
            print("Available GPIO pins:")
            for pin in sorted(gpio_pins):
                if configured_gpio := configured_gpios.get(pin):
                    print(f"- {pin} (used by {configured_gpio})")
                else:
                    print(f"- {pin}")
        except (ImportError, NotImplementedError):
            print("Board module not available. GPIO pins cannot be listed.")

    def _parse_devices(self) -> Tuple[Dict[str, ReadableDeviceType], Dict[str, WritableDeviceType]]:
        """Parse devices from the configuration."""
        all_devices = {
            name: device_type(device_config)
            for name, device_config in self._config.devices.items()
            if (device_type := self.device_types.get(device_config.type))
            and isinstance(device_type, (ReadableDeviceType, WritableDeviceType))
        }
        if unknown_devices := set(self.config.devices.keys()) - set(all_devices.keys()):
            print(f"Unknown devices found in config: {', '.join(unknown_devices)}", file=sys.stderr)
            print("Devices were not recognized as either a readable or writable device.", file=sys.stderr)

        read_devices = {name: device for name, device in all_devices.items() if isinstance(device, ReadableDeviceType)}
        write_devices = {name: device for name, device in all_devices.items() if isinstance(device, WritableDeviceType)}

        return read_devices, write_devices
