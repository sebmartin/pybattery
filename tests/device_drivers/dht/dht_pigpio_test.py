import pytest

from pybattery.device_drivers.dht.dht_pigpio import DhtSensor
from pybattery.device_drivers.dht.models import DhtModel, DhtStatus
from tests.device_drivers.dht.fake_pigpio import (
    FakePi,
)


@pytest.mark.parametrize(
    "model, temp, humidity",
    [
        # DHT11
        (DhtModel.DHT11, 0, 10),
        (DhtModel.DHT11, 19.5, 40.1),
        (DhtModel.DHT11, 60, 90),
        # DTHXX
        (DhtModel.DHTXX, -50, 0),
        (DhtModel.DHTXX, 19.5, 40.1),
        (DhtModel.DHTXX, 135.0, 110.0),
    ],
)
def test_dht11__valid(model, temp, humidity):
    fake_pi = FakePi(temp, humidity, model)
    sensor = DhtSensor(gpio=4, model=model, pi=fake_pi)
    timestamp, gpio, status, t, h = sensor.read()

    assert status == DhtStatus.DHT_GOOD
    assert t == temp
    assert h == humidity
    assert gpio == 4


def test_dht11__bad_checksum():
    model = DhtModel.DHT11
    fake_pi = FakePi(19.5, 40.1, model, checksum=123)
    sensor = DhtSensor(gpio=4, model=DhtModel.DHT11, pi=fake_pi)
    _, _, status, _, _ = sensor.read()

    assert status == DhtStatus.DHT_BAD_CHECKSUM


@pytest.mark.parametrize(
    "model, temp, humidity",
    [
        (DhtModel.DHT11, 61, 50),
        (DhtModel.DHT11, 20, 101),
        (DhtModel.DHT11, 20, 1),
        (DhtModel.DHTXX, -51.0, 50),
        (DhtModel.DHTXX, 136.0, 50),
        (DhtModel.DHTXX, 20.0, 111),
    ],
)
def test_dht11__bad_data(model, temp, humidity):
    fake_pi = FakePi(temp, humidity, model)
    sensor = DhtSensor(gpio=4, model=model, pi=fake_pi)
    _, _, status, _, _ = sensor.read()

    assert status == DhtStatus.DHT_BAD_DATA
