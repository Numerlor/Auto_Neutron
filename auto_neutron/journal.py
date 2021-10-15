# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import collections.abc
import json
from pathlib import Path

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401


class Journal(QtCore.QObject):
    """Keep track of a journal file and the state of the game from it."""

    system_sig = QtCore.Signal(str)
    loadout_sig = QtCore.Signal(dict)
    shut_down_sig = QtCore.Signal()

    def __init__(self, journal_path: Path):
        super().__init__()
        self.path = journal_path

    def tail(self) -> collections.abc.Generator[None, None, None]:
        """Follow a log file, and emit signals for new systems, loadout changes and game shut down."""
        with self.path.open(encoding="utf8") as journal_file:
            journal_file.seek(0, 2)
            while True:
                if line := journal_file.readline():
                    entry = json.loads(line)
                    if entry["event"] == "FSDJump":
                        self.system_sig.emit(entry["StarSystem"])

                    elif entry["event"] == "Loadout":
                        self.loadout_sig.emit(entry)

                    elif entry["event"] == "Shutdown":
                        self.shut_down_sig.emit()
                else:
                    yield

    def reload(self) -> None:
        """Parse the whole journal file and emit signals with the appropriate data."""
        loadout = None
        location = None
        shut_down = False
        with self.path.open(encoding="utf8") as journal_file:
            for line in journal_file:
                entry = json.loads(line)
                if entry["event"] == "Loadout":
                    loadout = entry
                elif entry["event"] == "Location":
                    location = entry["StarSystem"]
                elif entry["event"] == "Shutdown":
                    shut_down = True

        if location is not None:
            self.system_sig.emit(location)
        if loadout is not None:
            self.loadout_sig.emit(loadout)
        self.shut_down_sig.emit(shut_down)
