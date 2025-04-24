from pybattery.models.config import DeviceConfig
from adafruit_character_lcd.character_lcd import Character_LCD_Mono

LCD_COLUMNS = 16
LCD_ROWS = 2


class LcdDevice:
    """Control a 16x2 LCD display."""

    rs: int
    en: int
    d4: int
    d5: int
    d6: int
    d7: int

    def __init__(self, config: DeviceConfig) -> None:
        """Initialize the LCD display."""
        gpio = config.args.get("gpio", {})
        self.rs = gpio.get("rs", 26)
        self.en = gpio.get("en", 19)
        self.d4 = gpio.get("d4", 13)
        self.d5 = gpio.get("d5", 6)
        self.d6 = gpio.get("d6", 5)
        self.d7 = gpio.get("d7", 11)
        self._lcd = None

    @property
    def lcd(self) -> Character_LCD_Mono:
        """Return the LCD object."""
        from digitalio import DigitalInOut
        from adafruit_blinka.microcontroller.generic_linux.rpi_gpio_pin import Pin

        if not self._lcd:
            self._lcd = Character_LCD_Mono(
                DigitalInOut(Pin(self.rs)),
                DigitalInOut(Pin(self.en)),
                DigitalInOut(Pin(self.d4)),
                DigitalInOut(Pin(self.d5)),
                DigitalInOut(Pin(self.d6)),
                DigitalInOut(Pin(self.d7)),
                LCD_COLUMNS,
                LCD_ROWS,
            )
            self._lcd.clear()
        return self._lcd

    def write(self, value: str) -> None:
        """Write a value to the LCD display."""
        # Placeholder for actual implementation
        self.lcd.message = str(value)


Device = LcdDevice

__all__ = ["Device", "LcdDevice"]
