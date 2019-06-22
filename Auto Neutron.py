import sys
import os

from PyQt5 import QtWidgets, QtCore, QtGui

from temp_saves import write_image, write_templates

import MainWindows


# https://stackoverflow.com/a/44352931
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    # save ahk templates and file image to temp file
    write_templates(resource_path("ahk"))
    write_image(resource_path(""))
    QtCore.QCoreApplication.setApplicationName("Auto Neutron")
    QtCore.QCoreApplication.setOrganizationName("Numerlor")
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(resource_path("image.png")))
    path = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)
    # create org and app folders if not found
    if not os.path.isdir(path):
        if not os.path.isdir(path[:path.rfind("/")]):
            os.mkdir(path[:path.rfind("/")])
        os.mkdir(path)
    settings = QtCore.QSettings(path + "/config.ini", QtCore.QSettings.IniFormat)
    ui = MainWindows.Ui_MainWindow(settings, app)
    ui.setupUi()
    sys.exit(app.exec_())
