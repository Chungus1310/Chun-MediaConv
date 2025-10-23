import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "ChunMediaConv") -> logging.Logger:
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)
    
    log_dir = Path.home() / ".chunmediaconv" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "app.log"
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str = "ChunMediaConv") -> logging.Logger:
    return logging.getLogger(name)
