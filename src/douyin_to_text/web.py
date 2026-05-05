"""Local-only Gradio UI for douyin-to-text.

Launch with:  douyin-to-text-ui
Binds 127.0.0.1 by default — never share publicly without re-reading the
disclaimer in README.
"""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr

from douyin_to_text import __version__
from douyin_to_text.pipeline import transcribe_url


DISCLAIMER = """
> ⚠️ **仅供个人学习研究使用**。使用本工具时请遵守抖音用户协议、《著作权法》及相关法律法规。
> 禁止用于商业用途、批量抓取或视频/转写文本的再分发。详见
> [README 免责声明](https://github.com/bibigod/douyin-to-text#%EF%B8%8F-免责声明--disclaimer)。
"""


def _run(url: str, do_summary: bool, api_key: str, out_dir: str):
    url = (url or "").strip()
    if not url:
        return "请输入抖音链接", "", ""

    if (api_key or "").strip():
        os.environ["DASHSCOPE_API_KEY"] = api_key.strip()
    if not os.environ.get("DASHSCOPE_API_KEY"):
        return (
            "❌ 未配置 DASHSCOPE_API_KEY。请在下方输入框粘贴你的 key，"
            "或设置环境变量后重启服务。",
            "",
            "",
        )

    out = Path(out_dir).expanduser() if out_dir else Path("./transcripts")

    try:
        result = transcribe_url(url, out_dir=out, summarize=do_summary)
    except Exception as e:
        return f"❌ 失败：{e}", "", ""

    status = f"✅ 转写完成 → `{result.output_path}`"
    if result.summary_path:
        status += f"\n📝 总结完成 → `{result.summary_path}`"
    elif do_summary and result.summary and result.summary.startswith("(summary failed"):
        status += f"\n⚠️ 总结失败：{result.summary}（转写已保存）"

    return status, result.text, (result.summary or "")


def build_app() -> gr.Blocks:
    with gr.Blocks(title=f"douyin-to-text v{__version__}") as app:
        gr.Markdown(f"# 🎬 douyin-to-text  `v{__version__}`")
        gr.Markdown("**抖音视频 → 中文转写 + LLM 总结**（基于 Qwen Paraformer + qwen-plus）")
        gr.Markdown(DISCLAIMER)

        with gr.Row():
            url = gr.Textbox(
                label="抖音链接",
                placeholder="https://v.douyin.com/xxxxxx/",
                scale=4,
            )
            run_btn = gr.Button("开始转写", variant="primary", scale=1)

        with gr.Row():
            do_summary = gr.Checkbox(label="附带 LLM 总结（一句话概括 + 要点）", value=True)
            out_dir = gr.Textbox(
                label="输出目录", value="./transcripts", scale=2,
            )

        api_key = gr.Textbox(
            label="DASHSCOPE_API_KEY（留空则读环境变量）",
            type="password",
            placeholder="sk-...",
        )

        status = gr.Markdown(label="状态")

        with gr.Tab("📝 转写文本"):
            transcript = gr.Textbox(label="逐句转写", lines=18, interactive=False)
        with gr.Tab("🧠 LLM 总结"):
            summary = gr.Markdown()

        run_btn.click(
            _run,
            inputs=[url, do_summary, api_key, out_dir],
            outputs=[status, transcript, summary],
        )

    return app


def main() -> int:
    app = build_app()
    # Bind to localhost only — do not expose this UI publicly.
    app.launch(
        server_name="127.0.0.1",
        inbrowser=True,
        show_api=False,
        theme=gr.themes.Soft(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
