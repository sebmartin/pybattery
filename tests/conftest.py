import pytest

from pybattery.device_drivers.dht.fakes import FakePi
from pybattery.device_drivers.ds18b20.fakes import FakeSysfsReader
from pybattery.device_drivers.lcd.fakes import FakeLcd


@pytest.fixture
def fake_pigpio():
    return FakePi()


@pytest.fixture
def fake_sysfs():
    return FakeSysfsReader(sensors={"28-00000": "YES\nt=23456"})


@pytest.fixture
def fake_lcd():
    return FakeLcd()
