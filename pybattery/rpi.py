import os
from pathlib import Path


def is_raspberry_pi() -> bool:
    """Return True if running on a Raspberry Pi."""
    try:
        return "raspberry pi" in Path("/proc/device-tree/model").read_text().lower()
    except (FileNotFoundError, PermissionError):
        return False


def fake_devices_allowed() -> bool:
    """Return True if fake/stub hardware is permitted."""
    return is_raspberry_pi() or bool(os.getenv("ALLOW_FAKE_DEVICES"))


def require_hardware(name: str) -> None:
    """Raise if real hardware is required but not available."""
    if not fake_devices_allowed():
        raise RuntimeError(
            f"{name} requires a Raspberry Pi or ALLOW_FAKE_DEVICES=1"
        )
