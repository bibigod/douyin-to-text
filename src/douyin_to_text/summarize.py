"""Optional LLM summarization step (Qwen via DashScope).

Reuses the same DASHSCOPE_API_KEY the user already configured for ASR,
so no extra setup is needed to enable --summary.
"""

from dashscope import Generation


DEFAULT_MODEL = "qwen-plus"

_PROMPT = """你是一个善于提炼短视频要点的助手。下面是一段抖音视频的口语逐句转写稿（含口误、重复、断句），请总结为以下结构的中文 Markdown：

## 一句话概括
（不超过 30 字）

## 核心要点
- （3 到 7 条要点，每条一行，包含关键名词、数字、人物、事件）

## 实用信息（如有）
- （工具名、链接、价格、时间、操作步骤等。没有就省略整段。）

要求：
- 只输出 Markdown，不要任何前置说明
- 保留专有名词原文（如 Gemini 4、Photoshop、Neuralink）
- 不杜撰原文没有的内容

转写稿：
---
{transcript}
---
"""


def build_prompt(transcript: str) -> str:
    """Build the summarization prompt. Pure function, easy to unit-test."""
    return _PROMPT.format(transcript=transcript.strip())


def summarize_transcript(transcript: str, model: str = DEFAULT_MODEL) -> str:
    """Call Qwen to produce a Markdown summary of a transcript.

    Raises on API failure; caller decides whether to swallow.
    """
    response = Generation.call(
        model=model,
        messages=[{"role": "user", "content": build_prompt(transcript)}],
        result_format="message",
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Qwen summary failed: status={response.status_code} "
            f"code={response.code} msg={response.message}"
        )
    return response.output.choices[0].message.content.strip()
