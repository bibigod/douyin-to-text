import subprocess
import traceback
from unittest.mock import Mock

import pytest

from douyin_to_text.asr import mp4_to_mp3


@pytest.mark.parametrize(
    ("stderr", "detail"),
    [
        (
            (
                b"[in#0] Error opening input C:\\Users\\private-name\\video.mp4: "
                b"Invalid data found when processing input\n"
                b"comment: https://example.invalid/?token=private-token\xff"
            ),
            "Invalid data found when processing input",
        ),
        (b"unrecognized detail: private-token\xff", "未识别到可安全显示"),
        (None, "未识别到可安全显示"),
    ],
)
def test_mp4_to_mp3_reports_safe_ffmpeg_error(monkeypatch, tmp_path, stderr, detail):
    mp4 = tmp_path / "private-name.mp4"

    def fail(cmd, **kwargs):
        raise subprocess.CalledProcessError(4294967274, cmd, stderr=stderr)

    monkeypatch.setattr(subprocess, "run", fail)

    with pytest.raises(RuntimeError) as caught:
        mp4_to_mp3(mp4)

    message = str(caught.value)
    assert "4294967274" in message
    assert detail in message
    assert "视频能播放" in message
    assert "输出目录可写" in message
    assert "ffmpeg -version" in message
    rendered = "".join(traceback.format_exception(caught.value))
    assert "private-name" not in rendered
    assert "private-token" not in rendered


def test_mp4_to_mp3_keeps_successful_conversion(monkeypatch, tmp_path):
    mp4 = tmp_path / "video.mp4"
    mp3 = mp4.with_suffix(".mp3")
    run = Mock(return_value=subprocess.CompletedProcess(args=[], returncode=0))
    monkeypatch.setattr(subprocess, "run", run)

    assert mp4_to_mp3(mp4) == mp3
    run.assert_called_once_with(
        ["ffmpeg", "-y", "-i", str(mp4), "-vn", "-ar", "16000", "-ac", "1",
         "-codec:a", "libmp3lame", "-q:a", "5", str(mp3)],
        check=True, capture_output=True,
    )


def test_missing_ffmpeg_explains_how_to_recover(monkeypatch, tmp_path):
    run = Mock(side_effect=FileNotFoundError(2, "not found", "private-path"))
    monkeypatch.setattr(subprocess, "run", run)

    with pytest.raises(RuntimeError, match="找不到 FFmpeg") as caught:
        mp4_to_mp3(tmp_path / "video.mp4")

    assert "PATH" in str(caught.value)
    assert "重新打开终端" in str(caught.value)
    assert "ffmpeg -version" in str(caught.value)
    assert "private-path" not in "".join(traceback.format_exception(caught.value))


def test_mp3_input_does_not_overwrite_download(monkeypatch, tmp_path):
    audio = tmp_path / "bilibili.mp3"
    run = Mock()
    monkeypatch.setattr(subprocess, "run", run)

    converted = mp4_to_mp3(audio)

    assert converted == tmp_path / "bilibili.asr.mp3"
    assert run.call_args.args[0][-1] == str(converted)
