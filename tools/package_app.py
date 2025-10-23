import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional
import importlib.util

DEFAULT_FFMPEG_BIN = Path(r"C:\ffmpeg-2025-10-19-git-dc39a576ad-essentials_build\bin")
DEFAULT_UPX_DIR = Path(r"C:\upx-5.0.2-win64")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESOURCES_BIN = PROJECT_ROOT / "resources" / "bin"


def _find_ffmpeg_dir(explicit: Optional[str]) -> Path:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    for env_key in ("FFMPEG_BIN_DIR", "FFMPEG_DIR"):
        env_value = os.environ.get(env_key)
        if env_value:
            candidates.append(Path(env_value))
    candidates.append(DEFAULT_FFMPEG_BIN)

    for candidate in candidates:
        if not candidate:
            continue
        base = candidate if candidate.is_dir() else candidate.parent
        ffmpeg_path = candidate if candidate.is_file() else base / "ffmpeg.exe"
        ffprobe_path = base / "ffprobe.exe"
        if ffmpeg_path.exists() and ffprobe_path.exists():
            return base.resolve()
    raise FileNotFoundError(
        "Unable to locate ffmpeg.exe and ffprobe.exe. Use --ffmpeg-dir or set FFMPEG_DIR/FFMPEG_BIN_DIR."
    )


def _find_upx_dir(explicit: Optional[str]) -> Optional[Path]:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    for env_key in ("UPX_DIR", "UPX_PATH"):
        env_value = os.environ.get(env_key)
        if env_value:
            candidates.append(Path(env_value))
    candidates.append(DEFAULT_UPX_DIR)

    for candidate in candidates:
        if candidate and (candidate / "upx.exe").exists():
            return candidate.resolve()
    return None


def _sync_ffmpeg_binaries(source_dir: Path) -> None:
    RESOURCES_BIN.mkdir(parents=True, exist_ok=True)
    for binary_name in ("ffmpeg.exe", "ffprobe.exe"):
        src = source_dir / binary_name
        if not src.exists():
            raise FileNotFoundError(f"Missing required binary: {src}")
        dest = RESOURCES_BIN / binary_name
        shutil.copy2(src, dest)


def _prepare_assets() -> None:
    prepare_script = PROJECT_ROOT / "tools" / "prepare_assets.py"
    if not prepare_script.exists():
        return
    subprocess.run([sys.executable, str(prepare_script)], check=True, cwd=PROJECT_ROOT)


def _run_pyinstaller(upx_dir: Optional[Path]) -> None:
    if importlib.util.find_spec("PyInstaller") is None:
        raise ModuleNotFoundError(
            "PyInstaller is not installed in the active environment. Install it via 'pip install pyinstaller'."
        )
    env = os.environ.copy()
    if upx_dir:
        env.setdefault("UPX", str(upx_dir))
    cmd = [sys.executable, "-m", "PyInstaller", "build.spec"]
    subprocess.run(cmd, check=True, cwd=PROJECT_ROOT, env=env)


def main() -> None:
    parser = argparse.ArgumentParser(description="Package Chun MediaConv as a standalone build.")
    parser.add_argument("--ffmpeg-dir", help="Directory containing ffmpeg.exe and ffprobe.exe")
    parser.add_argument("--upx-dir", help="Directory containing upx.exe")
    parser.add_argument("--skip-build", action="store_true", help="Prepare assets only without invoking PyInstaller")
    args = parser.parse_args()

    ffmpeg_dir = _find_ffmpeg_dir(args.ffmpeg_dir)
    upx_dir = _find_upx_dir(args.upx_dir)

    print(f"Using FFmpeg from: {ffmpeg_dir}")
    if upx_dir:
        print(f"Using UPX from: {upx_dir}")
    else:
        print("UPX not found; build will proceed without executable compression.")

    try:
        _sync_ffmpeg_binaries(ffmpeg_dir)
        _prepare_assets()

        if not args.skip_build:
            _run_pyinstaller(upx_dir)
    except ModuleNotFoundError as exc:
        print(exc)
        print("Install the missing dependency and rerun the packaging script.")
        raise SystemExit(1)
if __name__ == "__main__":
    main()
