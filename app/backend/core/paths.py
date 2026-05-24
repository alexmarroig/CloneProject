from __future__ import annotations

import re
from pathlib import Path


_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$")


def sanitize_name(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} is required")
    if not _NAME_PATTERN.fullmatch(normalized):
        raise ValueError(
            f"{field} must match pattern [a-zA-Z0-9._-] and cannot start with punctuation"
        )
    return normalized


def resolve_inside(base_dir: Path, candidate: str | Path, field: str, must_exist: bool = False) -> Path:
    base = base_dir.resolve()
    target = Path(candidate)
    if not target.is_absolute():
        target = (base / target).resolve()
    else:
        target = target.resolve()
    if target != base and base not in target.parents:
        raise ValueError(f"{field} must stay inside {base}")
    if must_exist and not target.exists():
        raise FileNotFoundError(str(target))
    return target


def assert_extension(filename: str, allowed: set[str], field: str) -> str:
    name = Path(filename).name
    extension = Path(name).suffix.lower()
    if extension not in allowed:
        raise ValueError(f"{field} extension '{extension}' is not allowed")
    return name
