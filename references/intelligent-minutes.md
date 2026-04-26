# Intelligent Meeting Minutes

Use this reference when the user asks to summarize meeting audio or a transcript as "智能会议纪要".

## Output Requirements

Generate a business-oriented, structured meeting record. Do not write a chronological transcript and do not produce a simple abstract. Organize the content for both leadership review and follow-up execution.

Use objective, formal, concise Chinese. Preserve units, people, projects, technical scenarios, cooperation directions, and industry terms when supported by the transcript. Mark unknown information as `待核实`.

## Required Structure

### 一、会议信息

提炼：

- 会议主题
- 会议时间
- 参会单位
- 主要参会人员及其身份
- 提及人员/单位

If incomplete, write `待核实`.

Participant rule:

- Only list a person under `主要参会人员` when there is direct evidence that they attended or spoke, such as user-provided attendee list, meeting metadata, self-introduction, clear turn-taking, or explicit wording like `参会/到会/发言`.
- Do not infer attendance merely because a person is mentioned as a leader, reviewer, approver, source of experience, future recipient, or third-party contact.
- Put people or units that are only referenced in the discussion under `提及人员/单位`, with their relationship and `待核实` when needed.
- If the transcript says a material will be shown to someone, that person is a review/briefing target, not automatically a meeting participant.

### 二、会议总览

Use one paragraph under 300 Chinese characters. Cover background, core topic, discussion focus, and overall conclusion.

### 三、核心摘要卡片

Include:

- 核心结论
- 会议关注的主要问题
- 对方已有经验或实践
- 我方关切和需求
- 可能合作方向
- 后续推进重点

### 四、分主题纪要

Group by topic, not by speaking order. Under each topic include:

- 议题背景
- 主要观点
- 关键问题
- 相关案例或做法
- 对我方的启示
- 后续可推进事项

### 五、智能章节时间轴

Create chronological chapters from transcript timestamps. Each chapter includes:

- 时间点
- 小标题
- 100字以内内容概括

### 六、关键决策与共识

List explicit decisions, cooperation intentions, and advancement consensus. Use this format:

- 决策/共识：
- 对应问题：
- 讨论依据：
- 后续动作：

If no clear decision exists, state `未形成明确决策，以下为讨论倾向/待确认共识`.

### 七、待办事项

Use a table with:

| 待办事项 | 牵头方 | 配合方 | 输出成果 | 时间要求 | 备注 |
|---|---|---|---|---|---|

If owner or date is missing, write `待明确`.

### 八、金句或重要表达

Quote useful, viewpoint-rich statements and explain their meaning briefly. Do not beautify excessively and do not detach from the original meaning.

### 九、风险与待核实事项

List uncertainties, possible misunderstandings, missing materials, compliance risks, ownership risks, schedule risks, and terms that need verification.

## Editing Rules

- Compress greetings, filler, repeated phrases, and unfinished sentence fragments.
- Do not fabricate meeting participants, dates, organizations, or decisions.
- Separate `参会人员` from `提及人员`; this is especially important for leadership names, cited experts, approvers, and units discussed as potential stakeholders.
- Use neutral verbs such as `提出`, `介绍`, `认为`, `探讨`, `计划`, `建议`, `希望`.
- Keep hierarchy clear and directly reusable in reporting materials.
