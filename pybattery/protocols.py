from typing import Any, Dict, Protocol, runtime_checkable

from pybattery.models.config import DeviceConfig


@runtime_checkable
class ReadableDeviceType(Protocol):
    def __init__(self, config: DeviceConfig):
        pass

    def read(self) -> Dict[str, Any]:
        """Read the component's value."""
        ...


@runtime_checkable
class WritableDeviceType(Protocol):
    def __init__(self, config: DeviceConfig):
        pass

    def write(self, value: Any) -> None:
        """Write a value to the component."""
        ...
