import subprocess
from pathlib import Path


def _ffmpeg() -> str:
    from .preflight import executable
    value = executable("ffmpeg")
    if not value:
        raise RuntimeError("找不到 ffmpeg。请安装 FFmpeg 后重试。")
    return value


def extract_audio(video: Path, output: Path, force: bool = False) -> Path:
    if output.exists() and not force:
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [_ffmpeg(), "-y", "-i", str(video), "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(output)]
    process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if process.returncode:
        raise RuntimeError("音频提取失败：%s" % process.stderr[-1200:])
    return output


def extract_subtitles(video: Path, output: Path, force: bool = False) -> Path:
    if output.exists() and not force:
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [_ffmpeg(), "-y", "-i", str(video), "-map", "0:s:0", str(output)]
    process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if process.returncode:
        raise RuntimeError("字幕提取失败：%s" % process.stderr[-1200:])
    return output
