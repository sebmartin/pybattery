from enum import Enum
import sys


class OutputFormat(Enum):
    """Enum for read formats."""

    JSON = "json"
    YAML = "yaml"

class OutputWriter:
    def __init__(self, output_format: OutputFormat):
        self.output_format = output_format

    def write(self, data: dict, fd=None):
        fd = fd or sys.stdout
        if self.output_format == OutputFormat.JSON:
            import json
            json.dump(data, indent=2, fp=fd)
        elif self.output_format == OutputFormat.YAML:
            import yaml
            print(yaml.dump(data, default_flow_style=False), file=fd)
        else:
            raise ValueError(f"Unsupported format: {self.output_format}")