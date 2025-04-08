import argparse
from enum import Enum
from typing import Dict

from pybattery.components import list_components as _list_components
from pybattery.protocols import ReadableComponent, WritableComponent


class ReadFormat(Enum):
    """Enum for read formats."""

    JSON = "json"
    YAML = "yaml"


def read(component: str, format: str):
    """Read component data."""
    print(f"Reading {component} data in {format} format")


def write(**kwargs):
    """Write component data."""
    pass  # Placeholder for write functionality


def list_components(components: Dict[str, type]):
    """List all components in the pybattery package."""
    print("Available components:")
    for name, component in components.items():
        print(
            f"- {name}: {component.__doc__.strip().splitlines()[0][:80] if component.__doc__ else 'No description available'}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Battery management system")

    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
    components = _list_components()
    read_components = {
        name: component
        for name, component in components.items()
        if isinstance(component, ReadableComponent)
    }
    write_components = {
        name: component
        for name, component in components.items()
        if isinstance(component, WritableComponent)
    }

    read_parser = subparsers.add_parser("read", help="Read component data")
    read_parser.add_argument(
        "component", type=str, help="Component name to read", choices=read_components
    )
    read_parser.add_argument(
        "-f",
        "--format",
        type=str,
        help="Output format",
        choices=[f.value for f in ReadFormat],
        default=ReadFormat.YAML.value,
    )

    write_parser = subparsers.add_parser("write", help="Write component data")
    write_parser.add_argument(
        "component", type=str, help="Component name to write", choices=write_components
    )
    write_parser.add_argument("value", type=str, help="Value to write")

    list_parser = subparsers.add_parser("list", help="List all components")

    args = parser.parse_args().__dict__
    command = args.pop("command")
    {
        "read": read,
        "write": write,
        "list": lambda: list_components(components),
    }.get(command, lambda: parser.print_help())(**args)
