from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


DEFAULTS: Dict[str, Any] = {
    "output_root": "output",
    "language": "auto",
    "output_language": "zh-CN",
    "asr": {"model": "small", "device": "auto", "compute_type": "auto", "beam_size": 5},
    "chunking": {"target_minutes": 12, "min_minutes": 8, "max_minutes": 15, "overlap_seconds": 30},
    "keyframes": {
        "scene_threshold": 0.28,
        "normal_interval_seconds": 150,
        "deep_interval_seconds": 75,
        "max_per_chunk_normal": 4,
        "max_per_chunk_deep": 8,
        "jpeg_quality": 88,
    },
}


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return deepcopy(DEFAULTS)
    if not path.exists():
        raise FileNotFoundError("配置文件不存在: %s" % path)
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError("配置文件顶层必须是键值映射")
    return _merge(DEFAULTS, loaded)
