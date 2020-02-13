# Auto_Neutron
# Copyright (C) 2019-2020 Numerlor
#
# Auto_Neutron is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Auto_Neutron is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Auto_Neutron.  If not, see <https://www.gnu.org/licenses/>.

import ctypes
import sys
import traceback
from os import PathLike
from pathlib import Path

from PyQt5 import QtWidgets, QtCore, QtGui

from auto_neutron import hub
from auto_neutron.constants import APP, ORG, APPID
from auto_neutron.settings import Settings


# https://stackoverflow.com/a/44352931
def resource_path(relative_path: Path) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    base_path = getattr(sys, '_MEIPASS', Path(__file__).parent / "resources")
    return str(base_path / relative_path)


class ExceptionHandler(QtCore.QObject):
    """Handles exceptions when linked to sys.excepthook."""

    traceback_sig = QtCore.pyqtSignal(list)

    def __init__(self, output_file: PathLike):
        super().__init__()
        self.path = output_file
        self.cleared = False

    def handler(self, exctype, value, tb) -> None:  # noqa TYP001
        """
        Logs exceptions to `self.path` and sends a signal to open error window.

        `self.path` is truncated on the first exception,
        newlines are added if multiple exceptions occur.
        """
        exc = traceback.format_exception(exctype, value, tb)
        with open(self.path, 'a') as f:
            if not self.cleared:
                # clear file on first traceback
                f.seek(0)
                f.truncate()
                self.cleared = True
            else:
                # insert spacing newline
                exc.insert(0, "\n")
            f.write("".join(exc))

        sys.__excepthook__(exctype, value, tb)

        self.traceback_sig.emit(exc)


if __name__ == "__main__":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(resource_path(Path("icons_library.ico"))))
    app.setApplicationName(APP)
    app.setOrganizationName(ORG)

    path = Path(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation))
    # save traceback to logfile if Exception is raised
    ex_handler = ExceptionHandler(path / "traceback.log")
    sys.excepthook = ex_handler.handler
    # create org and app folders
    path.mkdir(parents=True, exist_ok=True)
    settings = Settings(path)
    ui = hub.Hub(settings, ex_handler)
    ui.startup()
    sys.exit(app.exec_())
