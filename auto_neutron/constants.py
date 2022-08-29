# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import os
from pathlib import Path
from string import Template

from PySide6 import QtCore
from __feature__ import snake_case, true_property  # noqa: F401

VERSION = "v2.2.1"
APP = "Auto_Neutron"
ORG = "Numerlor"
APPID = f"{ORG}|{APP}|{VERSION}"

SPANSH_API_URL = "https://spansh.co.uk/api"


def get_config_dir() -> Path:
    """Create the config directory constant after the app was initialzied."""
    return Path(
        QtCore.QStandardPaths.writable_location(QtCore.QStandardPaths.AppConfigLocation)
    )


JOURNAL_PATH = (
    Path(os.environ["userprofile"])
    / "Saved Games/Frontier Developments/Elite Dangerous"
)
STATUS_PATH = JOURNAL_PATH / "Status.json"
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

AHK_USER_SCRIPT_TEMPLATE = """\
SetKeyDelay, 50, 50
;bind to open map
send, {map_open_key}
; wait for map to open
sleep, {map_open_wait_delay}
;navigate to second map tab and focus on search field
send, {navigate_right_key}
send, {focus_key}
ClipOld := ClipboardAll
;system is the variable with the injected system
Clipboard := system
sleep, 100
Send, ^v
Clipboard := ClipOld
ClipOld =
SetKeyDelay, 1, 2
send, {submit_key}
"""
