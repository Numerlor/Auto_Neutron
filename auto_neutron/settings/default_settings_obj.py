# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from .toml_settings import TOMLSettings

_settings: TOMLSettings | None = None


def set_settings(settings: TOMLSettings) -> None:
    """Set the `settings` object for all categories."""
    global _settings
    _settings = settings


def get_settings() -> TOMLSettings:
    """Return the set default settings object, `set_settings` should be called before.."""
    assert _settings is not None, "Global settings uninitialized."
    return _settings
