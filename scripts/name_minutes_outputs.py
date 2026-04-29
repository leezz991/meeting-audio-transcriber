#!/usr/bin/env python
"""Rename meeting-minutes artifacts with datetime and Chinese topic."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


INVALID_CHARS = r'<>:"/\|?*'


def sanitize(value: str, max_len: int) -> str:
    value = value.strip()
    for char in INVALID_CHARS:
        value = value.replace(char, " ")
    value = re.sub(r"\s+", "", value)
    value = value.strip(". ")
    return (value or "会议纪要")[:max_len].rstrip(". ")


def parse_audio_datetime(path: Path | None) -> str | None:
    if not path:
        return None
    match = re.search(r"(\d{6})[_-]?(\d{4})", path.stem)
    if not match:
        return None
    yymmdd, hhmm = match.groups()
    return f"20{yymmdd[:2]}{yymmdd[2:4]}{yymmdd[4:6]}_{hhmm}"


def parse_minutes(markdown_text: str) -> tuple[str | None, str | None]:
    topic = None
    meeting_time = None
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if "会议主题" in stripped and "：" in stripped:
            topic = stripped.split("：", 1)[1].strip()
        elif "会议时间" in stripped and "：" in stripped:
            meeting_time = stripped.split("：", 1)[1].strip()
    return topic, meeting_time


def normalize_datetime(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"(20\d{2})\D{0,3}(\d{1,2})\D{0,3}(\d{1,2}).*?(\d{1,2})[:：时]?(\d{2})", value)
    if match:
        year, month, day, hour, minute = match.groups()
        return f"{int(year):04d}{int(month):02d}{int(day):02d}_{int(hour):02d}{int(minute):02d}"
    match = re.search(r"(20\d{6})[_-]?(\d{4})", value)
    if match:
        return f"{match.group(1)}_{match.group(2)}"
    return None


def build_name(markdown_file: Path, audio: Path | None, explicit_dt: str | None, explicit_topic: str | None) -> str:
    text = markdown_file.read_text(encoding="utf-8")
    parsed_topic, parsed_time = parse_minutes(text)
    dt = normalize_datetime(explicit_dt) or normalize_datetime(parsed_time) or parse_audio_datetime(audio)
    topic = explicit_topic or parsed_topic or "会议纪要"
    dt = dt or "日期时间待核实"
    return f"{dt}_{sanitize(topic, 48)}_智能会议纪要"


def move_if_exists(src: Path, dst: Path, dry_run: bool) -> Path | None:
    if not src.exists():
        return None
    if src == dst:
        return dst
    if dst.exists():
        raise SystemExit(f"Target already exists: {dst}")
    if not dry_run:
        src.rename(dst)
    return dst


def main() -> int:
    parser = argparse.ArgumentParser(description="Rename minutes .md/.pdf/.html files as 日期时间_会议主题_智能会议纪要.")
    parser.add_argument("markdown_file", type=Path)
    parser.add_argument("--audio", type=Path, help="Audio file used to infer YYMMDD_HHMM when minutes time is unavailable.")
    parser.add_argument("--datetime", help="Explicit meeting datetime, for example 2026年4月29日 15:16.")
    parser.add_argument("--topic", help="Explicit meeting topic.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.markdown_file.exists():
        raise SystemExit(f"Markdown file not found: {args.markdown_file}")

    base = build_name(args.markdown_file, args.audio, args.datetime, args.topic)
    targets = []
    for suffix in [".md", ".pdf", ".html"]:
        src = args.markdown_file.with_suffix(suffix)
        dst = args.markdown_file.with_name(base + suffix)
        moved = move_if_exists(src, dst, args.dry_run)
        if moved:
            targets.append(moved)

    for target in targets:
        print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
