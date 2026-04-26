#!/usr/bin/env python
"""Local audio transcription helper for the meeting-audio-transcriber skill."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np


DEFAULT_TERMS = {
    "小城市": "小程序",
    "小城区": "小程序",
    "小微信小程序": "微信小程序",
    "誉名": "域名",
    "誉誉": "名义",
    "信讯云": "信创云",
    "信讯环境": "信创环境",
    "信讯": "信创",
    "新创": "信创",
    "支出库": "知识库",
    "按月收集": "大约收集",
    "按钮等级": "安全等级",
    "交通听": "交通厅",
    "檯面": "台面",
}


def require(module: str, package_hint: str):
    try:
        return __import__(module)
    except ImportError as exc:
        raise SystemExit(f"Missing dependency {module}. Install with: python -m pip install {package_hint}") from exc


def ffmpeg_exe() -> str:
    imageio_ffmpeg = require("imageio_ffmpeg", "imageio-ffmpeg")
    return imageio_ffmpeg.get_ffmpeg_exe()


def run_ffmpeg(args: list[str]) -> None:
    subprocess.run([ffmpeg_exe(), *args], check=True)


def inspect_audio(path: Path) -> str:
    proc = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-i", str(path)],
        text=True,
        capture_output=True,
    )
    return proc.stderr.strip()


def convert_to_wav(src: Path, wav: Path, sample_seconds: float | None) -> None:
    args = ["-y", "-hide_banner", "-loglevel", "error"]
    if sample_seconds:
        args += ["-ss", "0", "-t", str(sample_seconds)]
    args += ["-i", str(src), "-ar", "16000", "-ac", "1", str(wav)]
    run_ffmpeg(args)


def read_wav_float32(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    if width != 2 or rate != 16000:
        raise RuntimeError(f"Expected 16-bit 16 kHz WAV, got width={width}, rate={rate}")
    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    return audio


def timestamp(seconds: float) -> str:
    sec = int(round(seconds))
    return f"{sec // 60:02d}:{sec % 60:02d}"


def load_terms(path: Path | None) -> dict[str, str]:
    terms = dict(DEFAULT_TERMS)
    if path:
        extra = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(extra, dict):
            raise SystemExit("--terms must point to a JSON object")
        terms.update({str(k): str(v) for k, v in extra.items()})
    return terms


def simplify_text(text: str) -> str:
    try:
        from opencc import OpenCC
    except ImportError:
        return text
    return OpenCC("t2s").convert(text)


def clean_text(text: str, terms: dict[str, str], simplify: bool) -> str:
    value = text.strip()
    if simplify:
        value = simplify_text(value)
    for old, new in terms.items():
        value = value.replace(old, new)
    return value


def write_markdown(path: Path, result: dict, model: str, terms: dict[str, str], simplify: bool, audio_info: str) -> None:
    lines = [
        f"# {path.stem.replace('_transcript', '')} 转录草稿",
        "",
        f"> 本地 Whisper {model} 模型自动转录；已做繁简转换和术语替换，仍需人工校对。",
        "",
        "## 音频信息",
        "",
        "```text",
        audio_info,
        "```",
        "",
        "## 转录正文",
        "",
    ]
    for seg in result.get("segments", []):
        text = clean_text(seg.get("text", ""), terms, simplify)
        if text:
            lines.append(f"[{timestamp(seg['start'])}-{timestamp(seg['end'])}] {text}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe meeting audio locally with Whisper.")
    parser.add_argument("audio", type=Path)
    parser.add_argument("--model", default="small")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--sample-seconds", type=float)
    parser.add_argument("--terms", type=Path)
    parser.add_argument("--prompt", default="中文会议讨论，可能涉及微信小程序、部署方式、运营方式、用户手机号、实名数据、信息收集、等保等级、爱山东、信创云、服务器、域名、注册、上线。")
    parser.add_argument("--no-simplify", action="store_true")
    parser.add_argument("--keep-wav", action="store_true")
    args = parser.parse_args()

    if not args.audio.exists():
        raise SystemExit(f"Audio file not found: {args.audio}")

    whisper = require("whisper", "openai-whisper")
    out_dir = args.output_dir or (Path.cwd() / "transcripts")
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = args.audio.stem + ("_sample" if args.sample_seconds else "")
    wav = out_dir / f"{stem}_16k_mono.wav"
    json_path = out_dir / f"{stem}_transcript_{args.model}.json"
    md_path = out_dir / f"{stem}_transcript_{args.model}_simplified.md"

    audio_info = inspect_audio(args.audio)
    convert_to_wav(args.audio, wav, args.sample_seconds)

    model = whisper.load_model(args.model)
    result = model.transcribe(
        read_wav_float32(wav),
        language=args.language,
        initial_prompt=args.prompt,
        verbose=False,
        fp16=False,
    )

    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    terms = load_terms(args.terms)
    write_markdown(md_path, result, args.model, terms, not args.no_simplify, audio_info)

    if not args.keep_wav:
        wav.unlink(missing_ok=True)

    print(md_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
