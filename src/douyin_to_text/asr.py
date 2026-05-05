"""Qwen Paraformer streaming ASR wrapper."""

import subprocess
from pathlib import Path

from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult


def mp4_to_mp3(mp4: Path) -> Path:
    """Extract 16kHz mono mp3 audio track via ffmpeg."""
    mp3 = mp4.with_suffix(".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp4), "-vn", "-ar", "16000", "-ac", "1",
         "-codec:a", "libmp3lame", "-q:a", "5", str(mp3)],
        check=True, capture_output=True,
    )
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
