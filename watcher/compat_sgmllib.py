"""Ensure sgmllib is available on Python 3.13+ (removed from stdlib). Required by feedparser."""
import importlib.util
import sys
from pathlib import Path

if "sgmllib" not in sys.modules:
    try:
        import sgmllib  # noqa: F401 — stdlib (<3.13) or sgmllib3k package
    except ImportError:
        _bundled = Path(__file__).resolve().parent / "vendor" / "sgmllib.py"
        if not _bundled.is_file():
            raise ImportError(
                "sgmllib is required by feedparser on Python 3.13+. "
                "Reinstall dependencies: pip install sgmllib3k"
            ) from None
        spec = importlib.util.spec_from_file_location("sgmllib", _bundled)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["sgmllib"] = mod
        spec.loader.exec_module(mod)
