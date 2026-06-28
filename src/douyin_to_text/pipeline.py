"""End-to-end pipeline: URL -> transcript text."""

import datetime
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from douyin_to_text.asr import mp4_to_mp3, transcribe_mp3
from douyin_to_text.fetcher import fetch_mp4
from douyin_to_text.summarize import summarize_transcript


def _sanitize(name: str, max_len: int = 40) -> str:
    name = re.sub(r"[\\/:*?\"<>|\r\n\t]+", "", name)
    name = re.sub(r"\s+", "_", name).strip("_- ")
    name = name.replace("抖音", "").replace("Douyin", "").strip("_- ")
    return (name[:max_len] or "untitled").rstrip("_- ")


@dataclass
class TranscribeResult:
    text: str
    output_path: Path
    raw_dir: Path
    page_title: str
    summary: str | None = None
    summary_path: Path | None = None


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
    mp3 = mp4_to_mp3(source_path, output=raw_dir / "audio.mp3")
    text = transcribe_mp3(mp3, on_sentence=on_sentence)
    (raw_dir / "transcript.txt").write_text(text, encoding="utf-8")

    if not keep_media:
        try:
            mp3.unlink()
        except OSError:
            pass

    return text


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
            # transcription is the main deliverable — summary failure is non-fatal
            summary = f"(summary failed: {e})"

    return TranscribeResult(
        text=text,
        output_path=out_path,
        raw_dir=raw_dir,
        page_title=page_title,
        summary=summary,
        summary_path=summary_path,
    )


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
