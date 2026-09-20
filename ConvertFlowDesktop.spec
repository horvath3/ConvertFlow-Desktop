# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None
root = Path.cwd()

# Data files to include
datas = [
    (str(root / "app" / "resources"), "app/resources"),
    (str(root / "tools" / "ffmpeg"), "tools/ffmpeg"),
]

# Hidden imports for PyInstaller
hiddenimports = [
    "PySide6.QtSvg",
    "PySide6.QtXml",
    "app.core.models",
    "app.core.video_profiles",
    "app.core.performance_profiles",
    "app.core.target_size_calculator",
    "app.core.hardware_detection",
    "app.utils.format_utils",
    "app.utils.file_utils",
    "app.utils.time_utils",
    "app.utils.logger",
]

# Exclude unnecessary modules to reduce size
excludes = [
    "tkinter",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "PIL",  # We use Pillow only at build time
    "cairosvg",
    "cairocffi",
]

a = Analysis(
    ["main.py"],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Application icon
icon_path = root / "app" / "resources" / "icons" / "app.ico"

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ConvertFlowDesktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip symbols for smaller size
    upx=True,    # UPX compression
    upx_exclude=[],  # Don't exclude anything from UPX
    console=False,
    icon=str(icon_path) if icon_path.exists() else None,
    version_file=None,  # Could add version file later
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name="ConvertFlowDesktop",
)