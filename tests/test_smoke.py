"""Smoke tests — pure-function only. Network/API tests live elsewhere."""

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
