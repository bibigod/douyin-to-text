# CLAUDE.md — douyin-to-text

This file is read by Claude Code (or any AI agent) entering this repo. It is the **single source of truth** for "how this project is meant to evolve" — read it before editing.

## What this project is (and isn't)

**Is**: a small, focused, open-source CLI/library that turns a Douyin share URL into a Chinese transcript txt, via Qwen Paraformer streaming ASR.

**Is not**:
- A full Douyin scraper (no user-feed crawl, no comment scraping, no like/follow automation)
- A video re-distribution platform (we never store, host, or upload video content)
- A general video tool (Whisper-based / multi-language belongs in `pyvideotrans`)

If a feature request would turn this into one of the "is not" items, push back or split it into a separate repo.

## Architecture (300-feet view)

```
cli.py ──▶ pipeline.transcribe_url ──┬──▶ fetcher.fetch_mp4   (Playwright + httpx)
                                     ├──▶ asr.mp4_to_mp3      (ffmpeg subprocess)
                                     └──▶ asr.transcribe_mp3  (DashScope streaming)
```

- **`fetcher.py`** — Playwright sniffs the network for `.mp4` requests on the video page, then re-downloads with httpx using the same cookies+UA. This is the fragile bit; if Douyin changes CDN naming, the URL filter in `on_response` breaks.
- **`asr.py`** — Streams 3200-byte chunks to Paraformer's `Recognition`. Sentence-end events are accumulated into a list. Don't buffer the whole audio — streaming is the whole point.
- **`pipeline.py`** — Glue. Owns directory layout: raw assets in `out_dir/.raw/<run_id>/`, user-facing `.txt` in `out_dir/`.
- **`cli.py`** — Thin argparse wrapper. Keep it thin.

## Conventions

- **Python 3.10+**, type-hinted, no `from __future__ import annotations` needed.
- **No mandatory deps beyond `dashscope`, `playwright`, `httpx`.** If a feature wants more, gate it behind an extras group in `pyproject.toml`.
- **No GUI in core.** A future Gradio UI lives in a separate `web/` dir or `[ui]` extra.
- **Comments**: only when *why* is non-obvious. Docstrings on public functions only.
- **Errors**: raise, don't `print + sys.exit` inside library code. CLI is the only layer allowed to print user-facing messages.
- **Logging**: stdlib `logging`; no `print` in library modules (CLI is exempt).

## What to ALWAYS push back on

1. **"Add login support / handle private videos"** — this crosses from "fair-use access to public content" into "circumventing access control." Hard no. See `README.md` disclaimer; we do not move that line.
2. **"Bundle a default API key"** — never. User must bring their own DASHSCOPE_API_KEY.
3. **"Mass scraping mode that hits 1000s of URLs"** — out of scope. If someone wants batch, they can shell-loop. We don't ship a crawler.
4. **"Auto-republish transcript to X / WeChat / blog"** — out of scope. We hand the user a txt; what they do with it is their problem (and their copyright burden).
5. **"Mock the Paraformer call in tests"** — integration tests must hit the real API with a fixture audio. Fake ASR responses have rotted before.

## What to PROACTIVELY suggest

- Bug-bash: when Douyin changes CDN domains, the `on_response` filter in `fetcher.py` is the first thing that breaks. Surface a clear "no mp4 captured — please file an issue with this video URL" message.
- Roadmap items in README are open invitations: batch mode (#1), LLM summary step (#2), Gradio UI (#3), other-platform fetchers (#4). Each is a separate module under `fetchers/` if and when added — keep ASR core untouched.

## Release / publishing

- `python -m build && twine upload dist/*` to PyPI.
- Tag releases as `v0.1.0`. Keep CHANGELOG.md once we have one.
- Don't commit the `transcripts/` or `_dy_cache/` directory. `.gitignore` covers them; double-check before `git add -A`.

## Legal posture (short version — full text in README disclaimer)

We follow the **yt-dlp model**: we are a tool, not a service; we don't host content; users are responsible for compliance with platform ToS and copyright. Disclaimer in `README.md` and `LICENSE` must stay verbatim — do not soften, sharpen, or remove without discussing first.

## Contact / maintenance

- Issues: GitHub Issues (template TBD).
- For the parent dev's local working setup (the `claude_env` venv, the `PROJECTS/douyin/` working copy, the `run.ps1` PowerShell launcher), see the parent repo's CLAUDE.md — those do **not** apply to this open-source repo, which must stay environment-agnostic.
