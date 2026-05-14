"""Markdown-to-HTML rendering pipeline with syntax highlighting."""

from __future__ import annotations

import mistletoe
from mistletoe import HTMLRenderer
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

# Shared Pygments formatter — used both during rendering and to emit CSS.
_HIGHLIGHT_FORMATTER = HtmlFormatter(
    noclasses=False,
    cssclass="highlight",
    style="material",
)

# Cache the generated Pygments CSS so we only compute it once.
_PYGMENTS_CSS: str | None = None


def _get_pygments_css() -> str:
    """Return the Pygments CSS definitions (lazily cached)."""
    global _PYGMENTS_CSS
    if _PYGMENTS_CSS is None:
        _PYGMENTS_CSS = _HIGHLIGHT_FORMATTER.get_style_defs(".highlight")
    return _PYGMENTS_CSS


class HighlightRenderer(HTMLRenderer):
    """Mistletoe renderer that adds Pygments syntax highlighting to
    fenced code blocks."""

    def render_block_code(self, token) -> str:
        """Render a fenced code block with syntax highlighting."""
        code = token.children[0].content if token.children else ""
        language = token.language or ""
        try:
            lexer = (
                get_lexer_by_name(language, stripall=True)
                if language
                else guess_lexer(code)
            )
        except ClassNotFound:
            lexer = guess_lexer(code)
        highlighted = highlight(code, lexer, _HIGHLIGHT_FORMATTER)
        return f'<div class="code-block">{highlighted}</div>'


def markdown_to_html(md_text: str, css: str = "") -> str:
    """Convert Markdown text to a full, styled HTML document.

    Parameters
    ----------
    md_text:
        Raw Markdown source.
    css:
        Optional CSS string to embed in the output.

    Returns
    -------
    Complete HTML string ready to display in a QTextBrowser.
    """
    body_html = mistletoe.markdown(md_text, HighlightRenderer)

    return f"""\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{_get_pygments_css()}
{css}
</style>
</head>
<body>
{body_html}
</body>
</html>"""
