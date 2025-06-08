import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

import yaml

from pybattery.models.utils import from_dict


@dataclass
class DeviceConfig:
    def __init__(self, description: str, type: str, args: Optional[Dict[str, Any]] = None):
        self.description = description
        self.type = type
        self.args = args or {}

    description: str
    type: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Config:
    devices: Dict[str, DeviceConfig]

    @classmethod
    def from_file(cls, config_path: Union[str, None] = None) -> "Config":
        """Read the configuration file."""
        config_path = config_path or os.path.abspath(f"{os.path.dirname(__file__)}/../../config.yml")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")
        with open(config_path, "r") as config_file:
            config = yaml.safe_load(config_file)
        return from_dict(Config, config)
