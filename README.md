# art-video-notes-skill

将本地绘画教学视频整理成适合复习的课堂笔记。它不是把视频丢给云端服务的“转文字工具”：视频、音频、截图、转录和缓存都留在本机；Codex 只在本地准备好的小章节材料上逐段写笔记。

适合 Photoshop、CSP 和其他板绘软件的长课，也适合一个目录中的多节课程。默认输出简体中文。

## 能做什么

- 读取视频时长、音轨、字幕、编码和分辨率，给出明确的环境问题；
- 优先复用内嵌字幕，或使用本地 `faster-whisper` 转录（中英混合及日、韩语可手工指定）；
- 自动检测 CUDA，优先 GPU；GPU 初始化或显存失败会退回 CPU `int8`；
- 按语音边界划分约 8–15 分钟章节，并在转录范围保留少量重叠；
- 结合定期采样、画面变化与视觉指代词提取、去重关键帧；
- 为每章输出可独立重跑的转录、图片、分析包和 Markdown 模板；
- 让 Codex 区分老师说过的内容、画面可见操作、以及明确标注的整理推断。

不会上传课程内容到额外 AI API；首次使用 faster-whisper 时，其开源模型权重会下载到本机缓存。

## 安装

系统要求：Windows 10/11、Python 3.10+、以及 [FFmpeg](https://ffmpeg.org/download.html)（`ffmpeg` 和 `ffprobe` 均需在 `PATH`）。macOS/Linux 同样可用，安装命令按平台调整即可。

在项目根目录 PowerShell 执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

该脚本建立 `.venv`，安装本地依赖与 `faster-whisper`，并将 Skill 安装到 `~/.codex/skills/art-course-notes`。若想先只验证无 ASR 的环境：

```powershell
.\install.ps1 -WithoutAsr
```

检查环境：

```powershell
.\.venv\Scripts\art-course-notes.exe check
.\.venv\Scripts\art-course-notes.exe check "D:\Courses\K大\01_色彩基础.mp4"
```

## 分析一个视频

```powershell
.\.venv\Scripts\art-course-notes.exe run "D:\Courses\K大\01_色彩基础.mp4" --mode deep --resume
```

若内嵌字幕质量很好，默认会优先使用；用 `--use-subtitles no` 强制本地 ASR，用 `--use-subtitles yes` 强制字幕。可用 `--language zh`、`en`、`ja` 或 `ko` 覆盖自动检测。

输出位于 `output/01_色彩基础/`：

```text
manifest.json                 # 处理状态、环境、输入指纹
transcript/transcript.json    # 带起止时间的机器可读转录
transcript/transcript.srt
transcript/transcript.vtt
chunks/chunk-001.json         # 可单独检查或重跑的章节证据
assets/keyframes/             # 去重后的关键截图
notes/chunk-001.md            # Codex 的逐章分析包
课堂笔记.md                    # 全课汇总模板与最终笔记
cache/                        # 本地音频或内嵌字幕缓存
```

预处理结束后，直接对 Codex 说“使用 `$art-course-notes` 完成 `output/.../notes` 中的章节笔记并汇总 `课堂笔记.md`”。Skill 会逐章读取转录和图片，不会把四小时材料一次塞进上下文。

## 分析目录与继续任务

```powershell
.\.venv\Scripts\art-course-notes.exe batch "D:\Courses\K大" --mode deep --resume
```

`--resume` 是显式的断点续跑说明（默认也会复用缓存）。音频、转录、章节和截图已存在时不会重复计算；只有加 `--force` 才重新生成。目录模式另会写入 `output/课程总笔记.md`，便于后续跨课汇总。

## normal 和 deep

| 模式 | 适用情况 | 截图密度 | 章节笔记 |
| --- | --- | --- | --- |
| `normal` | 一般复习、快速梳理 | 较低 | 保持核心证据 |
| `deep`（默认） | K大等正式课程、关键示范 | 较高 | 更适合逐章人工/Codex 审阅 |

可在 [`config.yaml`](config.yaml) 调整模型、语言、章节时长、重叠时间、场景阈值和截图数量。默认 `small` 是普通电脑的平衡选择；显存充足可改 `medium`，CPU 较慢时可改 `base`。模型越大通常越准，但耗时与显存也越高。

## 常见问题

- **找不到 FFmpeg/FFprobe**：安装 FFmpeg 后重新打开 PowerShell，运行 `art-course-notes check`。
- **GPU 失败或显存不足**：程序会退到 CPU；也可在配置中设置 `asr.device: cpu`、`asr.compute_type: int8` 或减小模型。
- **没有音轨**：用可用字幕轨，或提供带音轨的视频源。
- **转录为空或语言错误**：用 `--language zh` 等明确语言，或选择更大的模型。
- **只想重跑一个失败章节**：保留其余缓存；删除该课程对应的 `chunks/chunk-XXX.json` 与相关 `notes/chunk-XXX.md` 后用 `--force` 重新准备，或让 Codex 基于该章的现有证据单独补写。

## 测试和更新

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest -m integration
git pull
.\install.ps1
```

集成测试会在本地临时创建一段带内嵌字幕的短视频，覆盖视频检查、字幕转录、分章、截图和输出结构；若 FFmpeg/OpenCV 未安装会跳过。它不下载 Whisper 权重。真实 ASR 请先用 10–20 分钟课程片段烟雾测试，再处理完整长课。

## 隐私与 Git

`.gitignore` 排除了视频、音频、截图、模型、缓存和 `output/`。提交前仍建议运行 `git status`，确认未包含私人课程内容或账号信息。
