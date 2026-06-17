#!/usr/bin/env python3
"""CLI for Novel2Video PromptEngine."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from novel2video_promptengine.pipeline import generate_from_text, generate_markdown_report, result_to_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert novel text into storyboard JSON and AI video prompts.")
    parser.add_argument("--input", "-i", help="Path to a UTF-8 text file. If omitted, stdin is used.")
    parser.add_argument("--text", help="Novel text passed directly on the command line.")
    parser.add_argument("--platforms", default="jimeng,kling", help="Comma-separated platforms, e.g. jimeng,kling.")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown", help="Output format.")
    parser.add_argument("--out", "-o", help="Optional output file path.")
    parser.add_argument("--style", default="新国漫3D渲染，2.5D漫剧风格", help="Unified visual style anchor.")
    parser.add_argument("--use-llm", action="store_true", help="Use OpenAI-compatible LLM parsing instead of heuristics.")
    args = parser.parse_args()

    text = _read_text(args)
    platforms = [item.strip() for item in args.platforms.split(",") if item.strip()]
    result = generate_from_text(text, platforms=platforms, visual_style=args.style, use_llm=args.use_llm)
    output = result_to_json(result) if args.format == "json" else generate_markdown_report(result)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


def _read_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.input:
        return Path(args.input).read_text(encoding="utf-8")
    text = sys.stdin.read()
    if not text.strip():
        raise SystemExit("No input text. Use --input, --text, or pipe text to stdin.")
    return text


if __name__ == "__main__":
    raise SystemExit(main())
