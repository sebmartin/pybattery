from typing import List


class FakeLcd:
    """Records write_string/clear calls for assertion in tests."""

    def __init__(self):
        self.lines: List[str] = []
        self.clear_count: int = 0

    def clear(self) -> None:
        self.clear_count += 1
        self.lines = []

    def write_string(self, text: str) -> None:
        self.lines.append(text)
