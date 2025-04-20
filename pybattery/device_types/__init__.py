import importlib
from typing import Dict


def list_device_types() -> Dict[str, type]:
    """List all device types in the pybattery package."""
    import pkgutil
    import pybattery.device_types

    components = {}
    for _, name, _ in pkgutil.iter_modules(pybattery.device_types.__path__):
        module = importlib.import_module(f"pybattery.device_types.{name}")
        if hasattr(module, "Device") and isinstance(module.Device, type):
            components[name] = module.Device
    return components
