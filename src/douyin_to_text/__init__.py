"""douyin-to-text: Transcribe Douyin videos and local media files via Qwen Paraformer streaming ASR."""

__version__ = "0.5.0"

from douyin_to_text.pipeline import transcribe_url, transcribe_file

__all__ = ["transcribe_url", "transcribe_file", "__version__"]
