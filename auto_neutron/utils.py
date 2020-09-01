import logging
import os
import sys
import traceback
from pathlib import Path
from types import MethodType
from typing import List, Optional, Tuple

from PyQt5 import QtCore

from auto_neutron.constants import JPATH


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


class ExceptionHandler(QtCore.QObject):
    """Handles exceptions when linked to sys.excepthook."""

    traceback_sig = QtCore.pyqtSignal(list)

    def __init__(self, output_file: os.PathLike):
        super().__init__()
        self.path = output_file
        self.cleared = False

    def handler(self, exctype, value, tb) -> None:  # noqa TYP001
        """
        Logs exceptions to `self.path` and sends a signal to open error window.

        `self.path` is truncated on the first exception,
        newlines are added if multiple exceptions occur.
        """
        exc = traceback.format_exception(exctype, value, tb)
        with open(self.path, 'a') as f:
            if not self.cleared:
                # clear file on first traceback
                f.truncate(0)
                self.cleared = True
            else:
                # insert spacing newline
                f.write("\n")
            f.write("".join(exc))

        sys.__excepthook__(exctype, value, tb)

        self.traceback_sig.emit(exc)


def init_qt_logging(logger: logging.Logger) -> None:
    """Redirect QDebug calls to `logger`."""
    def handler(level: int, _context: QtCore.QMessageLogContext, message: str) -> None:
        original_find_caller = logger.findCaller

        def patched_caller(self, stack_info: bool) -> Tuple[str, int, str, Optional[str]]:  # noqa ANN001
            """Patch filename to be "Qt" for logs from this function."""
            _, lno, func, sinfo = original_find_caller(stack_info)
            return "<Qt>", lno, func, sinfo

        logger.findCaller = MethodType(patched_caller, logger)
        logger.log(QT_LOG_LEVELS[level], message)
        logger.findCaller = original_find_caller
    QtCore.qInstallMessageHandler(handler)
