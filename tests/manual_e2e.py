"""Headless end-to-end test: drive web._run as a generator without a browser.

Hits real Douyin + Paraformer + qwen-plus. Requires DASHSCOPE_API_KEY in env.
Run:  python tests/manual_e2e.py "<douyin url>"
"""

import os
import sys
import time

from douyin_to_text.web import _run


def main(url: str) -> int:
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("error: DASHSCOPE_API_KEY not set", file=sys.stderr)
        return 2

    started = time.time()
    print(f"==> driving _run() with url: {url}\n")
    last_status = ""
    last_text = ""
    last_summary = ""

    for i, (status, text, summary) in enumerate(
        _run(url, do_summary=True, api_key="", out_dir="./transcripts")
    ):
        elapsed = time.time() - started
        if status != last_status:
            print(f"[{elapsed:5.1f}s] status: {status!r}")
            last_status = status
        last_text = text
        last_summary = summary

    print(f"\n==> finished in {time.time() - started:.1f}s")
    print(f"transcript chars: {len(last_text)}")
    print(f"summary chars:    {len(last_summary)}")
    print(f"first sentence:   {last_text.splitlines()[0] if last_text else '(empty)'}")
    print(f"summary head:     {last_summary[:80] if last_summary else '(empty)'}")

    if not last_text:
        print("\n❌ FAIL: empty transcript")
        return 1
    print("\n✅ PASS")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python tests/manual_e2e.py '<douyin url>'")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
