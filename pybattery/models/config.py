from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class DeviceConfig:
    def __init__(self, description: str, type: str, args: Dict[str, Any]):
        self.description = description
        self.type = type
        self.args = args or {}

    description: str
    type: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Config:
    devices: Dict[str, DeviceConfig]
