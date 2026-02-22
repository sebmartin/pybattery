from typing import Any, Protocol, runtime_checkable

from pybattery.models.config import DeviceConfig


@runtime_checkable
class ReadableDeviceDriver(Protocol):
    def __init__(self, config: DeviceConfig):
        pass

    @property
    def description(self) -> str:
        """Get the device description."""
        ...

    def read(self) -> dict[str, Any] | None:
        """Read the component's value."""
        ...


@runtime_checkable
class WritableDeviceDriver(Protocol):
    def __init__(self, config: DeviceConfig):
        pass

    @property
    def description(self) -> str:
        """Get the device description."""
        ...

    def write(self, value: Any) -> None:
        """Write a value to the component."""
        ...
