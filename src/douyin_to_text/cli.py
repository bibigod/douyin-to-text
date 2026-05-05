"""Command-line entry: `douyin-to-text <url>`."""

import argparse
import os
import sys

from douyin_to_text import __version__
from douyin_to_text.pipeline import transcribe_url


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="douyin-to-text",
        description="Transcribe a Douyin video to Chinese text via Qwen Paraformer.",
    )
    parser.add_argument("url", help="a single Douyin share URL (batch not supported)")
    parser.add_argument("--out", default="./transcripts", help="output directory")
    parser.add_argument(
        "--keep-media", action="store_true",
        help="keep downloaded mp4/mp3 (default: deleted after transcription)",
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="also produce a Markdown summary via Qwen (reuses DASHSCOPE_API_KEY)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("error: env var DASHSCOPE_API_KEY is not set.", file=sys.stderr)
        print("        get one at https://dashscope.aliyun.com/", file=sys.stderr)
        return 2

    total = 4 if args.summary else 3
    print(f"[1/{total}] fetching mp4 from {args.url} ...")
    print(f"[2/{total}] extracting audio + streaming to Paraformer ...")
    if args.summary:
        print(f"[3/{total}] (summary will be generated after transcription) ...")
    result = transcribe_url(
        args.url,
        out_dir=args.out,
        on_sentence=lambda s: print(f"  · {s}"),
        keep_media=args.keep_media,
        summarize=args.summary,
    )
    print(f"\n[{total}/{total}] done.")
    print(f"      transcript -> {result.output_path}")
    if result.summary_path:
        print(f"      summary    -> {result.summary_path}")
    elif args.summary:
        print(f"      summary    -> {result.summary}")
    print(f"      raw assets -> {result.raw_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
