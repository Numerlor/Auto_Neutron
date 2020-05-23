import os
import sys
import traceback
from pathlib import Path
from typing import List

from PyQt5 import QtCore

from auto_neutron.constants import JPATH


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