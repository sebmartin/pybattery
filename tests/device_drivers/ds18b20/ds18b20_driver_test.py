from pathlib import Path
from typing import Any
from unittest import mock
import pytest

from pybattery.device_drivers.ds18b20 import Ds18b20Driver
from pybattery.device_drivers.ds18b20.ds18b20_driver import Ds18b20Config
from pybattery.models.config import DeviceConfig
from pybattery.models.protocols import ReadableDeviceDriver


@pytest.fixture
def config_args() -> dict[str, Any]:
    return Ds18b20Config(
        sensor_id="0a9cd44619ac",
    ).model_dump()


@pytest.fixture
def config(config_args) -> DeviceConfig:
    return DeviceConfig(
        driver="ds18b20",
        description="DS18B20 Sensor",
        args=config_args,
    )


@pytest.fixture(autouse=True)
def mock_data():
    with mock.patch(
        "pybattery.device_drivers.ds18b20.ds18b20_driver.open",
        mock.mock_open(read_data="fuck"),
    ) as mocked_open:
        yield mocked_open


@pytest.fixture
def bad_data():
    return "\n".join(
        [
            "33 01 55 05 7f a5 a5 66 00 : crc=00 NO",
            "33 01 55 05 7f a5 a5 66 00 t=19187",
        ]
    )


@pytest.fixture
def good_data():
    return "\n".join(
        [
            "33 01 55 05 7f a5 a5 66 4b : crc=4b YES",
            "33 01 55 05 7f a5 a5 66 4b t=19187",
        ]
    )


@pytest.fixture(autouse=True)
def mock_available_device_ids():
    with mock.patch("pybattery.device_drivers.ds18b20.ds18b20_driver.get_sensors") as mock_get_sensors:
        mock_get_sensors.return_value = [Path("/sys/bus/w1/devices/28-0a9cd44619ac")]
        yield mock_get_sensors


def test_is_readable(config, mock_data, good_data):
    mock.mock_open(mock_data, read_data=good_data)
    sensor = Ds18b20Driver(config)
    assert isinstance(sensor, ReadableDeviceDriver)


def test_read(config, mock_data, good_data):
    mock.mock_open(mock_data, read_data=good_data)
    sensor = Ds18b20Driver(config)
    assert sensor.read() == {
        "temperature": 19.187,
    }


def test_read__crc_failure(config, mock_data, bad_data):
    mock.mock_open(mock_data, read_data=bad_data)
    sensor = Ds18b20Driver(config)
    with pytest.raises(RuntimeError, match="CRC failed"):
        sensor.read()
