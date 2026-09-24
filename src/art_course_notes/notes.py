from pathlib import Path
from typing import Dict, Iterable, List

from .models import Chunk
from .utils import format_timestamp


CHUNK_TEMPLATE = """# {chunk_id}｜{start}–{end}\n\n> 证据规则：`spoken` 仅限老师明确说过的话；`visual` 只描述画面可见的操作；`inferred` 必须标注“根据画面/语音整理”。不确定的内容留入待确认，不要补写成事实。\n\n## 本节主题\n\n<!-- 用一句话说明本段解决的绘画问题。 -->\n\n## 核心结论\n\n<!-- 用项目符号；给每个重要结论保留 [HH:MM:SS]。 -->\n\n## 原理解释\n\n## 演示步骤\n\n1. \n\n## 判断标准与常见错误\n\n## 实用技巧\n\n## 关键截图\n\n{frames}\n\n## 待确认内容\n\n<!-- ASR 听不清、操作太快或无法由画面确定的地方。 -->\n\n## 原始转录（证据）\n\n{transcript}\n"""


def write_chunk_packets(course_dir: Path, chunks: Iterable[Chunk], force: bool = False) -> None:
    notes_dir = course_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        path = notes_dir / (chunk.id + ".md")
        if path.exists() and not force:
            continue
        frames = "\n".join("- ![%s](../%s)（视频位置：%s；请说明保留原因）" % (Path(frame).stem, frame, ":".join(Path(frame).stem.split("_")[-3:]) if "_" in Path(frame).stem else "见文件名") for frame in chunk.keyframes) or "- 本段未抽取到可用截图。"
        transcript = "\n".join("- [%s] %s" % (format_timestamp(item.start), item.text) for item in chunk.transcript) or "- （本段没有可用转录）"
        path.write_text(CHUNK_TEMPLATE.format(chunk_id=chunk.id, start=format_timestamp(chunk.start), end=format_timestamp(chunk.end), frames=frames, transcript=transcript), encoding="utf-8")


def write_course_skeleton(course_dir: Path, manifest: Dict[str, object], chunks: List[Chunk], force: bool = False) -> Path:
    output = course_dir / "课堂笔记.md"
    if output.exists() and not force:
        return output
    video = manifest.get("video", {})
    chapters = "\n".join("- [%s–%s](notes/%s.md)｜%s" % (format_timestamp(chunk.start), format_timestamp(chunk.end), chunk.id, chunk.id) for chunk in chunks)
    content = """# {title}\n\n## 课程信息\n\n- 视频文件：`{path}`\n- 视频长度：{duration}\n- 解析日期：{created}\n- 语言：{language}\n- ASR 模型：{model}\n- 分析模式：{mode}\n\n## 本课核心知识\n\n<!-- 阅读全部章节笔记后提炼 5–15 条。未完成时不要填充猜测。 -->\n\n## 课程章节\n\n{chapters}\n\n## 全课知识体系\n\n<!-- 用“基础原则 → 判断方法 → 实际步骤 → 易错点 → 练习方式”串联课程；每项须可回溯至章节证据。 -->\n\n## 重要口诀 / 原则\n\n<!-- 仅记录老师实际说过或明确写出的口诀。 -->\n\n## 软件与操作技巧汇总\n\n## 易错点汇总\n\n## 练习与作业建议\n\n<!-- 老师要求与整理建议分开标注。 -->\n\n## 术语表\n\n## 需要重新观看的位置\n\n<!-- 标记 ASR 不确定、理论复杂、演示快速或视觉依赖高的时间点。 -->\n""".format(title=course_dir.name, path=video.get("path", ""), duration=format_timestamp(float(video.get("duration", 0))), created=manifest.get("created_at", ""), language=manifest.get("language", "待识别"), model=manifest.get("asr_model", "待识别"), mode=manifest.get("mode", "deep"), chapters=chapters)
    output.write_text(content, encoding="utf-8")
    return output
