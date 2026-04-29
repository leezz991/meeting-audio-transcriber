---
name: meeting-audio-transcriber
description: Local meeting audio transcription, transcript cleanup, and intelligent meeting-minutes generation for recordings such as .mp3, .wav, .m4a, .flac, .mp4, and voice-recorder files. Use when the user asks to transcribe meeting audio, revise AI transcripts, add timestamps, assess speaker separation feasibility, summarize meeting recordings, or produce structured Chinese meeting minutes from audio/transcript content.
---

# Meeting Audio Transcriber

## Workflow

1. Confirm the audio path is readable and inspect duration, size, codec, channel count, and whether an API key is available. Prefer local processing unless the user explicitly requests or approves external API transcription.
2. Run `scripts/transcribe_audio.py` for local transcription. It installs no packages by itself; if dependencies are missing, install the smallest practical set such as `openai-whisper`, `imageio-ffmpeg`, and optionally `opencc-python-reimplemented`.
3. Use `small` as the default Whisper model for Chinese meetings. Use `base` only for quick sampling; use `medium` or larger when the user prioritizes accuracy and runtime is acceptable.
4. Generate both Markdown and JSON outputs. Put outputs in a nearby `transcripts/` folder unless the user specifies another location.
5. Assess speaker separation realistically:
   - If stereo channels are strongly separated by participant, infer rough speaker turns from channel balance.
   - If channels are highly correlated or all speech is biased to one channel, state that automatic speaker separation is unreliable.
   - Do not invent speaker names. Use `Speaker 1`, `Speaker 2`, etc. only when evidence supports a useful distinction.
6. Review the transcript for domain terms and apply conservative corrections. Keep uncertain terms as-is or mark them "待核实"; do not over-correct.
7. If the user asks for a meeting summary or minutes, read `references/intelligent-minutes.md` and generate the structured minutes from the cleaned transcript. Keep the required second-level headings exactly as specified so the PDF layout renderer can style sections consistently.
8. When minutes are generated, also create a PDF version for sharing unless the user asks for Markdown only. Use `scripts/minutes_to_pdf.py` with its default `color-blocks` layout and keep the `.md` and `.pdf` files in the same output folder.

## Script

Run from any workspace:

```powershell
python "D:\OneDrive\codex\skills\meeting-audio-transcriber\scripts\transcribe_audio.py" `
  "F:\REC_FILE\FOLDER01\260426_1735.mp3" `
  --model small `
  --language zh `
  --output-dir "D:\OneDrive\obsidian\obcodex\transcripts"
```

Useful options:

- `--sample-seconds 60`: transcribe only a short sample.
- `--terms terms.json`: apply project-specific find/replace terms.
- `--no-simplify`: keep original Chinese script instead of converting Traditional to Simplified.
- `--keep-wav`: keep the generated WAV for debugging or diarization experiments.

Generate a PDF from a Markdown meeting-minutes file:

```powershell
python "D:\OneDrive\codex\skills\meeting-audio-transcriber\scripts\minutes_to_pdf.py" `
  "D:\OneDrive\obsidian\obcodex\transcripts\260426_1735_intelligent_minutes.md"
```

The PDF script uses a local Chromium-family browser such as Microsoft Edge or Chrome in headless mode. If no browser is found, install Edge/Chrome or pass `--browser <path-to-browser.exe>`.

The default PDF layout is a stable color-block report. It parses the Markdown headings and renders each section into fixed cards with deterministic colors. Use `--layout plain` only when the user explicitly wants a simple document-style PDF.

## Term Correction

Use a JSON object for domain terms when known:

```json
{
  "小城市": "小程序",
  "小城区": "小程序",
  "誉名": "域名",
  "信讯云": "信创云",
  "交通听": "交通厅"
}
```

Only apply replacements that are plausible in context. For organization names, people names, compliance terms, platform names, and technical terms, prefer marking "待核实" over guessing.

## Quality Checks

- Include a short note on model, local/API route, duration, and known limitations.
- Preserve timestamps in the transcript so later summaries can cite sections.
- Strip filler, repetitions, and false starts only in the cleaned/minutes layer, not in raw JSON.
- For Chinese meeting notes, write in objective formal language and keep names, units, systems, projects, and compliance terms when identifiable.
- Do not treat every mentioned person as an attendee. Only list a person as a participant when the transcript, metadata, user-provided context, or direct self-identification supports that they attended or spoke. Put leaders, reviewers, case contacts, or people only mentioned in discussion under "提及人员/单位" or mark them "待核实".
- For stable PDF layout, keep the nine required `##` headings unchanged, keep paragraphs concise, prefer bullets/tables over long prose, and avoid deeply nested lists.
