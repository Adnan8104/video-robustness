"""Discover registered adapters; validation never downloads or loads weights."""
from dataclasses import dataclass
import importlib
from pathlib import Path
import pkgutil
import re

_ADAPTERS = {}


@dataclass(frozen=True)
class AdapterSpec:
    adapter: type

    def create(self, root):
        from .artifacts import download
        checkpoint = self.adapter.checkpoint
        download(checkpoint["url"], root / checkpoint["path"], checkpoint["sha256"])
        return self.adapter(root)

    def metadata(self, root):
        module = importlib.import_module(self.adapter.__module__)
        return dict(adapter=self.adapter.__module__ + "." + self.adapter.__name__,
            code_path=str(Path(module.__file__).resolve().relative_to(root)),
            checkpoint=dict(self.adapter.checkpoint), preprocessing=self.adapter.preprocessing)


def register(name):
    """Decorate an adapter in adapters/; it then becomes available in configs."""
    def add(adapter):
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", name) or name in _ADAPTERS:
            raise ValueError(f"Invalid or duplicate detector registration: {name}")
        if any(not callable(getattr(adapter, method, None)) for method in ("prepare_frames", "predict")):
            raise ValueError("Adapter must implement prepare_frames and predict")
        weights = adapter.checkpoint
        if not re.fullmatch(r"[0-9a-f]{64}", weights["sha256"]) or not weights["url"].startswith("https://"):
            raise ValueError("Adapter checkpoint needs HTTPS URL and SHA256")
        path = Path(weights["path"])
        if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "models":
            raise ValueError("Adapter checkpoint must stay under models/")
        if not isinstance(adapter.preprocessing, str) or not adapter.preprocessing:
            raise ValueError("Adapter must describe its preprocessing")
        _ADAPTERS[name] = AdapterSpec(adapter)
        return adapter
    return add


def discover():
    from . import adapters
    for module in sorted(pkgutil.iter_modules(adapters.__path__), key=lambda item: item.name):
        if not module.name.startswith("_"):
            importlib.import_module(f"{adapters.__name__}.{module.name}")


def detector_names():
    discover()
    return tuple(sorted(_ADAPTERS))


def get_adapter(name):
    discover()
    try:
        return _ADAPTERS[name]
    except KeyError:
        raise ValueError(f"Unknown detector: {name}") from None


def make_detector(root, name):
    return get_adapter(name).create(root)
