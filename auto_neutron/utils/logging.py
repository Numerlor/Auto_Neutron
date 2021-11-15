# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import collections.abc
import logging
import os
import typing as t
from contextlib import contextmanager
from types import MethodType

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401

log = logging.getLogger(__name__)

QT_LOG_LEVELS = {
    0: logging.DEBUG,
    4: logging.INFO,
    1: logging.WARNING,
    2: logging.ERROR,
    3: logging.CRITICAL,
}


class UsernameFormatter(logging.Formatter):
    """Redact Windows usernames from logs made using this formatter."""

    os_username = os.environ["USERNAME"]

    def format(self, record: logging.LogRecord) -> str:
        """Redact Windows usernames from `record` message."""
        message = super().format(record)
        if __debug__:
            return message
        return message.replace(f"\\{self.os_username}", "\\USERNAME")


@contextmanager
def patch_log_module(
    logger: logging.Logger, module_name: str
) -> collections.abc.Iterator[None]:
    """Patch logs using `logger` within this context manager to use `module_name` as the module name."""
    original_find_caller = logger.findCaller

    def patched_caller(
        self: logging.Logger, stack_info: bool, stack_level: int
    ) -> tuple[str, int, str, t.Optional[str]]:
        """Patch filename on logs after this was applied to be `module_name`."""
        _, lno, func, sinfo = original_find_caller(stack_info, stack_level)
        return module_name, lno, func, sinfo

    logger.findCaller = MethodType(patched_caller, logger)
    try:
        yield
    finally:
        logger.findCaller = original_find_caller


def init_qt_logging() -> None:
    """Redirect QDebug calls to `logger`."""

    def handler(level: int, _context: QtCore.QMessageLogContext, message: str) -> None:
        with patch_log_module(log, "<Qt>"):
            log.log(QT_LOG_LEVELS[level], message)

    QtCore.qInstallMessageHandler(handler)
