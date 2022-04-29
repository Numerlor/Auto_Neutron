# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import itertools
import logging
import typing as t
from pathlib import Path

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401
from auto_neutron.utils.logging import patch_log_module

if t.TYPE_CHECKING:
    import collections.abc
    from types import TracebackType

log = logging.getLogger(__name__)

X_OFFSET = -49985
Y_OFFSET = -40985
Z_OFFSET = -24105


class ExceptionHandler(QtCore.QObject):
    """Handles exceptions when linked to sys.excepthook."""

    triggered = QtCore.Signal()

    def handler(
        self,
        exctype: type[BaseException],
        value: BaseException,
        tb: TracebackType | None,
    ) -> None:
        """
        Log exception, mocking the module to the traceback's module and emit `traceback_sig`` with formatted exception.

        If the traceback is not provided, use "UNKNOWN" as the module name.
        """
        if exctype is KeyboardInterrupt:
            QtWidgets.QApplication.instance().exit()
            return

        if tb is None:
            module_to_patch = "UNKNOWN"
        else:
            module_to_patch = Path(tb.tb_frame.f_code.co_filename).stem
        with patch_log_module(log, module_to_patch):
            log.critical("Uncaught exception:", exc_info=(exctype, value, tb))
            log.critical(
                ""
            )  # log empty message to give a bit of space around traceback

        self.triggered.emit()


def create_interrupt_timer(parent: QtCore.QObject) -> QtCore.QTimer:
    """Interrupt the Qt event loop regularly to let python process signals."""
    timer = QtCore.QTimer(parent)
    timer.interval = 50
    timer.timeout.connect(lambda: None)
    timer.start()
    return timer


def create_request_delay_iterator() -> collections.abc.Iterator[int]:
    """Create an iterator for re-request delays."""
    return itertools.chain(iter([1, 2, 4, 4, 4, 6, 6]), itertools.cycle([10]))


def get_sector_midpoint(address: int) -> tuple[int, int, int]:
    """Get the mid-point of a sector of a system defined by `address`."""
    bit_num = address

    bit_num, layer = _pop_n_lower_bits(bit_num, 3)
    bit_num, low_z_dir = _pop_n_lower_bits(bit_num, 7 - layer)
    bit_num, high_z_dir = _pop_n_lower_bits(bit_num, 7)
    bit_num, low_y_dir = _pop_n_lower_bits(bit_num, 7 - layer)
    bit_num, high_y_dir = _pop_n_lower_bits(bit_num, 6)
    bit_num, low_x_dir = _pop_n_lower_bits(bit_num, 7 - layer)
    bit_num, high_x_dir = _pop_n_lower_bits(bit_num, 7)

    mid_x = (
        high_x_dir * 1280
        + low_x_dir * 2**layer * 10
        + X_OFFSET
        + (10 * (2**layer) // 2)
    )
    mid_y = (
        high_y_dir * 1280
        + low_y_dir * 2**layer * 10
        + Y_OFFSET
        + (10 * (2**layer) // 2)
    )
    mid_z = (
        high_z_dir * 1280
        + low_z_dir * 2**layer * 10
        + Z_OFFSET
        + (10 * (2**layer) // 2)
    )

    return mid_x, mid_y, mid_z


def _pop_n_lower_bits(number: int, n: int) -> tuple[int, int]:
    """Get n lower-order bits from ˙number` and return the number without those bits, and the bits themselves."""
    return number >> n, number & (1 << n) - 1


def cmdr_display_name(name: str | None) -> str:
    """Get the CMDR display name for `name`."""
    if name is not None:
        return name
    else:
        return _("<Main menu>")


def N_(arg: str) -> str:
    """Mark string for translation and return unchanged."""
    return arg
