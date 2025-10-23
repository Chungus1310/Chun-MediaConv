from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Union

PathLike = Union[str, os.PathLike[str]]


@lru_cache(maxsize=1)
def get_app_base_path() -> Path:
    """Return the runtime base directory (bundle root when frozen)."""
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _coerce_path_parts(parts: Iterable[PathLike]) -> Path:
    coerced: list[str] = []
    for part in parts:
        coerced.append(os.fspath(part))
    return Path(*coerced)


def resource_path(*relative_parts: PathLike) -> Path:
    """Return an absolute path inside the bundled resources directory."""
    base = get_app_base_path() / "resources"
    return (base / _coerce_path_parts(relative_parts)).resolve()


def ensure_directory(path: PathLike) -> Path:
    """Create the directory if it does not exist and return it."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

