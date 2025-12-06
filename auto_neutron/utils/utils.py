# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import itertools
import logging
import sys
import typing as t

from PySide6 import QtCore, QtWidgets

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
        """Log the raised exception, and emit `traceback_sig` with the formatted exception."""
        if exctype is KeyboardInterrupt:
            get_application().exit()
            return

        log.critical("Uncaught exception:", exc_info=(exctype, value, tb))

        self.triggered.emit()


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


def intern_list(list_: list[str]) -> list[str]:
    """Intern all strings in `list_`."""
    for index, string_to_intern in enumerate(list_):
        list_[index] = sys.intern(string_to_intern)
    return list_


_app_instance = None


def get_application() -> QtWidgets.QApplication:
    """Get the application's instance."""
    global _app_instance
    if _app_instance is None:
        _app_instance = QtWidgets.QApplication.instance()
        assert _app_instance is not None
    return t.cast(QtWidgets.QApplication, _app_instance)
