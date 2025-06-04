import argparse
import sys
from typing import List, Optional

from pybattery.api import Api
from pybattery.models.config import Config
from pybattery.output_writer import OutputFormat, OutputWriter


def list_devices(api):
    """List all available devices in the pybattery package."""
    data = {
        name: device.description
        for name, device in api.all_devices.items()
    }
    OutputWriter(OutputFormat.YAML).write({"devices": data})

def list_device_types(api):
    """List all available device types in the pybattery package."""
    data = {
        name: device_type.__doc__.strip().splitlines()[0] if device_type.__doc__ else "No description available"
        for name, device_type in api.device_types.items()
    }
    OutputWriter(OutputFormat.YAML).write({"device_types": data})

def read(api: Api, device_names: List[str], format):
    """Read data from specified devices."""
    if not device_names:
        return

    if data := api.read(device_names):
        OutputWriter(OutputFormat(format)).write(data)

def write(api: Api, device_name: str, value: str):
    """Write data to a specified device."""
    write_devices = api.write_devices
    if device_name not in write_devices:
        print(f"Device '{device_name}' not found.", file=sys.stderr)
        return
    device = write_devices[device_name]
    try:
        device.write(value)
    except Exception as e:
        print(f"Failed to write to device '{device_name}': {e}", file=sys.stderr)


def main(config: Optional[Config] = None):
    config = config or Config.from_file()
    api = Api(config=config)
    read_devices, write_devices = api.read_devices, api.write_devices

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
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.YAML.value,
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
    {
        "read": read,
        "write": write,
        "list": list_devices,
        "list-types": list_device_types,
        "list-gpio": api.list_gpio,
    }.get(command, lambda: parser.print_help())(api, **args)


if __name__ == "__main__":
    main()
