from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .chunking import create_chunks
from .keyframes import extract_keyframes
from .media import extract_audio, extract_subtitles
from .models import Chunk, Segment
from .notes import write_chunk_packets, write_course_skeleton
from .preflight import detect_runtime, inspect_video
from .transcript import load_segments, parse_srt, save_transcript, transcribe
from .utils import file_fingerprint, read_json, safe_stem, write_json


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _chunk_from_dict(data: Dict[str, Any]) -> Chunk:
    return Chunk(
        id=data["id"], start=float(data["start"]), end=float(data["end"]),
        transcript_start=float(data.get("transcript_start", data["start"])), transcript_end=float(data.get("transcript_end", data["end"])),
        transcript=[Segment(float(item["start"]), float(item["end"]), item["text"], item.get("language")) for item in data.get("transcript", [])],
        keyframes=list(data.get("keyframes", [])), topic_hint=data.get("topic_hint", ""), status=data.get("status", "pending"), error=data.get("error"),
    )


def _save_chunks(course_dir: Path, chunks: List[Chunk]) -> None:
    index = []
    for chunk in chunks:
        data = chunk.to_dict()
        path = course_dir / "chunks" / (chunk.id + ".json")
        write_json(path, data)
        index.append({"id": chunk.id, "start": chunk.start, "end": chunk.end, "path": path.relative_to(course_dir).as_posix(), "status": chunk.status, "error": chunk.error})
    write_json(course_dir / "chunks" / "index.json", index)


def _save_manifest(path: Path, manifest: Dict[str, Any]) -> None:
    manifest["updated_at"] = _utc_now()
    write_json(path, manifest)


def run_course(
    video: Path,
    config: Dict[str, Any],
    mode: str = "deep",
    force: bool = False,
    use_subtitles: str = "auto",
    logger=print,
) -> Path:
    """Run deterministic local preprocessing; semantic writing remains Codex work."""
    video = video.expanduser().resolve()
    if not video.is_file():
        raise FileNotFoundError("找不到视频文件: %s" % video)
    course_dir = Path(config["output_root"]).expanduser().resolve() / safe_stem(video)
    course_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = course_dir / "manifest.json"
    previous = read_json(manifest_path, default={})
    fingerprint = file_fingerprint(video)
    manifest: Dict[str, Any] = previous if previous.get("fingerprint") == fingerprint else {}
    manifest.update({"schema_version": 1, "fingerprint": fingerprint, "created_at": manifest.get("created_at", _utc_now()), "mode": mode, "asr_model": config["asr"]["model"], "phases": manifest.get("phases", {})})

    def phase(number: int, total: int, name: str, state: str = "running") -> None:
        logger("[%d/%d] %s" % (number, total, name))
        manifest["phases"][name] = {"status": state, "at": _utc_now()}
        _save_manifest(manifest_path, manifest)

    try:
        phase(1, 8, "检查视频与运行环境")
        video_info = inspect_video(video)
        runtime = detect_runtime()
        if not video_info["audio_tracks"] and not video_info["subtitle_tracks"]:
            raise RuntimeError("视频没有音轨或字幕轨，无法生成课堂笔记。")
        manifest["video"], manifest["runtime"] = video_info, runtime
        phase(1, 8, "检查视频与运行环境", "complete")

        transcript_json = course_dir / "transcript" / "transcript.json"
        transcript_srt = course_dir / "transcript" / "transcript.srt"
        transcript_vtt = course_dir / "transcript" / "transcript.vtt"
        segments = load_segments(transcript_json) if transcript_json.exists() and not force else []
        language = config.get("language", "auto")
        has_subtitles = bool(video_info["subtitle_tracks"])
        prefer_subtitles = use_subtitles == "yes" or (use_subtitles == "auto" and has_subtitles)
        if use_subtitles == "yes" and not has_subtitles:
            raise RuntimeError("已指定 --use-subtitles yes，但视频中没有字幕轨。")
        if not segments:
            if prefer_subtitles:
                phase(2, 8, "提取内嵌字幕")
                source_srt = extract_subtitles(video, course_dir / "cache" / "embedded.srt", force=force)
                segments = parse_srt(source_srt)
                if not segments:
                    raise RuntimeError("内嵌字幕为空或无法解析；可用 --use-subtitles no 改用本地 ASR。")
                language = video_info["subtitle_tracks"][0].get("language") or language
                save_transcript(segments, transcript_json, transcript_srt, transcript_vtt, language)
                phase(2, 8, "提取内嵌字幕", "complete")
            else:
                phase(2, 8, "提取 16kHz 单声道音频")
                audio = extract_audio(video, course_dir / "cache" / "audio_16k_mono.wav", force=force)
                phase(2, 8, "提取 16kHz 单声道音频", "complete")
                phase(3, 8, "本地 faster-whisper 转录")
                segments, language, device = transcribe(audio, config["asr"]["model"], language, config["asr"]["device"], config["asr"]["compute_type"], config["asr"]["beam_size"])
                if not segments:
                    raise RuntimeError("转录结果为空。请检查音轨、语言设置或选择更合适的模型。")
                manifest["asr_device"] = device
                save_transcript(segments, transcript_json, transcript_srt, transcript_vtt, language)
                phase(3, 8, "本地 faster-whisper 转录", "complete")
        else:
            logger("[2/8] 复用缓存的转录结果")
        manifest["language"] = language
        _save_manifest(manifest_path, manifest)

        chunk_index = course_dir / "chunks" / "index.json"
        if chunk_index.exists() and not force:
            chunks = [_chunk_from_dict(read_json(course_dir / item["path"])) for item in read_json(chunk_index, [])]
            logger("[4/8] 复用 %d 个章节缓存" % len(chunks))
        else:
            phase(4, 8, "按语音边界划分章节")
            spec = config["chunking"]
            chunks = create_chunks(segments, video_info["duration"], spec["target_minutes"], spec["min_minutes"], spec["max_minutes"], spec["overlap_seconds"])
            _save_chunks(course_dir, chunks)
            phase(4, 8, "按语音边界划分章节", "complete")

        phase(5, 8, "抽取并去重关键画面")
        chunks = extract_keyframes(video, course_dir, chunks, mode, config["keyframes"], force=force)
        _save_chunks(course_dir, chunks)
        phase(5, 8, "抽取并去重关键画面", "complete")

        phase(6, 8, "生成章节分析包")
        write_chunk_packets(course_dir, chunks, force=force)
        phase(6, 8, "生成章节分析包", "complete")
        phase(7, 8, "生成课堂笔记汇总骨架")
        write_course_skeleton(course_dir, manifest, chunks, force=force)
        phase(7, 8, "生成课堂笔记汇总骨架", "complete")
        phase(8, 8, "完成")
        manifest["status"] = "ready_for_codex_review"
        manifest["completed_at"] = _utc_now()
        phase(8, 8, "完成", "complete")
        return course_dir
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = str(exc)
        _save_manifest(manifest_path, manifest)
        raise


def write_course_index(course_directories: List[Path], output_root: Path) -> Path:
    path = output_root / "课程总笔记.md"
    lines = ["# 课程总笔记", "", "> 此文件只串联各课；完成每课的 Codex 审阅后再补全跨课知识体系。", ""]
    lines.extend("- [%s](%s/课堂笔记.md)" % (directory.name, directory.name) for directory in course_directories)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
