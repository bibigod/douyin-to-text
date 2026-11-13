from pathlib import Path
from unittest.mock import Mock

import pytest
import yt_dlp
from yt_dlp.utils import DownloadError

from douyin_to_text import fetcher, pipeline


@pytest.mark.parametrize("url", [
    "https://www.bilibili.com/video/BVexample/?p=2",
    "https://b23.tv/example",
])
def test_bilibili_link_flows_through_transcription(monkeypatch, tmp_path, url):
    downloader = Mock()

    def make_downloader(options):
        assert options["format"] == "bestaudio/best"
        assert options["noplaylist"]
        raw_dir = Path(options["paths"]["home"])
        media = raw_dir / (options["outtmpl"] % {"ext": "m4a"})
        media.write_bytes(b"downloaded")
        downloader.prepare_filename.return_value = str(media)
        return downloader

    downloader.__enter__ = Mock(return_value=downloader)
    downloader.__exit__ = Mock(return_value=False)
    downloader.extract_info.return_value = {"title": "B站示例"}
    monkeypatch.setattr(yt_dlp, "YoutubeDL", make_downloader)
    monkeypatch.setattr(fetcher, "fetch_mp4", Mock(side_effect=AssertionError("Douyin path")))

    def convert(media):
        assert media.suffix == ".m4a"
        assert media.read_bytes() == b"downloaded"
        mp3 = media.with_suffix(".mp3")
        mp3.write_bytes(b"converted")
        return mp3

    def transcribe(mp3, on_sentence):
        assert mp3.read_bytes() == b"converted"
        return "转写结果"

    monkeypatch.setattr(pipeline, "mp4_to_mp3", convert)
    monkeypatch.setattr(pipeline, "transcribe_mp3", transcribe)
    result = pipeline.transcribe_url(url, out_dir=tmp_path / "out%dir")

    downloader.extract_info.assert_called_once_with(url, download=True)
    assert result.page_title == "B站示例"
    assert result.output_path.read_text(encoding="utf-8") == "转写结果"
    assert not list(result.raw_dir.glob("bilibili.*"))


@pytest.mark.parametrize("url", [
    "https://v.douyin.com/example/?from=bilibili.com",
    "https://bilibili.com.example/video/BVexample",
])
def test_other_links_do_not_use_bilibili_downloader(monkeypatch, tmp_path, url):
    douyin = Mock(return_value=(tmp_path / "video.mp4", "抖音视频"))
    monkeypatch.setattr(fetcher, "fetch_mp4", douyin)

    assert fetcher.fetch_media(url, tmp_path) == douyin.return_value
    douyin.assert_called_once_with(url, tmp_path)


def test_bilibili_download_error_hides_private_details(monkeypatch, tmp_path):
    from unittest.mock import MagicMock

    downloader = MagicMock()
    downloader.__enter__.return_value.extract_info.side_effect = DownloadError("private-token")
    monkeypatch.setattr(yt_dlp, "YoutubeDL", Mock(return_value=downloader))

    with pytest.raises(RuntimeError, match="B 站视频下载失败") as caught:
        fetcher.fetch_media("https://b23.tv/example", tmp_path)
    assert "private-token" not in str(caught.value)
