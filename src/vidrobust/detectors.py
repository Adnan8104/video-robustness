"""Shared detector contract. Implementations live in adapters/."""
from pathlib import Path
from typing import Any, Protocol


class Detector(Protocol):
    checkpoint: dict
    preprocessing: str

    def __init__(self, root: Path): ...
    def prepare_frames(self, frames: list) -> Any: ...
    def predict(self, tensor: Any) -> dict: ...
