"""
Logging module - Provides unified log configuration and logger instances
"""

import logging
import sys
import os
from datetime import datetime
from typing import Any, Optional

EnableLogFile = False
LogLevel = logging.INFO

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

def setup(level=LogLevel, enableFile=EnableLogFile):
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
    logging.getLogger('httpx').setLevel(logging.WARNING)

    return root_logger

def enableFile(enable=True):
    """Enable or disable file logging"""
    global EnableLogFile
    EnableLogFile = enable
    setup(enableFile=enable)
    logging.info(f"File logging is {'enabled' if enable else 'disabled'}")

def setLog(level):
    """Set logging level"""
    global LogLevel
    LogLevel = level
    setup(level=level)
    logging.info(f"Log level has been set to {logging.getLevelName(level)}")

lg = logging.getLogger('dupfnd')

setup()


class LoggerAdapter:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def debug(self, msg: Any, *args: Any, exc_info: Optional[Any] = None,
              extra: Optional[dict] = None, stack_info: bool = False,
              stacklevel: int = 1, **kwargs) -> None:
        self._logger.debug(msg, *args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel, **kwargs)

    def info(self, msg: Any, *args: Any, exc_info: Optional[Any] = None,
             extra: Optional[dict] = None, stack_info: bool = False,
             stacklevel: int = 1, **kwargs) -> None:
        self._logger.info(msg, *args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel, **kwargs)

    def warn(self, msg: Any, *args: Any, exc_info: Optional[Any] = None,
             extra: Optional[dict] = None, stack_info: bool = False,
             stacklevel: int = 1, **kwargs) -> None:
        self._logger.warning(msg, *args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel, **kwargs)

    def error(self, msg: Any, *args: Any, exc_info: Optional[Any] = None,
              extra: Optional[dict] = None, stack_info: bool = False,
              stacklevel: int = 1, **kwargs) -> None:
        self._logger.error(msg, *args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel, **kwargs)

    def exception(self, msg: Any, *args: Any, exc_info: Optional[Any] = None,
                  extra: Optional[dict] = None, stack_info: bool = False,
                  stacklevel: int = 1, **kwargs) -> None:
        self._logger.exception(msg, *args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel, **kwargs)

    def critical(self, msg: Any, *args: Any, exc_info: Optional[Any] = None,
                 extra: Optional[dict] = None, stack_info: bool = False,
                 stacklevel: int = 1, **kwargs) -> None:
        self._logger.critical(msg, *args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel, **kwargs)

    def fatal(self, msg: Any, *args: Any, exc_info: Optional[Any] = None,
              extra: Optional[dict] = None, stack_info: bool = False,
              stacklevel: int = 1, **kwargs) -> None:
        self._logger.fatal(msg, *args, exc_info=exc_info, extra=extra, stack_info=stack_info, stacklevel=stacklevel, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._logger, name)


def get(name: str) -> LoggerAdapter:
    return LoggerAdapter(logging.getLogger(name))
