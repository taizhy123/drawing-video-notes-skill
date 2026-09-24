from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict


def executable(name: str) -> str | None:
    return shutil.which(name)


def _run_json(command: list[str]) -> Dict[str, Any]:
    process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or "命令失败: %s" % " ".join(command))
    import json
    return json.loads(process.stdout)


def inspect_video(video: Path) -> Dict[str, Any]:
    ffprobe = executable("ffprobe")
    if not ffprobe:
        raise RuntimeError("找不到 ffprobe。请先安装 FFmpeg 并把其 bin 目录加入 PATH。")
    raw = _run_json([ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(video)])
    streams = raw.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    subtitle_streams = [s for s in streams if s.get("codec_type") == "subtitle"]
    fmt = raw.get("format", {})
    return {
        "path": str(video.resolve()),
        "duration": float(fmt.get("duration") or 0),
        "size_bytes": int(fmt.get("size") or video.stat().st_size),
        "format": fmt.get("format_name"),
        "video": {
            "codec": video_stream.get("codec_name"), "width": video_stream.get("width"),
            "height": video_stream.get("height"), "fps": video_stream.get("r_frame_rate"),
        },
        "audio_tracks": [{"codec": s.get("codec_name"), "language": (s.get("tags") or {}).get("language")} for s in audio_streams],
        "subtitle_tracks": [{"codec": s.get("codec_name"), "language": (s.get("tags") or {}).get("language")} for s in subtitle_streams],
    }


def detect_runtime() -> Dict[str, Any]:
    result: Dict[str, Any] = {"ffmpeg": executable("ffmpeg"), "ffprobe": executable("ffprobe"), "cuda": False}
    try:
        import ctranslate2  # type: ignore
        result["ctranslate2"] = getattr(ctranslate2, "__version__", "installed")
        result["cuda"] = bool(ctranslate2.get_cuda_device_count())
    except Exception:
        result["ctranslate2"] = None
    try:
        import faster_whisper  # type: ignore
        result["faster_whisper"] = getattr(faster_whisper, "__version__", "installed")
    except Exception:
        result["faster_whisper"] = None
    return result
