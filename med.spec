# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for med.

Build with:  pyinstaller med.spec
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ── Paths ───────────────────────────────────────────────────────────────────

_block_cipher = None
_ROOT = Path(SPECPATH).resolve()
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

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="med",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

if sys.platform == "darwin":
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="med-collect",
    )
    app = BUNDLE(
        coll,
        name="med.app",
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
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="med",
    )

else:
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="med",
    )
