import logging
import os
from contextlib import contextmanager
from pathlib import Path
from types import MethodType, TracebackType
from typing import Iterator, List, Optional, Tuple, Type

from PySide6 import QtCore
# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property

from auto_neutron.constants import JPATH

log = logging.getLogger(__name__)

QT_LOG_LEVELS = {
    0: logging.DEBUG,
    4: logging.INFO,
    1: logging.WARNING,
    2: logging.ERROR,
    3: logging.CRITICAL,
}


def get_journals(n: int) -> List[Path]:
    """Get last n journals."""
    return sorted(JPATH.glob("*.log"), key=os.path.getctime, reverse=True)[:n]


@contextmanager
def patch_log_module(logger: logging.Logger, module_name: str) -> Iterator[None]:
    """Patch logs using `logger` within this context manager to use `module_name` as the module name."""
    original_find_caller = logger.findCaller

    def patched_caller(self: logging.Logger, stack_info: bool, stack_level: int) -> Tuple[str, int, str, Optional[str]]:
        """Patch filename on logs after this was applied to be `module_name`."""
        _, lno, func, sinfo = original_find_caller(stack_info, stack_level)
        return module_name, lno, func, sinfo

    logger.findCaller = MethodType(patched_caller, logger)
    try:
        yield
    finally:
        logger.findCaller = original_find_caller


class ExceptionHandler(QtCore.QObject):
    """Handles exceptions when linked to sys.excepthook."""

    triggered = QtCore.Signal()

    def handler(self, exctype: Type[BaseException], value: BaseException, tb: TracebackType) -> None:
        """Log exception using `self.logger` and emit `traceback_sig`` with formatted exception."""
        exception_file_path = Path(tb.tb_frame.f_code.co_filename)
        with patch_log_module(log, exception_file_path.stem):
            log.critical("Uncaught exception:", exc_info=(exctype, value, tb))
            log.critical("")  # log empty message to give a bit of space around traceback

        self.triggered.emit()


class UsernameFormatter(logging.Formatter):
    """Redact Windows usernames from logs made using this formatter."""
    os_username = os.environ["USERNAME"]

    def format(self, record: logging.LogRecord) -> str:
        """Redact Windows usernames from `record` message."""
        message = super().format(record)
        return message.replace(f"\\{self.os_username}", "\\USERNAME")


def init_qt_logging() -> None:
    """Redirect QDebug calls to `logger`."""
    def handler(level: int, _context: QtCore.QMessageLogContext, message: str) -> None:
        with patch_log_module(log, "<Qt>"):
            log.log(QT_LOG_LEVELS[level], message)
    QtCore.qInstallMessageHandler(handler)
