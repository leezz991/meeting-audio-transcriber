#!/usr/bin/env python
"""Render Chinese Markdown meeting minutes to PDF with a local browser."""

from __future__ import annotations

import argparse
import html
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


CSS = """
@page { size: A4; margin: 18mm 16mm; }
body {
  font-family: "Microsoft YaHei", "SimSun", "Noto Sans CJK SC", Arial, sans-serif;
  color: #1f2933;
  line-height: 1.65;
  font-size: 12.5px;
}
h1 { font-size: 24px; border-bottom: 2px solid #111827; padding-bottom: 8px; }
h2 { font-size: 18px; margin-top: 26px; border-bottom: 1px solid #d0d7de; padding-bottom: 4px; }
h3 { font-size: 15px; margin-top: 18px; }
p, li { orphans: 2; widows: 2; }
blockquote {
  margin: 12px 0;
  padding: 8px 12px;
  border-left: 4px solid #64748b;
  background: #f8fafc;
  color: #475569;
}
code, pre { font-family: Consolas, "Microsoft YaHei", monospace; }
pre {
  white-space: pre-wrap;
  background: #f6f8fa;
  padding: 10px;
  border: 1px solid #d0d7de;
  border-radius: 4px;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0 16px;
  font-size: 11px;
}
th, td {
  border: 1px solid #d0d7de;
  padding: 6px 7px;
  vertical-align: top;
}
th { background: #f3f4f6; font-weight: 700; }
tr, table, blockquote, pre { break-inside: avoid; }
"""


def find_browser(explicit: str | None) -> str:
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit)
    candidates.extend(
        [
            os.environ.get("BROWSER", ""),
            shutil.which("msedge") or "",
            shutil.which("chrome") or "",
            shutil.which("chromium") or "",
            shutil.which("chromium-browser") or "",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    )
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(Path(candidate))
    raise SystemExit("No Chromium-family browser found. Install Edge/Chrome or pass --browser.")


def markdown_to_html(markdown_text: str) -> str:
    try:
        import markdown
    except ImportError:
        escaped = html.escape(markdown_text)
        body = "<pre>" + escaped + "</pre>"
    else:
        body = markdown.markdown(markdown_text, extensions=["tables", "fenced_code", "nl2br"])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>Meeting Minutes</title>
  <style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""


def render_pdf(browser: str, html_path: Path, pdf_path: Path) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--disable-extensions",
        f"--print-to-pdf={pdf_path}",
        str(html_path),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        cmd[1] = "--headless"
        proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0 or not pdf_path.exists():
        raise SystemExit((proc.stderr or proc.stdout or "PDF rendering failed").strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Markdown meeting minutes to PDF.")
    parser.add_argument("markdown_file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--browser")
    parser.add_argument("--keep-html", action="store_true")
    args = parser.parse_args()

    if not args.markdown_file.exists():
        raise SystemExit(f"Markdown file not found: {args.markdown_file}")

    pdf_path = args.output or args.markdown_file.with_suffix(".pdf")
    browser = find_browser(args.browser)
    html_text = markdown_to_html(args.markdown_file.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / (args.markdown_file.stem + ".html")
        html_path.write_text(html_text, encoding="utf-8")
        render_pdf(browser, html_path, pdf_path)
        if args.keep_html:
            kept = args.markdown_file.with_suffix(".html")
            kept.write_text(html_text, encoding="utf-8")
            print(kept)

    print(pdf_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
