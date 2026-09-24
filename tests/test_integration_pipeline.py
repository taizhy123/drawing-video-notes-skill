import shutil
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("yaml")

from art_course_notes.config import DEFAULTS
from art_course_notes.pipeline import run_course


@pytest.mark.integration
def test_embedded_subtitle_video_reaches_note_structure(tmp_path: Path):
    pytest.importorskip("cv2")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("FFmpeg not installed")
    srt = tmp_path / "lesson.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:03,000\n这里先建立大明暗关系。\n", encoding="utf-8")
    video = tmp_path / "lesson.mp4"
    command = [ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=4", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-i", str(srt), "-map", "0:v", "-map", "1:a", "-map", "2:s", "-c:v", "mpeg4", "-c:a", "aac", "-c:s", "mov_text", "-shortest", str(video)]
    subprocess.run(command, check=True, capture_output=True)
    config = {**DEFAULTS, "output_root": str(tmp_path / "output")}
    course_dir = run_course(video, config, mode="normal", use_subtitles="yes", logger=lambda _: None)
    assert (course_dir / "manifest.json").exists()
    assert (course_dir / "transcript" / "transcript.json").exists()
    assert (course_dir / "chunks" / "index.json").exists()
    assert (course_dir / "课堂笔记.md").exists()
