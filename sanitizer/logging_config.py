import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name="DataSanitizer", log_file="sanitizer_engine.log", level=logging.INFO):
    """
    Sets up a rotating file logger for the application.
    Prevents duplicate handlers if called multiple times.
    """
    logger = logging.getLogger(name)
    
    # Check if handlers already exist to avoid duplicate logs
    if not logger.handlers:
        logger.setLevel(level)
        
        # Format
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # File Handler (rotating, max 5MB per file, up to 3 backups)
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
    return logger
