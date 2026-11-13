"""Qwen Paraformer streaming ASR wrapper."""

import subprocess
from pathlib import Path

from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult


# Only display known error phrases: stderr can include paths, URLs and media metadata.
_FFMPEG_ERROR_PHRASES = (
    "No such file or directory",
    "Permission denied",
    "No space left on device",
    "Invalid data found when processing input",
    "moov atom not found",
    "Output file does not contain any stream",
    "Unknown encoder 'libmp3lame'",
    "Invalid argument",
)


def mp4_to_mp3(mp4: Path) -> Path:
    """Extract 16kHz mono MP3 audio from a downloaded media file via FFmpeg."""
    mp3 = mp4.with_suffix(".mp3")
    if mp4.suffix.lower() == ".mp3":
        mp3 = mp4.with_suffix(".asr.mp3")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp4), "-vn", "-ar", "16000", "-ac", "1",
             "-codec:a", "libmp3lame", "-q:a", "5", str(mp3)],
            check=True, capture_output=True,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "找不到 FFmpeg。请安装 FFmpeg，将其可执行文件所在目录加入 PATH，"
            "重新打开终端并运行 ffmpeg -version，再重新启动本工具。"
        ) from None
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode("utf-8", errors="replace").lower()
        details = "；".join(phrase for phrase in _FFMPEG_ERROR_PHRASES if phrase.lower() in stderr)
        if not details:
            details = "未识别到可安全显示的 FFmpeg 错误详情"
        raise RuntimeError(
            f"FFmpeg 转码失败（退出状态 {exc.returncode}）：{details}。"
            "请确认下载的视频能播放且含有音轨，输出目录可写且磁盘空间充足，"
            "并运行 ffmpeg -version 确认当前环境能找到 FFmpeg，"
            "运行 ffmpeg -encoders 检查是否支持 libmp3lame。"
        ) from None
    return mp3


class _Collector(RecognitionCallback):
    def __init__(self, on_sentence=None):
        self.sentences: list[str] = []
        self._on_sentence = on_sentence

    def on_event(self, result: RecognitionResult) -> None:
        s = result.get_sentence()
        if "text" in s and RecognitionResult.is_sentence_end(s):
            text = s["text"]
            self.sentences.append(text)
            if self._on_sentence:
                self._on_sentence(text)

    def on_error(self, result):
        raise RuntimeError(f"ASR error: {result.message}")

    def on_complete(self):
        pass


def transcribe_mp3(mp3: Path, on_sentence=None) -> str:
    """Stream the mp3 to Paraformer; returns one-sentence-per-line text."""
    cb = _Collector(on_sentence=on_sentence)
    rec = Recognition(
        model="paraformer-realtime-v2",
        format="mp3",
        sample_rate=16000,
        callback=cb,
    )
    rec.start()
    with open(mp3, "rb") as f:
        while chunk := f.read(3200):
            rec.send_audio_frame(chunk)
    rec.stop()
    return "\n".join(s.strip() for s in cb.sentences if s.strip())
