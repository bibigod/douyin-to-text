"""Local-only Gradio UI for douyin-to-text.

Launch with:  douyin-to-text-ui
Binds 127.0.0.1 by default — never share publicly without re-reading the
disclaimer in README.
"""

from __future__ import annotations

import os
import queue
import threading
from pathlib import Path

import gradio as gr

from douyin_to_text import __version__
from douyin_to_text.config import CONFIG_FILE, get_saved_api_key, save_api_key
from douyin_to_text.pipeline import transcribe_url


DISCLAIMER = (
    "> ⚠️ **仅供个人学习研究使用**。使用本工具时请遵守抖音用户协议、《著作权法》及相关法律法规。"
    "禁止用于商业用途、批量抓取或视频/转写文本的再分发。"
    "[查看完整免责声明](https://github.com/bibigod/douyin-to-text#%EF%B8%8F-免责声明--disclaimer)"
)

INITIAL_STATUS = "💤 等待输入：粘贴抖音链接 → 点 **开始转写**"

STAGE_LABELS = {
    "fetching": "📥 [1/3] 正在抓取视频（Playwright 启动中，约 10–15 秒）...",
    "transcribing": "🎙️ [2/3] 转写音频（Paraformer 流式，按视频长度约 30–60 秒）...",
    "summarizing": "🧠 [3/3] LLM 总结中（qwen-plus，约 5–10 秒）...",
}


def _run(url: str, do_summary: bool, api_key: str, out_dir: str):
    """Generator yielding (status_md, transcript, summary_md)."""
    url = (url or "").strip()
    if not url:
        yield "❌ 请先输入抖音链接", "", ""
        return

    typed_key = (api_key or "").strip()
    if typed_key:
        os.environ["DASHSCOPE_API_KEY"] = typed_key
        # persist to ~/.douyin-to-text/config.json so next launch auto-fills
        if get_saved_api_key() != typed_key:
            try:
                save_api_key(typed_key)
            except Exception:
                pass
    elif get_saved_api_key():
        os.environ["DASHSCOPE_API_KEY"] = get_saved_api_key()

    if not os.environ.get("DASHSCOPE_API_KEY"):
        yield (
            "❌ 未配置 DASHSCOPE_API_KEY。请在下方输入框粘贴你的 key，或设置环境变量后重启。",
            "", "",
        )
        return

    out = Path(out_dir).expanduser() if out_dir else Path("./transcripts")

    # Run pipeline in a worker thread; main thread polls a queue for stage events
    # and yields fresh status to Gradio so the user sees real progress.
    events: queue.Queue = queue.Queue()
    holder: dict = {}

    def on_stage(name: str):
        events.put(("stage", name))

    def worker():
        try:
            holder["result"] = transcribe_url(
                url, out_dir=out, summarize=do_summary, on_stage=on_stage,
            )
        except Exception as e:
            holder["error"] = e
        finally:
            events.put(("done", None))

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    yield "🚀 启动中...", "", ""

    while True:
        kind, payload = events.get()
        if kind == "stage":
            yield STAGE_LABELS.get(payload, f"⏳ {payload}..."), "", ""
        elif kind == "done":
            break

    t.join()

    if "error" in holder:
        yield f"❌ 失败：{holder['error']}", "", ""
        return

    result = holder["result"]
    parts = [f"✅ 转写完成 → `{result.output_path}`"]
    if result.summary_path:
        parts.append(f"📝 总结完成 → `{result.summary_path}`")
    elif do_summary and result.summary and result.summary.startswith("(summary failed"):
        parts.append(f"⚠️ 总结失败：{result.summary}（转写已保存）")
    yield "\n\n".join(parts), result.text, (result.summary or "")


_CUSTOM_CSS = """
/* === 字体栈：mac 优先 → Windows → 鸿蒙 → 思源黑 fallback === */
.gradio-container, .gradio-container * {
    font-family:
        -apple-system, BlinkMacSystemFont,
        "Segoe UI", "Segoe UI Variable", Roboto,
        "PingFang SC", "Hiragino Sans GB",
        HarmonyOS_Sans_SC, "Microsoft YaHei UI", "Microsoft YaHei",
        "Source Han Sans SC", "Noto Sans CJK SC",
        "Helvetica Neue", Helvetica, Arial, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    letter-spacing: 0.01em;
}

/* === 容器：限宽居中，呼吸感 === */
.gradio-container {
    max-width: 1080px !important;
    margin: 0 auto !important;
    font-size: 15px;
    line-height: 1.65;
    color: #1f2328;
}

/* === 标题（H1/H2）：semibold 不要 bold === */
.gradio-container h1 {
    font-weight: 600 !important;
    font-size: 28px !important;
    line-height: 1.35 !important;
    color: #1f2328 !important;
    letter-spacing: -0.005em !important;
    margin-bottom: 4px !important;
}
.gradio-container h2 {
    font-weight: 600 !important;
    font-size: 20px !important;
    line-height: 1.4 !important;
    color: #1f2328 !important;
}

/* === 副标题 / 普通段落（紧贴 H1 那行） === */
.gradio-container .prose p,
.gradio-container .markdown p {
    font-size: 15px !important;
    line-height: 1.65 !important;
    color: #424a53 !important;
}

/* === 表单 label：medium weight，柔和色 === */
.gradio-container label > span,
.gradio-container .label-wrap > span,
.gradio-container .block-label {
    font-weight: 500 !important;
    font-size: 14px !important;
    color: #424a53 !important;
    letter-spacing: 0 !important;
}

/* === info / hint 灰字 === */
.gradio-container .info,
.gradio-container [data-testid="info"],
.gradio-container .form > .info {
    font-size: 13px !important;
    color: #6e7781 !important;
    line-height: 1.55 !important;
    font-weight: 400 !important;
}

/* === 输入框 === */
.gradio-container input[type="text"],
.gradio-container input[type="password"],
.gradio-container textarea {
    font-size: 15px !important;
    color: #1f2328 !important;
    line-height: 1.6 !important;
}
.gradio-container input::placeholder,
.gradio-container textarea::placeholder {
    color: #8c959f !important;
    font-weight: 400 !important;
}

/* === 按钮：medium，加点字距 === */
.gradio-container button.primary,
.gradio-container button[variant="primary"] {
    font-weight: 500 !important;
    font-size: 15px !important;
    letter-spacing: 0.02em !important;
}

/* === blockquote（免责声明）：小一号，灰色，左边线柔和 === */
.gradio-container blockquote {
    font-size: 13px !important;
    color: #6e7781 !important;
    line-height: 1.6 !important;
    border-left-color: #d0d7de !important;
    margin: 8px 0 !important;
    padding: 4px 12px !important;
}

/* === 等宽字体（路径 / 代码片段） === */
.gradio-container code,
.gradio-container kbd,
.gradio-container pre {
    font-family:
        "SF Mono", "JetBrains Mono", "Fira Code",
        "Cascadia Mono", "Consolas",
        "PingFang SC", monospace !important;
    font-size: 13px !important;
}

/* === 隐藏 Gradio 6 的底栏（API / 设置 / Built with Gradio） === */
footer { display: none !important; }
"""


def build_app() -> gr.Blocks:
    with gr.Blocks(
        title=f"douyin-to-text v{__version__}",
        analytics_enabled=False,
    ) as app:
        gr.Markdown(f"# 🎬 douyin-to-text  `v{__version__}`")
        gr.Markdown(
            "**抖音视频 → 中文转写 + LLM 总结**（基于 Qwen Paraformer + qwen-plus）"
        )
        gr.Markdown(DISCLAIMER)

        _saved_key = get_saved_api_key()
        _key_info = (
            f"已自动从 `{CONFIG_FILE}` 载入。要换 key，覆盖填入即可。"
            if _saved_key else
            "去 https://dashscope.aliyun.com/ 控制台申领（有免费额度）。"
            f"首次填入后会保存到 `{CONFIG_FILE}`，下次自动加载，不用重填。"
        )
        api_key = gr.Textbox(
            label="① DASHSCOPE_API_KEY  （必填）",
            info=_key_info,
            type="password",
            placeholder="sk-...",
            value=_saved_key,
        )

        with gr.Row():
            url = gr.Textbox(
                label="② 抖音链接",
                placeholder="例如：https://v.douyin.com/lXW3WOHHokM/   （从抖音 App 分享 → 复制链接）",
                scale=4,
            )
            run_btn = gr.Button("③ 开始转写", variant="primary", scale=1)

        do_summary = gr.Checkbox(
            label="附带 LLM 总结",
            info="勾选后额外生成一份 .md：一句话概括 + 核心要点 + 实用信息",
            value=True,
        )
        out_dir = gr.Textbox(
            label="输出目录",
            value="./transcripts",
            info="转写稿和总结都会保存到这里。原始 mp4/mp3 转写后会被自动删除。",
        )

        status = gr.Markdown(value=INITIAL_STATUS)

        with gr.Tab("📝 转写文本"):
            transcript = gr.Textbox(
                show_label=False,
                lines=12,
                interactive=False,
                placeholder="转写完成后，每一句视频对白会出现在这里。",
            )
        with gr.Tab("🧠 LLM 总结"):
            summary = gr.Markdown(value="*勾选「附带 LLM 总结」并完成转写后，这里会出现一句话概括 + 要点。*")

        gr.Markdown(
            "<sub>问题反馈 / 视频抓取失败 / CDN 域名变化："
            "[GitHub Issues](https://github.com/bibigod/douyin-to-text/issues)</sub>"
        )

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
        theme=gr.themes.Soft(),
        css=_CUSTOM_CSS,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
