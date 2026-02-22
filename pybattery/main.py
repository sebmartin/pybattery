import argparse
import sys
from typing import List, Optional

from pybattery.api import Api
from pybattery.models.config import Config
from pybattery.output_writer import OutputFormat, OutputWriter


def list_devices(api: Api, **kwargs):
    """List all available devices."""
    data = {
        name: device.description
        for name, device in api.all_devices.items()
    }
    OutputWriter(OutputFormat.YAML).write({"devices": data})


def list_drivers(api: Api, **kwargs):
    """List all available device drivers."""
    data = {
        name: driver.__doc__.strip().splitlines()[0] if driver.__doc__ else "No description available"
        for name, driver in api.device_drivers.items()
    }
    OutputWriter(OutputFormat.YAML).write({"device_drivers": data})


def read(api: Api, device_names: List[str], format: str, **kwargs):
    """Read data from specified devices."""
    if not device_names:
        return

    if data := api.read(device_names):
        OutputWriter(OutputFormat(format)).write(data)


def write(api: Api, device_name: str, value: str, **kwargs):
    """Write data to a specified device."""
    device = api.write_devices.get(device_name)
    if device is None:
        print(f"Error: '{device_name}' is not a writable device", file=sys.stderr)
        sys.exit(1)
    api.write(device, value)


def main(config: Optional[Config] = None):
    try:
        config = config or Config.from_file()
    except (FileNotFoundError, Exception) as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

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
        "device_name",
        metavar="device",
        type=str,
        help="Name of device to write to",
        choices=list(write_devices.keys()),
    )
    write_parser.add_argument("value", type=str, help="Value to write")

    subparsers.add_parser("devices", help="List available devices")
    subparsers.add_parser("drivers", help="List available device drivers")

    args = parser.parse_args().__dict__
    command = args.pop("command")
    {
        "read": read,
        "write": write,
        "devices": list_devices,
        "drivers": list_drivers,
    }.get(command, lambda **_: parser.print_help())(api, **args)


if __name__ == "__main__":
    main()
