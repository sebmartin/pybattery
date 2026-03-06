import pytest

from pybattery.device_drivers.dht import (
    DhtDevice, PigpioHardware,
    _decode_dht11, _decode_dhtxx, _edges_to_bits,
)
from pybattery.device_drivers.dht.fakes import FakePi
from pybattery.models.config import DeviceConfig


def _bytes_to_bits(byte_list):
    """Convert a list of byte values to a flat list of 40 bits."""
    bits = []
    for b in byte_list:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits


def _dht11_bits(hum_int, hum_dec, temp_int, temp_dec):
    """Build a valid 40-bit DHT11 pattern with correct checksum."""
    checksum = (hum_int + hum_dec + temp_int + temp_dec) & 0xFF
    return _bytes_to_bits([hum_int, hum_dec, temp_int, temp_dec, checksum])


def _dhtxx_bits(hum_raw, temp_raw):
    """Build a valid 40-bit DHTXX pattern with correct checksum."""
    b0, b1 = (hum_raw >> 8) & 0xFF, hum_raw & 0xFF
    b2, b3 = (temp_raw >> 8) & 0xFF, temp_raw & 0xFF
    checksum = (b0 + b1 + b2 + b3) & 0xFF
    return _bytes_to_bits([b0, b1, b2, b3, checksum])


@pytest.fixture
def config():
    return DeviceConfig(description="Test DHT sensor", driver="dht", args={"gpio": 17})


@pytest.fixture
def dhtxx_config():
    return DeviceConfig(
        description="Test DHTXX sensor", driver="dht",
        args={"gpio": 17, "model": "DHTXX"},
    )


# --- DhtDevice integration tests (FakePi -> PigpioHardware -> decode) ---

def test_dht_read_returns_status(config):
    """DhtDevice.read() always returns a dict with required keys."""
    hw = PigpioHardware(pi=FakePi())
    device = DhtDevice(config, hardware=hw)
    result = device.read()
    assert "status" in result
    assert "timestamp" in result
    assert "temperature" in result
    assert "humidity" in result


def test_dht11_read_through_hardware(config):
    """Full path: FakePi -> PigpioHardware.trigger/read_bits -> decode -> result."""
    fake_pi = FakePi(temperature=25.3, humidity=45.0, model="DHT11")
    hw = PigpioHardware(pi=fake_pi)
    device = DhtDevice(config, hardware=hw)
    result = device.read()
    assert result["status"] == "ok"
    assert result["temperature"] == pytest.approx(25.3)
    assert result["humidity"] == pytest.approx(45.0)


def test_dhtxx_read_through_hardware(dhtxx_config):
    """Full path for DHTXX model through real hardware layer."""
    fake_pi = FakePi(temperature=24.1, humidity=65.2, model="DHTXX")
    hw = PigpioHardware(pi=fake_pi)
    device = DhtDevice(dhtxx_config, hardware=hw)
    result = device.read()
    assert result["status"] == "ok"
    assert result["temperature"] == pytest.approx(24.1)
    assert result["humidity"] == pytest.approx(65.2)


def test_dhtxx_negative_temperature(dhtxx_config):
    """DHTXX with negative temperature through full hardware path."""
    fake_pi = FakePi(temperature=-10.5, humidity=50.0, model="DHTXX")
    hw = PigpioHardware(pi=fake_pi)
    device = DhtDevice(dhtxx_config, hardware=hw)
    result = device.read()
    assert result["status"] == "ok"
    assert result["temperature"] == pytest.approx(-10.5)
    assert result["humidity"] == pytest.approx(50.0)


def test_dht11_bad_checksum_returns_error(config):
    """Bad checksum through full hardware path returns error."""
    fake_pi = FakePi(temperature=25.0, humidity=45.0, model="DHT11", checksum=0xFF)
    hw = PigpioHardware(pi=fake_pi)
    device = DhtDevice(config, hardware=hw)
    result = device.read()
    assert result["status"] == "error"
    assert result["temperature"] is None


def test_dht_hardware_error_returns_error_dict(config):
    """When hardware raises, read() returns error dict without raising."""
    fake_pi = FakePi(error=RuntimeError("pigpio error"))
    hw = PigpioHardware(pi=fake_pi)
    device = DhtDevice(config, hardware=hw)
    result = device.read()
    assert result["status"] == "error"
    assert "error" in result


def test_dht_triggers_correct_gpio(config):
    """DhtDevice.read() triggers the configured GPIO pin via write(gpio, 0)."""
    fake_pi = FakePi(temperature=20.0, humidity=50.0)
    hw = PigpioHardware(pi=fake_pi)
    device = DhtDevice(config, hardware=hw)
    device.read()
    assert 17 in fake_pi.triggered_gpios


def test_dht_config_gpio_default():
    """DhtDevice uses default GPIO 13 when not specified."""
    config = DeviceConfig(description="Test DHT", driver="dht")
    hw = PigpioHardware(pi=FakePi())
    device = DhtDevice(config, hardware=hw)
    assert device.gpio == 13


# --- DHT11 parametrized tests ---

@pytest.mark.parametrize("temp,humidity", [
    (0, 20),
    (19.5, 40.1),
    (50, 80),
])
def test_dht11_various_values(config, temp, humidity):
    """DHT11 correctly reads various temperature/humidity values."""
    fake_pi = FakePi(temperature=temp, humidity=humidity, model="DHT11")
    hw = PigpioHardware(pi=fake_pi)
    device = DhtDevice(config, hardware=hw)
    result = device.read()
    assert result["status"] == "ok"
    assert result["temperature"] == pytest.approx(temp)
    assert result["humidity"] == pytest.approx(humidity)


# --- DHTXX parametrized tests ---

@pytest.mark.parametrize("temp,humidity", [
    (-40.0, 0.0),
    (19.5, 40.1),
    (80.0, 99.9),
])
def test_dhtxx_various_values(dhtxx_config, temp, humidity):
    """DHTXX correctly reads various temperature/humidity values."""
    fake_pi = FakePi(temperature=temp, humidity=humidity, model="DHTXX")
    hw = PigpioHardware(pi=fake_pi)
    device = DhtDevice(dhtxx_config, hardware=hw)
    result = device.read()
    assert result["status"] == "ok"
    assert result["temperature"] == pytest.approx(temp)
    assert result["humidity"] == pytest.approx(humidity)


# --- Pure decode function tests ---

def test_decode_dht11_direct():
    """_decode_dht11 returns correct values for valid bits."""
    bits = _dht11_bits(60, 0, 22, 5)
    result = _decode_dht11(bits)
    assert result is not None
    assert result["humidity"] == 60.0
    assert result["temperature"] == pytest.approx(22.5)


def test_decode_dht11_insufficient_bits():
    """_decode_dht11 returns None when fewer than 40 bits."""
    assert _decode_dht11([0] * 39) is None


def test_decode_dhtxx_checksum_failure():
    """_decode_dhtxx returns None on bad checksum."""
    bits = _dhtxx_bits(500, 241)
    bits[-1] ^= 1
    assert _decode_dhtxx(bits) is None


def test_decode_dhtxx_insufficient_bits():
    """_decode_dhtxx returns None when fewer than 40 bits."""
    assert _decode_dhtxx([0] * 39) is None


# --- Out-of-range data validation tests ---

@pytest.mark.parametrize("temp,humidity", [
    (61, 50),    # temp too high for DHT11
    (20, 101),   # humidity too high
    (20, 8),     # humidity too low (DHT11 min is 9)
    (-1, 50),    # temp below DHT11 minimum
])
def test_dht11_bad_data_returns_error(config, temp, humidity):
    """DHT11 readings outside physical range return error."""
    fake_pi = FakePi(temperature=temp, humidity=humidity, model="DHT11")
    hw = PigpioHardware(pi=fake_pi)
    device = DhtDevice(config, hardware=hw)
    result = device.read()
    assert result["status"] == "error"
    assert result["temperature"] is None


@pytest.mark.parametrize("temp,humidity", [
    (-51.0, 50),   # temp too low for DHTXX
    (136.0, 50),   # temp too high
    (20.0, 111),   # humidity too high
])
def test_dhtxx_bad_data_returns_error(dhtxx_config, temp, humidity):
    """DHTXX readings outside physical range return error."""
    fake_pi = FakePi(temperature=temp, humidity=humidity, model="DHTXX")
    hw = PigpioHardware(pi=fake_pi)
    device = DhtDevice(dhtxx_config, hardware=hw)
    result = device.read()
    assert result["status"] == "error"
    assert result["temperature"] is None


# --- Edge-to-bits timing tests ---

def _simulate_edges(data_bits):
    """Simulate DHT edge events for a sequence of data bits."""
    edges = []
    tick = 1000
    # Response pulse
    edges.append((1, tick))
    tick += 80
    edges.append((0, tick))
    # Data bits
    for bit in data_bits:
        tick += 50
        edges.append((1, tick))
        tick += 26 if bit == 0 else 70
        edges.append((0, tick))
    return edges


def test_edges_to_bits_decodes_mixed_pattern():
    """_edges_to_bits correctly decodes a realistic DHT11 bit pattern."""
    data_bits = _dht11_bits(45, 0, 25, 3)
    edges = _simulate_edges(data_bits)
    result = _edges_to_bits(edges)
    assert result == data_bits
    assert _decode_dht11(result) == {"temperature": 25.3, "humidity": 45.0}


def test_edges_to_bits_empty():
    """_edges_to_bits returns empty list when no edges received."""
    assert _edges_to_bits([]) == []


def test_edges_to_bits_insufficient():
    """_edges_to_bits returns partial bits when not enough edges."""
    data_bits = [1, 0, 1]
    edges = _simulate_edges(data_bits)
    assert _edges_to_bits(edges) == [1, 0, 1]
