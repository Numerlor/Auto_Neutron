# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import os
import typing
from pathlib import Path
from string import Template

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401

VERSION = "2.0.4"
APP = "Auto_Neutron"
ORG = "Numerlor"
APPID = f"{ORG}|{APP}|{VERSION}"

SPANSH_API_URL = "https://spansh.co.uk/api"


class FrameShiftDrive(typing.NamedTuple):
    """Hold information about a frame shift drive module."""

    _SIZE_CONSTANTS = {2: 2.0, 3: 2.15, 4: 2.3, 5: 2.45, 6: 2.6, 7: 2.75}
    _CLASS_CONSTANTS = {1: 11, 2: 10, 3: 8, 4: 10, 5: 12}
    size: int
    class_: int
    max_fuel_usage: float
    optimal_mass: float

    @property
    def rating_const(self) -> int:
        """Get the linear rating const for the FSD's class rating."""
        return self._CLASS_CONSTANTS[self.class_]

    @property
    def size_const(self) -> float:
        """Get the power constant for the FSD's size."""
        return self._SIZE_CONSTANTS[self.size]


def get_config_dir() -> Path:
    """Create the config directory constant after the app was initialzied."""
    return Path(
        QtCore.QStandardPaths.writable_location(QtCore.QStandardPaths.AppConfigLocation)
    )


FSD_CONSTANTS = {
    "int_hyperdrive_size2_class1": FrameShiftDrive(2, 1, 0.60, 48),
    "int_hyperdrive_size2_class2": FrameShiftDrive(2, 2, 0.60, 54),
    "int_hyperdrive_size2_class3": FrameShiftDrive(2, 3, 0.60, 60),
    "int_hyperdrive_size2_class4": FrameShiftDrive(2, 4, 0.80, 75),
    "int_hyperdrive_size2_class5": FrameShiftDrive(2, 5, 0.90, 90),
    "int_hyperdrive_size3_class1": FrameShiftDrive(3, 1, 1.20, 80),
    "int_hyperdrive_size3_class2": FrameShiftDrive(3, 2, 1.20, 90),
    "int_hyperdrive_size3_class3": FrameShiftDrive(3, 3, 1.20, 100),
    "int_hyperdrive_size3_class4": FrameShiftDrive(3, 4, 1.50, 125),
    "int_hyperdrive_size3_class5": FrameShiftDrive(3, 5, 1.80, 150),
    "int_hyperdrive_size4_class1": FrameShiftDrive(4, 1, 2.00, 280),
    "int_hyperdrive_size4_class2": FrameShiftDrive(4, 2, 2.00, 315),
    "int_hyperdrive_size4_class3": FrameShiftDrive(4, 3, 2.00, 350),
    "int_hyperdrive_size4_class4": FrameShiftDrive(4, 4, 2.50, 438),
    "int_hyperdrive_size4_class5": FrameShiftDrive(4, 5, 3.00, 525),
    "int_hyperdrive_size5_class1": FrameShiftDrive(5, 1, 3.30, 560),
    "int_hyperdrive_size5_class2": FrameShiftDrive(5, 2, 3.30, 630),
    "int_hyperdrive_size5_class3": FrameShiftDrive(5, 3, 3.30, 700),
    "int_hyperdrive_size5_class4": FrameShiftDrive(5, 4, 4.10, 875),
    "int_hyperdrive_size5_class5": FrameShiftDrive(5, 5, 5.00, 1050),
    "int_hyperdrive_size6_class1": FrameShiftDrive(6, 1, 5.30, 960),
    "int_hyperdrive_size6_class2": FrameShiftDrive(6, 2, 5.30, 1080),
    "int_hyperdrive_size6_class3": FrameShiftDrive(6, 3, 5.30, 1200),
    "int_hyperdrive_size6_class4": FrameShiftDrive(6, 4, 6.60, 1500),
    "int_hyperdrive_size6_class5": FrameShiftDrive(6, 5, 8.00, 1800),
    "int_hyperdrive_size7_class1": FrameShiftDrive(7, 1, 8.50, 1440),
    "int_hyperdrive_size7_class2": FrameShiftDrive(7, 2, 8.50, 1620),
    "int_hyperdrive_size7_class3": FrameShiftDrive(7, 3, 8.50, 1800),
    "int_hyperdrive_size7_class4": FrameShiftDrive(7, 4, 10.60, 2250),
    "int_hyperdrive_size7_class5": FrameShiftDrive(7, 5, 12.80, 2700),
}
BOOSTER_CONSTANTS = {
    "int_guardianfsdbooster_size1": 4.0,
    "int_guardianfsdbooster_size2": 6.0,
    "int_guardianfsdbooster_size3": 7.75,
    "int_guardianfsdbooster_size4": 9.25,
    "int_guardianfsdbooster_size5": 10.5,
}

JOURNAL_PATH = (
    Path(os.environ["userprofile"])
    / "Saved Games/Frontier Developments/Elite Dangerous"
)
STATUS_PATH = JOURNAL_PATH / "Status.json"
AHK_PATH = Path(os.environ["PROGRAMW6432"]) / "AutoHotkey/AutoHotkey.exe"
ROUTE_FILE_NAME = "route.csv"
AHK_TEMPLATE = Template(
    """\
stdin := FileOpen("*", "r")

${hotkey}::
    while not stdin.AtEof
    {
        system := Trim(stdin.ReadLine(),"`n ")
    }
    ${user_script}
"""
)
