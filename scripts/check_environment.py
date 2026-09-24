from __future__ import annotations

import json
import sys
from pathlib import Path

from art_course_notes.preflight import detect_runtime, inspect_video


def main() -> int:
    runtime = detect_runtime()
    print(json.dumps(runtime, ensure_ascii=False, indent=2))
    if len(sys.argv) > 1:
        print(json.dumps(inspect_video(Path(sys.argv[1])), ensure_ascii=False, indent=2))
    return 0 if runtime["ffmpeg"] and runtime["ffprobe"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
