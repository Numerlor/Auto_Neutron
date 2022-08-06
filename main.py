# Auto_Neutron
# Copyright (C) 2019 Numerlor
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

from __future__ import annotations

import ctypes
import logging
import sys
from logging import handlers
from pathlib import Path

import babel
from PySide6 import QtGui, QtNetwork, QtWidgets

import auto_neutron.locale
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron import hub, win_theme_change_listener
from auto_neutron.constants import APP, APPID, ORG, VERSION, get_config_dir
from auto_neutron.settings import General, set_settings
from auto_neutron.settings.toml_settings import TOMLSettings
from auto_neutron.utils.file import base_path
from auto_neutron.utils.logging import (
    SessionBackupHandler,
    UsernameFormatter,
    init_qt_logging,
)
from auto_neutron.utils.utils import ExceptionHandler, create_interrupt_timer

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)
app = QtWidgets.QApplication(sys.argv)
app.window_icon = QtGui.QIcon(str(base_path() / "resources/icons_library.ico"))
app.application_name = APP
app.organization_name = ORG
app.set_style("Fusion")

auto_neutron.network_mgr = QtNetwork.QNetworkAccessManager()

# create org and app folders
get_config_dir().mkdir(parents=True, exist_ok=True)

root_logger = logging.getLogger()

log_format = UsernameFormatter(
    "{asctime} | {module:>16} | {levelname:>7} | {message}",
    datefmt="%H:%M:%S",
    style="{",
)
root_logger.setLevel(logging.DEBUG)
if __debug__:
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(log_format)
    root_logger.addHandler(stream_handler)
    qt_interrupt_timer = create_interrupt_timer(app)

    logger_path = Path("logs/log.log")
    logger_path.parent.mkdir(exist_ok=True)
    file_handler = handlers.RotatingFileHandler(
        logger_path, maxBytes=1024 * 1024 // 4, backupCount=3, encoding="utf8"
    )
else:
    file_handler = SessionBackupHandler(
        get_config_dir() / "Auto_Neutron.log", backup_count=2
    )

init_qt_logging()

file_handler.setFormatter(log_format)
root_logger.addHandler(file_handler)

# save traceback to logfile if Exception is raised
ex_handler = ExceptionHandler()
sys.excepthook = ex_handler.handler

set_settings(TOMLSettings((get_config_dir() / "config.toml")))
auto_neutron.locale.set_active_locale(babel.Locale.parse(General.locale))
root_logger.info(f"Starting Auto_Neutron ver {VERSION}")
with win_theme_change_listener.create_listener() as listener:
    hub = hub.Hub(ex_handler, listener)
    sys.exit(app.exec())
