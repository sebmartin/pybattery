import json
import sys
from enum import Enum
from typing import Any, Dict, List, Tuple, Union

import yaml

from pybattery.models.config import Config
from pybattery.protocols import ReadableDeviceType, WritableDeviceType


class ReadFormat(Enum):
    """Enum for read formats."""

    JSON = "json"
    YAML = "yaml"


def read(
    config: Dict[str, Any],
    device_names: List[str],
    read_devices: Dict[str, ReadableDeviceType],
    format: str,
    **kwargs,
):
    """Read component data."""
    unknown_devices = set(device_names) - set(read_devices.keys())
    if unknown_devices:
        print(f"Unknown devices: {', '.join(unknown_devices)}", file=sys.stderr)

    output = {device_name: device.read() for device_name in device_names if (device := read_devices.get(device_name))}
    if len(device_names) == 1:
        output = output.get(device_names[0])

    if format == ReadFormat.JSON.value:
        print(json.dumps(output, indent=4))
    elif format == ReadFormat.YAML.value:
        print(yaml.dump(output, indent=4))


def write(config: Config, device: WritableDeviceType, value: str, **kwargs):
    """Write component data."""
    print(f"Writing {value} to {device}")


def list_devices(config: Config, **kwargs):
    """List all available devices in the pybattery package."""
    print("Available devices:")
    for name, device in config.devices.items():
        print(f"- {name}: {device.description}")


def list_device_types(device_types: Dict[str, type], **kwargs):
    """List all available device types in the pybattery package."""
    print("Available device types:")
    for name, device_type in device_types.items():
        print(
            f"- {name}: {device_type.__doc__.strip().splitlines()[0][:80] if device_type.__doc__ else 'No description available'}"
        )


def list_gpio(config: Config, **kwargs):
    """List all available GPIO pins on the board."""
    try:
        import board

        def parse_gpio(gpio: Union[str, List[str]]):
            return gpio if isinstance(gpio, list) else [gpio]

        configured_gpios = {
            gpio: device
            for device, device_config in config.devices.items()
            for gpio in parse_gpio(device_config.args.get("gpio", []))
        }

        print("Board identified as:", str(board.board_id))

        gpio_pins = [pin for pin in dir(board) if not pin.startswith("_")]
        print("Available GPIO pins:")
        for pin in sorted(gpio_pins):
            if configured_gpio := configured_gpios.get(pin):
                print(f"- {pin} (used by {configured_gpio})")
            else:
                print(f"- {pin}")
    except (ImportError, NotImplementedError):
        print("Board module not available. GPIO pins cannot be listed.")


def parse_devices(
    config: Config, device_types: Dict[str, type]
) -> Tuple[Dict[str, ReadableDeviceType], Dict[str, WritableDeviceType]]:
    """Parse devices from the configuration."""
    all_devices = {
        name: device_type(device_config)
        for name, device_config in config.devices.items()
        if (device_type := device_types.get(device_config.type))
        and issubclass(device_type, (ReadableDeviceType, WritableDeviceType))
    }
    if unknown_devices := set(config.devices.keys()) - set(all_devices.keys()):
        print(f"Unknown devices found in config: {', '.join(unknown_devices)}", file=sys.stderr)
        print("Devices were not recognized as either a readable or writable device.", file=sys.stderr)

    read_devices = {name: device for name, device in all_devices.items() if isinstance(device, ReadableDeviceType)}
    write_devices = {name: device for name, device in all_devices.items() if isinstance(device, WritableDeviceType)}

    return read_devices, write_devices