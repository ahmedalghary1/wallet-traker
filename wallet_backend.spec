# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


ROOT = Path(SPECPATH)

datas = [
    (str(ROOT / "templates"), "templates"),
    (str(ROOT / "static"), "static"),
    (str(ROOT / "media" / "receipts" / ".gitkeep"), "media/receipts"),
]

hiddenimports = [
    "wallet_tracker.settings",
    "wallet_tracker.urls",
    "wallet_tracker.wsgi",
    "wallet_tracker.desktop_paths",
    "core",
    "core.admin",
    "core.apps",
    "core.context_processors",
    "core.forms",
    "core.models",
    "core.urls",
    "core.utils",
    "core.views",
]
for package in ("core.migrations", "openpyxl", "waitress"):
    hiddenimports += collect_submodules(package)

excludes = [
    "IPython",
    "matplotlib",
    "numpy",
    "pandas",
    "pytest",
    "tkinter",
]

a = Analysis(
    [str(ROOT / "run_app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="wallet_backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "electron_app" / "assets" / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="wallet_backend",
)
