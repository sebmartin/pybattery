import importlib
import pkgutil
from typing import Dict

import pybattery.device_drivers


def list_device_drivers() -> Dict[str, type]:
    """List all device drivers in the pybattery package."""
    drivers = {}
    for _, name, _ in pkgutil.iter_modules(pybattery.device_drivers.__path__):
        module = importlib.import_module(f"pybattery.device_drivers.{name}")
        if hasattr(module, "Device") and isinstance(module.Device, type):
            drivers[name] = module.Device
    return drivers
