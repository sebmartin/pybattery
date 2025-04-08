import importlib
from typing import Dict


def list_components() -> Dict[str, type]:
    """List all components in the pybattery package."""
    import pkgutil
    import pybattery.components

    components = {}
    for _, name, _ in pkgutil.iter_modules(pybattery.components.__path__):
        module = importlib.import_module(f"pybattery.components.{name}")
        if hasattr(module, "Component") and isinstance(module.Component, type):
            components[name] = module.Component()
    return components
