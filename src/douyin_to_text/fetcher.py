"""Download media from Douyin and Bilibili video links."""

from pathlib import Path
from urllib.parse import urlsplit

import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def fetch_media(target_url: str, raw_dir: Path) -> tuple[Path, str]:
    url = urlsplit(target_url)
    host = (url.hostname or "").rstrip(".")
    if url.scheme in ("https", "http") and (
        host in ("bilibili.com", "b23.tv") or host.endswith(".bilibili.com")
    ):
        return _fetch_bilibili(target_url, raw_dir)
    return fetch_mp4(target_url, raw_dir)


def _fetch_bilibili(target_url: str, raw_dir: Path) -> tuple[Path, str]:
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError

    options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "playlist_items": "1",
        "paths": {"home": str(raw_dir.resolve())},
        "outtmpl": "bilibili.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        # yt-dlp can print the raw failure before raising DownloadError.
        "logger": _QuietDownloadLogger(),
    }
    try:
        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(target_url, download=True)
            if info and info.get("_type") == "playlist":
                info = next((entry for entry in info["entries"] if entry), None)
            if info:
                path = raw_dir / Path(downloader.prepare_filename(info)).name
                if path.is_file() and path.stat().st_size:
                    return path, info.get("title") or ""
    except DownloadError:
        pass
    raise RuntimeError(
        "B 站视频下载失败。请确认链接能在未登录时播放，并尝试更新 yt-dlp 后重试。"
    )


class _QuietDownloadLogger:
    def debug(self, message):
        pass

    warning = error = debug


def fetch_mp4(target_url: str, raw_dir: Path) -> tuple[Path, str]:
    """Open a Douyin video page, sniff its mp4 URL, download.

    Returns (mp4_path, page_title).
    """
    from playwright.sync_api import Error, sync_playwright

    mp4_urls: list[str] = []

    def on_response(resp):
        u = resp.url
        ct = resp.headers.get("content-type", "")
        is_mp4 = ".mp4" in u or "video/mp4" in ct
        from_douyin_cdn = (
            "douyin" in u or "bytecdn" in u or "ixigua" in u or "douyinvod" in u
        )
        if is_mp4 and from_douyin_cdn:
            mp4_urls.append(u)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            user_agent=UA, viewport={"width": 1280, "height": 800}, locale="zh-CN"
        )
        page = ctx.new_page()
        page.on("response", on_response)
        page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2500)
        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        try:
            video_src = page.evaluate("document.querySelector('video')?.src || ''")
            if video_src and "blob:" not in video_src:
                mp4_urls.append(video_src)
        except Error:
            pass
        try:
            page_title = page.title() or ""
        except Error:
            page_title = ""
        cookies = ctx.cookies()
        browser.close()

    if not mp4_urls:
        raise RuntimeError("No mp4 URL captured. Video may use HLS/DASH or be blocked.")

    mp4_url = max(set(mp4_urls), key=len)

    cookie_jar = {c["name"]: c["value"] for c in cookies}
    headers = {"User-Agent": UA, "Referer": "https://www.douyin.com/", "Range": "bytes=0-"}
    out_path = raw_dir / "video.mp4"
    with httpx.Client(
        cookies=cookie_jar, headers=headers, follow_redirects=True, timeout=60
    ) as client, client.stream("GET", mp4_url) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.writelines(r.iter_bytes(64 * 1024))
    return out_path, page_title
