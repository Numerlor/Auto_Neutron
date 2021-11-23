# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

import typing as t
from base64 import b64decode, b64encode
from pathlib import Path

from PySide6.QtCore import QByteArray
from PySide6.QtGui import QFont

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401

from .category_meta import SettingsCategory, SettingsParams


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


def _path_serializer(path: t.Union[None, Path, str]) -> str:
    if path is None:
        return ""
    return str(path)


def _path_deserializer(path_string: str) -> t.Optional[Path]:
    if path_string == "":
        return None
    return Path(path_string)


class Paths(metaclass=SettingsCategory):  # noqa D101
    ahk: t.Optional[Path] = SettingsParams(
        str, "", _path_serializer, _path_deserializer
    )
    csv: t.Optional[Path] = SettingsParams(
        str, "", _path_serializer, _path_deserializer
    )
    alert_sound: t.Union[None, Path, str] = SettingsParams(
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
