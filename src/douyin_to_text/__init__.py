"""douyin-to-text: Transcribe Douyin videos via Qwen Paraformer streaming ASR."""

__version__ = "0.4.0"

from douyin_to_text.pipeline import transcribe_url

__all__ = ["transcribe_url", "__version__"]
