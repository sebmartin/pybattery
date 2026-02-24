import pytest

from pybattery.device_drivers.ds18b20 import Ds18b20Device
from pybattery.device_drivers.ds18b20.fakes import FakeSysfsReader
from pybattery.models.config import DeviceConfig


@pytest.fixture
def reader():
    return FakeSysfsReader(sensors={"28-abc123": "YES\nt=23456\n"})


@pytest.fixture
def config():
    return DeviceConfig(description="Test DS18B20", driver="ds18b20", args={"sensor_id": "28-abc123"})


def test_ds18b20_read_temperature(config, reader):
    """Successful read returns correct temperature in Celsius."""
    device = Ds18b20Device(config, reader=reader)
    result = device.read()
    assert result == {"temperature": 23.456}


def test_ds18b20_missing_sensor_returns_error_on_read():
    """When sensor is not found, read() returns error payload; init does not raise."""
    config = DeviceConfig(
        description="Test DS18B20", driver="ds18b20", args={"sensor_id": "28-nonexistent"}
    )
    reader = FakeSysfsReader(sensors={})
    device = Ds18b20Device(config, reader=reader)
    result = device.read()
    assert result["status"] == "error"
    assert result["temperature"] is None


def test_ds18b20_missing_sensor_id_raises():
    """Constructor raises RuntimeError when sensor_id is not configured."""
    config = DeviceConfig(description="Test DS18B20", driver="ds18b20")
    reader = FakeSysfsReader(sensors={})
    with pytest.raises(RuntimeError, match="sensor_id is required"):
        Ds18b20Device(config, reader=reader)


def test_ds18b20_malformed_file_returns_error(config):
    """Malformed w1_slave file returns error result without raising."""
    reader = FakeSysfsReader(sensors={"28-abc123": "YES\nno_t_here\n"})
    device = Ds18b20Device(config, reader=reader)
    result = device.read()
    assert result["status"] == "error"
    assert result["temperature"] is None


def test_ds18b20_negative_temperature():
    """Negative temperatures are parsed correctly."""
    config = DeviceConfig(description="Test DS18B20", driver="ds18b20", args={"sensor_id": "28-cold"})
    reader = FakeSysfsReader(sensors={"28-cold": "YES\nt=-5500\n"})
    device = Ds18b20Device(config, reader=reader)
    result = device.read()
    assert result == {"temperature": -5.5}
