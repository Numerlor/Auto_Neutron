# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

import os
import typing
from pathlib import Path

VERSION = "2.0a1"
APP = "Auto_Neutron"
ORG = "Numerlor"
APPID = f"{ORG}|{APP}|{VERSION}"


class FrameShiftDrive(typing.NamedTuple):
    """Hold information about a frame shift drive module."""

    max_fuel_usage: float
    optimal_mass: float
    size_const: float
    rating_const: int


FSD_CONSTANTS = {
    "int_hyperdrive_size2_class1": FrameShiftDrive(0.60, 48, 2.00, 11),
    "int_hyperdrive_size2_class2": FrameShiftDrive(0.60, 54, 2.00, 10),
    "int_hyperdrive_size2_class3": FrameShiftDrive(0.60, 60, 2.00, 8),
    "int_hyperdrive_size2_class4": FrameShiftDrive(0.80, 75, 2.00, 10),
    "int_hyperdrive_size2_class5": FrameShiftDrive(0.90, 90, 2.00, 12),
    "int_hyperdrive_size3_class1": FrameShiftDrive(1.20, 80, 2.15, 11),
    "int_hyperdrive_size3_class2": FrameShiftDrive(1.20, 90, 2.15, 10),
    "int_hyperdrive_size3_class3": FrameShiftDrive(1.20, 100, 2.15, 8),
    "int_hyperdrive_size3_class4": FrameShiftDrive(1.50, 125, 2.15, 10),
    "int_hyperdrive_size3_class5": FrameShiftDrive(1.80, 150, 2.15, 12),
    "int_hyperdrive_size4_class1": FrameShiftDrive(2.00, 280, 2.30, 11),
    "int_hyperdrive_size4_class2": FrameShiftDrive(2.00, 315, 2.30, 10),
    "int_hyperdrive_size4_class3": FrameShiftDrive(2.00, 350, 2.30, 8),
    "int_hyperdrive_size4_class4": FrameShiftDrive(2.50, 438, 2.30, 10),
    "int_hyperdrive_size4_class5": FrameShiftDrive(3.00, 525, 2.30, 12),
    "int_hyperdrive_size5_class1": FrameShiftDrive(3.30, 560, 2.45, 11),
    "int_hyperdrive_size5_class2": FrameShiftDrive(3.30, 630, 2.45, 10),
    "int_hyperdrive_size5_class3": FrameShiftDrive(3.30, 700, 2.45, 8),
    "int_hyperdrive_size5_class4": FrameShiftDrive(4.10, 875, 2.45, 10),
    "int_hyperdrive_size5_class5": FrameShiftDrive(5.00, 1050, 2.45, 12),
    "int_hyperdrive_size6_class1": FrameShiftDrive(5.30, 960, 2.60, 11),
    "int_hyperdrive_size6_class2": FrameShiftDrive(5.30, 1080, 2.60, 10),
    "int_hyperdrive_size6_class3": FrameShiftDrive(5.30, 1200, 2.60, 8),
    "int_hyperdrive_size6_class4": FrameShiftDrive(6.60, 1500, 2.60, 10),
    "int_hyperdrive_size6_class5": FrameShiftDrive(8.00, 1800, 2.60, 12),
    "int_hyperdrive_size7_class1": FrameShiftDrive(8.50, 1440, 2.75, 11),
    "int_hyperdrive_size7_class2": FrameShiftDrive(8.50, 1620, 2.75, 10),
    "int_hyperdrive_size7_class3": FrameShiftDrive(8.50, 1800, 2.75, 8),
    "int_hyperdrive_size7_class4": FrameShiftDrive(10.60, 2250, 2.75, 10),
    "int_hyperdrive_size7_class5": FrameShiftDrive(12.80, 2700, 2.75, 12),
}
BOOSTER_CONSTANTS = {
    "int_guardianfsdbooster_size1": 4.0,
    "int_guardianfsdbooster_size2": 6.0,
    "int_guardianfsdbooster_size3": 7.75,
    "int_guardianfsdbooster_size4": 9.25,
    "int_guardianfsdbooster_size5": 10.5,
}

# Constant until localization is figured out.
LAST_JOURNALS_TEXT = ("Last journal", "Second to last", "Third to last")

JPATH = (
    Path(os.environ["userprofile"])
    / "Saved Games/Frontier Developments/Elite Dangerous"
)
STATUS_PATH = (
    Path(os.environ["userprofile"])
    / "Saved Games/Frontier Developments/Elite Dangerous/Status.json"
)
AHK_PATH = Path(os.environ["PROGRAMW6432"]) / "AutoHotkey/AutoHotkey.exe"
