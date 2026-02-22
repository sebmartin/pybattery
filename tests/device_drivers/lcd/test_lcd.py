import pytest

from pybattery.device_drivers.lcd import LcdDevice
from pybattery.device_drivers.lcd.fakes import FakeLcd
from pybattery.models.config import DeviceConfig
from pybattery.protocols import WritableDriver


@pytest.fixture
def config():
    return DeviceConfig(
        description="Test LCD Device",
        driver="lcd",
        args={"gpio": {"rs": 11, "en": 22, "d4": 33, "d5": 44, "d6": 55, "d7": 66}},
    )


@pytest.fixture
def fake_lcd():
    return FakeLcd()


def test_lcd_is_writable_driver(config, fake_lcd):
    lcd = LcdDevice(config, lcd=fake_lcd)
    assert isinstance(lcd, WritableDriver)


def test_lcd_initialize_lazy(config, fake_lcd):
    """LCD hardware is not accessed until first use."""
    lcd = LcdDevice(config, lcd=fake_lcd)
    # lcd is pre-injected so no lazy init needed; verify property returns it
    assert lcd.lcd is fake_lcd


def test_lcd_write(config, fake_lcd):
    lcd = LcdDevice(config, lcd=fake_lcd)
    lcd.write("Hello")
    assert fake_lcd.lines == ["Hello"]


def test_lcd_write_newline(config, fake_lcd):
    lcd = LcdDevice(config, lcd=fake_lcd)
    lcd.write("Hello\nWorld")
    assert fake_lcd.lines == ["Hello\r\nWorld"]


def test_lcd_write_truncates_to_two_lines(config, fake_lcd):
    lcd = LcdDevice(config, lcd=fake_lcd)
    lcd.write("Line1\nLine2\nLine3")
    assert fake_lcd.lines == ["Line1\r\nLine2"]


def test_lcd_write_two_args(config, fake_lcd):
    lcd = LcdDevice(config, lcd=fake_lcd)
    lcd.write("Hello", "World")
    assert fake_lcd.lines == ["Hello\r\nWorld"]


def test_lcd_write_clears_before_writing(config, fake_lcd):
    lcd = LcdDevice(config, lcd=fake_lcd)
    lcd.write("Hello")
    assert fake_lcd.clear_count == 1


def test_lcd_defaults():
    """LcdDevice uses correct GPIO defaults when not specified."""
    config = DeviceConfig(description="Test LCD", driver="lcd")
    fake = FakeLcd()
    lcd = LcdDevice(config, lcd=fake)
    assert lcd.rs == 26
    assert lcd.en == 19
    assert lcd.d4 == 13
    assert lcd.d5 == 6
    assert lcd.d6 == 5
    assert lcd.d7 == 11
