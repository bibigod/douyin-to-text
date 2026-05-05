# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/bibigod/douyin-to-text/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/bibigod/douyin-to-text/releases/tag/v0.1.0
