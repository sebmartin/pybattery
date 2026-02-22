import os
from unittest import mock

import pytest

from pybattery.rpi import fake_devices_allowed, is_raspberry_pi, require_hardware


def test_is_raspberry_pi_returns_false_on_macos():
    """is_raspberry_pi() returns False when /proc/device-tree/model does not exist."""
    with mock.patch("pybattery.rpi.Path") as mock_path:
        mock_path.return_value.read_text.side_effect = FileNotFoundError
        assert is_raspberry_pi() is False


def test_is_raspberry_pi_returns_true_when_model_matches():
    """is_raspberry_pi() returns True when model file contains 'raspberry pi'."""
    with mock.patch("pybattery.rpi.Path") as mock_path:
        mock_path.return_value.read_text.return_value = "Raspberry Pi 4 Model B Rev 1.4"
        assert is_raspberry_pi() is True


def test_is_raspberry_pi_returns_false_for_other_model():
    """is_raspberry_pi() returns False for non-Pi devices."""
    with mock.patch("pybattery.rpi.Path") as mock_path:
        mock_path.return_value.read_text.return_value = "Some Other Board"
        assert is_raspberry_pi() is False


def test_fake_devices_allowed_when_env_var_set():
    """fake_devices_allowed() returns True when ALLOW_FAKE_DEVICES is set."""
    with mock.patch.dict(os.environ, {"ALLOW_FAKE_DEVICES": "1"}):
        with mock.patch("pybattery.rpi.is_raspberry_pi", return_value=False):
            assert fake_devices_allowed() is True


def test_fake_devices_not_allowed_without_env_or_pi():
    """fake_devices_allowed() returns False on non-Pi without the env var."""
    with mock.patch.dict(os.environ, {}, clear=True):
        with mock.patch("pybattery.rpi.is_raspberry_pi", return_value=False):
            assert fake_devices_allowed() is False


def test_require_hardware_raises_without_pi_or_env():
    """require_hardware() raises RuntimeError when not on Pi and env var not set."""
    with mock.patch("pybattery.rpi.fake_devices_allowed", return_value=False):
        with pytest.raises(RuntimeError, match="ALLOW_FAKE_DEVICES"):
            require_hardware("TestDevice")


def test_require_hardware_does_not_raise_when_allowed():
    """require_hardware() does not raise when fake devices are allowed."""
    with mock.patch("pybattery.rpi.fake_devices_allowed", return_value=True):
        require_hardware("TestDevice")  # should not raise
