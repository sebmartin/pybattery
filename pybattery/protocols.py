from typing import Any, Dict, Optional, Protocol, runtime_checkable

from pybattery.models.config import DeviceConfig


@runtime_checkable
class ReadableDeviceType(Protocol):
    def __init__(self, config: DeviceConfig):
        pass

    @property
    def description(self) -> str:
        """Get the device description."""
        ...

    def read(self) -> Optional[Dict[str, Any]]:
        """Read the component's value."""
        ...


@runtime_checkable
class WritableDeviceType(Protocol):
    def __init__(self, config: DeviceConfig):
        pass

    @property
    def description(self) -> str:
        """Get the device description."""
        ...

    def write(self, value: Any) -> None:
        """Write a value to the component."""
        ...
