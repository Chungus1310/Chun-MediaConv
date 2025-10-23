# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

block_cipher = None

try:
    spec_file = Path(__file__).resolve()
except NameError:
    spec_file = Path(os.getcwd()).resolve() / "build.spec"

project_root = spec_file.parent if spec_file.parent.exists() else Path(os.getcwd()).resolve()

default_ffmpeg_dir = Path(r"C:\ffmpeg-2025-10-19-git-dc39a576ad-essentials_build\bin")

ffmpeg_candidate_dirs = []
for env_key in ("FFMPEG_BIN_DIR", "FFMPEG_DIR"):
    env_value = os.environ.get(env_key)
    if env_value:
        ffmpeg_candidate_dirs.append(Path(env_value))

ffmpeg_candidate_dirs.extend([
    default_ffmpeg_dir,
    project_root / "resources" / "bin",
])


def _resolve_ffmpeg_dir() -> Path:
    for candidate in ffmpeg_candidate_dirs:
        if not candidate:
            continue
        ffmpeg_path = candidate / "ffmpeg.exe"
        ffprobe_path = candidate / "ffprobe.exe"
        if ffmpeg_path.exists() and ffprobe_path.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "FFmpeg binaries were not found. Set FFMPEG_DIR/FFMPEG_BIN_DIR or place ffmpeg.exe and ffprobe.exe in resources/bin."
    )


ffmpeg_source_dir = _resolve_ffmpeg_dir()

ffmpeg_binaries = [
    (str(ffmpeg_source_dir / 'ffmpeg.exe'), 'resources/bin'),
    (str(ffmpeg_source_dir / 'ffprobe.exe'), 'resources/bin'),
]

default_upx_dir = Path(r"C:\upx-5.0.2-win64")
upx_candidate_dirs = []
for env_key in ("UPX_DIR", "UPX_PATH"):
    env_value = os.environ.get(env_key)
    if env_value:
        upx_candidate_dirs.append(Path(env_value))

upx_candidate_dirs.append(default_upx_dir)


def _resolve_upx_dir() -> Path:
    for candidate in upx_candidate_dirs:
        if not candidate:
            continue
        upx_exec = candidate / "upx.exe"
        if upx_exec.exists():
            return candidate.resolve()
    return Path()


resolved_upx_dir = _resolve_upx_dir()
if resolved_upx_dir:
    os.environ.setdefault("UPX", str(resolved_upx_dir))

use_upx = bool(resolved_upx_dir)

data_items = []
icons_dir = project_root / "resources" / "icons"
if icons_dir.exists():
    data_items.append((str(icons_dir / "*.svg"), 'resources/icons'))

icons_png_dir = project_root / "resources" / "icons_png"
if icons_png_dir.exists():
    data_items.append((str(icons_png_dir / "*.png"), 'resources/icons_png'))

a = Analysis(
    ['main.py'],
    pathex=[str(project_root), str(project_root / 'src')],
    binaries=ffmpeg_binaries,
    datas=data_items,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL.ImageTk',
        '_tkinter',
        'tkinter',
        'customtkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChunMediaConv',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=use_upx,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'resources' / 'icons' / 'icon.ico') if (project_root / 'resources' / 'icons' / 'icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=use_upx,
    upx_exclude=[],
    name='ChunMediaConv',
)
