"""Markdown rendering with Pygments highlighting and CJK typography.

中文排版适配点：
- 中英文之间自动加空格（盘古之白），处理时跳过代码块/行内代码
- smartypants 只对拉丁文本有意义，中文引号不做转换
"""

import re

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from marko import Markdown
from marko.ext import footnote
from marko.ext.gfm import GFM
from marko.html_renderer import HTMLRenderer

html_formatter = HtmlFormatter(nowrap=False)


class PygmentsRenderer(HTMLRenderer):
    """Render fenced code blocks with Pygments."""

    def render_fenced_code(self, element):
        code = element.children[0].children if element.children else ""
        if isinstance(code, str):
            language = getattr(element, "lang", None) or ""
            try:
                lexer = get_lexer_by_name(language) if language else TextLexer()
            except ValueError:
                lexer = TextLexer()
            return highlight(code, lexer, html_formatter)
        return super().render_fenced_code(element)


markdown_with_pygments = Markdown(
    extensions=[GFM, footnote.make_extension()],
    renderer=PygmentsRenderer,
)

# ---------------------------------------------------------------------------
# 盘古之白：中英文之间加空格（跳过代码）
# ---------------------------------------------------------------------------

_CJK = r"\u2e80-\u9fff\uf900-\ufaff\uff01-\uff60\u3000-\u303f"
_PLACEHOLDER = "\x00{}\x00"


def _protect_code(text):
    """把代码块和行内代码替换为占位符，避免排版处理碰它们。"""
    saved = []

    def _stash(match):
        saved.append(match.group(0))
        return _PLACEHOLDER.format(len(saved) - 1)

    text = re.sub(r"```.*?```", _stash, text, flags=re.S)
    text = re.sub(r"`[^`\n]+`", _stash, text)
    return text, saved


def _restore_code(text, saved):
    for i, chunk in enumerate(saved):
        text = text.replace(_PLACEHOLDER.format(i), chunk)
    return text


def add_cjk_spacing(text):
    """在 CJK 字符与拉丁字母/数字之间插入空格。"""
    text, saved = _protect_code(text)
    text = re.sub(rf"([{_CJK}])([A-Za-z0-9])", r"\1 \2", text)
    text = re.sub(rf"([A-Za-z0-9])([{_CJK}])", r"\1 \2", text)
    return _restore_code(text, saved)


# ---------------------------------------------------------------------------
# 正文渲染：提取首个 H1 作为标题（学 lucumr：标题写在正文里）
# ---------------------------------------------------------------------------

def render_markdown(content):
    """渲染 Markdown，返回 {title, html_title, fragment}。"""
    lines = content.split("\n")
    filtered = []
    title = None
    found_heading = False
    for line in lines:
        if not found_heading and line.startswith("# "):
            title = line[2:].strip()
            found_heading = True
            continue
        filtered.append(line)

    body = add_cjk_spacing("\n".join(filtered))
    fragment = markdown_with_pygments.convert(body)

    if title is not None:
        spaced = add_cjk_spacing(title)
        html_title = markdown_with_pygments.convert(f"# {spaced}")
        # 取 <h1> 内文
        html_title = html_title[html_title.index("<h1>") + 4 : html_title.index("</h1>")]
    else:
        html_title = None

    return {
        "title": title,
        "html_title": html_title,
        "fragment": fragment,
    }


def plain_text_from_html(html):
    """去掉 HTML 标签，用于生成摘要。"""
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_pygments_css():
    return html_formatter.get_style_defs(".highlight")
