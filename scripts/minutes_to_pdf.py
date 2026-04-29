#!/usr/bin/env python
"""Render Chinese Markdown meeting minutes to a stable color-block PDF."""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


CSS = """
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; }
body {
  font-family: "Microsoft YaHei", "SimSun", "Noto Sans CJK SC", Arial, sans-serif;
  color: #25313f;
  line-height: 1.55;
  font-size: 11.5px;
  background: #ffffff;
  margin: 0;
}
.page {
  border: 1px solid #d6dde7;
  border-radius: 8px;
  padding: 20px 22px 18px;
  min-height: 270mm;
}
.doc-title {
  font-size: 20px;
  line-height: 1.35;
  margin: 0 0 12px;
  font-weight: 800;
  color: #111827;
}
.subtitle {
  margin: 0 0 16px;
  color: #64748b;
  font-size: 10px;
}
.section {
  margin: 12px 0 14px;
  break-inside: avoid;
}
.section-title {
  font-size: 14px;
  font-weight: 800;
  margin: 0 0 8px;
  color: #1f2937;
}
.block {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 11px 13px;
  background: #f8fafc;
}
.block-blue { background: #eef8fc; border-color: #d5edf6; }
.block-purple { background: #f4f1ff; border-color: #e5dcff; }
.block-green { background: #f6fbe9; border-color: #e8f5c4; }
.block-orange { background: #fff5ed; border-color: #ffe0c8; }
.block-gray { background: #f8fafc; border-color: #e5e7eb; }
.block-yellow { background: #fffbea; border-color: #fde68a; }
.card-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin: 12px 0 14px;
  break-inside: avoid-page;
  page-break-inside: avoid;
}
.card-row .section {
  flex: 1 1 0;
  margin: 0;
  min-width: 0;
}
.section.full {
  width: 100%;
}
h3 {
  font-size: 12px;
  margin: 10px 0 5px;
  color: #334155;
}
p {
  margin: 5px 0;
}
ul, ol {
  margin: 5px 0 5px 18px;
  padding: 0;
}
li {
  margin: 2px 0;
}
blockquote {
  margin: 7px 0;
  padding: 7px 10px;
  border-left: 4px solid #facc15;
  background: #fffdf0;
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
  margin: 8px 0;
  font-size: 10.5px;
  background: #ffffff;
}
th, td {
  border: 1px solid #d0d7de;
  padding: 5px 6px;
  vertical-align: top;
}
th { background: #f3f4f6; font-weight: 700; }
tr, table, blockquote, pre { break-inside: avoid; }
.footer {
  margin-top: 12px;
  text-align: right;
  color: #9ca3af;
  font-size: 9px;
}
@media print {
  .page { border-color: #d6dde7; }
  .card-row {
    display: flex;
    break-inside: avoid-page;
    page-break-inside: avoid;
  }
}
"""


BLOCK_CLASSES = ["block-gray", "block-blue", "block-purple", "block-green", "block-orange", "block-yellow"]


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


def markdown_fragment(markdown_text: str) -> str:
    try:
        import markdown
    except ImportError:
        escaped = html.escape(markdown_text)
        return "<pre>" + escaped + "</pre>"
    else:
        return markdown.markdown(markdown_text, extensions=["tables", "fenced_code", "nl2br"])


def split_minutes(markdown_text: str) -> tuple[str, str, list[tuple[str, str]]]:
    lines = markdown_text.splitlines()
    title = "智能会议纪要"
    preface: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_body: list[str] = []

    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip() or title
            continue
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            if current_title is not None:
                sections.append((current_title, current_body))
            current_title = match.group(1).strip()
            current_body = []
        elif current_title is None:
            preface.append(line)
        else:
            current_body.append(line)

    if current_title is not None:
        sections.append((current_title, current_body))

    return title, "\n".join(preface).strip(), [(heading, "\n".join(body).strip()) for heading, body in sections]


def is_long_section(markdown_text: str) -> bool:
    meaningful_lines = [line for line in markdown_text.splitlines() if line.strip()]
    table_rows = sum(1 for line in meaningful_lines if line.lstrip().startswith("|"))
    bullet_rows = sum(1 for line in meaningful_lines if re.match(r"^\s*[-*]\s+", line))
    return len(markdown_text) > 850 or len(meaningful_lines) > 26 or table_rows > 5 or bullet_rows > 12


def should_use_half_card(title: str, markdown_text: str) -> bool:
    if any(key in title for key in ["关键决策", "待办事项", "分主题纪要", "智能章节时间轴"]):
        return False
    if is_long_section(markdown_text):
        return False
    return any(key in title for key in ["会议信息", "会议总览", "核心摘要", "金句", "风险"])


def section_html(idx: int, heading: str, body_md: str, full: bool) -> str:
    block_class = BLOCK_CLASSES[idx % len(BLOCK_CLASSES)]
    section_class = "section full" if full else "section"
    return "\n".join(
        [
            f'<section class="{section_class}">',
            f'<h2 class="section-title">{html.escape(heading)}</h2>',
            f'<div class="block {block_class}">{markdown_fragment(body_md)}</div>',
            "</section>",
        ]
    )


def flush_half_cards(parts: list[str], pending: list[str]) -> None:
    while len(pending) >= 2:
        left = pending.pop(0)
        right = pending.pop(0)
        parts.append(f'<div class="card-row">{left}{right}</div>')
    if pending:
        parts.append(pending.pop(0).replace('class="section"', 'class="section full"', 1))


def markdown_to_html(markdown_text: str, layout: str) -> str:
    if layout == "plain":
        body = markdown_fragment(markdown_text)
    else:
        title, preface, sections = split_minutes(markdown_text)
        parts = [f'<main class="page">', f"<h1 class=\"doc-title\">{html.escape(title)}</h1>"]
        if preface:
            parts.append(f'<div class="block block-gray">{markdown_fragment(preface)}</div>')

        pending_half_cards: list[str] = []
        for idx, (heading, body_md) in enumerate(sections):
            if should_use_half_card(heading, body_md):
                pending_half_cards.append(section_html(idx, heading, body_md, full=False))
                if len(pending_half_cards) == 2:
                    flush_half_cards(parts, pending_half_cards)
                continue
            flush_half_cards(parts, pending_half_cards)
            parts.append(section_html(idx, heading, body_md, full=True))

        flush_half_cards(parts, pending_half_cards)
        parts.append('<div class="footer">内容由 AI 生成，重要信息请人工核实</div>')
        parts.append("</main>")
        body = "\n".join(parts)

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
    parser.add_argument("--layout", choices=["color-blocks", "plain"], default="color-blocks")
    parser.add_argument("--keep-html", action="store_true")
    args = parser.parse_args()

    if not args.markdown_file.exists():
        raise SystemExit(f"Markdown file not found: {args.markdown_file}")

    pdf_path = args.output or args.markdown_file.with_suffix(".pdf")
    browser = find_browser(args.browser)
    html_text = markdown_to_html(args.markdown_file.read_text(encoding="utf-8"), args.layout)

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
