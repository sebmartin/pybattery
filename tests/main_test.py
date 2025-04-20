import sys
from textwrap import dedent
from typing import Any, Dict, List
from unittest import mock

import pytest
import yaml

from pybattery.main import main
from pybattery.models.config import Config, DeviceConfig
from pybattery.models.utils import from_dict


@pytest.fixture
def fake_config():
    config_yaml = dedent(
        """
        devices:
            test-reader:
                description: Test read device
                type: test_read_device_type
                data: this is read-only data from the config
            test-writer:
                description: Test write device
                type: test_write_device_type
            test-reader-writer:
                description: Test read-write device
                type: test_read_write_device_type
                data: this is read-write data from the config
        """
    ).strip()
    config_dict = yaml.safe_load(config_yaml)
    return from_dict(Config, config_dict)


@pytest.fixture(autouse=True)
def mock_device_types():
    with mock.patch("pybattery.main._list_device_types") as mock_list_device_types:

        class Device:
            def __init__(self, config: DeviceConfig):
                self.config = config
                self.data = config.args.get("data", None)

        class ReadDevice(Device):
            """Test read device"""

            def read(self) -> Dict[str, Any]:
                return {"data": self.data}

        class WriteDevice(Device):
            """Test write device"""

            outputs: List[Any] = []

            def write(self, value: Any) -> None:
                # self.outputs.append(value)
                print(f"Writing {value} to {self.__class__.__name__}")

        class ReadWriteDevice(ReadDevice, WriteDevice):
            """Test read-write device"""

        mock_list_device_types.return_value = {
            "test_read_device_type": ReadDevice,
            "test_write_device_type": WriteDevice,
            "test_read_write_device_type": ReadWriteDevice,
        }
        yield mock_list_device_types


def test_help(capsys):
    test_args = ["main.py", "--help"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 0


def test_list(fake_config, capsys):
    test_args = ["main.py", "list"]
    with mock.patch.object(sys, "argv", test_args):
        main(fake_config)

    captured = capsys.readouterr()
    output = dedent(
        """
        Available devices:
        - test-reader: Test read device
        - test-writer: Test write device
        - test-reader-writer: Test read-write device
        """
    )
    assert output.strip() == captured.out.strip()


def test_list_device_types(fake_config, capsys):
    test_args = ["main.py", "list-types"]
    with mock.patch.object(sys, "argv", test_args):
        main(fake_config)

    captured = capsys.readouterr()
    output = dedent(
        """
        Available device types:
        - test_read_device_type: Test read device
        - test_write_device_type: Test write device
        - test_read_write_device_type: Test read-write device
        """
    )
    assert output.strip() == captured.out.strip()


def test_read__one_device__default_format(fake_config, capsys):
    test_args = ["main.py", "read", "test-reader"]
    with mock.patch.object(sys, "argv", test_args):
        main(fake_config)

    captured = capsys.readouterr()
    output = "data: this is read-only data from the config"
    assert output.strip() == captured.out.strip()


@pytest.mark.parametrize("format", ["json", "yaml"])
def test_read__one_device(format, fake_config, capsys):
    test_args = ["main.py", "read", "test-reader", "-f", f"{format}"]
    with mock.patch.object(sys, "argv", test_args):
        main(fake_config)

    captured = capsys.readouterr()
    if format == "json":
        expected_output = dedent(
            """
            {
                "data": "this is read-only data from the config"
            }
            """
        )
    elif format == "yaml":
        expected_output = "data: this is read-only data from the config"

    assert expected_output.strip() == captured.out.strip()


def test_read__invalid_device(fake_config, capsys):
    test_args = ["main.py", "read", "test-writer"]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit):
            main(fake_config)

    captured = capsys.readouterr()
    output = dedent(
        """
        usage: main.py read [-h] [-f {json,yaml}] [device [device ...]]
        main.py read: error: argument device: invalid choice: 'test-writer' (choose from 'test-reader', 'test-reader-writer')
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
        main.py write: error: argument device: invalid choice: 'test-reader' (choose from 'test-writer', 'test-reader-writer')
        """
    )
    assert output.strip() == captured.err.strip()
