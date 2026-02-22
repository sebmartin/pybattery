import io
import os

__is_rpi: bool | None = None


def is_raspberrypi() -> bool:
    global __is_rpi
    if __is_rpi is None:
        try:
            with io.open("/sys/firmware/devicetree/base/model", "r") as m:
                if "raspberry pi" in m.read().lower():
                    __is_rpi = True
        except Exception:
            pass
        __is_rpi = False
    return __is_rpi


def allow_fake_devices() -> bool:
    return bool(os.environ.get("ALLOW_FAKE_DEVICES", False)) or is_raspberrypi()


def assert_allow_devices():
    if not allow_fake_devices():
        raise RuntimeError("Some devices failed to initialize")
