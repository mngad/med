# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for med.

Build with:  pyinstaller med.spec
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ── Paths ───────────────────────────────────────────────────────────────────

_block_cipher = None
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"

# ── Data files ──────────────────────────────────────────────────────────────

datas = collect_data_files(
    "med",
    includes=["**/*.css", "**/*.qss"],
    subdir="resources",
)

# ── Hidden imports ──────────────────────────────────────────────────────────

hiddenimports = collect_submodules("med")
hiddenimports += [
    "mistletoe",
    "mistletoe.html_renderer",
    "pygments",
    "pygments.lexers",
    "pygments.formatters",
    "pygments.styles",
    "pygments.lexers.python",
    "PySide6.QtNetwork",
    "PySide6.QtPrintSupport",
    "shiboken6",
]

# ── Analysis ────────────────────────────────────────────────────────────────

a = Analysis(
    ["src/med/main.py"],
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
        name="med",
        icon=None,
        bundle_identifier="io.mngad.med",
        version="0.1.0",
        info_plist={
            "CFBundleName": "med",
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
        name="med",
        icon=None,
        console=False,
        version="0.1.0",
    )

else:
    coll = COLLECT(
        a,
        name="med",
        strip=False,
        upx=True,
        upx_exclude=[],
    )
