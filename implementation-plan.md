# Implementation Plan — Markdown Editor (Python Desktop App)

## Phase 0: Project Scaffolding

### Step 0.1 — Initialise the project
- Create a `pyproject.toml` (or `setup.cfg` + `requirements.txt`) with:
  - Project metadata (name, version, description, author).
  - Dependencies: `PyQt6` (or `PySide6`) for the GUI, `mistune` or `markdown` for rendering, `pygments` for code-highlighting in preview.
  - Dev dependencies: `pyinstaller` (packaging), `black` / `ruff` (linting).
- Create a `src/` layout:
  ```
  src/
    markdown_editor/
      __init__.py
      main.py
      app.py
  ```

### Step 0.2 — Entry point & window shell
- `main.py`: Parse arguments (optional), create `QApplication`, instantiate `AppWindow`, call `sys.exit(app.exec())`.
- `app.py`: Create a bare `QMainWindow` with:
  - Window title "Untitled — Markdown Editor".
  - Default size ~1200×800, centred on screen.
  - Basic menu bar placeholder (File, Edit, View, Help).
- Verify: double-click or `python -m markdown_editor` launches an empty window.

### Step 0.3 — Hot-reload dev workflow
- Add a `Makefile` or `justfile` with targets: `run`, `lint`, `format`, `build`.
- `run` target: `python -m markdown_editor`.

---

## Phase 1: Core Editor & Preview Pane

### Step 1.1 — Split-screen layout with `QSplitter`
- Create a horizontal `QSplitter` as the central widget.
- Left pane: `QPlainTextEdit` (the editor).
- Right pane: `QTextBrowser` or `QWebEngineView` (the preview — start with `QTextBrowser` using rich text for quick iteration; swap to `QWebEngineView` later if needed).
- Default split ratio 50:50, save/restore splitter state.

### Step 1.2 — Live Markdown rendering
- Connect the editor's `textChanged` signal to a debounced render function.
- Render pipeline: raw Markdown → parse to HTML → display in preview pane.
- Use `mistune` with `pygments` for fenced code blocks.
- Debounce rendering at ~150ms to avoid jank.

### Step 1.3 — Synchronised scrolling
- On editor scroll, map the visible first line to an approximate position in the preview.
- Use block-level mapping: split both editor text and rendered HTML into blocks, align by block index.
- Scroll the preview pane programmatically via `QTextBrowser.scrollToAnchor` or `QScrollBar.setValue`.

### Step 1.4 — Preview CSS styling
- Embed a minimal CSS stylesheet into the HTML wrapper so the preview looks polished (fonts, spacing, heading sizes, code block styling).
- Keep the stylesheet as a separate `.css` file in `resources/` that gets read at startup.

---

## Phase 2: Layout Modes

### Step 2.1 — View menu & mode state
- Add `Mode` enum: `SPLIT`, `PREVIEW_ONLY`, `EDITOR_ONLY`.
- Store current mode in `AppWindow`.
- Add View menu items: "Split View", "Preview Only", "Focus Mode" with checkmarks and keyboard shortcuts (`Cmd+1`, `Cmd+2`, `Cmd+3`).

### Step 2.2 — Toggle implementations
- **Preview Only**: hide editor pane (`editor.hide()`), make preview take full width.
- **Focus Mode**: hide preview pane, editor takes full width.
- **Split View**: show both, restore splitter.
- Save splitter sizes before hiding so they can be restored.

---

## Phase 3: File System Integration

### Step 3.1 — File I/O abstraction
- `Document` data class: `file_path: Optional[str]`, `content: str`, `is_modified: bool`.
- `load_file(path)`: read UTF-8 text, set editor content, track path.
- `save_file(path=None)`: if path is None and `file_path` isn't set, trigger Save As; otherwise write to `file_path`.
- After save: set `is_modified = False`, update title bar.

### Step 3.2 — Title bar integration
- Format: `"filename.md — Markdown Editor"` or `"*filename.md — Markdown Editor"` when dirty.
- Connect editor's `modificationChanged` signal → update title bar.
- On new doc: show "Untitled — Markdown Editor".

### Step 3.3 — Native dialogs
- **Open**: `QFileDialog.getOpenFileName` with filter `"Markdown (*.md);;All Files (*)"`.
- **Save As**: `QFileDialog.getSaveFileName`.
- **Save**: if `file_path` exists, write directly; else delegate to Save As.
- Hook into File menu: New (`Cmd+N`), Open (`Cmd+O`), Save (`Cmd+S`), Save As (`Cmd+Shift+S`).

### Step 3.4 — Unsaved changes guard
- Before New/Open/Quit: if `is_modified`, show `QMessageBox` with Save / Discard / Cancel.
- Handle window close event (`closeEvent`) to trigger this guard.

---

## Phase 4: Toolbar

### Step 4.1 — Toolbar creation
- Add a `QToolBar` below the menu bar, non-movable and non-floatable for a clean look.
- Use `QAction` for each button with clear icons (either bundled SVGs or Unicode fallback).

### Step 4.2 — Formatting actions
- **Bold**: wrap selected text with `**` or insert `****` with cursor between asterisks.
- **Italic**: wrap with `*` or insert `**` with cursor inside.
- **Heading**: insert `# ` at line start or toggle heading level.
- **List**: insert `- ` at line start (or toggle).
- **Link**: insert `[text](url)` template, select "text" part for replacement.
- **Code**: wrap selection in backticks or insert inline code / fenced block.
- Each action works on either selected text (wrap) or inserts a template at cursor position.

### Step 4.3 — Keyboard shortcuts
- Register shortcuts in the menu (they'll work globally):
  - `Cmd/Ctrl+S`: Save
  - `Cmd/Ctrl+O`: Open
  - `Cmd/Ctrl+N`: New
  - `Cmd/Ctrl+Shift+S`: Save As
  - `Cmd/Ctrl+B`: Bold
  - `Cmd/Ctrl+I`: Italic
  - `Cmd/Ctrl+Q`: Quit

---

## Phase 5: Design & Theming

### Step 5.1 — Light & Dark themes
- Define two `QPalette` configurations and two CSS stylesheets.
- Detect OS theme at startup via platform-specific calls:
  - macOS: read `AppleInterfaceStyle` defaults.
  - Windows: check registry for `AppsUseLightTheme`.
  - Linux: check `gsettings` or `XDG` portal.
- Add View menu toggle "Dark Mode" / "Light Mode" with auto-detect option.

### Step 5.2 — Premium styling
- Apply a polished stylesheet: subtle background colours, clean borders, rounded corners on toolbars.
- Style the splitter handle to be slim but grab-able.
- Style scrollbars to match the theme.
- Style the menu bar and toolbar for a cohesive look.

### Step 5.3 — Typography settings
- `Settings` dialog (or preferences pane) with font family picker for:
  - Editor font (monospace choices: Fira Code, JetBrains Mono, SF Mono, Cascadia Code, Courier New).
  - Preview font (serif/sans-serif choices: Inter, Georgia, system-ui).
  - Font size spinner.
- Store settings in `QSettings` (cross-platform native config storage).
- Apply fonts on startup and immediately on settings change.

### Step 5.4 — Settings persistence
- Use `QSettings` with org/app namespacing.
- Persist: theme preference, editor/preview font family & size, window geometry, splitter state, last opened directory.
- Load settings in `AppWindow.__init__`, save on `closeEvent`.

---

## Phase 6: Packaging & Distribution

### Step 6.1 — PyInstaller spec
- Create `markdown-editor.spec` for PyInstaller.
- Bundle resources: CSS files, fonts, icons.
- Set up for one-file or one-folder output per platform.
- Add entries for hidden imports (PyQt6 platform plugins, mistune plugins).

### Step 6.2 — Platform-specific adjustments
- **macOS**: `.app` bundle with Info.plist (bundle identifier, file association for `.md`), code signing placeholder.
- **Windows**: `.exe` with optional installer (NSIS or WiX toolchain notes).
- **Linux**: AppImage or `.deb` via `linuxdeploy` / `fpm`.

### Step 6.3 — CI/CD (optional but recommended)
- GitHub Actions workflow to build on push/tag for all three platforms.
- Upload artifacts to releases.

---

## Phase 7: Polish & Edge Cases

### Step 7.1 — Error handling
- File read errors (permissions, encoding) → show error dialog, don't crash.
- File write errors → error dialog, don't lose data (keep in memory).
- Large files (>1MB) → warn but allow.

### Step 7.2 — Performance
- Lazy-load the preview: don't render on every keystroke; debounce.
- Use `QPlainTextEdit` over `QTextEdit` for large documents (better perf).
- Profile and optimize render pipeline if needed.

### Step 7.3 — Accessibility
- Ensure all toolbar buttons have tooltips and accessible names.
- Ensure keyboard navigation works through the entire app.
- Respect system font scaling / accessibility settings.

### Step 7.4 — Final testing
- Manual test checklist: open/save/edit across platforms, theme switching, layout modes, keyboard shortcuts, large files, Unicode/emoji in Markdown.
- Cross-platform smoke test on macOS, Windows, Linux.

---

## Execution Order Summary

| Phase | What | Depends On |
|-------|------|------------|
| 0 | Scaffolding | — |
| 1 | Editor & Preview | Phase 0 |
| 2 | Layout Modes | Phase 1 |
| 3 | File System | Phase 1 |
| 4 | Toolbar | Phase 1 |
| 5 | Design & Theming | Phase 4 |
| 6 | Packaging | Phase 5 |
| 7 | Polish | Phase 6 |

Phases 2, 3, and 4 can be tackled in parallel after Phase 1 is solid.
