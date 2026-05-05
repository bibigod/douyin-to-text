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
    mp3 = mp4_to_mp3(mp4)
    text = transcribe_mp3(mp3, on_sentence=on_sentence)

    (raw_dir / "transcript.txt").write_text(text, encoding="utf-8")
    (raw_dir / "source_url.txt").write_text(url, encoding="utf-8")
    (raw_dir / "page_title.txt").write_text(page_title, encoding="utf-8")

    if not keep_media:
        for f in (mp4, mp3):
            try:
                f.unlink()
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
