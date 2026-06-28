"""Smoke tests — pure-function only. Network/API tests live elsewhere."""

import subprocess
import tempfile
import wave
from pathlib import Path

from douyin_to_text import __version__, transcribe_url
from douyin_to_text.pipeline import _sanitize


def test_version_exposed():
    assert __version__
    assert isinstance(__version__, str)


def test_public_api_importable():
    assert callable(transcribe_url)


def test_sanitize_strips_unsafe_chars():
    assert _sanitize("a/b\\c:d*e?f\"g<h>i|j") == "abcdefghij"


def test_sanitize_collapses_whitespace():
    assert _sanitize("hello   world  foo") == "hello_world_foo"


def test_sanitize_drops_tabs_and_newlines():
    # tabs/newlines/cr are unsafe filename chars — stripped, not collapsed
    assert _sanitize("hello\tworld\nfoo") == "helloworldfoo"


def test_sanitize_removes_platform_words():
    assert _sanitize("某视频 - 抖音") == "某视频"
    assert _sanitize("clip - Douyin") == "clip"


def test_sanitize_truncates():
    long = "a" * 200
    assert len(_sanitize(long, max_len=40)) == 40


def test_sanitize_empty_fallback():
    assert _sanitize("") == "untitled"
    assert _sanitize("///") == "untitled"


def test_summary_prompt_includes_transcript():
    from douyin_to_text.summarize import build_prompt

    p = build_prompt("hello world")
    assert "hello world" in p
    assert "Markdown" in p
    assert "一句话概括" in p


def test_summary_prompt_strips_whitespace():
    from douyin_to_text.summarize import build_prompt

    a = build_prompt("  abc  ")
    b = build_prompt("abc")
    assert a == b


def test_transcribe_file_importable():
    from douyin_to_text import transcribe_file
    assert callable(transcribe_file)


def test_sanitize_with_file_stems():
    """Common file stems should produce readable slugs."""
    assert _sanitize("会议录制") == "会议录制"
    assert _sanitize("meeting-2024") == "meeting-2024"
    assert _sanitize("video (1)") == "video_(1)"
    assert _sanitize("C:/Users/test/video") == "CUserstestvideo"
    assert _sanitize("你好世界.mp4") == "你好世界.mp4"


def test_sanitize_trailing_dashes_and_underscores():
    """Trailing separators should be stripped."""
    assert _sanitize("hello---") == "hello"
    assert _sanitize("hello___") == "hello"
    assert _sanitize("hello_-_") == "hello"


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
