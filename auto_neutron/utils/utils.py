# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import collections.abc
import itertools
import logging
import sys
from pathlib import Path
from types import TracebackType

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401
from auto_neutron.utils.logging import patch_log_module

log = logging.getLogger(__name__)


class ExceptionHandler(QtCore.QObject):
    """Handles exceptions when linked to sys.excepthook."""

    triggered = QtCore.Signal()

    def handler(
        self, exctype: type[BaseException], value: BaseException, tb: TracebackType
    ) -> None:
        """Log exception using `self.logger` and emit `traceback_sig`` with formatted exception."""
        if exctype is KeyboardInterrupt:
            sys.exit()

        exception_file_path = Path(tb.tb_frame.f_code.co_filename)
        with patch_log_module(log, exception_file_path.stem):
            log.critical("Uncaught exception:", exc_info=(exctype, value, tb))
            log.critical(
                ""
            )  # log empty message to give a bit of space around traceback

        self.triggered.emit()


def create_interrupt_timer() -> QtCore.QTimer:
    """Interrupt the Qt event loop regularly to let python process signals."""
    timer = QtCore.QTimer()
    timer.interval = 50
    timer.timeout.connect(lambda: None)
    timer.start()
    return timer


def create_request_delay_iterator() -> collections.abc.Iterator[int]:
    """Create an iterator for re-request delays."""
    return itertools.chain(iter([1, 2, 4, 4, 4, 6, 6]), itertools.cycle([10]))
