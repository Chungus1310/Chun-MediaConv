import subprocess
import re
from typing import Dict, List, Optional
from enum import Enum
import platform

class AccelerationType(Enum):
    CUDA = "cuda"
    VULKAN = "vulkan"
    OPENCL = "opencl"
    VIDEOTOOLBOX = "videotoolbox"
    QSV = "qsv"
    DXVA2 = "dxva2"
    D3D11VA = "d3d11va"
    NONE = "none"

class HardwareDetector:
    def __init__(self, ffmpeg_path: str):
        self.ffmpeg_path = ffmpeg_path
        self.available_hwaccels: List[str] = []
        self.available_encoders: Dict[str, List[str]] = {}
        self.available_decoders: Dict[str, List[str]] = {}
        self.detected_gpu: Optional[str] = None
        self.best_acceleration: AccelerationType = AccelerationType.NONE
        
    def detect(self) -> bool:
        if not self.ffmpeg_path:
            return False
            
        try:
            self._detect_hwaccels()
            self._detect_encoders()
            self._detect_gpu()
            self._determine_best_acceleration()
            return self.best_acceleration != AccelerationType.NONE
        except Exception:
            return False
            
    def _detect_hwaccels(self):
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-hwaccels"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            lines = result.stdout.split('\n')
            in_list = False
            for line in lines:
                line = line.strip()
                if line == "Hardware acceleration methods:":
                    in_list = True
                    continue
                if in_list and line:
                    self.available_hwaccels.append(line)
        except Exception:
            pass
            
    def _detect_encoders(self):
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-encoders"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            hw_patterns = {
                "h264": r"h264_(\w+)",
                "hevc": r"hevc_(\w+)",
                "vp9": r"vp9_(\w+)",
                "av1": r"av1_(\w+)"
            }
            
            for codec, pattern in hw_patterns.items():
                self.available_encoders[codec] = []
                for match in re.finditer(pattern, result.stdout):
                    hw_type = match.group(1)
                    self.available_encoders[codec].append(hw_type)
        except Exception:
            pass
            
    def _detect_gpu(self):
        system = platform.system()
        
        if system == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "name"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                
                lines = result.stdout.split('\n')
                for line in lines[1:]:
                    line = line.strip()
                    if line:
                        self.detected_gpu = line
                        break
            except Exception:
                pass
                
    def _determine_best_acceleration(self):
        if not self.available_hwaccels:
            self.best_acceleration = AccelerationType.NONE
            return
            
        system = platform.system()
        gpu_lower = (self.detected_gpu or "").lower()
        
        priority_order = []
        
        if system == "Windows":
            if "nvidia" in gpu_lower:
                priority_order = [
                    AccelerationType.CUDA,
                    AccelerationType.D3D11VA,
                    AccelerationType.DXVA2,
                    AccelerationType.VULKAN,
                    AccelerationType.OPENCL
                ]
            elif "amd" in gpu_lower or "radeon" in gpu_lower:
                priority_order = [
                    AccelerationType.VULKAN,
                    AccelerationType.D3D11VA,
                    AccelerationType.OPENCL,
                    AccelerationType.DXVA2
                ]
            elif "intel" in gpu_lower:
                priority_order = [
                    AccelerationType.QSV,
                    AccelerationType.D3D11VA,
                    AccelerationType.VULKAN,
                    AccelerationType.OPENCL
                ]
            else:
                priority_order = [
                    AccelerationType.D3D11VA,
                    AccelerationType.DXVA2,
                    AccelerationType.VULKAN,
                    AccelerationType.OPENCL
                ]
        elif system == "Darwin":
            priority_order = [AccelerationType.VIDEOTOOLBOX]
        else:
            priority_order = [
                AccelerationType.VULKAN,
                AccelerationType.OPENCL
            ]
            
        for accel_type in priority_order:
            if accel_type.value in self.available_hwaccels:
                self.best_acceleration = accel_type
                return
                
        self.best_acceleration = AccelerationType.NONE
        
    def get_acceleration_args(self, codec: str = "h264") -> List[str]:
        if self.best_acceleration == AccelerationType.NONE:
            return []
            
        args = []
        
        if self.best_acceleration == AccelerationType.CUDA:
            # Allow FFmpeg to choose the best transfer path; forcing CUDA output
            # frames often introduces additional filter requirements that are
            # unavailable in minimalist builds. Keeping the default output format
            # avoids those failures while still enabling GPU-accelerated decode
            # when the binary supports it.
            args.extend(["-hwaccel", "cuda"])
            if codec in self.available_encoders and "nvenc" in self.available_encoders[codec]:
                return args
                
        elif self.best_acceleration == AccelerationType.VULKAN:
            args.extend(["-hwaccel", "vulkan"])
            
        elif self.best_acceleration == AccelerationType.OPENCL:
            args.extend(["-hwaccel", "opencl"])
            
        elif self.best_acceleration == AccelerationType.QSV:
            args.extend(["-hwaccel", "qsv", "-hwaccel_output_format", "qsv"])
            
        elif self.best_acceleration in [AccelerationType.D3D11VA, AccelerationType.DXVA2]:
            args.extend(["-hwaccel", self.best_acceleration.value])
            
        elif self.best_acceleration == AccelerationType.VIDEOTOOLBOX:
            args.extend(["-hwaccel", "videotoolbox"])
            
        return args
        
    def get_encoder(self, codec: str, fallback: str) -> str:
        if self.best_acceleration == AccelerationType.NONE:
            return fallback
            
        if codec not in self.available_encoders:
            return fallback
            
        hw_encoders = self.available_encoders[codec]
        
        if self.best_acceleration == AccelerationType.CUDA and "nvenc" in hw_encoders:
            return f"{codec}_nvenc"
        elif self.best_acceleration == AccelerationType.QSV and "qsv" in hw_encoders:
            return f"{codec}_qsv"
        elif self.best_acceleration == AccelerationType.VIDEOTOOLBOX and "videotoolbox" in hw_encoders:
            return f"{codec}_videotoolbox"
        elif self.best_acceleration in [AccelerationType.D3D11VA, AccelerationType.DXVA2]:
            # d3d11va/dxva2 are primarily for decode; prefer vendor-specific encoders if present
            if "amf" in hw_encoders:
                return f"{codec}_amf"
            if "qsv" in hw_encoders:
                return f"{codec}_qsv"
            if "nvenc" in hw_encoders:
                return f"{codec}_nvenc"
        elif self.best_acceleration == AccelerationType.VULKAN and "vulkan" in hw_encoders:
            return f"{codec}_vulkan"
        elif self.best_acceleration == AccelerationType.OPENCL:
            # OpenCL generally assists filters; fall back to best available encoder
            if "nvenc" in hw_encoders:
                return f"{codec}_nvenc"
            if "qsv" in hw_encoders:
                return f"{codec}_qsv"
            if "amf" in hw_encoders:
                return f"{codec}_amf"
        # Linux/others: consider vaapi when present
        if "vaapi" in hw_encoders:
            return f"{codec}_vaapi"
            
        return fallback
        
    def get_info(self) -> Dict[str, any]:
        return {
            "gpu": self.detected_gpu or "None detected",
            "acceleration": self.best_acceleration.value,
            "hwaccels": self.available_hwaccels,
            "encoders": self.available_encoders
        }
