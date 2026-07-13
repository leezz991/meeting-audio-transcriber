import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "minutes_to_pdf.py"
SPEC = importlib.util.spec_from_file_location("minutes_to_pdf", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FallbackMarkdownTests(unittest.TestCase):
    def test_common_minutes_markdown_is_semantic_html(self):
        source = """> 处理方式：本地整理

- **会议主题：** 团队早会
- **会议时间：** 08:32

| 待办事项 | 牵头方 |
|---|---|
| 核对台账 | 项目组 |

### 主题一：项目推进

正文。"""
        rendered = MODULE.fallback_markdown_fragment(source)
        self.assertIn("<blockquote>", rendered)
        self.assertIn("<ul>", rendered)
        self.assertIn("<strong>会议主题：</strong>", rendered)
        self.assertIn("<table>", rendered)
        self.assertIn("<h3>", rendered)
        self.assertNotIn("<pre>&gt;", rendered)
        self.assertNotIn("**会议主题", rendered)

    def test_color_blocks_render_section_bodies_as_markdown(self):
        source = "# 测试纪要\n\n## 一、会议信息\n\n- **主题：** 测试\n\n## 二、会议总览\n\n正常段落。"
        rendered = MODULE.markdown_to_html(source, "color-blocks")
        self.assertIn("<strong>主题：</strong>", rendered)
        self.assertNotIn("- **主题：**", rendered)


if __name__ == "__main__":
    unittest.main()

