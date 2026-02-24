from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from pybattery.models.config import DeviceConfig
from pybattery.models.device import Device

W1_BASE = Path("/sys/bus/w1/devices")


@runtime_checkable
class OneWireReader(Protocol):
    def read(self, sensor_id: str) -> str: ...


class SysfsReader:
    """Reads one-wire sensor data from the Linux sysfs interface."""

    def read(self, sensor_id: str) -> str:
        path = W1_BASE / sensor_id / "w1_slave"
        return path.read_text()


def _parse_temperature(content: str) -> Optional[float]:
    """Parse temperature in Celsius from w1_slave file content."""
    for line in content.splitlines():
        if "t=" in line:
            t_str = line.split("t=")[-1].strip()
            try:
                return int(t_str) / 1000.0
            except ValueError:
                return None
    return None


class Ds18b20Device(Device):
    """Read temperature data from a DS18B20 one-wire thermometer sensor."""

    def __init__(self, config: DeviceConfig, reader: Optional[OneWireReader] = None) -> None:
        super().__init__(config)
        self.sensor_id: str = config.args.get("sensor_id", "")
        if reader is not None:
            self._reader: OneWireReader = reader
        else:
            self._reader = SysfsReader()
        self._validate_sensor()

    def _validate_sensor(self) -> None:
        """Validate config only. Sensor presence is checked on first read()."""
        if not self.sensor_id:
            raise RuntimeError("DS18B20 sensor_id is required in config")

    def read(self) -> Dict[str, Any]:
        """Read the temperature from the DS18B20 sensor."""
        try:
            content = self._reader.read(self.sensor_id)
            temperature = _parse_temperature(content)
            if temperature is None:
                return {"status": "error", "temperature": None}
            return {"temperature": temperature}
        except FileNotFoundError:
            return {"status": "error", "temperature": None}


Device = Ds18b20Device

__all__ = ["Device", "Ds18b20Device", "OneWireReader", "SysfsReader"]
