"""Phase 5 theming & typography integration tests."""
from PySide6.QtWidgets import QApplication, QFontComboBox, QSpinBox
from PySide6.QtGui import QFont
import sys

app = QApplication.instance() or QApplication(sys.argv)
from med.app import AppWindow  # noqa: E402

# ---- 5.1: Theme detection & toggle ------------------------------------------

w = AppWindow()
assert w._detect_os_theme() in ("light", "dark")
print("✓ OS theme detection works")

initial = w._theme
w._toggle_theme()
assert w._theme != initial
assert w._act_dark_mode.isChecked() == (w._theme == "dark")
print("✓ Theme toggle updates checkmark")

w._toggle_theme()
assert w._theme == initial
print("✓ Theme toggle is idempotent")

# ---- 5.2: Stylesheets loaded ------------------------------------------------

assert hasattr(w, "_app_qss") and "QMainWindow" in w._app_qss
assert hasattr(w, "_app_dark_qss") and "QMainWindow" in w._app_dark_qss
print("✓ Light & dark QSS loaded from resources")

# ---- 5.3: Preview CSS -------------------------------------------------------

css = w._preview_css()
assert "font-family" in css
assert "font-size" in css
print("✓ Preview CSS includes font overrides")

# ---- 5.4: Font defaults -----------------------------------------------------

assert w._editor_font.family() == "Menlo"
assert w._editor_font.pointSize() == 13
assert w._preview_font_family == "Helvetica Neue"
assert w._preview_font_size == 15
print("✓ Font defaults are correct")

# ---- 5.5: Font reset helper -------------------------------------------------

combo = QFontComboBox()
spin = QSpinBox()
pcombo = QFontComboBox()
pspin = QSpinBox()
combo.setCurrentFont(QFont("Arial", 20))
spin.setValue(20)
pcombo.setCurrentFont(QFont("Helvetica", 20))
pspin.setValue(20)

AppWindow._reset_font_defaults(combo, spin, pcombo, pspin)
assert combo.currentFont().family() == "Menlo"
assert spin.value() == 13
assert pcombo.currentFont().family() == "Helvetica Neue"
assert pspin.value() == 15
print("✓ Font reset helper restores defaults")

print()
print("All Phase 5 tests passed ✓")
