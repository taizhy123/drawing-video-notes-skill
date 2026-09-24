---
name: art-course-notes
description: Create structured study notes from local drawing-course or digital-painting tutorial videos, preserving timestamps, key visual evidence, and the distinction between what was spoken, seen, and inferred. Use for long art lessons rather than ordinary video transcription or meeting summaries.
metadata:
  short-description: Convert local drawing lessons into evidence-based study notes
---

# Art Course Notes

Turn a local drawing lesson into a reviewable Chinese study note. This skill is for lessons where the instructor's canvas changes and software operations are evidence, not merely a transcript.

## Privacy and scope

Use the repository's local pipeline. Do not send video, audio, frames, transcript, or user course material to third-party AI APIs. Local FFmpeg, OpenCV, and faster-whisper are allowed. Codex's own analysis is used only after local preprocessing has produced small reviewable chapter packets.

Before processing, confirm the target is a local file or directory and use the existing project configuration. Do not run a multi-hour source in a single context or overwrite a completed note unless the user requests regeneration.

## Workflow

1. From the repository root, run `art-course-notes check <video>` and resolve clear preflight errors (missing FFmpeg, audio track, or dependencies).
2. Prepare one video with `art-course-notes run <video> --mode deep --resume`, or a folder with `art-course-notes batch <folder> --mode deep --resume`. Let cache/resume stand unless the user asks for `--force`.
3. Read the generated `manifest.json` and work chapter by chapter from `notes/chunk-*.md`, its matching `chunks/chunk-*.json`, and the linked keyframes. Finish each chunk note before moving to the next; do not load all chapter transcripts at once.
4. Replace the placeholders in each chunk note with concise learning notes, then consolidate them into `课堂笔记.md` using the output structure in [the evidence guide](references/note-evidence.md).
5. Verify final Markdown links use paths relative to the course output folder, important claims have selective `[HH:MM:SS]` timestamps, and uncertain items remain explicit.

## Evidence rules

Classify statements in your working analysis as `spoken`, `visual`, or `inferred`.

- `spoken`: the instructor explicitly said it; keep a nearby timestamp.
- `visual`: directly visible canvas/software action; describe only what is observable.
- `inferred`: a useful synthesis of both; label it as “根据画面/语音整理” rather than instructor speech.

Never fill ASR gaps with invented art theory. When a demonstrative phrase such as “这里” depends on the image, link the relevant screenshot and explain why it matters. Read [the evidence guide](references/note-evidence.md) before drafting or consolidating notes.

## Completion

The result is complete only when `课堂笔记.md` teaches the lesson's problem, principles, steps, judgement criteria, mistakes, techniques, and visual evidence—not when a transcript merely exists. Report failed chunks from `chunks/index.json`; rerun only those preparation stages if needed.
