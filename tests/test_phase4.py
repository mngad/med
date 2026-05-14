"""Phase 4 formatting tests."""
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTextCursor
import sys

app = QApplication.instance() or QApplication(sys.argv)
from med.app import AppWindow  # noqa: E402

w = AppWindow()
keep = QTextCursor.MoveMode.KeepAnchor


def sel(w, s, e):
    c = w._editor.textCursor()
    c.setPosition(s)
    c.setPosition(e, keep)
    w._editor.setTextCursor(c)


# Bold
w._editor.setPlainText("hello world")
sel(w, 0, 5)
w._format_bold()
assert w._editor.toPlainText() == "**hello** world"
print("✓ Bold")

# Italic
w._editor.setPlainText("hello world")
sel(w, 0, 5)
w._format_italic()
assert w._editor.toPlainText() == "*hello* world"
print("✓ Italic")

# Link
w._editor.setPlainText("hello world")
sel(w, 0, 5)
w._format_link()
assert w._editor.toPlainText() == "[hello](url) world"
print("✓ Link")

# Heading toggle
w._editor.setPlainText("line one\nline two")
c = w._editor.textCursor()
c.setPosition(0)
w._editor.setTextCursor(c)
w._format_heading()
assert w._editor.toPlainText() == "# line one\nline two"
w._format_heading()
assert w._editor.toPlainText() == "line one\nline two"
print("✓ Heading")

# List toggle
c.setPosition(0)
w._editor.setTextCursor(c)
w._format_list()
assert w._editor.toPlainText() == "- line one\nline two"
w._format_list()
assert w._editor.toPlainText() == "line one\nline two"
print("✓ List")

# Inline code (empty doc — insert template)
w._editor.clear()
w._format_code()
assert w._editor.toPlainText() == "``", f"Got: {w._editor.toPlainText()!r}"
print("✓ Code inline")

# Fenced code block (multi-line selection)
w._editor.setPlainText("line1\nline2")
sel(w, 0, 11)
w._format_code()
assert w._editor.toPlainText() == "```\nline1\nline2\n```", f"Got: {w._editor.toPlainText()!r}"
print("✓ Code fenced")

# Inline code (single-line selection)
w._editor.setPlainText("some code here")
sel(w, 5, 9)
w._format_code()
assert w._editor.toPlainText() == "some `code` here", f"Got: {w._editor.toPlainText()!r}"
print("✓ Code inline sel")

print()
print("All Phase 4 tests passed ✓")
