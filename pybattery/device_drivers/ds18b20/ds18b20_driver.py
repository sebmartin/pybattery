from typing import Any, Dict

from pathlib import Path
import time

from pydantic import BaseModel

from pybattery.models.config import DeviceConfig
from pybattery.models.device_driver import DeviceDriver

BASE_DIR = Path("/sys/bus/w1/devices")


class Ds18b20Config(BaseModel):
    sensor_id: str


class Ds18b20Driver(DeviceDriver):
    """
    Read temperature data from a DS18B20 thermometer sensor.
    """

    def __init__(self, config: DeviceConfig) -> None:
        super().__init__(config)

        ds18b20_config = Ds18b20Config(**config.args)
        self.sensor_path = BASE_DIR / f"28-{ds18b20_config.sensor_id}"

        available_sensors = get_sensors()
        available_sensor_ids = [
            s.name.lstrip("28-") for s in available_sensors
        ] or "None"
        if self.sensor_path not in available_sensors:
            raise ValueError(
                f"Invalid DS18B20 temperature sensor ID: {ds18b20_config.sensor_id}. "
                f"Available sensor IDs: {available_sensor_ids}"
            )

    def read(self) -> Dict[str, Any]:
        """
        Read the component's value.
        """
        return {
            "temperature": read_temp(self.sensor_path),
        }


def read_temp(sensor_path: Path):
    with open(sensor_path / "w1_slave") as f:
        lines = f.readlines()

    if lines[0].strip().endswith("YES"):
        temp_raw = lines[1].split("t=")[1]
        return float(temp_raw) / 1000.0
    raise RuntimeError("CRC failed")


def get_sensors() -> list[Path]:
    return list(BASE_DIR.glob("28-*"))
