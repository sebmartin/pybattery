import argparse
from enum import Enum
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

from pybattery.device_types import list_device_types as _list_device_types
from pybattery.models.config import Config
from pybattery.models.utils import from_dict
from pybattery.protocols import ReadableDeviceType, WritableDeviceType
import os
import yaml
import json


class ReadFormat(Enum):
    """Enum for read formats."""

    JSON = "json"
    YAML = "yaml"


def read_config() -> Config:
    """Read the configuration file."""
    config_path = os.path.abspath(f"{os.path.dirname(__file__)}/../config.yml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)
    return from_dict(Config, config)


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


def _parse_devices(
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


def main(config: Optional[Config] = None):
    config = config or read_config()
    device_types = _list_device_types()
    read_devices, write_devices = _parse_devices(config=config, device_types=device_types)

    parser = argparse.ArgumentParser(description="Battery management system")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    read_parser = subparsers.add_parser("read", help="Read device data")
    read_parser.add_argument(
        "device_names",
        metavar="device",
        type=str,
        nargs="*",
        help="Name of device to read",
        choices=list(read_devices.keys()),
    )
    read_parser.add_argument(
        "-f",
        "--format",
        type=str,
        help="Output format",
        choices=[f.value for f in ReadFormat],
        default=ReadFormat.YAML.value,
    )

    write_parser = subparsers.add_parser("write", help="Write device data")
    write_parser.add_argument(
        "device_name", metavar="device", type=str, help="Name of device to write to", choices=list(write_devices.keys())
    )
    write_parser.add_argument("value", type=str, help="Value to write")

    subparsers.add_parser("list", help="List available devices")
    subparsers.add_parser("list-types", help="List available device types")
    subparsers.add_parser("list-gpio", help="List available GPIO pins on the board")

    args = parser.parse_args().__dict__
    command = args.pop("command")
    computed_args = {
        "config": config,
        "device_types": device_types,
        "read_devices": read_devices,
        "write_devices": write_devices,
        **args,
    }
    # selected_device = args.pop("device") if "device" in args else None
    {
        "read": read,
        "write": write,
        "list": list_devices,
        "list-types": list_device_types,
        "list-gpio": list_gpio,
    }.get(command, lambda: parser.print_help())(**computed_args)


if __name__ == "__main__":
    main()
