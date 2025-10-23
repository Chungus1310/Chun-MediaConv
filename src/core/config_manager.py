import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import shutil

from src.utils.paths import resource_path

@dataclass
class AppConfig:
    ffmpeg_path: str = ""
    output_directory: str = ""
    temp_directory: str = ""
    max_parallel_conversions: int = 2
    gpu_acceleration: bool = True
    cleanup_on_exit: bool = True
    theme: str = "default"
    last_preset: str = "balanced"
    
class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".chunmediaconv"
        self.config_file = self.config_dir / "config.json"
        self.presets_file = self.config_dir / "presets.json"
        self.history_file = self.config_dir / "history.json"
        self.config: Optional[AppConfig] = None
        self.presets: Dict[str, Any] = {}
        
    def initialize(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config_file.exists():
            self.load_config()
        else:
            self.config = AppConfig()
            self._set_defaults()
            self.save_config()
            
        if self.presets_file.exists():
            self.load_presets()
            self._ensure_default_presets()
        else:
            self._create_default_presets()
            self.save_presets()
            
    def _set_defaults(self):
        ffmpeg_path = self._find_ffmpeg()
        if ffmpeg_path:
            self.config.ffmpeg_path = ffmpeg_path
            
        self.config.output_directory = str(Path.home() / "Videos" / "ChunMediaConv")
        Path(self.config.output_directory).mkdir(parents=True, exist_ok=True)
        
        self.config.temp_directory = str(self.config_dir / "temp")
        Path(self.config.temp_directory).mkdir(parents=True, exist_ok=True)
        
    def _find_ffmpeg(self) -> str:
        candidates = []

        resource_bin_dir = resource_path("bin")
        candidates.append(resource_bin_dir)
        candidates.append(resource_bin_dir / "ffmpeg.exe")

        for env_key in ("FFMPEG_PATH", "FFMPEG_BIN", "FFMPEG_BIN_DIR", "FFMPEG_DIR"):
            env_value = os.environ.get(env_key)
            if not env_value:
                continue
            env_path = Path(env_value)
            if env_path.is_dir():
                candidates.append(env_path / "ffmpeg.exe")
                candidates.append(env_path / "ffmpeg")
            else:
                candidates.append(env_path)

        external_paths = [
            Path(r"C:\ffmpeg-2025-10-19-git-dc39a576ad-essentials_build\bin\ffmpeg.exe"),
            Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
        ]

        candidates.extend(external_paths)

        for candidate in candidates:
            if candidate.is_dir():
                ffmpeg_candidate = candidate / "ffmpeg.exe"
                ffprobe_candidate = candidate / "ffprobe.exe"
                if ffmpeg_candidate.exists() and ffprobe_candidate.exists():
                    return str(ffmpeg_candidate)
                ffmpeg_alt = candidate / "ffmpeg"
                ffprobe_alt = candidate / "ffprobe"
                if ffmpeg_alt.exists() and ffprobe_alt.exists():
                    return str(ffmpeg_alt)
            elif candidate.exists():
                sibling = candidate.with_name("ffprobe.exe" if candidate.suffix.lower() == ".exe" else "ffprobe")
                if sibling.exists():
                    return str(candidate)

        ffmpeg_in_path = shutil.which("ffmpeg")
        if ffmpeg_in_path:
            return ffmpeg_in_path

        return ""
        
    def _create_default_presets(self):
        self.presets = self._default_presets()

    def _ensure_default_presets(self):
        defaults = self._default_presets()
        if not self.presets:
            self.presets = defaults
            self.save_presets()
            return

        updated = False
        for key, value in defaults.items():
            existing = self.presets.get(key)
            if not existing or existing.get("version", 0) < value.get("version", 1):
                self.presets[key] = value
                updated = True

        deprecated_presets = {"lossless"}
        for key in deprecated_presets:
            if key in self.presets:
                del self.presets[key]
                updated = True

        if updated:
            self.save_presets()

    def _default_presets(self) -> Dict[str, Any]:
        common_mp4_flags = {
            "pixel_format": "yuv420p",
            "video_profile": "high",
            "gop_mode": "half_fps",
            "b_frames": 2,
            "movflags": "+faststart",
            "color_primaries": "bt709",
            "color_trc": "bt709",
            "colorspace": "bt709",
            "audio_sample_rate": 48000
        }

        presets: Dict[str, Any] = {
            "ultra_fast": {
                "name": "Ultra Fast",
                "description": "Fastest conversion, lower quality",
                "container": "mp4",
                "video_codec": "h264",
                "video_preset": "ultrafast",
                "encoding_mode": "crf",
                "crf": 28,
                "audio_codec": "aac",
                "audio_bitrate": "128k",
                "use_hardware_acceleration": True,
                **common_mp4_flags,
                "version": 2
            },
            "balanced": {
                "name": "Balanced",
                "description": "Good balance of speed and quality",
                "container": "mp4",
                "video_codec": "h264",
                "video_preset": "medium",
                "encoding_mode": "crf",
                "crf": 22,
                "audio_codec": "aac",
                "audio_bitrate": "192k",
                "use_hardware_acceleration": True,
                **common_mp4_flags,
                "version": 2
            },
            "high_quality": {
                "name": "High Quality",
                "description": "Visually transparent quality",
                "container": "mp4",
                "video_codec": "h264",
                "video_preset": "slow",
                "encoding_mode": "crf",
                "crf": 18,
                "audio_codec": "aac",
                "audio_bitrate": "256k",
                "use_hardware_acceleration": True,
                **common_mp4_flags,
                "version": 2
            },
            "small_size": {
                "name": "Small Size",
                "description": "HEVC efficiency for tight storage",
                "container": "mp4",
                "video_codec": "h265",
                "video_preset": "slow",
                "encoding_mode": "crf",
                "crf": 27,
                "audio_codec": "aac",
                "audio_bitrate": "128k",
                "use_hardware_acceleration": True,
                **common_mp4_flags,
                "version": 2
            },
            "youtube": {
                "name": "YouTube Optimized",
                "description": "Aligned with YouTube ingest guidance",
                "container": "mp4",
                "video_codec": "h264",
                "video_preset": "medium",
                "encoding_mode": "crf",
                "crf": 20,
                "audio_codec": "aac",
                "audio_bitrate": "192k",
                "use_hardware_acceleration": True,
                **common_mp4_flags,
                "force_cfr": True,
                "version": 2
            },
            "instagram": {
                "name": "Instagram Optimized",
                "description": "Ready for feed and reels",
                "container": "mp4",
                "video_codec": "h264",
                "video_preset": "medium",
                "encoding_mode": "crf",
                "crf": 21,
                "audio_codec": "aac",
                "audio_bitrate": "128k",
                "use_hardware_acceleration": True,
                **common_mp4_flags,
                "framerate": 30,
                "video_filters": ["scale='min(1080\\,iw)':-2"],
                "maxrate": "8M",
                "bufsize": "16M",
                "version": 2
            },
            "archival_lossless": {
                "name": "Archival Lossless",
                "description": "FFV1 + FLAC preservation master",
                "container": "mkv",
                "video_codec": "ffv1",
                "encoding_mode": "lossless",
                "audio_codec": "flac",
                "audio_sample_rate": 48000,
                "b_frames": 0,
                "gop_mode": "custom",
                "gop_size": 1,
                "extra_video_options": [
                    "-level", "3",
                    "-slices", "16",
                    "-slicecrc", "1"
                ],
                "use_hardware_acceleration": False,
                "version": 2
            },
            "editing_mezzanine": {
                "name": "Editing Mezzanine",
                "description": "ProRes 422 HQ ready for NLEs",
                "container": "mov",
                "video_codec": "prores",
                "video_encoder": "prores_ks",
                "encoding_mode": "lossless",
                "video_profile": "3",
                "pixel_format": "yuv422p10le",
                "audio_codec": "pcm",
                "audio_encoder": "pcm_s24le",
                "audio_sample_rate": 48000,
                "audio_channels": 2,
                "b_frames": 0,
                "gop_mode": "custom",
                "gop_size": 1,
                "use_hardware_acceleration": False,
                "version": 2
            },
            "webm_vp9": {
                "name": "WebM VP9",
                "description": "Web-optimized VP9 + Opus",
                "container": "webm",
                "video_codec": "vp9",
                "video_encoder": "libvpx-vp9",
                "video_preset": "good",
                "encoding_mode": "crf",
                "crf": 30,
                "gop_mode": "custom",
                "gop_size": 240,
                "b_frames": 0,
                "extra_video_options": [
                    "-b:v", "0",
                    "-row-mt", "1",
                    "-tile-columns", "2",
                    "-tile-rows", "1"
                ],
                "audio_codec": "opus",
                "audio_encoder": "libopus",
                "audio_bitrate": "128k",
                "audio_sample_rate": 48000,
                "use_hardware_acceleration": False,
                "version": 2
            },
            "hardware_h264": {
                "name": "Hardware H.264",
                "description": "Hardware-accelerated H.264",
                "container": "mp4",
                "video_codec": "h264",
                "encoding_mode": "cq",
                "cq": 20,
                "maxrate": "8M",
                "bufsize": "24M",
                "extra_video_options": ["-rc", "vbr", "-spatial_aq", "1"],
                "audio_codec": "aac",
                "audio_bitrate": "160k",
                "use_hardware_acceleration": True,
                **common_mp4_flags,
                "version": 2
            },
            "animation": {
                "name": "Animation & Screen",
                "description": "Preserve flat graphics and UI captures",
                "container": "mp4",
                "video_codec": "h264",
                "video_preset": "slow",
                "encoding_mode": "crf",
                "crf": 20,
                "video_tune": "animation",
                "audio_codec": "aac",
                "audio_bitrate": "128k",
                "use_hardware_acceleration": True,
                **common_mp4_flags,
                "version": 2
            }
        }

        return presets
        
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.config = AppConfig(**data)
        except Exception as e:
            self.config = AppConfig()
            self._set_defaults()
            
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
        except Exception:
            pass
            
    def load_presets(self):
        try:
            with open(self.presets_file, 'r') as f:
                self.presets = json.load(f)
        except Exception:
            self._create_default_presets()
            
    def save_presets(self):
        try:
            with open(self.presets_file, 'w') as f:
                json.dump(self.presets, f, indent=2)
        except Exception:
            pass
            
    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        return self.presets.get(name)
        
    def add_custom_preset(self, name: str, preset_data: Dict[str, Any]):
        self.presets[name] = preset_data
        self.save_presets()
        
    def cleanup_temp_files(self):
        temp_dir = Path(self.config.temp_directory)
        if temp_dir.exists():
            for item in temp_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception:
                    pass
