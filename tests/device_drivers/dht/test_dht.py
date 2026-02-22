import pytest

from pybattery.device_drivers.dht import DhtDevice
from pybattery.device_drivers.dht.fakes import FakePigpio
from pybattery.models.config import DeviceConfig


@pytest.fixture
def config():
    return DeviceConfig(description="Test DHT sensor", driver="dht", args={"gpio": 17})


def test_dht_read_returns_status(config):
    """DhtDevice.read() always returns a dict with a status key."""
    hw = FakePigpio(bits=[])
    device = DhtDevice(config, hardware=hw)
    result = device.read()
    assert "status" in result
    assert "timestamp" in result
    assert "temperature" in result
    assert "humidity" in result


def test_dht_read_timeout_returns_error_dict(config):
    """When sensor returns insufficient bits, read() returns error dict without raising."""
    hw = FakePigpio(bits=[])  # no bits → decode fails
    device = DhtDevice(config, hardware=hw)
    result = device.read()
    assert result["status"] == "error"
    assert result["temperature"] is None
    assert result["humidity"] is None


def test_dht_read_hardware_error_returns_error_dict(config):
    """When hardware raises, read() returns error dict without raising."""
    hw = FakePigpio(error=RuntimeError("pigpio error"))
    device = DhtDevice(config, hardware=hw)
    result = device.read()
    assert result["status"] == "error"
    assert "error" in result


def test_dht_triggers_correct_gpio(config):
    """DhtDevice.read() triggers the configured GPIO pin."""
    hw = FakePigpio(bits=[])
    device = DhtDevice(config, hardware=hw)
    device.read()
    assert hw.triggered_gpios == [17]


def test_dht_config_gpio_default():
    """DhtDevice uses default GPIO 13 when not specified."""
    config = DeviceConfig(description="Test DHT", driver="dht")
    hw = FakePigpio(bits=[])
    device = DhtDevice(config, hardware=hw)
    assert device.gpio == 13
