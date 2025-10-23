import subprocess
import re
import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing
import platform

from PySide6.QtCore import QObject, Signal, QThread

from src.core.hardware_detector import HardwareDetector
from src.core.format_compatibility import FormatCompatibility, FormatInfo
from src.utils.temp_manager import TempFileManager
from src.utils.logger import get_logger

logger = get_logger()

class ConversionWorker(QObject):
    progress = Signal(float, str)
    finished = Signal(bool, str)
    error = Signal(str)
    
    _DEFAULT_VIDEO_ENCODERS = {
        "h264": "libx264",
        "h265": "libx265",
        "vp9": "libvpx-vp9",
        "vp8": "libvpx",
        "av1": "libaom-av1",
        "mpeg4": "mpeg4",
        "mjpeg": "mjpeg",
        "ffv1": "ffv1",
        "prores": "prores_ks"
    }

    _DEFAULT_AUDIO_ENCODERS = {
        "aac": "aac",
        "alac": "alac",
        "mp3": "libmp3lame",
        "opus": "libopus",
        "vorbis": "libvorbis",
        "flac": "flac",
        "pcm": "pcm_s16le",
        "ac3": "ac3",
        "dts": "dca"
    }

    def __init__(self, job_config: Dict[str, Any], ffmpeg_path: str, hw_detector: HardwareDetector):
        super().__init__()
        self.job_config = job_config
        self.ffmpeg_path = ffmpeg_path
        self.hw_detector = hw_detector
        self.process: Optional[subprocess.Popen] = None
        self.should_stop = False
        self.temp_manager = TempFileManager()
        self.format_compat = FormatCompatibility()
        self.temp_dir = None
        
    def run(self):
        try:
            # Create per-job temp working directory
            self.temp_dir = self.temp_manager.create_temp_dir(prefix="job_")
            input_file = self.job_config["input_file"]
            output_file = self.job_config["output_file"]
            
            self.progress.emit(0.0, "Analyzing input file...")
            input_info = self._get_input_info(input_file)
            
            if not input_info:
                self.error.emit("Failed to analyze input file")
                self.finished.emit(False, "Analysis failed")
                return
                
            self.progress.emit(5.0, "Building conversion command...")
            command = self._build_ffmpeg_command(input_file, output_file, input_info)
            logger.debug("FFmpeg command: %s", " ".join(command))
            
            self.progress.emit(10.0, "Starting conversion...")
            success, result_message = self._execute_conversion(command, input_info.get("duration", 0))
            
            if success:
                self.progress.emit(100.0, "Conversion complete!")
                self.finished.emit(True, output_file)
            else:
                if result_message and result_message != "Conversion cancelled":
                    self.error.emit(result_message)
                self.finished.emit(False, result_message or "Conversion failed")
                
        except Exception as e:
            self.error.emit(f"Conversion error: {str(e)}")
            self.finished.emit(False, str(e))
        finally:
            if self.temp_dir is not None:
                self.temp_manager.cleanup_file(self.temp_dir)
            
    def stop(self):
        self.should_stop = True
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
                    
    def _get_input_info(self, input_file: str) -> Optional[Dict[str, Any]]:
        try:
            command = [
                self.ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe") if platform.system() == "Windows" else self.ffmpeg_path.replace("ffmpeg", "ffprobe"),
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                input_file
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            data = json.loads(result.stdout)
            
            info = {
                "duration": float(data.get("format", {}).get("duration", 0)),
                "size": int(data.get("format", {}).get("size", 0)),
                "bitrate": int(data.get("format", {}).get("bit_rate", 0)),
                "video_streams": [],
                "audio_streams": [],
                "subtitle_streams": []
            }
            
            for stream in data.get("streams", []):
                if stream["codec_type"] == "video":
                    fps_value = 0.0
                    rate = stream.get("r_frame_rate") or stream.get("avg_frame_rate")
                    if rate and rate != "0/0":
                        try:
                            fps_value = float(Fraction(rate))
                        except (ValueError, ZeroDivisionError):
                            fps_value = 0.0
                    info["video_streams"].append({
                        "codec": stream.get("codec_name"),
                        "width": stream.get("width", 0),
                        "height": stream.get("height", 0),
                        "fps": fps_value
                    })
                elif stream["codec_type"] == "audio":
                    info["audio_streams"].append({
                        "codec": stream.get("codec_name"),
                        "sample_rate": stream.get("sample_rate"),
                        "channels": stream.get("channels")
                    })
                elif stream["codec_type"] == "subtitle":
                    info["subtitle_streams"].append({
                        "codec": stream.get("codec_name")
                    })
                    
            return info
            
        except Exception:
            return None
            
    def _build_ffmpeg_command(self, input_file: str, output_file: str, input_info: Dict) -> list:
        command = [self.ffmpeg_path, "-y"]

        config = dict(self.job_config)
        output_ext = Path(output_file).suffix.lower().lstrip('.')
        fmt_info = self.format_compat.get_format_info(output_ext)

        is_audio_container = bool(fmt_info and fmt_info.type == "audio")

        if config.get("use_hardware_acceleration", True) and not is_audio_container:
            hw_args = self.hw_detector.get_acceleration_args(config.get("video_codec", "h264"))
            command.extend(hw_args)

        command.extend(["-i", input_file])

        if config.get("conversion_type") == "video_to_audio" or is_audio_container:
            command.extend(["-vn"])
        else:
            self._apply_video_settings(command, config, fmt_info, output_ext, input_info)

        if config.get("conversion_type") != "audio_to_video":
            self._apply_audio_settings(command, config, fmt_info, output_ext)

        if config.get("start_time"):
            command.extend(["-ss", config["start_time"]])
            
        if config.get("duration"):
            command.extend(["-t", config["duration"]])
            
        threads = config.get("threads", min(multiprocessing.cpu_count(), 8))
        command.extend(["-threads", str(threads)])
        
        command.extend(["-hide_banner", "-loglevel", "info", "-stats"])
        
        command.append(output_file)
        
        return command

    def _apply_video_settings(
        self,
        command: List[str],
        config: Dict[str, Any],
        fmt_info: Optional[FormatInfo],
        output_ext: str,
        input_info: Dict[str, Any]
    ) -> None:
        if config.get("video_copy"):
            command.extend(["-c:v", "copy"])
            return

        video_codec = self._normalize_video_codec(config.get("video_codec", "h264"))
        audio_codec = self._normalize_audio_codec(config.get("audio_codec", "aac"))

        if fmt_info and video_codec not in fmt_info.supported_video_codecs:
            video_codec, audio_codec = self.format_compat.get_fallback_codec(output_ext, video_codec, audio_codec)
            config["video_codec"] = video_codec
            config["audio_codec"] = audio_codec

        encoder = config.get("video_encoder")
        if not encoder:
            default_encoder = self._DEFAULT_VIDEO_ENCODERS.get(video_codec, f"lib{video_codec}")
            if config.get("use_hardware_acceleration", True):
                encoder = self.hw_detector.get_encoder(video_codec, default_encoder)
            else:
                encoder = default_encoder

        command.extend(["-c:v", encoder])

        preset = config.get("video_preset")
        mapped_preset = self._map_encoder_preset(encoder, preset)

        encoding_mode = (config.get("encoding_mode") or "crf").lower()

        if encoding_mode == "crf":
            crf_value = config.get("crf", 23)
            command.extend(["-crf", str(crf_value)])
        elif encoding_mode == "bitrate":
            video_bitrate = config.get("video_bitrate", "5M")
            command.extend(["-b:v", str(video_bitrate)])
        elif encoding_mode == "target_size":
            target_mb = float(config.get("target_size_mb", 50))
            duration = max(float(input_info.get("duration", 0.0)), 1.0)
            audio_bitrate = self._extract_audio_bitrate_kbps(config.get("audio_bitrate"))
            total_kbits = target_mb * 8000
            video_kbps = max(int((total_kbits - audio_bitrate * duration) / duration), 300)
            command.extend(["-b:v", f"{video_kbps}k"])
        elif encoding_mode == "cq":
            cq_value = config.get("cq", 20)
            command.extend(["-cq", str(cq_value)])
        elif encoding_mode == "lossless":
            pass

        if mapped_preset:
            command.extend(["-preset", mapped_preset])

        video_tune = self._map_encoder_tune(encoder, config.get("video_tune"))
        if video_tune:
            command.extend(["-tune", video_tune])

        video_profile = config.get("video_profile")
        if video_profile:
            command.extend(["-profile:v", str(video_profile)])

        video_level = config.get("video_level")
        if video_level:
            command.extend(["-level", str(video_level)])

        if config.get("pixel_format"):
            command.extend(["-pix_fmt", str(config["pixel_format"])])

        if config.get("maxrate"):
            command.extend(["-maxrate", str(config["maxrate"])])

        if config.get("bufsize"):
            command.extend(["-bufsize", str(config["bufsize"])])

        if config.get("force_cfr"):
            command.extend(["-vsync", "cfr"])

        gop_size = self._resolve_gop_size(config, input_info)
        if gop_size:
            command.extend(["-g", str(gop_size)])

        b_frames = config.get("b_frames")
        if b_frames is not None:
            command.extend(["-bf", str(b_frames)])

        filters: List[str] = []
        if config.get("scale_width") or config.get("scale_height"):
            width = config.get("scale_width", -2)
            height = config.get("scale_height", -2)
            filters.append(f"scale={width}:{height}")

        if config.get("video_filters"):
            vf_setting = config["video_filters"]
            if isinstance(vf_setting, list):
                filters.extend([str(v) for v in vf_setting if v])
            else:
                filters.append(str(vf_setting))

        if filters:
            command.extend(["-vf", ",".join(filters)])

        if config.get("framerate"):
            command.extend(["-r", str(config["framerate"])])

        if config.get("movflags") and output_ext in {"mp4", "mov"}:
            movflags = config["movflags"]
            if isinstance(movflags, list):
                command.extend(["-movflags", " ".join(movflags)])
            else:
                command.extend(["-movflags", str(movflags)])
        elif output_ext == "mp4":
            command.extend(["-movflags", "+faststart"])

        for opt_flag, opt_value in self._iter_video_options(config.get("extra_video_options", []), encoder):
            command.append(opt_flag)
            if opt_value is not None:
                command.append(opt_value)

        if config.get("color_primaries"):
            command.extend(["-color_primaries", str(config["color_primaries"])])

        if config.get("color_trc"):
            command.extend(["-color_trc", str(config["color_trc"])])

        if config.get("colorspace"):
            command.extend(["-colorspace", str(config["colorspace"])])

    def _map_encoder_preset(self, encoder: str, preset: Optional[str]) -> Optional[str]:
        if not preset:
            return None

        preset_str = str(preset).strip().lower()
        if not preset_str:
            return None

        if "nvenc" in (encoder or "").lower():
            allowed = {
                "default", "slow", "medium", "fast", "hp", "hq", "bd",
                "ll", "llhq", "llhp", "lossless", "losslesshp",
                "p1", "p2", "p3", "p4", "p5", "p6", "p7"
            }
            mapping = {
                "ultrafast": "p1",
                "superfast": "p2",
                "veryfast": "p3",
                "faster": "p4",
                "fast": "p5",
                "medium": "p6",
                "slow": "p7",
                "slower": "slow",
                "veryslow": "slow",
            }
            mapped = mapping.get(preset_str, preset_str)
            return mapped if mapped in allowed else None

        return str(preset)

    def _map_encoder_tune(self, encoder: str, tune: Optional[str]) -> Optional[str]:
        if not tune:
            return None

        tune_str = str(tune).strip().lower()
        if not tune_str:
            return None

        # NVENC and most hardware encoders do not support x264 tune flags
        if "nvenc" in (encoder or "").lower():
            return None

        return str(tune)

    def _apply_audio_settings(
        self,
        command: List[str],
        config: Dict[str, Any],
        fmt_info: Optional[FormatInfo],
        output_ext: str
    ) -> None:
        if config.get("audio_copy"):
            command.extend(["-c:a", "copy"])
            return

        if (config.get("audio_codec") or "").lower() == "copy":
            command.extend(["-c:a", "copy"])
            return

        audio_codec = self._normalize_audio_codec(config.get("audio_codec", "aac"))
        video_codec = self._normalize_video_codec(config.get("video_codec", "h264"))

        if fmt_info and audio_codec not in fmt_info.supported_audio_codecs:
            video_codec, audio_codec = self.format_compat.get_fallback_codec(output_ext, video_codec, audio_codec)
            config["audio_codec"] = audio_codec
            config["video_codec"] = video_codec

        encoder = config.get("audio_encoder") or self._DEFAULT_AUDIO_ENCODERS.get(audio_codec, audio_codec)
        command.extend(["-c:a", encoder])

        audio_bitrate = config.get("audio_bitrate")
        if audio_bitrate and self._is_lossy_audio(audio_codec):
            command.extend(["-b:a", str(audio_bitrate)])

        if config.get("audio_sample_rate"):
            command.extend(["-ar", str(config["audio_sample_rate"])])

        if config.get("audio_channels"):
            command.extend(["-ac", str(config["audio_channels"])])

        extra_audio_options = config.get("extra_audio_options", [])
        if extra_audio_options:
            command.extend([str(opt) for opt in extra_audio_options])

    def _normalize_video_codec(self, codec: Optional[str]) -> str:
        if not codec:
            return "h264"
        codec_lower = codec.lower()
        mapping = {
            "libx264": "h264",
            "x264": "h264",
            "libx265": "h265",
            "x265": "h265",
            "hevc": "h265",
            "libvpx-vp9": "vp9",
            "libvpx": "vp8",
            "vp10": "av1",
            "libaom-av1": "av1",
            "libaom": "av1",
            "libxvid": "mpeg4",
            "xvid": "mpeg4",
            "ffvhuff": "ffv1"
        }
        if codec_lower in mapping:
            return mapping[codec_lower]
        if codec_lower.startswith("lib"):
            codec_lower = codec_lower[3:]
        if codec_lower.startswith("x") and codec_lower not in {"xvid"}:
            codec_lower = codec_lower[1:]
        if codec_lower == "vpx-vp9":
            return "vp9"
        if codec_lower == "vpx":
            return "vp8"
        if codec_lower == "xvid":
            return "mpeg4"
        return codec_lower

    def _normalize_audio_codec(self, codec: Optional[str]) -> str:
        if not codec:
            return "aac"
        codec_lower = codec.lower()
        lib_map = {
            "libopus": "opus",
            "libvorbis": "vorbis",
            "libmp3lame": "mp3",
            "pcm_s16le": "pcm",
            "pcm_s24le": "pcm",
            "pcm_s32le": "pcm"
        }
        return lib_map.get(codec_lower, codec_lower)

    def _resolve_gop_size(self, config: Dict[str, Any], input_info: Dict[str, Any]) -> Optional[int]:
        mode = (config.get("gop_mode") or "half_fps").lower()
        fps = self._extract_source_fps(input_info)
        default_g = config.get("gop_size")

        if fps <= 0 and not default_g:
            return None

        if mode == "half_fps" and fps > 0:
            return max(1, int(round(fps / 2)))
        if mode == "same_fps" and fps > 0:
            return max(1, int(round(fps)))
        if mode == "double_fps" and fps > 0:
            return max(1, int(round(fps * 2)))
        if mode == "seconds" and fps > 0:
            seconds = float(config.get("gop_seconds", 2))
            return max(1, int(round(fps * seconds)))
        if mode == "custom" and default_g:
            return int(default_g)

        return default_g if default_g else None

    def _extract_source_fps(self, input_info: Dict[str, Any]) -> float:
        streams = input_info.get("video_streams", [])
        if not streams:
            return 0.0
        fps = streams[0].get("fps")
        try:
            return float(fps) if fps else 0.0
        except (TypeError, ValueError):
            return 0.0

    def _extract_audio_bitrate_kbps(self, audio_bitrate: Optional[str]) -> int:
        if not audio_bitrate:
            return 128
        if isinstance(audio_bitrate, str) and audio_bitrate.endswith("k"):
            try:
                return int(audio_bitrate[:-1])
            except ValueError:
                return 128
        try:
            return int(audio_bitrate)
        except (TypeError, ValueError):
            return 128

    def _iter_video_options(self, options: List[str], encoder: str) -> List[Tuple[str, Optional[str]]]:
        if not options:
            return []
        filtered: List[Tuple[str, Optional[str]]] = []
        encoder_lower = (encoder or "").lower()
        skip_nvenc_only = {"-rc", "-spatial_aq", "-temporal_aq", "-aq-strength"}
        i = 0
        while i < len(options):
            flag = options[i]
            next_item = options[i + 1] if i + 1 < len(options) else None
            next_item_str = str(next_item) if next_item is not None else None
            value = next_item_str if next_item_str is not None and not next_item_str.startswith('-') else None
            if flag in skip_nvenc_only and "nvenc" not in encoder_lower:
                i += 2 if value is not None else 1
                continue
            filtered.append((str(flag), str(value) if value is not None else None))
            i += 2 if value is not None else 1
        return filtered

    def _is_lossy_audio(self, codec: str) -> bool:
        codec_info = self.format_compat.audio_codecs.get(codec)
        if not codec_info:
            return True
        return codec_info.get("lossy", True)
        
    def _execute_conversion(self, command: list, duration: float) -> Tuple[bool, str]:
        try:
            output_lines: List[str] = []
            cancelled = False
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
            
            assert self.process.stdout is not None

            for line in self.process.stdout:
                stripped = line.rstrip()
                if stripped:
                    output_lines.append(stripped)
                    if len(output_lines) > 200:
                        output_lines.pop(0)

                if self.should_stop:
                    cancelled = True
                    self.stop()
                    break

                match = time_pattern.search(line)
                if match and duration > 0:
                    hours, minutes, seconds = map(float, match.groups())
                    current_time = hours * 3600 + minutes * 60 + seconds
                    progress = min((current_time / duration) * 90 + 10, 99)
                    self.progress.emit(progress, f"Converting... {progress:.1f}%")
            
            self.process.wait()

            if cancelled:
                return False, "Conversion cancelled"

            if self.process.returncode == 0:
                return True, ""

            tail = "\n".join(output_lines[-20:]) if output_lines else ""
            message = f"ffmpeg exited with code {self.process.returncode}".strip()
            if tail:
                message = f"{message}\n{tail}"
            return False, message
            
        except Exception as exc:
            return False, str(exc)

class ConversionEngine:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.hw_detector = None
        self.format_compat = FormatCompatibility()
        self.active_workers: Dict[str, tuple] = {}
        self.executor = ThreadPoolExecutor(max_workers=config_manager.config.max_parallel_conversions)
        
    def initialize_hardware(self) -> bool:
        ffmpeg_path = self.config_manager.config.ffmpeg_path
        if not ffmpeg_path:
            return False
            
        self.hw_detector = HardwareDetector(ffmpeg_path)
        return self.hw_detector.detect()
        
    def create_conversion_job(self, job_config: Dict[str, Any]) -> Optional[ConversionWorker]:
        if not self.hw_detector:
            if not self.initialize_hardware():
                return None
                
        worker = ConversionWorker(
            job_config,
            self.config_manager.config.ffmpeg_path,
            self.hw_detector
        )
        
        return worker
        
    def get_hardware_info(self) -> Dict[str, Any]:
        if not self.hw_detector:
            return {"status": "not initialized"}
        return self.hw_detector.get_info()
