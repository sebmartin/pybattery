import sys
from textwrap import dedent
from typing import Any, Dict, List, Optional
from unittest import mock

import pytest
import yaml
from yaml import Loader
import json

from pybattery.main import main
from pybattery.models.config import Config, DeviceConfig
from pybattery.models.device import Device
from pybattery.models.utils import from_dict
from pybattery.output_writer import OutputFormat


@pytest.fixture
def fake_config():
    config_yaml = dedent(
        """
        devices:
            test-reader:
                description: Test read device
                driver: test_read_driver
                data: this is read-only data from the config
            test-writer:
                description: Test write device
                driver: test_write_driver
            test-reader-writer:
                description: Test read-write device
                driver: test_read_write_driver
                data: this is read-write data from the config
        """
    ).strip()
    config_dict = yaml.safe_load(config_yaml)
    return from_dict(Config, config_dict)


@pytest.fixture(autouse=True)
def mock_device_drivers():
    with mock.patch("pybattery.api.list_device_drivers") as mock_list:

        class FakeDevice(Device):
            def __init__(self, config: DeviceConfig):
                super().__init__(config)
                self.data = config.args.get("data", None)

        class ReadDevice(FakeDevice):
            """Test read device"""

            def read(self) -> Optional[Dict[str, Any]]:
                return {"data": self.data}

        class WriteDevice(FakeDevice):
            """Test write device"""

            outputs: List[Any] = []

            def write(self, value: Any) -> None:
                print(f"Writing {value} to {self.__class__.__name__}")

        class ReadWriteDevice(ReadDevice, WriteDevice):
            """Test read-write device"""

        mock_list.return_value = {
            "test_read_driver": ReadDevice,
            "test_write_driver": WriteDevice,
            "test_read_write_driver": ReadWriteDevice,
        }
        yield mock_list


def test_help(capsys):
    test_args = ["main.py", "--help"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 0


def test_devices(fake_config, capsys):
    test_args = ["main.py", "devices"]
    with mock.patch.object(sys, "argv", test_args):
        main(fake_config)

    captured = capsys.readouterr()
    assert yaml.load(captured.out, Loader=Loader) == {
        "devices": {
            "test-reader": "Test read device",
            "test-reader-writer": "Test read-write device",
            "test-writer": "Test write device",
        }
    }, "Output should be valid YAML"


def test_drivers(fake_config, capsys):
    test_args = ["main.py", "drivers"]
    with mock.patch.object(sys, "argv", test_args):
        main(fake_config)

    captured = capsys.readouterr()
    assert yaml.load(captured.out, Loader=Loader) == {
        "device_drivers": {
            "test_read_driver": "Test read device",
            "test_write_driver": "Test write device",
            "test_read_write_driver": "Test read-write device",
        }
    }, "Output should be valid YAML"


def test_read__one_device__default_format(fake_config, capsys):
    test_args = ["main.py", "read", "test-reader"]
    with mock.patch.object(sys, "argv", test_args):
        main(fake_config)

    captured = capsys.readouterr()
    output = "data: this is read-only data from the config"
    assert output.strip() == captured.out.strip()


@pytest.mark.parametrize("format", [OutputFormat.JSON, OutputFormat.YAML])
def test_read__one_device(format, fake_config, capsys):
    test_args = ["main.py", "read", "test-reader", "-f", format.value]
    with mock.patch.object(sys, "argv", test_args):
        main(fake_config)

    captured = capsys.readouterr()
    if format == OutputFormat.JSON:
        data = json.loads(captured.out)
    elif format == OutputFormat.YAML:
        data = yaml.load(captured.out, Loader=Loader)

    assert data == {"data": "this is read-only data from the config"}


def test_read__invalid_device(fake_config, capsys):
    test_args = ["main.py", "read", "test-writer"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit):
            main(fake_config)

    captured = capsys.readouterr()
    output = dedent(
        """
        usage: main.py read [-h] [-f {json,yaml}] [device ...]
        main.py read: error: argument device: invalid choice: 'test-writer' (choose from test-reader, test-reader-writer)
        """
    )
    assert output.strip() == captured.err.strip()


def test_write__invalid_device(fake_config, capsys):
    test_args = ["main.py", "write", "test-reader", "some-value"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit):
            main(fake_config)

    captured = capsys.readouterr()
    output = dedent(
        """
        usage: main.py write [-h] device value
        main.py write: error: argument device: invalid choice: 'test-reader' (choose from test-writer, test-reader-writer)
        """
    )
    assert output.strip() == captured.err.strip()


def test_write__valid_device(fake_config, capsys):
    test_args = ["main.py", "write", "test-writer", "hello"]
    with mock.patch.object(sys, "argv", test_args):
        main(fake_config)

    captured = capsys.readouterr()
    assert "Writing hello to WriteDevice" in captured.out


def test_config_error_displays_cleanly(capsys):
    """Config loading errors show a clean message, not a traceback."""
    test_args = ["main.py", "devices"]
    with mock.patch.object(sys, "argv", test_args):
        with mock.patch("pybattery.main.Config.from_file", side_effect=FileNotFoundError("no config")):
            with pytest.raises(SystemExit) as exc:
                main()
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Error loading config" in captured.err
