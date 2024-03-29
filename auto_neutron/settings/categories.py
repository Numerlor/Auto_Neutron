# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

import typing as t
import winreg
from base64 import b64decode, b64encode
from contextlib import suppress
from pathlib import Path

from PySide6.QtCore import QByteArray
from PySide6.QtGui import QFont
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron import Theme
from auto_neutron.constants import AHK_USER_SCRIPT_TEMPLATE

from .category_meta import SettingsCategory, SettingsParams

AHK_DEFAULT_GALAXY_KEY = "{Numpad7}"
AHK_DEFAULT_NAVIGATE_RIGHT_KEY = "e"
AHK_DEFAULT_FOCUS_KEY = "{Space}"
AHK_DEFAULT_SUBMIT_KEY = "{enter}"
AHK_DEFAULT_MAP_WAIT_DELAY = 850


class General(metaclass=SettingsCategory):  # noqa: D101
    save_on_quit: t.Annotated[bool, SettingsParams(True)]
    copy_mode: t.Annotated[bool, SettingsParams(True)]
    last_route_index: t.Annotated[int, SettingsParams(0)]
    locale: t.Annotated[str, SettingsParams("en")]
    last_checked_release: t.Annotated[str, SettingsParams("")]
    loop_routes: t.Annotated[bool, SettingsParams(False)]


class AHK(metaclass=SettingsCategory):  # noqa: D101
    simple_mode: t.Annotated[bool, SettingsParams(True)]
    bind: t.Annotated[str, SettingsParams("F5", fallback_paths=("General.bind",))]
    user_script: t.Annotated[
        str,
        SettingsParams(
            AHK_USER_SCRIPT_TEMPLATE.format(
                map_open_key=AHK_DEFAULT_GALAXY_KEY,
                navigate_right_key=AHK_DEFAULT_NAVIGATE_RIGHT_KEY,
                focus_key=AHK_DEFAULT_FOCUS_KEY,
                submit_key=AHK_DEFAULT_SUBMIT_KEY,
                map_open_wait_delay=AHK_DEFAULT_MAP_WAIT_DELAY,
            ),
            fallback_paths=("General.script",),
        ),
    ]
    map_open_key: t.Annotated[str, SettingsParams(AHK_DEFAULT_GALAXY_KEY)]
    navigate_right_key: t.Annotated[str, SettingsParams(AHK_DEFAULT_NAVIGATE_RIGHT_KEY)]
    focus_key: t.Annotated[str, SettingsParams(AHK_DEFAULT_FOCUS_KEY)]
    submit_key: t.Annotated[str, SettingsParams(AHK_DEFAULT_SUBMIT_KEY)]
    map_open_wait_delay: t.Annotated[int, SettingsParams(AHK_DEFAULT_MAP_WAIT_DELAY)]

    @classmethod
    def get_script(cls) -> str:
        """
        Return the current AHK script.

        If simple mode is enabled, return the filled template, otherwise return the user script.
        """
        if cls.simple_mode:
            return AHK_USER_SCRIPT_TEMPLATE.format(
                map_open_key=cls.map_open_key,
                navigate_right_key=cls.navigate_right_key,
                focus_key=cls.focus_key,
                submit_key=cls.submit_key,
                map_open_wait_delay=cls.map_open_wait_delay,
            )
        else:
            return cls.user_script


def _path_serializer(path: Path | str | None) -> str:
    if path is None:
        return ""
    return str(path)


def _path_deserializer(path_string: str) -> Path | None:
    if path_string == "":
        return None
    return Path(path_string)


_AHK_REG_PATH = r"SOFTWARE\AutoHotkey"


def _ahk_deserializer(path_string: str) -> Path | None:
    """Return Path from `path_string`, to find ahk path from registry if not set."""
    serialized = _path_deserializer(path_string)
    if serialized is None:
        with (
            suppress(FileNotFoundError),
            winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AHK_REG_PATH) as reg_handle,
        ):
            return Path(
                winreg.QueryValueEx(reg_handle, "InstallDir")[0], "AutoHotkey.exe"
            )
        with (
            suppress(FileNotFoundError),
            winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _AHK_REG_PATH) as reg_handle,
        ):
            return Path(
                winreg.QueryValueEx(reg_handle, "InstallDir")[0], "AutoHotkey.exe"
            )
        return None

    return serialized


class Paths(metaclass=SettingsCategory):  # noqa: D101
    ahk: t.Annotated[
        Path | None, SettingsParams("", _path_serializer, _ahk_deserializer)
    ]
    csv: t.Annotated[
        Path | None, SettingsParams("", _path_serializer, _path_deserializer)
    ]
    alert_sound: t.Annotated[
        Path | str | None,
        SettingsParams("", _path_serializer, _path_deserializer),
    ]


def _font_deserializer(val: str) -> QFont:
    font = QFont()
    font.from_string(val)
    return font


class Window(metaclass=SettingsCategory):  # noqa: D101
    geometry: t.Annotated[
        QByteArray,
        SettingsParams(
            "AdnQywADAAAAAAJ/AAAA+QAABDQAAAH9AAACgAAAARgAAAQzAAAB/AAAAAAAAAAAB4AAAAKAAAABGAAABDMAAAH8",
            lambda val: b64encode(val.data()).decode(),
            lambda val: QByteArray(b64decode(val.encode())),
        ),
    ]
    dark_mode: t.Annotated[Theme, SettingsParams(True, None, Theme)]
    autoscroll: t.Annotated[bool, SettingsParams(True)]
    font: t.Annotated[
        QFont,
        SettingsParams(
            "Arial,9,-1,5,700,0,0,0,0,0,0,0,0,0,0,1",
            lambda val: val.to_string(),
            _font_deserializer,
        ),
    ]


class Alerts(metaclass=SettingsCategory):  # noqa: D101
    audio: t.Annotated[bool, SettingsParams(False)]
    visual: t.Annotated[bool, SettingsParams(False)]
    threshold: t.Annotated[int, SettingsParams(150)]
