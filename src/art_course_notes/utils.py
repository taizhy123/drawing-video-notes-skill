import hashlib
import json
import re
from pathlib import Path
from typing import Any


def format_timestamp(seconds: float, milliseconds: bool = False) -> str:
    """Format a non-negative number of seconds as HH:MM:SS(.mmm)."""
    seconds = max(0.0, float(seconds))
    total_ms = int(round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, ms = divmod(remainder, 1000)
    value = "%02d:%02d:%02d" % (hours, minutes, whole_seconds)
    return "%s.%03d" % (value, ms) if milliseconds else value


def safe_stem(path: Path) -> str:
    stem = re.sub(r"[<>:\\|?*\"/]+", "_", path.stem).strip(" ._")
    return stem or "course"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def file_fingerprint(path: Path) -> str:
    stat = path.stat()
    raw = "%s:%s:%s" % (path.resolve(), stat.st_size, stat.st_mtime_ns)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_newer_than(target: Path, source: Path) -> bool:
    return target.exists() and target.stat().st_mtime_ns >= source.stat().st_mtime_ns
