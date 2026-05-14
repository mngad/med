"""Main application window for med."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QPlainTextEdit,
    QTextBrowser,
    QMessageBox,
    QFileDialog,
    QToolBar,
    QApplication,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QFontComboBox,
    QSpinBox,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSizeGrip,
    QWidget,
)
from importlib import resources

from PySide6.QtCore import Qt, Signal, QSettings, QTimer, QPoint
from PySide6.QtGui import QAction, QKeySequence, QFont, QTextCursor, QPalette, QMouseEvent

from med.renderer import markdown_to_html


class AppWindow(QMainWindow):
    """The main window hosting the editor/preview split and all chrome."""

    # Signal emitted when the document's dirty state changes.
    dirty_changed = Signal(bool)

    # ------------------------------------------------------------------ #
    #  Initialisation
    # ------------------------------------------------------------------ #

    def __init__(self, file_path: Optional[str] = None) -> None:
        super().__init__()
        self._file_path: Optional[str] = None
        self._dirty: bool = False
        self._current_mode: str = "split"
        self._css: str = ""
        self._theme: str = "light"
        self._editor_font: QFont = QFont("Menlo", 13)
        self._preview_font_family: str = "system-ui"
        self._preview_font_size: int = 15

        # Debounced rendering: only re-render after 150ms of idle typing.
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(150)
        self._render_timer.timeout.connect(self._render_preview)

        # When True, suppress scroll-sync feedback loops.
        self._suppress_scroll_sync = False

        self._setup_window()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_shortcuts()
        self._connect_signals()
        self._restore_settings()
        self._load_resources()
        self._apply_theme()

        if file_path:
            self._load_file(file_path)
        else:
            self._new_document()

    # ------------------------------------------------------------------ #
    #  Window geometry & chrome
    # ------------------------------------------------------------------ #

    def _setup_window(self) -> None:
        """Configure window title, size, and chrome."""
        self.setWindowTitle("med")
        self.resize(1200, 800)
        self._centre_on_screen()

        # Frameless window — custom chrome
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Window drag state
        self._dragging = False
        self._drag_position = QPoint()

        # Traffic light buttons (macOS style)
        self._setup_traffic_lights()

        # Resize grip (bottom-right corner)
        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)

        # Status bar — hidden by default, toggled via View menu
        self._status_label = QLabel("Words: 0  |  Characters: 0")
        self._status_label.setStyleSheet("padding: 2px 10px; font-size: 11px;")
        self.statusBar().addPermanentWidget(self._status_label)
        self.statusBar().setVisible(False)
        self._act_toggle_status = QAction("Show Status &Bar", self)
        self._act_toggle_status.setCheckable(True)
        self._act_toggle_status.setChecked(False)
        self._act_toggle_status.toggled.connect(self.statusBar().setVisible)

    def _setup_traffic_lights(self) -> None:
        """Create macOS-style traffic light buttons at the top-left."""
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 12, 0, 0)
        layout.setSpacing(8)

        for color_normal, color_hover, tooltip, callback in [
            ("#ff5f57", "#e0443e", "Close", self.close),
            ("#febc2e", "#d4a01c", "Minimize", self.showMinimized),
            ("#28c840", "#1ea831", "Zoom", self._toggle_maximize),
        ]:
            btn = QPushButton()
            btn.setFixedSize(12, 12)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color_normal};
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {color_hover};
                }}
            """)
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        # Stretchable spacer so buttons stay top-left
        layout.addStretch()

        container.resize(self.width(), 40)
        container.show()
        self._traffic_container = container

    def _toggle_maximize(self) -> None:
        """Toggle maximized / normal window state."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ── Window dragging ─────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Begin window drag on left-click anywhere except traffic lights."""
        if event.button() == Qt.LeftButton:
            # Don't drag if clicking traffic lights (they're children)
            child = self.childAt(event.position().toPoint())
            if child is None or child not in self._traffic_container.findChildren(QPushButton):
                self._dragging = True
                self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Move the window while dragging."""
        if self._dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """End window drag."""
        if event.button() == Qt.LeftButton:
            self._dragging = False
        super().mouseReleaseEvent(event)

    def _centre_on_screen(self) -> None:
        """Move the window to the centre of the primary screen."""
        screen = QApplication.primaryScreen()
        if screen is not None:
            centre = screen.availableGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(centre)
            self.move(frame.topLeft())

    # ------------------------------------------------------------------ #
    #  Menu bar
    # ------------------------------------------------------------------ #

    def _setup_menus(self) -> None:
        """Build the File / Edit / View / Help menus."""
        mb = self.menuBar()

        # --- File ---
        file_menu = mb.addMenu("&File")

        self._act_new = QAction("&New", self)
        file_menu.addAction(self._act_new)

        self._act_open = QAction("&Open...", self)
        file_menu.addAction(self._act_open)

        file_menu.addSeparator()

        self._act_save = QAction("&Save", self)
        file_menu.addAction(self._act_save)

        self._act_save_as = QAction("Save &As...", self)
        file_menu.addAction(self._act_save_as)

        file_menu.addSeparator()

        self._act_quit = QAction("&Quit", self)
        self._act_quit.setMenuRole(QAction.QuitRole)
        file_menu.addAction(self._act_quit)

        # --- Edit ---
        edit_menu = mb.addMenu("&Edit")

        self._act_undo = QAction("&Undo", self)
        edit_menu.addAction(self._act_undo)

        self._act_redo = QAction("&Redo", self)
        edit_menu.addAction(self._act_redo)

        # --- View ---
        view_menu = mb.addMenu("&View")

        self._act_split = QAction("&Split View", self)
        self._act_split.setCheckable(True)
        self._act_split.setChecked(True)
        view_menu.addAction(self._act_split)

        self._act_preview_only = QAction("Preview &Only", self)
        self._act_preview_only.setCheckable(True)
        view_menu.addAction(self._act_preview_only)

        self._act_editor_only = QAction("&Focus Mode", self)
        self._act_editor_only.setCheckable(True)
        view_menu.addAction(self._act_editor_only)

        view_menu.addSeparator()

        self._act_dark_mode = QAction("&Dark Mode", self)
        self._act_dark_mode.setCheckable(True)
        view_menu.addAction(self._act_dark_mode)

        view_menu.addSeparator()

        self._act_toggle_toolbar = QAction("Show &Toolbar", self)
        self._act_toggle_toolbar.setCheckable(True)
        self._act_toggle_toolbar.setChecked(False)
        view_menu.addAction(self._act_toggle_toolbar)

        view_menu.addAction(self._act_toggle_status)

        view_menu.addSeparator()

        self._act_preferences = QAction("&Preferences...", self)
        view_menu.addAction(self._act_preferences)

    # ------------------------------------------------------------------ #
    #  Toolbar (minimal placeholder — Phase 4 will flesh this out)
    # ------------------------------------------------------------------ #

    def _setup_toolbar(self) -> None:
        """Create the formatting toolbar."""
        self._toolbar = QToolBar("Formatting")
        self._toolbar.setMovable(False)
        self._toolbar.setFloatable(False)
        self.addToolBar(Qt.TopToolBarArea, self._toolbar)
        self._toolbar.setVisible(False)  # Hidden by default, toggle via View

        # Bold
        self._act_bold = QAction("B", self)
        self._act_bold.setToolTip("Bold (Cmd/Ctrl+B)")
        self._act_bold.triggered.connect(self._format_bold)
        font = self._act_bold.font()
        font.setBold(True)
        self._act_bold.setFont(font)
        self._toolbar.addAction(self._act_bold)

        # Italic
        self._act_italic = QAction("I", self)
        self._act_italic.setToolTip("Italic (Cmd/Ctrl+I)")
        self._act_italic.triggered.connect(self._format_italic)
        font = self._act_italic.font()
        font.setItalic(True)
        self._act_italic.setFont(font)
        self._toolbar.addAction(self._act_italic)

        self._toolbar.addSeparator()

        # Heading
        self._act_heading = QAction("H", self)
        self._act_heading.setToolTip("Toggle heading")
        self._act_heading.triggered.connect(self._format_heading)
        self._toolbar.addAction(self._act_heading)

        # List
        self._act_list = QAction("≡", self)
        self._act_list.setToolTip("Toggle bullet list")
        self._act_list.triggered.connect(self._format_list)
        self._toolbar.addAction(self._act_list)

        # Link
        self._act_link = QAction("⛓", self)
        self._act_link.setToolTip("Insert link (Cmd/Ctrl+K)")
        self._act_link.triggered.connect(self._format_link)
        self._toolbar.addAction(self._act_link)

        # Code
        self._act_code = QAction("</>", self)
        self._act_code.setToolTip("Code")
        self._act_code.triggered.connect(self._format_code)
        self._toolbar.addAction(self._act_code)

    # ------------------------------------------------------------------ #
    #  Central widget: splitter → editor | preview
    # ------------------------------------------------------------------ #

    def _setup_central_widget(self) -> None:
        """Create the QSplitter holding the editor and preview panes."""
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(2)

        # --- Editor ---
        self._editor = QPlainTextEdit()
        self._editor.setFont(QFont("Menlo", 13))
        self._editor.setTabStopDistance(32)
        self._editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self._splitter.addWidget(self._editor)

        # --- Preview ---
        self._preview = QTextBrowser()
        self._preview.setOpenExternalLinks(True)
        self._splitter.addWidget(self._preview)

        self._splitter.setSizes([600, 600])
        self.setCentralWidget(self._splitter)

    # ------------------------------------------------------------------ #
    #  Keyboard shortcuts
    # ------------------------------------------------------------------ #

    def _setup_shortcuts(self) -> None:
        """Bind standard keyboard shortcuts."""
        self._act_new.setShortcut(QKeySequence.New)          # Cmd/Ctrl+N
        self._act_open.setShortcut(QKeySequence.Open)        # Cmd/Ctrl+O
        self._act_save.setShortcut(QKeySequence.Save)        # Cmd/Ctrl+S
        self._act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._act_quit.setShortcut(QKeySequence.Quit)        # Cmd/Ctrl+Q
        self._act_undo.setShortcut(QKeySequence.Undo)
        self._act_redo.setShortcut(QKeySequence.Redo)

        self._act_split.setShortcut(QKeySequence("Ctrl+1"))
        self._act_preview_only.setShortcut(QKeySequence("Ctrl+2"))
        self._act_editor_only.setShortcut(QKeySequence("Ctrl+3"))

        # Bold / Italic
        self._act_bold.setShortcut(QKeySequence.Bold)
        self._act_italic.setShortcut(QKeySequence.Italic)
        self._act_link.setShortcut(QKeySequence("Ctrl+K"))

        # Toolbar & status bar toggles
        self._act_toggle_toolbar.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self._act_toggle_status.setShortcut(QKeySequence("Ctrl+Shift+B"))

    # ------------------------------------------------------------------ #
    #  Signal wiring
    # ------------------------------------------------------------------ #

    def _connect_signals(self) -> None:
        """Wire menu actions and editor signals."""
        # File actions
        self._act_new.triggered.connect(self._new_document)
        self._act_open.triggered.connect(self._open_dialog)
        self._act_save.triggered.connect(self._save)
        self._act_save_as.triggered.connect(self._save_as_dialog)
        self._act_quit.triggered.connect(self.close)

        # Edit actions
        self._act_undo.triggered.connect(self._editor.undo)
        self._act_redo.triggered.connect(self._editor.redo)

        # View mode actions
        self._act_split.triggered.connect(lambda: self._set_mode("split"))
        self._act_preview_only.triggered.connect(lambda: self._set_mode("preview"))
        self._act_editor_only.triggered.connect(lambda: self._set_mode("editor"))

        # Theme toggle
        self._act_dark_mode.triggered.connect(self._toggle_theme)

        # Preferences
        self._act_preferences.triggered.connect(self._show_preferences)

        # Status bar updates on content change
        self._editor.textChanged.connect(self._update_status_bar)

        # Toolbar visibility toggle (deferred — _toolbar created after menus)
        self._act_toggle_toolbar.toggled.connect(self._toolbar.setVisible)

        # Editor dirty tracking
        self._editor.modificationChanged.connect(self._on_modification_changed)

        # Live rendering
        self._editor.textChanged.connect(self._schedule_render)

        # Synchronised scrolling (editor → preview)
        self._editor.verticalScrollBar().valueChanged.connect(
            self._sync_scroll_editor_to_preview
        )

    # ------------------------------------------------------------------ #
    #  Resource loading (CSS + QSS)
    # ------------------------------------------------------------------ #

    def _load_resources(self) -> None:
        """Load preview CSS and app stylesheets from package resources."""
        try:
            self._css = resources.read_text("med.resources", "preview.css")
            self._app_qss = resources.read_text("med.resources", "app.qss")
            self._app_dark_qss = resources.read_text(
                "med.resources", "app_dark.qss"
            )
        except Exception:
            self._css = ""
            self._app_qss = ""
            self._app_dark_qss = ""

    # ------------------------------------------------------------------ #
    #  Theme management
    # ------------------------------------------------------------------ #

    @staticmethod
    def _detect_os_theme() -> str:
        """Return 'light' or 'dark' based on the OS colour scheme."""
        # Qt 6.5+ provides this directly.
        app = QApplication.instance()
        if app is not None:
            scheme = app.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Dark:
                return "dark"
        return "light"

    def _apply_theme(self) -> None:
        """Apply the current theme to the app and preview."""
        dark = self._theme == "dark"

        # App-wide stylesheet
        qss = self._app_dark_qss if dark else self._app_qss
        self.setStyleSheet(qss)

        # Toolbar button colours for dark mode (they use palette, not QSS)
        if dark:
            pal = QPalette()
            pal.setColor(QPalette.ButtonText, Qt.GlobalColor.white)
            self._toolbar.setPalette(pal)
        else:
            self._toolbar.setPalette(QPalette())

        # Update check mark
        self._act_dark_mode.setChecked(dark)

        # Re-render preview with correct CSS body class
        self._render_preview()

    def _toggle_theme(self) -> None:
        """Switch between light and dark themes."""
        self._theme = "dark" if self._theme == "light" else "light"
        self._apply_theme()

    # ------------------------------------------------------------------ #
    #  Preferences (font settings)
    # ------------------------------------------------------------------ #

    def _show_preferences(self) -> None:
        """Open the preferences dialog for editor/preview typography."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Preferences")
        dlg.setMinimumWidth(420)

        layout = QVBoxLayout(dlg)
        form = QFormLayout()

        # --- Editor font ---
        editor_font_label = QLabel("Editor font:")
        editor_font_combo = QFontComboBox()
        editor_font_combo.setCurrentFont(self._editor_font)
        form.addRow(editor_font_label, editor_font_combo)

        editor_size_label = QLabel("Editor font size:")
        editor_size_spin = QSpinBox()
        editor_size_spin.setRange(9, 36)
        editor_size_spin.setValue(self._editor_font.pointSize())
        form.addRow(editor_size_label, editor_size_spin)

        # --- Preview font ---
        preview_font_label = QLabel("Preview font:")
        preview_font_combo = QFontComboBox()
        preview_font = QFont(self._preview_font_family, self._preview_font_size)
        preview_font_combo.setCurrentFont(preview_font)
        form.addRow(preview_font_label, preview_font_combo)

        preview_size_label = QLabel("Preview font size:")
        preview_size_spin = QSpinBox()
        preview_size_spin.setRange(10, 32)
        preview_size_spin.setValue(self._preview_font_size)
        form.addRow(preview_size_label, preview_size_spin)

        # --- Reset button ---
        reset_btn = QPushButton("Reset to defaults")
        reset_btn.clicked.connect(lambda: self._reset_font_defaults(
            editor_font_combo, editor_size_spin,
            preview_font_combo, preview_size_spin,
        ))
        form.addRow("", reset_btn)

        layout.addLayout(form)

        # --- Dialog buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() == QDialog.Accepted:
            self._editor_font = editor_font_combo.currentFont()
            self._editor_font.setPointSize(editor_size_spin.value())
            self._editor.setFont(self._editor_font)

            self._preview_font_family = preview_font_combo.currentFont().family()
            self._preview_font_size = preview_size_spin.value()

            # Re-render to apply preview font changes
            self._render_preview()

    @staticmethod
    def _reset_font_defaults(
        editor_combo: QFontComboBox,
        editor_spin: QSpinBox,
        preview_combo: QFontComboBox,
        preview_spin: QSpinBox,
    ) -> None:
        """Reset font controls to their default values."""
        editor_combo.setCurrentFont(QFont("Menlo", 13))
        editor_spin.setValue(13)
        preview_combo.setCurrentFont(QFont("system-ui", 15))
        preview_spin.setValue(15)

    # ------------------------------------------------------------------ #
    #  Markdown rendering
    # ------------------------------------------------------------------ #

    def _schedule_render(self) -> None:
        """(Re-)start the debounced render timer."""
        self._render_timer.start()

    def _render_preview(self) -> None:
        """Convert editor content to HTML and display in the preview pane."""
        md_text = self._editor.toPlainText().replace("\u2029", "\n")
        if not md_text.strip():
            self._preview.clear()
            return
        html = markdown_to_html(md_text, css=self._preview_css())
        self._preview.setHtml(html)

    def _preview_css(self) -> str:
        """Build the full preview CSS including user font preferences."""
        css = self._css
        # Inject user-chosen preview font
        css += f"""
body {{
    font-family: "{self._preview_font_family}", system-ui, sans-serif !important;
    font-size: {self._preview_font_size}px !important;
}}
"""
        # Dark mode body class
        if self._theme == "dark":
            css += "body { color: #e4e4e7; background-color: #18181b; }"
            css += self._app_dark_qss.replace("QPlainTextEdit {", ".dark-override {")  # nop — just ensure dark selectors
        return css

    # ------------------------------------------------------------------ #
    #  Synchronised scrolling
    # ------------------------------------------------------------------ #

    def _sync_scroll_editor_to_preview(self, _value: int) -> None:
        """Scroll the preview to match the editor's current position."""
        if self._suppress_scroll_sync:
            return

        editor_sb = self._editor.verticalScrollBar()
        preview_sb = self._preview.verticalScrollBar()

        editor_max = editor_sb.maximum()
        preview_max = preview_sb.maximum()

        if editor_max == 0 or preview_max == 0:
            return

        ratio = editor_sb.value() / editor_max
        self._suppress_scroll_sync = True
        preview_sb.setValue(int(ratio * preview_max))
        self._suppress_scroll_sync = False

    # ------------------------------------------------------------------ #
    #  Toolbar formatting helpers
    # ------------------------------------------------------------------ #

    def _wrap_selection(self, prefix: str, suffix: str | None = None) -> None:
        """Wrap the current selection with *prefix*…*suffix*.

        If nothing is selected, insert the pair and place the cursor
        between them.
        """
        suffix = suffix or prefix
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            text = cursor.selectedText()
            cursor.clearSelection()
            cursor.setPosition(start)
            cursor.insertText(prefix)
            cursor.setPosition(start + len(prefix))
            cursor.setPosition(end + len(prefix), QTextCursor.KeepAnchor)
            cursor.insertText(text)
            cursor.setPosition(end + len(prefix))
            cursor.insertText(suffix)
        else:
            pos = cursor.position()
            cursor.insertText(prefix + suffix)
            cursor.setPosition(pos + len(prefix))
            self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def _prepend_line(self, prefix: str, toggle: bool = True) -> None:
        """Prepend *prefix* to the start of the current line.

        If *toggle* is True and the line already starts with *prefix*,
        remove it instead.
        """
        cursor = self._editor.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        line = cursor.selectedText()
        if toggle and line.startswith(prefix):
            # Remove prefix
            cursor.setPosition(cursor.selectionStart())
            cursor.setPosition(
                cursor.selectionStart() + len(prefix), QTextCursor.KeepAnchor
            )
            cursor.removeSelectedText()
        else:
            cursor.setPosition(cursor.selectionStart())
            cursor.insertText(prefix)
        self._editor.setFocus()

    def _format_bold(self) -> None:
        """Wrap selection / insert bold marker."""
        self._wrap_selection("**")

    def _format_italic(self) -> None:
        """Wrap selection / insert italic marker."""
        self._wrap_selection("*")

    def _format_heading(self) -> None:
        """Toggle heading marker (# ) on the current line."""
        self._prepend_line("# ")

    def _format_list(self) -> None:
        """Toggle bullet-list marker (- ) on the current line."""
        self._prepend_line("- ")

    def _format_link(self) -> None:
        """Insert a [text](url) template."""
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"[{text}](url)")
        else:
            pos = cursor.position()
            cursor.insertText("[text](url)")
            # Select "text" so the user can just start typing.
            cursor.setPosition(pos + 1)
            cursor.setPosition(pos + 5, QTextCursor.KeepAnchor)
            self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def _format_code(self) -> None:
        """Wrap selection in backticks or insert a fenced code block."""
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            # If selection spans multiple lines, make a fenced code block.
            selected = cursor.selectedText()
            if "\n" in selected or "\u2029" in selected:
                selected = selected.replace("\u2029", "\n")
                cursor.insertText(f"```\n{selected}\n```")
            else:
                self._wrap_selection("`")
        else:
            self._wrap_selection("`")

    # ------------------------------------------------------------------ #
    #  Document management
    # ------------------------------------------------------------------ #

    def _new_document(self) -> None:
        """Create a fresh, untitled document."""
        if self._dirty and not self._confirm_discard():
            return
        self._editor.clear()
        self._file_path = None
        self._set_dirty(False)
        self._update_title()

    def _load_file(self, path: str) -> None:
        """Load a Markdown file into the editor."""
        file_path = Path(path)
        size_mb = file_path.stat().st_size / (1024 * 1024)

        # Warn for large files
        if size_mb > 1.0:
            result = QMessageBox.warning(
                self,
                "Large File",
                f"This file is {size_mb:.1f} MB and may be slow to edit.\n\n"
                "Continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                return

        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            QMessageBox.critical(self, "Error Opening File", str(exc))
            return

        self._editor.setPlainText(text)
        self._file_path = str(path)
        self._set_dirty(False)
        self._update_title()
        self._render_preview()

    def _save(self) -> None:
        """Save the current document (triggers Save As if untitled)."""
        if self._file_path is None:
            self._save_as_dialog()
            return
        self._write_file(self._file_path)

    def _write_file(self, path: str) -> None:
        """Write editor content to *path* and update state."""
        try:
            Path(path).write_text(self._editor.toPlainText(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Error Saving File", str(exc))
            return
        self._file_path = path
        self._set_dirty(False)
        self._update_title()

    def _open_dialog(self) -> None:
        """Show the Open File dialog."""
        if self._dirty and not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown File",
            "",
            "Markdown Files (*.md);;All Files (*)",
        )
        if path:
            self._load_file(path)

    def _save_as_dialog(self) -> None:
        """Show the Save As dialog."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save As",
            self._file_path or "untitled.md",
            "Markdown Files (*.md);;All Files (*)",
        )
        if path:
            self._write_file(path)

    # ------------------------------------------------------------------ #
    #  Dirty state & title bar
    # ------------------------------------------------------------------ #

    def _on_modification_changed(self, modified: bool) -> None:
        """Track editor modification state."""
        self._set_dirty(modified)

    def _set_dirty(self, dirty: bool) -> None:
        """Update dirty flag and emit signal if changed."""
        if dirty != self._dirty:
            self._dirty = dirty
            self.dirty_changed.emit(dirty)
            self._update_title()

    def _update_title(self) -> None:
        """Refresh the window title based on path and dirty state."""
        name = Path(self._file_path).name if self._file_path else "Untitled"
        prefix = "• " if self._dirty else ""
        self.setWindowTitle(f"{prefix}{name} — med")
        self._traffic_container.raise_()

    # ------------------------------------------------------------------ #
    #  Layout modes
    # ------------------------------------------------------------------ #

    def _set_mode(self, mode: str) -> None:
        """Switch between split / preview-only / editor-only layout."""
        self._current_mode = mode

        self._act_split.setChecked(mode == "split")
        self._act_preview_only.setChecked(mode == "preview")
        self._act_editor_only.setChecked(mode == "editor")

        if mode == "split":
            self._editor.show()
            self._preview.show()
            self._splitter.setSizes([self.width() // 2, self.width() // 2])
        elif mode == "preview":
            self._editor.hide()
            self._preview.show()
        elif mode == "editor":
            self._editor.show()
            self._preview.hide()

    # ------------------------------------------------------------------ #
    #  Status bar
    # ------------------------------------------------------------------ #

    def _update_status_bar(self) -> None:
        """Refresh the status bar with word / character counts."""
        text = self._editor.toPlainText()
        word_count = len(text.split()) if text.strip() else 0
        char_count = len(text)
        self._status_label.setText(
            f"Words: {word_count}  |  Characters: {char_count}"
        )

    # ------------------------------------------------------------------ #
    #  Settings persistence
    # ------------------------------------------------------------------ #

    def _restore_settings(self) -> None:
        """Restore window geometry, splitter state, theme, and fonts."""
        settings = QSettings()

        # Geometry
        geo = settings.value("window/geometry")
        if geo is not None:
            self.restoreGeometry(geo)
        else:
            self._centre_on_screen()

        splitter_state = settings.value("window/splitter")
        if splitter_state is not None:
            self._splitter.restoreState(splitter_state)

        # Theme — use saved or auto-detect
        saved_theme = settings.value("theme", "auto")
        if saved_theme == "auto":
            self._theme = self._detect_os_theme()
        else:
            self._theme = str(saved_theme)

        # Editor font
        ef_str = settings.value("editor_font")
        if ef_str is not None:
            font = QFont()
            if font.fromString(str(ef_str)):
                self._editor_font = font
        self._editor.setFont(self._editor_font)

        # Preview font
        pf_family = settings.value("preview_font_family")
        if pf_family is not None:
            self._preview_font_family = str(pf_family)
        pf_size = settings.value("preview_font_size")
        if pf_size is not None:
            self._preview_font_size = int(pf_size)

    def _save_settings(self) -> None:
        """Persist all user-configurable state."""
        settings = QSettings()
        settings.setValue("window/geometry", self.saveGeometry())
        settings.setValue("window/splitter", self._splitter.saveState())
        settings.setValue("theme", self._theme)
        settings.setValue("editor_font", self._editor_font.toString())
        settings.setValue("preview_font_family", self._preview_font_family)
        settings.setValue("preview_font_size", self._preview_font_size)

    # ------------------------------------------------------------------ #
    #  Close / quit handling
    # ------------------------------------------------------------------ #

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Handle the window close event — guard unsaved changes."""
        if self._dirty and not self._confirm_discard():
            event.ignore()
            return
        self._save_settings()
        event.accept()

    def _confirm_discard(self) -> bool:
        """Ask the user whether to discard unsaved changes.

        Returns True if it's safe to proceed (saved or discarded).
        """
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Unsaved Changes")
        msg.setText("The document has been modified.")
        msg.setInformativeText("Do you want to save your changes?")
        msg.setStandardButtons(
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        msg.setDefaultButton(QMessageBox.Save)

        result = msg.exec()

        if result == QMessageBox.Save:
            self._save()
            return not self._dirty  # False if save was cancelled / failed
        elif result == QMessageBox.Discard:
            return True
        else:  # Cancel
            return False
