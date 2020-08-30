# This file is part of Auto_Neutron.
# Copyright (C) 2019-2020  Numerlor


import pickle
from base64 import b64decode, b64encode
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union

from PyQt5.QtCore import QByteArray, QSettings
from PyQt5.QtGui import QFont


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

    The `cls._settings` value must be set to a QSettings object before any access is attempted.

    Each annotated name in the class represents a value in the underlying QSettings category,
    metadata in its `SettingsParams` value that's used when it's accessed or set on the class.

    On access, if the requested name is a setting, its value is fetched from the category given by the class name,
    using the `on_load` callable (if present) to modify the value before it's returned to the user.

    On attribtue setting the same behaviour applies but in reverse.
    The user given value is passed through `on_save` before being passed to the QSettings object.
    Attribute setting without using the `delay_sync` context manager automatically syncs the settings to the ini file.
    """

    def __init__(cls, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any]):
        super().__init__(name, bases, namespace)
        cls._settings: Optional[QSettings] = None
        cls._auto_sync = True

    def __getattribute__(cls, key: str):
        """
        Get an attribute from the class, if the attribute is an annotated setting fetch its value from `cls._settings`.

        If the SettingsParams object of the setting defines an `on_load` callable, the callable is applied to `value`
        before it's returned to the caller..
        """
        getattr_ = super().__getattribute__
        value: SettingsParams = getattr_(key)
        if key in getattr_("__annotations__"):
            settings_val = getattr_("_settings").value(f"{cls.__name__}/{key}", value.default, value.setting_type)
            if value.on_load is not None:
                return value.on_load(settings_val)
            return settings_val
        return value

    def __setattr__(cls, key: str, value: Any):
        """
        Set the attribute of the object, if the attribute is an annotated setting set it on `cls._settings`.

        When setting an attribute of an annotated setting, the actual value of the attribute is left unchanged,
        if `cls._auto_sync` is true, the settings are synced to the file after they're set.

        If the SettingsParams object of the setting defines an `on_save` callable, the callable is applied to `value`
        before it's saved to `cls._settings`.
        """
        if key in cls.__annotations__:
            if super().__getattribute__(key).on_save is not None:
                value = super().__getattribute__(key).on_save(value)
            cls._settings.setValue(f"{cls.__name__}/{key}", value)
            if cls._auto_sync:
                cls._settings.sync()
        else:
            super().__setattr__(key, value)

    @contextmanager
    def delay_sync(cls) -> None:
        """Delay settings sync until the end of the context manager."""
        cls._auto_sync = False
        yield
        cls._auto_sync = True
        cls._settings.sync()


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
            'Clipboard := "|SYSTEMDATA|"\n'
            "sleep, 100\n"
            "Send, ^v\n"
            "Clipboard := ClipOld\n"
            "ClipOld =\n"
            "SetKeyDelay, 1, 2\n"
            "send, {enter}\n"
        )
    )

    last_route: Tuple[int, List[Union[str, float, float, int]]] = SettingsParams(
        str,
        "gASVBwAAAAAAAABLAF2UhpQu",  # (0, [[]])
        lambda val: b64encode(pickle.dumps(val)).decode(),
        lambda val: pickle.loads(b64decode(val.encode()))
    )
    copy_mode: bool = SettingsParams(bool, True)


def _path_serializer(path: Optional[Path]) -> str:
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
    alert_sound: Optional[Path] = SettingsParams(str, "", _path_serializer, _path_deserializer)


class Window(metaclass=SettingsCategory):  # noqa D101
    geometry: QByteArray = SettingsParams(
        str,
        "AdnQywADAAAAAABkAAAAZAAAAmMAAAF7AAAAbAAAAIIAAAJbAAABcwAAAAAAAAAAB4AAAABsAAAAggAAAlsAAAFz",
        lambda val: b64encode(val.data()).decode(),
        lambda val: QByteArray(b64decode(val.encode()))
    )
    dark_mode: bool = SettingsParams(bool, True)
    autoscroll: bool = SettingsParams(bool, True)

    def _font_deserializer(val: str) -> QFont:
        font = QFont()
        font.fromString(val)
        return font

    font: QFont = SettingsParams(
        str,
        'Arial,-1,-1,5,50,0,0,0,0,0',
        lambda val: val.toString(),
        _font_deserializer
    )
    del _font_deserializer


class Alerts(metaclass=SettingsCategory):  # noqa D101
    audio: bool = SettingsParams(bool, False)
    visual: bool = SettingsParams(bool, False)
    threshold: int = SettingsParams(int, 150)


def set_settings(settings: QSettings) -> None:
    """Set the `settings` object for all categories."""
    for category in General, Paths, Window, Alerts:
        category._settings = settings
