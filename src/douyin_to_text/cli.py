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
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("error: env var DASHSCOPE_API_KEY is not set.", file=sys.stderr)
        print("        get one at https://dashscope.aliyun.com/", file=sys.stderr)
        return 2

    print(f"[1/3] fetching mp4 from {args.url} ...")
    print("[2/3] extracting audio + streaming to Paraformer ...")
    result = transcribe_url(
        args.url,
        out_dir=args.out,
        on_sentence=lambda s: print(f"  · {s}"),
        keep_media=args.keep_media,
    )
    print(f"\n[3/3] done. transcript -> {result.output_path}")
    print(f"      raw assets    -> {result.raw_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
