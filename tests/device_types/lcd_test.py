import pytest
import mock
from mock import MagicMock
from pybattery.device_types.lcd import LcdDevice
from pybattery.protocols import WritableDeviceType
from pybattery.models.config import DeviceConfig


@pytest.fixture
def mock_lcd_api():
    mock = MagicMock()
    return mock

@pytest.fixture(autouse=True)
def mock_gpio():
    with mock.patch("pybattery.device_types.lcd.GPIO") as mock_gpio:
        yield mock_gpio


@pytest.fixture(autouse=True)
def mock_lcd_factory(mock_lcd_api):
    with mock.patch("pybattery.device_types.lcd.CharLCD", return_value=mock_lcd_api) as lcd_factory:
        yield lcd_factory


@pytest.fixture
def config():
    """Fixture to provide a mock DeviceConfig."""
    return DeviceConfig(
        description="Test LCD Device",
        type="lcd",
        args={"gpio": {"rs": 11, "en": 22, "d4": 33, "d5": 44, "d6": 55, "d7": 66}},
    )


def test_lcd_is_readable_device_type(config: DeviceConfig):
    lcd = LcdDevice(config)
    assert isinstance(lcd, WritableDeviceType), "LcdDevice should be a WritableDeviceType"


def test_lcd_initialize(config: DeviceConfig, mock_lcd_factory, mock_gpio):
    lcd = LcdDevice(config)
    _ = lcd.lcd
    _ = lcd.lcd  # Ensure the LCD is initialized only once

    mock_lcd_factory.assert_called_once_with(
        numbering_mode=mock_gpio.BCM, cols=16, rows=2, pin_rs=11, pin_e=22, pins_data=[33, 44, 55, 66], auto_linebreaks=False,
    )
    assert lcd.lcd is not None, "LCD should be initialized"


def test_lcd_initialize__defaults(mock_gpio, mock_lcd_factory, mock_lcd_api):
    minimal_config = DeviceConfig(
        description="Test LCD Device",
        type="lcd"
    )
    lcd = LcdDevice(minimal_config)
    _ = lcd.lcd

    mock_lcd_api.clear.assert_called_once()
    mock_lcd_factory.assert_called_once_with(
        numbering_mode=mock_gpio.BCM, cols=16, rows=2, pin_rs=26, pin_e=19, pins_data=[13, 6, 5, 11], auto_linebreaks=False
    )
    assert lcd.lcd is not None, "LCD should be initialized"

@pytest.mark.parametrize("value, expected", [
    ("Hello", "Hello"),
    ("Hello\nWorld", "Hello\r\nWorld"),
    ("Line1\nLine2\nLine3", "Line1\r\nLine2"),
])
def test_lcd_write(value: str, expected: str, config: DeviceConfig, mock_lcd_api):
    lcd = LcdDevice(config)

    lcd.write(value)
    assert mock_lcd_api.clear.call_count == 2
    mock_lcd_api.write_string.assert_called_once_with(expected)


def test_lcd_write_two_args(config: DeviceConfig, mock_lcd_api):
    lcd = LcdDevice(config)

    lcd.write("Hello", "World")
    mock_lcd_api.write_string.assert_called_once_with("Hello\r\nWorld")