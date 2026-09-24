import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .models import Segment
from .utils import format_timestamp, read_json, write_json


def _choose_device(requested: str, compute_type: str) -> Tuple[str, str]:
    if requested != "auto":
        return requested, ("int8" if requested == "cpu" and compute_type == "auto" else compute_type)
    try:
        import ctranslate2  # type: ignore
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16" if compute_type == "auto" else compute_type
    except Exception:
        pass
    return "cpu", "int8" if compute_type == "auto" else compute_type


def transcribe(audio: Path, model: str, language: str, device: str, compute_type: str, beam_size: int) -> Tuple[List[Segment], str, str]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:
        raise RuntimeError("未安装 faster-whisper。运行 pip install -e .[asr] 后重试。") from exc
    chosen_device, chosen_compute = _choose_device(device, compute_type)
    try:
        whisper = WhisperModel(model, device=chosen_device, compute_type=chosen_compute)
        raw, info = whisper.transcribe(str(audio), language=None if language == "auto" else language, beam_size=int(beam_size), vad_filter=True)
        return [Segment(float(s.start), float(s.end), s.text.strip(), getattr(info, "language", None)) for s in raw if s.text.strip()], getattr(info, "language", "unknown"), chosen_device
    except RuntimeError as exc:
        if chosen_device == "cuda":
            # A GPU can report available yet fail through OOM or a mismatched CUDA runtime.
            return transcribe(audio, model, language, "cpu", "int8", beam_size)
        raise RuntimeError("本地 ASR 失败：%s" % exc) from exc


def load_segments(path: Path) -> List[Segment]:
    data = read_json(path, default={})
    return [Segment(float(item["start"]), float(item["end"]), item["text"], item.get("language")) for item in data.get("segments", [])]


def save_transcript(segments: Iterable[Segment], json_path: Path, srt_path: Path, vtt_path: Path, language: str) -> None:
    data = {"language": language, "segments": [segment.to_dict() for segment in segments]}
    write_json(json_path, data)
    entries = []
    for index, segment in enumerate(data["segments"], 1):
        start = format_timestamp(segment["start"], milliseconds=True).replace(".", ",")
        end = format_timestamp(segment["end"], milliseconds=True).replace(".", ",")
        entries.append("%d\n%s --> %s\n%s\n" % (index, start, end, segment["text"]))
    srt_path.write_text("\n".join(entries), encoding="utf-8")
    vtt_path.write_text("WEBVTT\n\n" + "\n".join(entry.replace(",", ".") for entry in entries), encoding="utf-8")


_SRT_TIME = re.compile(r"(\d{1,2}:\d{2}:\d{2}[,.]\d+)\s+-->\s+(\d{1,2}:\d{2}:\d{2}[,.]\d+)")


def _parse_time(value: str) -> float:
    hours, minutes, seconds = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def parse_srt(path: Path) -> List[Segment]:
    blocks = re.split(r"\r?\n\s*\r?\n", path.read_text(encoding="utf-8", errors="replace").strip())
    result: List[Segment] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        time_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if time_index is None:
            continue
        match = _SRT_TIME.search(lines[time_index])
        if not match:
            continue
        text = " ".join(lines[time_index + 1:])
        if text:
            result.append(Segment(_parse_time(match.group(1)), _parse_time(match.group(2)), text))
    return result
