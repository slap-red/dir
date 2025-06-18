# logger_config.py

import logging
import os
import json
from logging.handlers import RotatingFileHandler

class DetailFormatter(logging.Formatter):
    """A custom formatter to include extra data in text logs."""
    def format(self, record):
        # Start with the standard format
        log_string = super().format(record)
        
        # Add extra details if they exist
        extra_items = {k: v for k, v in record.__dict__.items() if k not in logging.LogRecord.__dict__}
        if extra_items:
            try:
                # Use json.dumps for a consistent, readable format
                details_str = json.dumps(extra_items)
                log_string += f" -- Details: {details_str}"
            except TypeError:
                pass # Ignore errors if extra data isn't serializable
        return log_string

def setup_logger(config=None):
    """Sets up a rotating file logger with detailed formatting."""
    log_level = 'INFO'
    log_file = 'logs/scraper.log'
    if config:
        log_level = config.get('logging', 'log_level', fallback='INFO').upper()
        log_file = config.get('logging', 'log_file_path', fallback='logs/scraper.log')

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger = logging.getLogger("slapdotred_scraper")
    logger.setLevel(log_level)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    # Use the new detailed formatter
    fh = RotatingFileHandler(log_file, maxBytes=1*1024*1024, backupCount=5)
    formatter = DetailFormatter('%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')
    fh.setFormatter(formatter)
    
    logger.addHandler(fh)
    
    return logger
