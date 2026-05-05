# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-05-05

### Added
- **API Key 持久化**：`config.py` 模块。首次填入后自动保存到
  `~/.douyin-to-text/config.json`，下次启动 UI 时自动加载，无需重填。POSIX
  系统会 chmod 0600。
- **真实进度反馈**：`pipeline.transcribe_url` 新增 `on_stage` 回调；UI 用
  线程 + 队列在三个真实节点（fetching / transcribing / summarizing）上
  yield 状态，用户不再看到"转圈不知道死活"。
- `INSTALL.md`：零基础 10 分钟上手傻瓜式指南（中文，含 Python/ffmpeg/API
  Key 申请的全流程）。
- `tests/manual_e2e.py`：headless 端到端测试脚本，无需开浏览器即可验证
  整条链路。

### Changed
- **UI 信息架构**：API Key 移到顶部常驻（编号 ①②③），不再折叠 Accordion——
  没填 Key 就跑不动，藏起来反而有反作用。
- **UI 排版**：参考 GitHub Primer + 中文 Web 字体最佳实践重写 CSS
  ——苹方/雅黑系统字体栈、4px 栅格字号（13/14/15/20/28）、行高 1.65、
  字重 500/600（不再用 700）、灰阶 `#1f2328`/`#424a53`/`#6e7781`、
  抗锯齿、letter-spacing +0.01em。
- **UI footer 隐藏**：去掉 Gradio 6 默认的"通过 API 使用 / 设置"调试入口。
- 表单 label 信息更准确：每个字段下方加了 `info` 灰字提示，含
  Key 申请链接和"mp4 转写后会自动删除"等约束说明。

### Notes
- `_HIDE_FOOTER_CSS` 改名 `_CUSTOM_CSS`，因为它已不止隐藏 footer
- Gradio 6 把 `css` 和 `theme` 都从 `Blocks()` 构造器移到 `launch()`，
  代码已适配

### Added
- Local Gradio Web UI: `douyin-to-text-ui` (binds 127.0.0.1 only)
- New extras: `pip install "douyin-to-text[ui]"` for the UI
- First PyPI release — installable via `pip install douyin-to-text`

### Notes
- Tested against Gradio 6.x; theme is passed to `launch()` per Gradio 6 API change
- The UI deliberately does not expose `share=True` — keeping the project on the
  "tool, not service" side of the legal posture

## [0.2.0] - 2026-05-05

### Added
- `--summary` flag: produce a Markdown summary (一句话概括 / 核心要点 / 实用信息) via Qwen `qwen-plus`, reusing the same DASHSCOPE_API_KEY
- `summarize_transcript()` and `build_prompt()` exposed in `douyin_to_text.summarize`
- `TranscribeResult.summary` and `.summary_path` fields
- 2 new prompt-builder unit tests

### Changed
- CLI progress shows `[1/4] [2/4] [3/4] [4/4]` when `--summary` is used
- Summary failure is non-fatal: transcript still saves; failure recorded in result

## [0.1.0] - 2026-05-05

### Added
- Initial CLI: `douyin-to-text <url>` — Douyin URL → Chinese transcript txt
- Library API: `from douyin_to_text import transcribe_url`
- Playwright-based mp4 sniffer with httpx redownload (cookie + UA replay)
- Qwen Paraformer streaming ASR via DashScope SDK
- Default media auto-cleanup after transcription (`--keep-media` to opt out)
- MIT license + bilingual disclaimer
- Smoke tests for pure helpers
- GitHub Actions CI: ruff lint + pytest

[Unreleased]: https://github.com/bibigod/douyin-to-text/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/bibigod/douyin-to-text/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/bibigod/douyin-to-text/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/bibigod/douyin-to-text/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/bibigod/douyin-to-text/releases/tag/v0.1.0
