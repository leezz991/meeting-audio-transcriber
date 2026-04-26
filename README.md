# Meeting Audio Transcriber 中文说明

这是一个用于 Codex 的本地技能，面向中文会议录音的转写、修订和智能会议纪要生成。适合处理 `.mp3`、`.wav`、`.m4a`、`.flac`、`.mp4` 等常见音频或录音文件。

## 主要功能

- 本地转录会议录音，默认不上传外部 API。
- 使用 Whisper 生成带时间戳的转写稿。
- 输出 Markdown 转录稿和 JSON 原始结果。
- 对中文转写做繁简转换和常见术语修订。
- 判断录音是否具备说话人区分条件。
- 根据转写内容生成结构化“智能会议纪要”。
- 同步生成 PDF 版会议纪要，便于转发查看。
- 区分“参会人员”和“会议中提及的人物/单位”，避免把被讨论对象误列为参会人。

## 目录结构

```text
meeting-audio-transcriber/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   └── intelligent-minutes.md
└── scripts/
    ├── minutes_to_pdf.py
    └── transcribe_audio.py
```

## 环境依赖

建议使用 Python 3.10 或以上版本。

首次使用前安装依赖：

```powershell
python -m pip install openai-whisper imageio-ffmpeg opencc-python-reimplemented
```

说明：

- `openai-whisper`：本地语音识别。
- `imageio-ffmpeg`：提供本地 ffmpeg，用于音频格式转换。
- `opencc-python-reimplemented`：将繁体识别结果转换为简体中文。
- `markdown`：将 Markdown 纪要转换为 HTML 后生成 PDF。多数 Codex 环境已内置，缺失时可单独安装。

PDF 生成依赖本机已安装的 Microsoft Edge、Chrome 或其他 Chromium 系浏览器。

## 基本用法

```powershell
python "D:\OneDrive\codex\skills\meeting-audio-transcriber\scripts\transcribe_audio.py" `
  "F:\REC_FILE\FOLDER01\260426_1735.mp3" `
  --model small `
  --language zh `
  --output-dir "D:\OneDrive\obsidian\obcodex\transcripts"
```

常用参数：

- `--model small`：默认推荐，中文会议准确度和速度较均衡。
- `--model base`：用于快速试跑，准确度较低。
- `--model medium`：准确度更好，但速度更慢、资源占用更高。
- `--sample-seconds 60`：只转录前 60 秒，用于试验效果。
- `--terms terms.json`：加载自定义术语替换表。
- `--no-simplify`：不做繁简转换。
- `--keep-wav`：保留中间 WAV 文件，便于调试。

## 输出文件

脚本会生成：

- `*_transcript_<model>_simplified.md`：带时间戳的中文转录稿。
- `*_transcript_<model>.json`：Whisper 原始转录结果。

示例：

```text
260426_1735_transcript_small_simplified.md
260426_1735_transcript_small.json
```

## 生成 PDF 版会议纪要

当已经有 Markdown 纪要文件时，可以运行：

```powershell
python "D:\OneDrive\codex\skills\meeting-audio-transcriber\scripts\minutes_to_pdf.py" `
  "D:\OneDrive\obsidian\obcodex\transcripts\260426_1735_intelligent_minutes.md"
```

默认会在同目录生成：

```text
260426_1735_intelligent_minutes.pdf
```

如果浏览器没有被自动找到，可以显式指定：

```powershell
python "scripts\minutes_to_pdf.py" "minutes.md" --browser "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
```

## 自定义术语修订

可以创建一个 JSON 文件，例如 `terms.json`：

```json
{
  "小城市": "小程序",
  "小城区": "小程序",
  "誉名": "域名",
}
```

然后运行：

```powershell
python "scripts\transcribe_audio.py" "meeting.mp3" --terms "terms.json"
```

建议只替换上下文明确的词。对人名、单位名、平台名、合规术语不确定时，应在纪要中标注“待核实”，不要强行改写。

## 生成智能会议纪要

当 Codex 使用本技能时，会读取：

```text
references/intelligent-minutes.md
```

纪要默认采用以下结构：

1. 会议信息
2. 会议总览
3. 核心摘要卡片
4. 分主题纪要
5. 智能章节时间轴
6. 关键决策与共识
7. 待办事项
8. 金句或重要表达
9. 风险与待核实事项

这个框架适合直接整理成汇报材料，也便于后续推进人员跟踪待办。

### 参会人识别规则

会议纪要中要严格区分：

- `主要参会人员`：只有在录音、元数据、用户提供名单、自我介绍或明确发言证据支持时才列入。
- `提及人员/单位`：只是在会议中被讨论、被请示、被引用经验、未来要汇报或审批的人和单位。

例如，录音中出现“给副院长看”“邓总的经验”时，除非有明确证据表明其本人参会或发言，否则不能把这些人物直接列为参会人，应写为“提及人员/单位：待核实”。

## 说话人区分说明

本技能会先判断录音是否具备自动区分说话人的条件：

- 如果左右声道明显对应不同说话人，可以尝试做粗略区分。
- 如果左右声道高度相关，或多人声音混在同一声道，则不强行标注说话人。
- 不会凭空生成真实姓名；无法确认时使用“待核实”。

## 注意事项

- 本地 Whisper 转录可能误识别专有名词，需要人工校对。
- 会议纪要会压缩口语、重复和无效寒暄，但不会编造未出现的信息。
- 涉及人名、单位、合规要求、平台名称、项目结论时，应优先保守表达。
- 被提到的人物不等于参会人员；没有明确参会证据时，应标注为“提及人员/单位”或“待核实”。
- 音频质量、背景噪声、多人同时说话都会影响准确度。

## GitHub 仓库

仓库地址：

```text
https://github.com/leezz991/meeting-audio-transcriber
```
