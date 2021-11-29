# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import typing as t

from PySide6.QtCore import QSettings

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401

_settings: t.Optional[QSettings] = None


def set_settings(settings: QSettings) -> None:
    """Set the `settings` object for all categories."""
    global _settings
    _settings = settings


def get_settings() -> QSettings:
    """Return the set default settings object, `set_settings` should be called before.."""
    assert _settings is not None, "Global settings uninitialized."
    return _settings
