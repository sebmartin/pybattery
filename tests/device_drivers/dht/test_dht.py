import pytest

from pybattery.device_drivers.dht import DhtDevice, AdafruitHardware
from pybattery.device_drivers.dht.fakes import FakeDht
from pybattery.models.config import DeviceConfig


@pytest.fixture
def config():
    return DeviceConfig(description="Test DHT sensor", driver="dht", args={"gpio": 17})


@pytest.fixture
def dhtxx_config():
    return DeviceConfig(
        description="Test DHTXX sensor", driver="dht",
        args={"gpio": 17, "model": "DHTXX"},
    )


# --- DhtDevice integration tests ---

def test_dht_read_returns_required_keys(config):
    """DhtDevice.read() always returns a dict with required keys."""
    hw = AdafruitHardware(sensor=FakeDht())
    result = DhtDevice(config, hardware=hw).read()
    assert "status" in result
    assert "timestamp" in result
    assert "temperature" in result
    assert "humidity" in result


def test_dht11_successful_read(config):
    """DHT11 returns correct temperature and humidity."""
    hw = AdafruitHardware(sensor=FakeDht(temperature=25.3, humidity=45.0))
    result = DhtDevice(config, hardware=hw).read()
    assert result["status"] == "ok"
    assert result["temperature"] == pytest.approx(25.3)
    assert result["humidity"] == pytest.approx(45.0)


def test_dhtxx_successful_read(dhtxx_config):
    """DHTXX returns correct temperature and humidity."""
    hw = AdafruitHardware(sensor=FakeDht(temperature=24.1, humidity=65.2))
    result = DhtDevice(dhtxx_config, hardware=hw).read()
    assert result["status"] == "ok"
    assert result["temperature"] == pytest.approx(24.1)
    assert result["humidity"] == pytest.approx(65.2)


def test_dhtxx_negative_temperature(dhtxx_config):
    """DHTXX handles negative temperature."""
    hw = AdafruitHardware(sensor=FakeDht(temperature=-10.5, humidity=50.0))
    result = DhtDevice(dhtxx_config, hardware=hw).read()
    assert result["status"] == "ok"
    assert result["temperature"] == pytest.approx(-10.5)


def test_dht_sensor_error_returns_error_dict(config):
    """When sensor raises, read() returns error dict without raising."""
    hw = AdafruitHardware(sensor=FakeDht(error=RuntimeError("sensor error")))
    result = DhtDevice(config, hardware=hw).read()
    assert result["status"] == "error"
    assert "error" in result
    assert result["temperature"] is None


def test_dht_sensor_returns_none_gives_error(config):
    """When sensor returns None values, read() returns error."""
    fake = FakeDht()
    fake._temperature = None
    hw = AdafruitHardware(sensor=fake)
    result = DhtDevice(config, hardware=hw).read()
    assert result["status"] == "error"
    assert result["temperature"] is None


def test_dht_config_gpio_default():
    """DhtDevice uses default GPIO 13 when not specified."""
    config = DeviceConfig(description="Test DHT", driver="dht")
    device = DhtDevice(config, hardware=AdafruitHardware(sensor=FakeDht()))
    assert device.gpio == 13


@pytest.mark.parametrize("temp,humidity", [
    (0, 20),
    (19.5, 40.1),
    (50, 80),
])
def test_dht11_various_values(config, temp, humidity):
    hw = AdafruitHardware(sensor=FakeDht(temperature=temp, humidity=humidity))
    result = DhtDevice(config, hardware=hw).read()
    assert result["status"] == "ok"
    assert result["temperature"] == pytest.approx(temp)
    assert result["humidity"] == pytest.approx(humidity)


@pytest.mark.parametrize("temp,humidity", [
    (-40.0, 0.0),
    (19.5, 40.1),
    (80.0, 99.9),
])
def test_dhtxx_various_values(dhtxx_config, temp, humidity):
    hw = AdafruitHardware(sensor=FakeDht(temperature=temp, humidity=humidity))
    result = DhtDevice(dhtxx_config, hardware=hw).read()
    assert result["status"] == "ok"
    assert result["temperature"] == pytest.approx(temp)
    assert result["humidity"] == pytest.approx(humidity)
