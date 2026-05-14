"""Markdown-to-HTML rendering pipeline with syntax highlighting."""

from __future__ import annotations

import mistletoe
from mistletoe import HTMLRenderer
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

# Cache for Pygments formatters and CSS — one per theme.
_FORMATTERS: dict[str, HtmlFormatter] = {}
_PYGMENTS_CSS: dict[str, str] = {}

# Light theme: clean syntax on light backgrounds.
_LIGHT_STYLE = "friendly"
# Dark theme: GitHub-dark syntax on dark backgrounds.
_DARK_STYLE = "github-dark"


def _get_formatter(dark: bool) -> HtmlFormatter:
    """Return (and cache) a Pygments HtmlFormatter for the given mode."""
    key = "dark" if dark else "light"
    if key not in _FORMATTERS:
        style = _DARK_STYLE if dark else _LIGHT_STYLE
        _FORMATTERS[key] = HtmlFormatter(
            noclasses=False,
            cssclass="highlight",
            style=style,
        )
    return _FORMATTERS[key]


def _get_pygments_css(dark: bool) -> str:
    """Return (and cache) the Pygments CSS for the given mode."""
    key = "dark" if dark else "light"
    if key not in _PYGMENTS_CSS:
        _PYGMENTS_CSS[key] = _get_formatter(dark).get_style_defs(".highlight")
    return _PYGMENTS_CSS[key]


class HighlightRenderer(HTMLRenderer):
    """Mistletoe renderer with Pygments syntax highlighting.

    Reads ``_current_dark`` from the module to choose the colour scheme.
    """

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
        highlighted = highlight(code, lexer, _get_formatter(_current_dark))
        return f'<div class="code-block">{highlighted}</div>'


# Module-level flag — mistletoe instantiates the renderer class, so we
# communicate the theme choice through this global.
_current_dark = False


def markdown_to_html(md_text: str, *, css: str = "", dark: bool = False) -> str:
    """Convert Markdown text to a full, styled HTML document.

    Parameters
    ----------
    md_text:
        Raw Markdown source.
    css:
        Optional CSS string to embed in the output.
    dark:
        If True, use a dark syntax-highlighting scheme.

    Returns
    -------
    Complete HTML string ready to display in a QTextBrowser.
    """
    global _current_dark
    _current_dark = dark
    body_html = mistletoe.markdown(md_text, HighlightRenderer)

    return f"""\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{_get_pygments_css(dark)}
{css}
</style>
</head>
<body>
{body_html}
</body>
</html>"""
