from typing import Any
import pigpio

from unittest import mock
import pytest

from pybattery.device_drivers.dht.dht_driver import Dht11Driver, DhtConfig
from pybattery.device_drivers.dht.models import DhtModel, DhtStatus
from pybattery.models.config import DeviceConfig
from tests.device_drivers.dht.fake_pigpio import FakePi


@pytest.fixture
def fake_pi():
    return FakePi(19.5, 20.0, DhtModel.DHT11)


@pytest.fixture
def config_args() -> dict[str, Any]:
    return DhtConfig(
        gpio=4,
        model=DhtModel.DHT11,
    ).model_dump()


@pytest.fixture
def config(config_args) -> DeviceConfig:
    return DeviceConfig(
        driver="dht",
        description="DHT11 Sensor",
        args=config_args,
    )


def test_config(fake_pi, config):
    _ = Dht11Driver(config, fake_pi)
    assert fake_pi.mode_gpio == config.args["gpio"]
    assert fake_pi.mode == pigpio.INPUT


def test_read(fake_pi, config):
    driver = Dht11Driver(config, fake_pi)
    output = driver.read()
    assert output == {
        "humidity": 20.0,
        "status": DhtStatus.DHT_GOOD,
        "temperature": 19.5,
        "timestamp": mock.ANY,
    }


def test_read__runtime_error(fake_pi, config):
    driver = Dht11Driver(config, fake_pi)
    fake_pi.data = None  # Cause an exception on read
    output = driver.read()

    assert output == {
        "humidity": 0,
        "status": DhtStatus.DHT_BAD_DATA,
        "temperature": 0,
        "timestamp": mock.ANY,
    }
