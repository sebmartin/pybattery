from typing import Optional
from pybattery.models.config import DeviceConfig
from pybattery.models.device import Device

from RPLCD.gpio import CharLCD
from RPi import GPIO

LCD_COLUMNS = 16
LCD_ROWS = 2

class LcdDevice(Device):
    """Control a 16x2 LCD display."""
    rs: int
    en: int
    d4: int
    d5: int
    d6: int
    d7: int

    def __init__(self, config: DeviceConfig) -> None:
        """Initialize the LCD display."""
        super().__init__(config)

        gpio = config.args.get("gpio", {})
        self.rs = gpio.get("rs", 26)
        self.en = gpio.get("en", 19)
        self.d4 = gpio.get("d4", 13)
        self.d5 = gpio.get("d5", 6)
        self.d6 = gpio.get("d6", 5)
        self.d7 = gpio.get("d7", 11)

        self._lcd: Optional[CharLCD] = None

    @property
    def lcd(self) -> CharLCD:
        """Return the LCD object."""

        if not self._lcd:
            self._lcd = CharLCD(
                numbering_mode=GPIO.BCM,
                cols=LCD_COLUMNS,
                rows=LCD_ROWS,
                pin_rs=self.rs,
                pin_e=self.en,
                pins_data=[
                    self.d4,
                    self.d5,
                    self.d6,
                    self.d7,
                ],
                auto_linebreaks=False,
            )
            self._lcd.clear()
        return self._lcd

    def write(self, value: str, *other_lines) -> None:
        """
        Write a value to the LCD display. `value` can container carriage returns \r\n to
        print on multiple lines. Alternatively, `other_lines` can be used to add additional lines
        to the display.

        e.g. write("Line 1\r\nLine 2") == write("Line 1", "Line 2")
        """
        # Placeholder for actual implementation
        self.lcd.clear()
        lines = value.split("\n") + list(other_lines)
        self.lcd.write_string("\r\n".join(lines[:LCD_ROWS]))


Device = LcdDevice

__all__ = ["Device", "LcdDevice"]
