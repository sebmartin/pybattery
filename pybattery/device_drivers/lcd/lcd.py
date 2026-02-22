from enum import IntEnum
from typing import Literal, Protocol

from pybattery.rpi import assert_allow_devices


class NumberingMode(IntEnum):
    BOARD = 10
    BCM = 11


class LcdProtocol(Protocol):
    def write_string(self, text: str): ...
    def clear(self): ...


class FakeCharLCD(LcdProtocol):
    def __init__(self, *args, **kwargs):
        self.lines = []

    def write_string(self, text: str):
        self.lines.append(text)

    def clear(self):
        self.lines = []


def create_lcd(
    numbering_mode: NumberingMode | None = None,
    pin_rs: int | None = None,
    pin_rw: int | None = None,
    pin_e: int | None = None,
    pins_data: list[int] | None = None,
    pin_backlight: int | None = None,
    backlight_mode: Literal["active_high", "active_low"] = "active_low",
    backlight_enabled=True,
    cols: int = 20,
    rows: int = 4,
    dotsize: Literal[8, 10] = 8,
    charmap: Literal["A02", "A02", "ST0B"] | None = None,
    auto_linebreaks=True,
    compat_mode=False,
) -> LcdProtocol:
    try:
        from RPLCD.gpio import CharLCD  # pyright: ignore[reportMissingImports]
    except ImportError:
        assert_allow_devices()
        CharLCD = FakeCharLCD

    return CharLCD(
        numbering_mode=numbering_mode,
        pin_rs=pin_rs,
        pin_rw=pin_rw,
        pin_e=pin_e,
        pins_data=pins_data,
        pin_backlight=pin_backlight,
        backlight_mode=backlight_mode,
        backlight_enabled=backlight_enabled,
        cols=cols,
        rows=rows,
        dotsize=dotsize,
        charmap=charmap,
        auto_linebreaks=auto_linebreaks,
        compat_mode=compat_mode,
    )
