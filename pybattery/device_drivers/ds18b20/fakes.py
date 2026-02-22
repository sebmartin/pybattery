from typing import Dict, Optional


class FakeSysfsReader:
    """Controllable fake for OneWireReader. Configure sensor data or missing sensors."""

    def __init__(self, sensors: Optional[Dict[str, str]] = None):
        self._sensors = sensors or {}

    def read(self, sensor_id: str) -> str:
        if sensor_id not in self._sensors:
            raise FileNotFoundError(f"Sensor '{sensor_id}' not found")
        return self._sensors[sensor_id]
