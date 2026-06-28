"""Command-line entry: `douyin-to-text <url|file> ...`."""

import argparse
import os
import sys

from douyin_to_text import __version__
from douyin_to_text.pipeline import transcribe_url, transcribe_file


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="douyin-to-text",
        description="Transcribe a Douyin video or local media file to Chinese text via Qwen Paraformer.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    # ---- url ----
    url_p = sub.add_parser("url", help="Transcribe from a Douyin share URL")
    url_p.add_argument("url", help="a single Douyin share URL")
    url_p.add_argument("--out", default="./transcripts", help="output directory")
    url_p.add_argument("--keep-media", action="store_true",
                       help="keep downloaded mp4/mp3 (default: deleted)")
    url_p.add_argument("--summary", action="store_true",
                       help="also produce a Markdown summary via Qwen")

    # ---- file ----
    file_p = sub.add_parser("file", help="Transcribe a local video or audio file")
    file_p.add_argument("path", help="path to a local media file")
    file_p.add_argument("--out", default="./transcripts", help="output directory")
    file_p.add_argument("--keep-media", action="store_true",
                        help="keep the extracted mp3 (default: deleted)")
    file_p.add_argument("--summary", action="store_true",
                        help="also produce a Markdown summary via Qwen")
    file_p.add_argument("--title", default=None,
                        help="output file title (default: sanitized filename)")

    args = parser.parse_args()

    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("error: env var DASHSCOPE_API_KEY is not set.", file=sys.stderr)
        print("        get one at https://dashscope.aliyun.com/", file=sys.stderr)
        return 2

    if args.command == "url":
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

    elif args.command == "file":
        total = 3 if args.summary else 2
        print(f"[1/{total}] extracting audio + streaming to Paraformer ...")
        if args.summary:
            print(f"[2/{total}] (summary will be generated after transcription) ...")
        result = transcribe_file(
            args.path,
            out_dir=args.out,
            title=args.title,
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
