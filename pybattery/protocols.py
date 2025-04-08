from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class ReadableComponent(Protocol):
    def read(self) -> Dict[str, Any]:
        """Read the component's value."""
        ...


@runtime_checkable
class WritableComponent(Protocol):
    def write(self, value: Dict[str, Any]) -> None:
        """Write a value to the component."""
        ...
