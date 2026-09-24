from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .config import load_config
from .pipeline import run_course, write_course_index
from .preflight import detect_runtime, inspect_video


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}


def _add_run_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, default=Path("config.yaml"), help="配置文件路径")
    parser.add_argument("--output-root", type=Path, help="覆盖配置中的输出目录")
    parser.add_argument("--mode", choices=("normal", "deep"), default="deep")
    parser.add_argument("--language", default=None, help="auto、zh、en、ja、ko 等")
    parser.add_argument("--use-subtitles", choices=("auto", "yes", "no"), default="auto")
    parser.add_argument("--force", action="store_true", help="重新生成已缓存的阶段和模板")
    parser.add_argument("--resume", action="store_true", help="兼容显式调用；默认就会断点续跑")


def _config(args: argparse.Namespace):
    config = load_config(args.config if args.config and args.config.exists() else None)
    if args.output_root:
        config["output_root"] = str(args.output_root)
    if args.language:
        config["language"] = args.language
    return config


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="art-course-notes", description="离线绘画课程预处理与 Codex 笔记分析包")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="检查本地环境或视频信息")
    check.add_argument("video", type=Path, nargs="?")
    run = subparsers.add_parser("run", help="处理一个课程视频")
    run.add_argument("video", type=Path)
    _add_run_options(run)
    batch = subparsers.add_parser("batch", help="逐个处理目录内的视频")
    batch.add_argument("directory", type=Path)
    _add_run_options(batch)
    args = parser.parse_args(argv)
    if args.command == "check":
        print(detect_runtime())
        if args.video:
            print(inspect_video(args.video.expanduser().resolve()))
        return 0
    config = _config(args)
    if args.command == "run":
        course = run_course(args.video, config, args.mode, args.force, args.use_subtitles)
        print("已准备完成：%s" % course)
        return 0
    directory = args.directory.expanduser().resolve()
    videos = sorted(path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS)
    if not videos:
        raise FileNotFoundError("目录中没有支持的视频文件: %s" % directory)
    courses = [run_course(video, config, args.mode, args.force, args.use_subtitles) for video in videos]
    print("课程索引：%s" % write_course_index(courses, Path(config["output_root"]).expanduser().resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
