import os
import shutil
import tempfile
import atexit
from pathlib import Path
from typing import Optional
import uuid

class TempFileManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.base_temp_dir = Path(tempfile.gettempdir()) / "chunmediaconv"
        self.session_dir = self.base_temp_dir / str(uuid.uuid4())
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        atexit.register(self.cleanup_all)
        
    def create_temp_file(self, suffix: str = "", prefix: str = "temp_") -> Path:
        temp_file = self.session_dir / f"{prefix}{uuid.uuid4()}{suffix}"
        temp_file.touch()
        return temp_file
        
    def create_temp_dir(self, prefix: str = "temp_") -> Path:
        temp_dir = self.session_dir / f"{prefix}{uuid.uuid4()}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir
        
    def get_temp_path(self, filename: str) -> Path:
        return self.session_dir / filename
        
    def cleanup_file(self, file_path: Path):
        try:
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
        except Exception:
            pass
            
    def cleanup_session(self):
        try:
            if self.session_dir.exists():
                shutil.rmtree(self.session_dir)
        except Exception:
            pass
            
    def cleanup_all(self):
        try:
            if self.base_temp_dir.exists():
                for item in self.base_temp_dir.iterdir():
                    try:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                    except Exception:
                        pass
        except Exception:
            pass
            
    def get_session_size(self) -> int:
        total_size = 0
        try:
            for item in self.session_dir.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception:
            pass
        return total_size
