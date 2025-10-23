from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class FormatInfo:
    name: str
    extension: str
    type: str
    supported_video_codecs: List[str]
    supported_audio_codecs: List[str]
    container_features: List[str]
    
class FormatCompatibility:
    def __init__(self):
        self.formats = self._initialize_formats()
        self.video_codecs = self._initialize_video_codecs()
        self.audio_codecs = self._initialize_audio_codecs()
        
    def _initialize_formats(self) -> Dict[str, FormatInfo]:
        return {
            "mp4": FormatInfo(
                name="MP4",
                extension="mp4",
                type="video",
                supported_video_codecs=["h264", "h265"],
                supported_audio_codecs=["aac", "alac"],
                container_features=["chapters", "subtitles", "metadata"]
            ),
            "mkv": FormatInfo(
                name="Matroska",
                extension="mkv",
                type="video",
                supported_video_codecs=["h264", "h265", "vp9", "av1", "mpeg4", "ffv1"],
                supported_audio_codecs=["aac", "mp3", "ac3", "flac", "opus", "vorbis", "dts"],
                container_features=["chapters", "subtitles", "metadata", "multiple_audio", "multiple_subtitles"]
            ),
            "webm": FormatInfo(
                name="WebM",
                extension="webm",
                type="video",
                supported_video_codecs=["vp8", "vp9", "av1"],
                supported_audio_codecs=["vorbis", "opus"],
                container_features=["subtitles", "metadata"]
            ),
            "avi": FormatInfo(
                name="AVI",
                extension="avi",
                type="video",
                supported_video_codecs=["mpeg4", "mjpeg"],
                supported_audio_codecs=["mp3", "ac3", "pcm"],
                container_features=["metadata"]
            ),
            "mov": FormatInfo(
                name="QuickTime",
                extension="mov",
                type="video",
                supported_video_codecs=["h264", "h265", "prores"],
                supported_audio_codecs=["aac", "alac", "pcm"],
                container_features=["chapters", "metadata"]
            ),
            "flv": FormatInfo(
                name="Flash Video",
                extension="flv",
                type="video",
                supported_video_codecs=["h264", "flv1"],
                supported_audio_codecs=["aac", "mp3"],
                container_features=["metadata"]
            ),
            "mp3": FormatInfo(
                name="MP3 Audio",
                extension="mp3",
                type="audio",
                supported_video_codecs=[],
                supported_audio_codecs=["mp3"],
                container_features=["metadata", "id3tags"]
            ),
            "aac": FormatInfo(
                name="AAC Audio",
                extension="aac",
                type="audio",
                supported_video_codecs=[],
                supported_audio_codecs=["aac"],
                container_features=["metadata"]
            ),
            "flac": FormatInfo(
                name="FLAC Lossless",
                extension="flac",
                type="audio",
                supported_video_codecs=[],
                supported_audio_codecs=["flac"],
                container_features=["metadata", "lossless"]
            ),
            "wav": FormatInfo(
                name="WAV Audio",
                extension="wav",
                type="audio",
                supported_video_codecs=[],
                supported_audio_codecs=["pcm"],
                container_features=["lossless"]
            ),
            "ogg": FormatInfo(
                name="Ogg Vorbis",
                extension="ogg",
                type="audio",
                supported_video_codecs=[],
                supported_audio_codecs=["vorbis", "opus"],
                container_features=["metadata"]
            ),
            "opus": FormatInfo(
                name="Opus Audio",
                extension="opus",
                type="audio",
                supported_video_codecs=[],
                supported_audio_codecs=["opus"],
                container_features=["metadata"]
            ),
            "m4a": FormatInfo(
                name="M4A Audio",
                extension="m4a",
                type="audio",
                supported_video_codecs=[],
                supported_audio_codecs=["aac", "alac"],
                container_features=["metadata"]
            )
        }
        
    def _initialize_video_codecs(self) -> Dict[str, Dict[str, any]]:
        return {
            "h264": {
                "name": "H.264 / AVC",
                "quality": "good",
                "speed": "fast",
                "hw_support": True,
                "fallback": "libx264"
            },
            "h265": {
                "name": "H.265 / HEVC",
                "quality": "excellent",
                "speed": "slow",
                "hw_support": True,
                "fallback": "libx265"
            },
            "vp9": {
                "name": "VP9",
                "quality": "excellent",
                "speed": "slow",
                "hw_support": False,
                "fallback": "libvpx-vp9"
            },
            "av1": {
                "name": "AV1",
                "quality": "excellent",
                "speed": "very_slow",
                "hw_support": False,
                "fallback": "libaom-av1"
            },
            "mpeg4": {
                "name": "MPEG-4",
                "quality": "moderate",
                "speed": "fast",
                "hw_support": False,
                "fallback": "mpeg4"
            },
            "ffv1": {
                "name": "FFV1",
                "quality": "lossless",
                "speed": "slow",
                "hw_support": False,
                "fallback": "ffv1"
            },
            "prores": {
                "name": "Apple ProRes",
                "quality": "excellent",
                "speed": "medium",
                "hw_support": False,
                "fallback": "prores_ks"
            },
            "vp8": {
                "name": "VP8",
                "quality": "good",
                "speed": "medium",
                "hw_support": False,
                "fallback": "libvpx"
            }
        }
        
    def _initialize_audio_codecs(self) -> Dict[str, Dict[str, any]]:
        return {
            "aac": {
                "name": "AAC",
                "quality": "good",
                "lossy": True,
                "bitrates": ["96k", "128k", "192k", "256k", "320k"]
            },
            "mp3": {
                "name": "MP3",
                "quality": "good",
                "lossy": True,
                "bitrates": ["96k", "128k", "192k", "256k", "320k"]
            },
            "opus": {
                "name": "Opus",
                "quality": "excellent",
                "lossy": True,
                "bitrates": ["96k", "128k", "192k", "256k"]
            },
            "vorbis": {
                "name": "Vorbis",
                "quality": "good",
                "lossy": True,
                "bitrates": ["96k", "128k", "192k", "256k"]
            },
            "flac": {
                "name": "FLAC",
                "quality": "lossless",
                "lossy": False,
                "bitrates": []
            },
            "alac": {
                "name": "Apple Lossless",
                "quality": "lossless",
                "lossy": False,
                "bitrates": []
            },
            "pcm": {
                "name": "PCM (Uncompressed)",
                "quality": "lossless",
                "lossy": False,
                "bitrates": []
            }
        }
        
    def get_compatible_video_codecs(self, format_name: str) -> List[str]:
        fmt = self.formats.get(format_name)
        if not fmt:
            return []
        return fmt.supported_video_codecs
        
    def get_compatible_audio_codecs(self, format_name: str) -> List[str]:
        fmt = self.formats.get(format_name)
        if not fmt:
            return []
        return fmt.supported_audio_codecs
        
    def get_fallback_codec(self, format_name: str, requested_video_codec: str, requested_audio_codec: str) -> Tuple[str, str]:
        fmt = self.formats.get(format_name)
        if not fmt:
            return ("libx264", "aac")
            
        video_codec = requested_video_codec
        audio_codec = requested_audio_codec
        
        if requested_video_codec not in fmt.supported_video_codecs and fmt.supported_video_codecs:
            video_codec = fmt.supported_video_codecs[0]
            
        if requested_audio_codec not in fmt.supported_audio_codecs and fmt.supported_audio_codecs:
            audio_codec = fmt.supported_audio_codecs[0]
            
        return (video_codec, audio_codec)
        
    def is_format_compatible(self, format_name: str, video_codec: Optional[str], audio_codec: Optional[str]) -> bool:
        fmt = self.formats.get(format_name)
        if not fmt:
            return False
            
        if video_codec and fmt.type == "video":
            if video_codec not in fmt.supported_video_codecs:
                return False
                
        if audio_codec:
            if audio_codec not in fmt.supported_audio_codecs:
                return False
                
        return True
        
    def get_format_info(self, format_name: str) -> Optional[FormatInfo]:
        return self.formats.get(format_name)
        
    def get_video_formats(self) -> List[str]:
        return [k for k, v in self.formats.items() if v.type == "video"]
        
    def get_audio_formats(self) -> List[str]:
        return [k for k, v in self.formats.items() if v.type == "audio"]
        
    def get_all_formats(self) -> List[str]:
        return list(self.formats.keys())
        
    def supports_lossless(self, format_name: str, audio_codec: str) -> bool:
        codec_info = self.audio_codecs.get(audio_codec)
        if codec_info:
            return not codec_info.get("lossy", True)
        return False
