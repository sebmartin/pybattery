from typing import Any, Dict


class ThermoComponent:
    """
    Base class for all Thermo components.
    """

    def read(self) -> Dict[str, Any]:
        """
        Read the component's value.
        """
        return {}
