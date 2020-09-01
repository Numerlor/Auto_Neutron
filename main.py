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
import logging
import sys
from logging import handlers
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets

from auto_neutron import hub
from auto_neutron.constants import APP, APPID, ORG
from auto_neutron.settings import set_settings
from auto_neutron.utils import ExceptionHandler, init_qt_logging


# https://stackoverflow.com/a/44352931
def resource_path(relative_path: Path) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    base_path = getattr(sys, '_MEIPASS', Path(__file__).parent / "resources")
    return str(base_path / relative_path)


ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)
app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon(resource_path(Path("icons_library.ico"))))
app.setApplicationName(APP)
app.setOrganizationName(ORG)

path = Path(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation))
# create org and app folders
path.mkdir(parents=True, exist_ok=True)

log_format = logging.Formatter("{asctime} | {module:>7} | {levelname} | {message}", datefmt="%H:%M:%S", style="{")
file_handler = handlers.RotatingFileHandler(path / "log.log", maxBytes=2*1024*1024, backupCount=3, encoding="utf8")
file_handler.setFormatter(log_format)

root_logger = logging.getLogger()
root_logger.addHandler(file_handler)
if __debug__:
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(log_format)
    root_logger.addHandler(stream_handler)
    root_logger.setLevel(logging.DEBUG)
else:
    root_logger.setLevel(logging.INFO)
init_qt_logging(root_logger)

# save traceback to logfile if Exception is raised
ex_handler = ExceptionHandler(path / "traceback.log")
sys.excepthook = ex_handler.handler

set_settings(QtCore.QSettings(str(path / "config.ini"), QtCore.QSettings.IniFormat))
ui = hub.Hub(ex_handler)
ui.startup()
sys.exit(app.exec_())
