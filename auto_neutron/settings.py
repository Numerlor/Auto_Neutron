# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

import collections.abc
import pickle  # noqa S403
from base64 import b64decode, b64encode
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, NamedTuple, Optional, Union

from PySide6.QtCore import QByteArray, QSettings
from PySide6.QtGui import QFont

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401

__all__ = ["General", "Paths", "Window", "Alerts", "set_settings"]

_settings: Optional[QSettings] = None


def set_settings(settings: QSettings) -> None:
    """Set the `settings` object for all categories."""
    global _settings
    _settings = settings


def get_settings() -> QSettings:
    return _settings


class SettingsParams(NamedTuple):
    """
    Metadata for a setting in `SettingsCategory`.

    `settings_type` contains the tpye under which QSetting saved the object
    `default` is the default value of the setting
    `on_save` is a callable that's applied before an user given value is saved
    `on_load` is a callable that's applied before a value from settings is returned to the user
    """

    setting_type: type
    default: Any
    on_save: Optional[Callable[[Any], Any]] = None
    on_load: Optional[Callable[[Any], Any]] = None


class SettingsCategory(type):
    """
    Create a class representing a category from a QSettings ini file.

    An example class would look like this:

    >>> class Category(metaclass=SettingsCategory):
    ...     setting1: type = SettingsParams(..., ...)
    ...     setting2: type = SettingsParams(..., ..., ..., ...)
    ...

    A QSettings object must be set through `set_settings` before any access is attempted.

    Each annotated name in the class represents a value in the underlying QSettings category,
    metadata in its `SettingsParams` value that's used when it's accessed or set on the class.

    On access, if the requested name is a setting, its value is fetched from the category given by the class name,
    using the `on_load` callable (if present) to modify the value before it's returned to the user.

    On attribtue setting the same behaviour applies but in reverse.
    The user given value is passed through `on_save` before being passed to the QSettings object.
    Attribute setting without using the `delay_sync` context manager automatically syncs the settings to the ini file.

    A `settings_getter` kwarg can be specified when creating a new class to a function which returns the settings
    object to be used by the class.
    """

    def __new__(
        metacls,
        *args,
        settings_getter: collections.abc.Callable[[], QSettings] = get_settings,
        **kwargs,
    ):
        obj = super().__new__(metacls, *args, **kwargs)
        obj._settings_getter = settings_getter
        return obj

    def __init__(cls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]):
        super().__init__(name, bases, namespace)
        cls._auto_sync = True

    def __getattribute__(cls, key: str):
        """
        If the attribute is an annotated setting, fetch its value from the class' settings instead of the class itself.

        If the SettingsParams object of the setting defines an `on_load` callable, the callable is applied to `value`
        before it's returned to the caller.
        """
        getattr_ = super().__getattribute__
        value: SettingsParams = getattr_(key)
        if key in getattr_("__annotations__"):
            settings_val = cls._settings_getter().value(
                f"{cls.__name__}/{key}", value.default, value.setting_type
            )
            if value.on_load is not None:
                return value.on_load(settings_val)
            return settings_val
        return value

    def __setattr__(cls, key: str, value: Any):
        """
        Set the attribute of the object, if the attribute is an annotated setting set it on `_settings`.

        When setting an attribute of an annotated setting, the actual value of the attribute is left unchanged,
        if `cls._auto_sync` is true, the settings are synced to the file after they're set.

        If the SettingsParams object of the setting defines an `on_save` callable, the callable is applied to `value`
        before it's saved to the class' settings.
        """
        if key in cls.__annotations__:
            if super().__getattribute__(key).on_save is not None:
                value = super().__getattribute__(key).on_save(value)
            cls._settings_getter().set_value(f"{cls.__name__}/{key}", value)
            if cls._auto_sync:
                cls._settings_getter().sync()
        else:
            super().__setattr__(key, value)

    @contextmanager
    def delay_sync(cls) -> None:
        """Delay settings sync until the end of the context manager."""
        cls._auto_sync = False
        yield
        cls._auto_sync = True
        cls._settings_getter().sync()


class General(metaclass=SettingsCategory):  # noqa D101
    save_on_quit: bool = SettingsParams(bool, True)
    bind: str = SettingsParams(str, "F5")
    script: str = SettingsParams(
        str,
        (
            "SetKeyDelay, 50, 50\n"
            ";bind to open map\n"
            "send, {Numpad7}\n"
            "; wait for map to open\n"
            "sleep, 850\n"
            ";navigate to second map tab and focus on search field\n"
            "send, e\n"
            "send, {Space}\n"
            "ClipOld := ClipboardAll\n"
            ";system is the variable with the injected system\n"
            "Clipboard := system\n"
            "sleep, 100\n"
            "Send, ^v\n"
            "Clipboard := ClipOld\n"
            "ClipOld =\n"
            "SetKeyDelay, 1, 2\n"
            "send, {enter}\n"
        ),
    )
    copy_mode: bool = SettingsParams(bool, True)
    last_route_index: int = SettingsParams(int, 0)


def _path_serializer(path: Union[None, Path, str]) -> str:
    if path is None:
        return ""
    return str(path)


def _path_deserializer(path_string: str) -> Optional[Path]:
    if path_string == "":
        return None
    return Path(path_string)


class Paths(metaclass=SettingsCategory):  # noqa D101
    ahk: Optional[Path] = SettingsParams(str, "", _path_serializer, _path_deserializer)
    csv: Optional[Path] = SettingsParams(str, "", _path_serializer, _path_deserializer)
    alert_sound: Union[None, Path, str] = SettingsParams(
        str, "", _path_serializer, _path_deserializer
    )


def _font_deserializer(val: str) -> QFont:
    font = QFont()
    font.from_string(val)
    return font


class Window(metaclass=SettingsCategory):  # noqa D101
    geometry: QByteArray = SettingsParams(
        str,
        "AdnQywADAAAAAAJ/AAAA+QAABDQAAAH9AAACgAAAARgAAAQzAAAB/AAAAAAAAAAAB4AAAAKAAAABGAAABDMAAAH8",
        lambda val: b64encode(val.data()).decode(),
        lambda val: QByteArray(b64decode(val.encode())),
    )
    dark_mode: bool = SettingsParams(bool, True)
    autoscroll: bool = SettingsParams(bool, True)
    font: QFont = SettingsParams(
        str,
        "Arial,9,-1,5,700,0,0,0,0,0,0,0,0,0,0,1",
        lambda val: val.to_string(),
        _font_deserializer,
    )


class Alerts(metaclass=SettingsCategory):  # noqa D101
    audio: bool = SettingsParams(bool, False)
    visual: bool = SettingsParams(bool, False)
    threshold: int = SettingsParams(int, 150)
