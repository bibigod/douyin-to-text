# 本地视频/音频文件支持 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `transcribe_file()` API 和 `douyin-to-text file` CLI 子命令，支持对本地音视频文件直接做语音识别 + 可选摘要。

**Architecture:** 从 `transcribe_url()` 中提取共享核心 `_transcribe_media()`，两个公开入口 (`transcribe_url` / `transcribe_file`) 各自获取媒体源后复用同一核心。`mp4_to_mp3()` 新增可选 `output` 参数，使本地文件模式的临时 mp3 能落在 `.raw/` 目录而非源文件旁边。

**Tech Stack:** Python 3.10+, argparse subparsers, ffmpeg, DashScope Paraformer

---

### Task 1: 修改 `mp4_to_mp3()` 支持可选输出路径

**Files:**
- Modify: `src/douyin_to_text/asr.py:9-17`

- [ ] **Step 1: 添加 `output` 参数**

```python
def mp4_to_mp3(source: Path, output: Path | None = None) -> Path:
    """Extract 16kHz mono mp3 audio track via ffmpeg.

    Args:
        source: Input video or audio file.
        output: Destination path for the mp3. Defaults to source.with_suffix('.mp3').
    """
    mp3 = output if output is not None else source.with_suffix(".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(source), "-vn", "-ar", "16000", "-ac", "1",
         "-codec:a", "libmp3lame", "-q:a", "5", str(mp3)],
        check=True, capture_output=True,
    )
    return mp3
```

- [ ] **Step 2: 验证现有测试仍然通过**

```bash
pytest tests/test_smoke.py -v
```
Expected: 10 passed

- [ ] **Step 3: Commit**

```bash
git add src/douyin_to_text/asr.py
git commit -m "feat: add optional output path to mp4_to_mp3"
```

---

### Task 2: 从 `transcribe_url()` 提取共享核心 `_transcribe_media()`

**Files:**
- Modify: `src/douyin_to_text/pipeline.py` (entire file)

- [ ] **Step 1: 新增 `_transcribe_media()` 内部函数**

在 `transcribe_url()` 上方插入。该函数只负责"已有媒体文件 → 提取音频 → 转写"，不管来源：

```python
def _transcribe_media(
    source_path: Path,
    raw_dir: Path,
    *,
    keep_media: bool = False,
    on_sentence=None,
) -> str:
    """Extract audio and transcribe from a local media file.

    The source file is never moved or deleted. The extracted mp3 is placed
    inside raw_dir and cleaned up after transcription (unless keep_media).

    Args:
        source_path: Path to a video or audio file.
        raw_dir: Existing work directory for intermediate files.
        keep_media: If True, keep the extracted mp3.
        on_sentence: Optional callback(str) for live sentence streaming.

    Returns:
        Transcribed text, one sentence per line.
    """
    from douyin_to_text.asr import mp4_to_mp3, transcribe_mp3

    mp3 = mp4_to_mp3(source_path, output=raw_dir / "audio.mp3")
    text = transcribe_mp3(mp3, on_sentence=on_sentence)
    (raw_dir / "transcript.txt").write_text(text, encoding="utf-8")

    if not keep_media:
        try:
            mp3.unlink()
        except OSError:
            pass

    return text
```

- [ ] **Step 2: 重构 `transcribe_url()` 调用 `_transcribe_media()`**

将 `transcribe_url()` 内部的转写部分替换为对 `_transcribe_media()` 的调用。完整重构后的 `transcribe_url()`：

```python
def transcribe_url(
    url: str,
    out_dir: Path | str = "./transcripts",
    on_sentence=None,
    on_stage=None,
    keep_media: bool = False,
    summarize: bool = False,
) -> TranscribeResult:
    """Download a Douyin video, transcribe its audio, save as txt.

    By default the mp4/mp3 are deleted after transcription; only the text
    survives. Pass keep_media=True to retain raw media (your own copyright
    responsibility).

    Args:
        url: a single Douyin share URL (batch is intentionally not supported).
        out_dir: directory to write the readable .txt into.
        on_sentence: optional callback(str) for live sentence streaming.
        keep_media: if True, keep mp4/mp3 in raw_dir; default False (deleted).
        summarize: if True, call Qwen to write a Markdown summary alongside.
            Reuses DASHSCOPE_API_KEY. If the LLM call fails, the transcript
            still succeeds; the error is attached but not raised.
    """
    def _stage(name: str):
        if on_stage:
            on_stage(name)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = out_dir / ".raw" / uuid.uuid4().hex[:10]
    raw_dir.mkdir(parents=True, exist_ok=True)

    _stage("fetching")
    mp4, page_title = fetch_mp4(url, raw_dir)

    _stage("transcribing")
    text = _transcribe_media(mp4, raw_dir, keep_media=keep_media, on_sentence=on_sentence)

    (raw_dir / "source_url.txt").write_text(url, encoding="utf-8")
    (raw_dir / "page_title.txt").write_text(page_title, encoding="utf-8")

    if not keep_media:
        try:
            mp4.unlink()
        except OSError:
            pass

    today = datetime.date.today().isoformat()
    slug = _sanitize(page_title) if page_title else raw_dir.name
    out_path = out_dir / f"{today}_{slug}.txt"
    out_path.write_text(text, encoding="utf-8")

    summary: str | None = None
    summary_path: Path | None = None
    if summarize:
        _stage("summarizing")
        try:
            summary = summarize_transcript(text)
            summary_path = out_path.with_suffix(".md")
            header = f"# {page_title}\n\n> 来源: {url}\n\n" if page_title else f"> 来源: {url}\n\n"
            summary_path.write_text(header + summary, encoding="utf-8")
        except Exception as e:
            summary = f"(summary failed: {e})"

    return TranscribeResult(
        text=text,
        output_path=out_path,
        raw_dir=raw_dir,
        page_title=page_title,
        summary=summary,
        summary_path=summary_path,
    )
```

- [ ] **Step 3: 验证现有测试仍然通过**

```bash
pytest tests/test_smoke.py -v
```
Expected: 10 passed

- [ ] **Step 4: Commit**

```bash
git add src/douyin_to_text/pipeline.py
git commit -m "refactor: extract _transcribe_media shared core from transcribe_url"
```

---

### Task 3: 新增 `transcribe_file()` 公开 API

**Files:**
- Modify: `src/douyin_to_text/pipeline.py` (追加在 `transcribe_url` 下方)

- [ ] **Step 1: 在 `test_smoke.py` 中先写失败的导入测试**

```python
def test_transcribe_file_importable():
    from douyin_to_text.pipeline import transcribe_file
    assert callable(transcribe_file)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_smoke.py::test_transcribe_file_importable -v
```
Expected: FAIL with ImportError

- [ ] **Step 3: 实现 `transcribe_file()`**

追加在 `pipeline.py` 的 `transcribe_url()` 下方：

```python
def transcribe_file(
    path: Path | str,
    out_dir: Path | str = "./transcripts",
    *,
    title: str | None = None,
    on_sentence=None,
    on_stage=None,
    keep_media: bool = False,
    summarize: bool = False,
) -> TranscribeResult:
    """Transcribe a local video or audio file, save as txt.

    The source file is never moved or modified. Only the extracted mp3
    (placed in a .raw/ work directory) is cleaned up after transcription.

    Args:
        path: Path to a local media file (.mp4, .mov, .mp3, .wav, etc.).
        out_dir: directory to write the readable .txt into.
        title: Optional output slug. Defaults to sanitized file stem.
        on_sentence: optional callback(str) for live sentence streaming.
        on_stage: optional callback(str) for stage names.
        keep_media: if True, keep the extracted mp3; default False.
        summarize: if True, call Qwen to write a Markdown summary alongside.
    """
    def _stage(name: str):
        if on_stage:
            on_stage(name)

    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"Expected a file, got a directory: {path}")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = out_dir / ".raw" / uuid.uuid4().hex[:10]
    raw_dir.mkdir(parents=True, exist_ok=True)

    slug = _sanitize(title) if title else _sanitize(path.stem)

    _stage("transcribing")
    text = _transcribe_media(path, raw_dir, keep_media=keep_media, on_sentence=on_sentence)

    (raw_dir / "source_file.txt").write_text(str(path), encoding="utf-8")

    today = datetime.date.today().isoformat()
    out_path = out_dir / f"{today}_{slug}.txt"
    out_path.write_text(text, encoding="utf-8")

    summary: str | None = None
    summary_path: Path | None = None
    if summarize:
        _stage("summarizing")
        try:
            summary = summarize_transcript(text)
            summary_path = out_path.with_suffix(".md")
            header = f"# {slug}\n\n> 来源: {path}\n\n"
            summary_path.write_text(header + summary, encoding="utf-8")
        except Exception as e:
            summary = f"(summary failed: {e})"

    return TranscribeResult(
        text=text,
        output_path=out_path,
        raw_dir=raw_dir,
        page_title=slug,
        summary=summary,
        summary_path=summary_path,
    )
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_smoke.py::test_transcribe_file_importable -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/douyin_to_text/pipeline.py tests/test_smoke.py
git commit -m "feat: add transcribe_file public API for local media"
```

---

### Task 4: CLI 改为子命令模式（`url` / `file`）

**Files:**
- Modify: `src/douyin_to_text/cli.py` (整个文件)

- [ ] **Step 1: 重写 `cli.py` 使用 argparse 子命令**

```python
"""Command-line entry: `douyin-to-text <url|file> ...`."""

import argparse
import os
import sys
from pathlib import Path

from douyin_to_text import __version__
from douyin_to_text.pipeline import transcribe_url, transcribe_file


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="douyin-to-text",
        description="Transcribe a Douyin video or local media file to Chinese text via Qwen Paraformer.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    # ---- url ----
    url_p = sub.add_parser("url", help="Transcribe from a Douyin share URL")
    url_p.add_argument("url", help="a single Douyin share URL")
    url_p.add_argument("--out", default="./transcripts", help="output directory")
    url_p.add_argument("--keep-media", action="store_true",
                       help="keep downloaded mp4/mp3 (default: deleted)")
    url_p.add_argument("--summary", action="store_true",
                       help="also produce a Markdown summary via Qwen")

    # ---- file ----
    file_p = sub.add_parser("file", help="Transcribe a local video or audio file")
    file_p.add_argument("path", help="path to a local media file")
    file_p.add_argument("--out", default="./transcripts", help="output directory")
    file_p.add_argument("--keep-media", action="store_true",
                        help="keep the extracted mp3 (default: deleted)")
    file_p.add_argument("--summary", action="store_true",
                        help="also produce a Markdown summary via Qwen")
    file_p.add_argument("--title", default=None,
                        help="output file title (default: sanitized filename)")

    args = parser.parse_args()

    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("error: env var DASHSCOPE_API_KEY is not set.", file=sys.stderr)
        print("        get one at https://dashscope.aliyun.com/", file=sys.stderr)
        return 2

    if args.command == "url":
        total = 4 if args.summary else 3
        print(f"[1/{total}] fetching mp4 from {args.url} ...")
        print(f"[2/{total}] extracting audio + streaming to Paraformer ...")
        if args.summary:
            print(f"[3/{total}] (summary will be generated after transcription) ...")
        result = transcribe_url(
            args.url,
            out_dir=args.out,
            on_sentence=lambda s: print(f"  · {s}"),
            keep_media=args.keep_media,
            summarize=args.summary,
        )
        print(f"\n[{total}/{total}] done.")
        print(f"      transcript -> {result.output_path}")
        if result.summary_path:
            print(f"      summary    -> {result.summary_path}")
        elif args.summary:
            print(f"      summary    -> {result.summary}")
        print(f"      raw assets -> {result.raw_dir}")

    elif args.command == "file":
        total = 3 if args.summary else 2
        print(f"[1/{total}] extracting audio + streaming to Paraformer ...")
        if args.summary:
            print(f"[2/{total}] (summary will be generated after transcription) ...")
        result = transcribe_file(
            args.path,
            out_dir=args.out,
            title=args.title,
            on_sentence=lambda s: print(f"  · {s}"),
            keep_media=args.keep_media,
            summarize=args.summary,
        )
        print(f"\n[{total}/{total}] done.")
        print(f"      transcript -> {result.output_path}")
        if result.summary_path:
            print(f"      summary    -> {result.summary_path}")
        elif args.summary:
            print(f"      summary    -> {result.summary}")
        print(f"      raw assets -> {result.raw_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 运行测试验证无回归**

```bash
pytest tests/test_smoke.py -v
```
Expected: 11 passed

- [ ] **Step 3: 手动验证 help 输出**

```bash
python -m douyin_to_text.cli --help
```
Expected: 显示 `url` 和 `file` 两个子命令

```bash
python -m douyin_to_text.cli url --help
```
Expected: 显示 URL 模式参数

```bash
python -m douyin_to_text.cli file --help
```
Expected: 显示 file 模式参数（含 `--title`）

- [ ] **Step 4: Commit**

```bash
git add src/douyin_to_text/cli.py
git commit -m "feat: add file subcommand for local media transcription"
```

---

### Task 5: 导出 `transcribe_file` 到公共 API

**Files:**
- Modify: `src/douyin_to_text/__init__.py`

- [ ] **Step 1: 更新 `__init__.py`**

```python
"""douyin-to-text: Transcribe Douyin videos and local media files via Qwen Paraformer streaming ASR."""

__version__ = "0.5.0"

from douyin_to_text.pipeline import transcribe_url, transcribe_file

__all__ = ["transcribe_url", "transcribe_file", "__version__"]
```

- [ ] **Step 2: 运行测试验证**

```bash
pytest tests/test_smoke.py -v
```
Expected: 11 passed（`test_transcribe_file_importable` 现在从顶层导入）

注意：`test_transcribe_file_importable` 目前导入 `douyin_to_text.pipeline.transcribe_file`，更新后应改为从 `douyin_to_text` 导入。更新测试：

```python
def test_transcribe_file_importable():
    from douyin_to_text import transcribe_file
    assert callable(transcribe_file)
```

- [ ] **Step 3: Commit**

```bash
git add src/douyin_to_text/__init__.py tests/test_smoke.py
git commit -m "feat: export transcribe_file from public API, bump to 0.5.0"
```

---

### Task 6: 新增文件名词干清洗测试

**Files:**
- Modify: `tests/test_smoke.py` (追加)

- [ ] **Step 1: 添加测试**

```python
def test_sanitize_with_file_stems():
    """Common file stems should produce readable slugs."""
    assert _sanitize("会议录制") == "会议录制"
    assert _sanitize("meeting-2024") == "meeting-2024"
    assert _sanitize("video (1)") == "video_(1)"
    assert _sanitize("C:/Users/test/video") == "C:Userstestvideo"
    assert _sanitize("你好世界.mp4") == "你好世界.mp4"


def test_sanitize_trailing_dashes_and_underscores():
    """Trailing separators should be stripped."""
    assert _sanitize("hello---") == "hello"
    assert _sanitize("hello___") == "hello"
    assert _sanitize("hello_-_") == "hello"
```

- [ ] **Step 2: 运行测试验证通过**

```bash
pytest tests/test_smoke.py -v
```
Expected: 13 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_smoke.py
git commit -m "test: add sanitize tests for file stems and trailing separators"
```

---

### Task 7: 新增 `mp4_to_mp3` 纯音频输入测试

**Files:**
- Modify: `tests/test_smoke.py` (追加)

- [ ] **Step 1: 添加测试（使用 Python wave 生成测试 wav 文件）**

```python
import subprocess
import tempfile
from pathlib import Path


def _ffmpeg_available() -> bool:
    """Check if ffmpeg is on PATH and can be invoked."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def test_mp4_to_mp3_accepts_audio():
    """mp4_to_mp3 should convert a pure audio file (wav) to mp3."""
    if not _ffmpeg_available():
        import pytest
        pytest.skip("ffmpeg not available")

    from douyin_to_text.asr import mp4_to_mp3

    with tempfile.TemporaryDirectory() as td:
        wav_path = Path(td) / "test.wav"
        # Generate a minimal valid WAV: 1 second of silence, 16kHz mono 16-bit
        import struct
        import wave

        sample_rate = 16000
        num_samples = sample_rate  # 1 second
        with wave.open(str(wav_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(b"\x00\x00" * num_samples)

        mp3 = mp4_to_mp3(wav_path, output=Path(td) / "out.mp3")
        assert mp3.exists()
        assert mp3.stat().st_size > 0
```

- [ ] **Step 2: 运行测试验证通过**

```bash
pytest tests/test_smoke.py::test_mp4_to_mp3_accepts_audio -v
```
Expected: PASS (or SKIP if no ffmpeg)

- [ ] **Step 3: 运行全部测试确认无回归**

```bash
pytest tests/test_smoke.py -v
```
Expected: 14 passed

- [ ] **Step 4: Commit**

```bash
git add tests/test_smoke.py
git commit -m "test: add mp4_to_mp3 pure-audio conversion test"
```

---

### Task 8: 更新 `pyproject.toml` 版本号

**Files:**
- Modify: `pyproject.toml:7`

- [ ] **Step 1: 修改版本号**

```diff
-version = "0.4.0"
+version = "0.5.0"
```

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.5.0"
```
