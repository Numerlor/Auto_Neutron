import os
import sys

import ctypes
import traceback
from PyQt5 import QtWidgets, QtCore, QtGui

import hub
import popups
from appinfo import APP, ORG, APPID


# https://stackoverflow.com/a/44352931
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class ExceptionHandler:

    def __init__(self, output_file):
        self.path = output_file
        self.cleared = False
        self.w = popups.CrashPop()

    def handler(self, exctype, value, tb):
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

        self.w.add_traceback(exc)
        self.w.show()


if __name__ == "__main__":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(resource_path("icons/icons_library.ico")))
    app.setApplicationName(APP)
    app.setOrganizationName(ORG)

    path = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)
    # save traceback to logfile if Exception is raised
    sys.excepthook = ExceptionHandler(path + "/traceback.log").handler
    # create org and app folders if not found
    if not os.path.isdir(path):
        if not os.path.isdir(path[:path.rfind("/")]):
            os.mkdir(path[:path.rfind("/")])
        os.mkdir(path)
    settings = QtCore.QSettings(path + "/config.ini", QtCore.QSettings.IniFormat)
    ui = hub.Hub(settings)
    ui.startup()
    sys.exit(app.exec_())
