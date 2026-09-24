from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from .models import Chunk, Segment
from .utils import format_timestamp


VISUAL_CUES = ("这里", "这边", "看一下", "这样画", "不要这样", "边缘", "这个颜色", "这个结构", "you see", "look here", "like this", "don't do")


def _hash(frame) -> int:
    import cv2  # type: ignore
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (9, 8))
    diff = small[:, 1:] > small[:, :-1]
    value = 0
    for bit in diff.flatten():
        value = (value << 1) | int(bit)
    return value


def _distance(first: int, second: int) -> int:
    return bin(first ^ second).count("1")


def _cue_times(segments: Iterable[Segment]) -> Set[int]:
    return {int((segment.start + segment.end) / 2) for segment in segments if any(cue in segment.text.lower() for cue in VISUAL_CUES)}


def _candidate_times(chunk: Chunk, mode: str, interval: int) -> List[int]:
    values = {int(chunk.start), int((chunk.start + chunk.end) / 2), max(int(chunk.end) - 1, int(chunk.start))}
    values.update(range(int(chunk.start + interval), int(chunk.end), interval))
    values.update(_cue_times(chunk.transcript))
    return sorted(value for value in values if chunk.start <= value <= chunk.end)


def extract_keyframes(video: Path, course_dir: Path, chunks: List[Chunk], mode: str, settings: Dict[str, object], force: bool = False) -> List[Chunk]:
    """Sample scene/cue-aware frames and reject visual near-duplicates.

    It intentionally samples a bounded candidate set rather than decoding every
    frame of a multi-hour course. Images are saved with Windows-safe writes.
    """
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise RuntimeError("未安装 OpenCV。运行 pip install -e . 后重试。") from exc
    keyframe_dir = course_dir / "assets" / "keyframes"
    keyframe_dir.mkdir(parents=True, exist_ok=True)
    interval = int(settings["deep_interval_seconds"] if mode == "deep" else settings["normal_interval_seconds"])
    limit = int(settings["max_per_chunk_deep"] if mode == "deep" else settings["max_per_chunk_normal"])
    threshold = float(settings["scene_threshold"])
    quality = int(settings["jpeg_quality"])
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError("OpenCV 无法读取视频；文件可能损坏或编码不受支持。")
    seen_hashes: List[int] = []
    try:
        for chunk in chunks:
            existing = [path for path in chunk.keyframes if (course_dir / path).exists()]
            if existing and not force:
                chunk.keyframes = existing
                continue
            selected: List[str] = []
            previous_mean = None
            for seconds in _candidate_times(chunk, mode, interval):
                if len(selected) >= limit:
                    break
                capture.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
                ok, frame = capture.read()
                if not ok:
                    continue
                frame_hash = _hash(frame)
                mean = float(frame.mean())
                scene_changed = previous_mean is not None and abs(mean - previous_mean) / 255.0 >= threshold
                cue = seconds in _cue_times(chunk.transcript)
                periodic = seconds in {int(chunk.start), int((chunk.start + chunk.end) / 2), max(int(chunk.end) - 1, int(chunk.start))}
                previous_mean = mean
                if not (scene_changed or cue or periodic or not selected):
                    continue
                if any(_distance(frame_hash, old) <= 5 for old in seen_hashes):
                    continue
                label = "%s_%s" % (chunk.id, format_timestamp(seconds).replace(":", "_"))
                destination = keyframe_dir / (label + ".jpg")
                encoded, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                if not encoded:
                    continue
                buffer.tofile(str(destination))
                selected.append(destination.relative_to(course_dir).as_posix())
                seen_hashes.append(frame_hash)
            chunk.keyframes = selected
    finally:
        capture.release()
    return chunks
