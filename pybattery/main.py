import argparse
from enum import Enum
from typing import Optional


from pybattery import api
from pybattery.device_types import list_device_types as _list_device_types
from pybattery.models.config import Config


class ReadFormat(Enum):
    """Enum for read formats."""

    JSON = "json"
    YAML = "yaml"


def main(config: Optional[Config] = None):
    config = config or Config.from_file()
    device_types = _list_device_types()
    read_devices, write_devices = api.parse_devices(config=config, device_types=device_types)

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
        "read": api.read,
        "write": api.write,
        "list": api.list_devices,
        "list-types": api.list_device_types,
        "list-gpio": api.list_gpio,
    }.get(command, lambda: parser.print_help())(**computed_args)


if __name__ == "__main__":
    main()
