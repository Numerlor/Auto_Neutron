import os
import sys
import traceback

from PyQt5 import QtWidgets, QtCore, QtGui

import MainWindows
from temp_saves import write_image, write_templates


# https://stackoverflow.com/a/44352931
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class ExceptionHandler:
    def __init__(self, output_file):
        self.path = output_file

    def handler(self, exctype, value, tb):
        f = open(self.path, 'w')
        exception_lines = traceback.format_exception(exctype, value, tb)
        for line in exception_lines:
            f.write(line)
        f.flush()
        f.close()
        sys.__excepthook__(exctype, value, tb)
        sys.exit(1)


if __name__ == "__main__":
    # save ahk templates and file image to temp file
    write_templates(resource_path("ahk"))
    write_image(resource_path(""))
    QtCore.QCoreApplication.setApplicationName("Auto Neutron")
    QtCore.QCoreApplication.setOrganizationName("Numerlor")
    path = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)
    # save traceback to logfile if Exception is raised
    sys.excepthook = ExceptionHandler(path + "/traceback.log").handler
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(resource_path("image.png")))
    # create org and app folders if not found
    if not os.path.isdir(path):
        if not os.path.isdir(path[:path.rfind("/")]):
            os.mkdir(path[:path.rfind("/")])
        os.mkdir(path)
    settings = QtCore.QSettings(path + "/config.ini", QtCore.QSettings.IniFormat)
    ui = MainWindows.Ui_MainWindow(settings, app)
    ui.setupUi()
    sys.exit(app.exec_())
