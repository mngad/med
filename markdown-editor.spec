# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Markdown Editor desktop application.

Build with:  pyinstaller markdown-editor.spec
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ── Paths ───────────────────────────────────────────────────────────────────

_block_cipher = None
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"

# ── Data files ──────────────────────────────────────────────────────────────

# Collect package resource files (CSS, QSS, etc.)
datas = collect_data_files(
    "markdown_editor",
    includes=["**/*.css", "**/*.qss"],
    subdir="resources",
)

# ── Hidden imports ──────────────────────────────────────────────────────────

hiddenimports = collect_submodules("markdown_editor")
hiddenimports += [
    # mistletoe / pygments extras
    "markdown_it",
    "mistletoe",
    "mistletoe.html_renderer",
    "pygments",
    "pygments.lexers",
    "pygments.formatters",
    "pygments.styles",
    "pygments.lexers.python",
    # PySide6 platform plugins
    "PySide6.QtNetwork",
    "PySide6.QtPrintSupport",
    "shiboken6",
]

# ── Analysis ────────────────────────────────────────────────────────────────

a = Analysis(
    ["src/markdown_editor/main.py"],
    pathex=[str(_SRC)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=_block_cipher,
    noarchive=False,
)

# ── Platform-specific bundles ───────────────────────────────────────────────

if sys.platform == "darwin":
    app = BUNDLE(
        a,
        name="Markdown Editor",
        icon=None,  # Add an .icns path here when you have one
        bundle_identifier="local.markdown-editor.app",
        version="0.1.0",
        info_plist={
            "CFBundleName": "Markdown Editor",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleDocumentTypes": [
                {
                    "CFBundleTypeName": "Markdown File",
                    "CFBundleTypeRole": "Editor",
                    "LSHandlerRank": "Default",
                    "LSItemContentTypes": ["net.daringfireball.markdown"],
                    "CFBundleTypeExtensions": ["md", "markdown"],
                },
            ],
            "NSHighResolutionCapable": True,
        },
    )

elif sys.platform == "win32":
    exe = EXE(
        a,
        name="MarkdownEditor",
        icon=None,  # Add an .ico path here when you have one
        console=False,
        version="0.1.0",
    )

else:
    # Linux: single-folder output
    coll = COLLECT(
        a,
        name="markdown-editor",
        strip=False,
        upx=True,
        upx_exclude=[],
    )
