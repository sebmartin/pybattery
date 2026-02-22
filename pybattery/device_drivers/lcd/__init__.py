from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from pybattery.models.config import DeviceConfig
from pybattery.models.device import Device
from pybattery.rpi import fake_devices_allowed

try:
    from RPLCD.gpio import CharLCD
    from RPi import GPIO
    _HAS_RPLCD = True
except ImportError:
    _HAS_RPLCD = False
    CharLCD = None
    GPIO = None

LCD_COLUMNS = 16
LCD_ROWS = 2


@runtime_checkable
class LcdHardware(Protocol):
    def clear(self) -> None: ...
    def write_string(self, text: str) -> None: ...


def _create_lcd(rs: int, en: int, d4: int, d5: int, d6: int, d7: int) -> LcdHardware:
    """Factory: return real CharLCD or FakeLcd based on hardware availability."""
    if _HAS_RPLCD and not fake_devices_allowed():
        return CharLCD(
            numbering_mode=GPIO.BCM,
            cols=LCD_COLUMNS,
            rows=LCD_ROWS,
            pin_rs=rs,
            pin_e=en,
            pins_data=[d4, d5, d6, d7],
            auto_linebreaks=False,
        )
    from pybattery.device_drivers.lcd.fakes import FakeLcd
    return FakeLcd()


class LcdDevice(Device):
    """Control a 16x2 LCD display."""

    def __init__(self, config: DeviceConfig, lcd: Optional[LcdHardware] = None) -> None:
        """Initialize the LCD display."""
        super().__init__(config)
        gpio = config.args.get("gpio", {})
        self.rs = gpio.get("rs", 26)
        self.en = gpio.get("en", 19)
        self.d4 = gpio.get("d4", 13)
        self.d5 = gpio.get("d5", 6)
        self.d6 = gpio.get("d6", 5)
        self.d7 = gpio.get("d7", 11)
        self._lcd: Optional[LcdHardware] = lcd

    @property
    def lcd(self) -> LcdHardware:
        """Return the LCD object, initializing lazily on first access."""
        if self._lcd is None:
            self._lcd = _create_lcd(self.rs, self.en, self.d4, self.d5, self.d6, self.d7)
            self._lcd.clear()
        return self._lcd

    def write(self, value: str, *other_lines: str) -> None:
        """
        Write a value to the LCD display. `value` can contain carriage returns \\r\\n to
        print on multiple lines. Alternatively, `other_lines` can be used to add additional lines
        to the display.

        e.g. write("Line 1\\r\\nLine 2") == write("Line 1", "Line 2")
        """
        self.lcd.clear()
        lines = value.split("\n") + list(other_lines)
        self.lcd.write_string("\r\n".join(lines[:LCD_ROWS]))


Device = LcdDevice

__all__ = ["Device", "LcdDevice", "LcdHardware"]
