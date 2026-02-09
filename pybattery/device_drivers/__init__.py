import importlib
from typing import Dict


def list_device_drivers() -> Dict[str, type]:
    """List all device drivers in the pybattery package."""
    import pkgutil
    import pybattery.device_drivers

    components = {}
    for _, name, _ in pkgutil.iter_modules(pybattery.device_drivers.__path__):
        module = importlib.import_module(f"pybattery.device_drivers.{name}")
        if hasattr(module, "DeviceDriver") and isinstance(module.DeviceDriver, type):
            components[name] = module.DeviceDriver
    return components
