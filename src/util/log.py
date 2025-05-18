"""
Logging module - Provides unified log configuration and logger instances
"""

import logging
import sys
import os
from datetime import datetime

ENABLE_FILE_LOGGING = False
LOG_LEVEL = logging.INFO

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

def setup(level=LOG_LEVEL, enableFile=ENABLE_FILE_LOGGING):
    """Configure logging system"""
    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d|%(levelname)s| %(message)s',
        datefmt='%H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(console_handler)

    if enableFile:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('flask').setLevel(logging.INFO)

    return root_logger

def enableFile(enable=True):
    """Enable or disable file logging"""
    global ENABLE_FILE_LOGGING
    ENABLE_FILE_LOGGING = enable
    setup(enableFile=enable)
    logging.info(f"File logging is {'enabled' if enable else 'disabled'}")

def setLog(level):
    """Set logging level"""
    global LOG_LEVEL
    LOG_LEVEL = level
    setup(level=level)
    logging.info(f"Log level has been set to {logging.getLevelName(level)}")

lg = logging.getLogger('dupfnd')

setup()

def get(name):
    """Get logger for specific module"""
    return logging.getLogger(name)
