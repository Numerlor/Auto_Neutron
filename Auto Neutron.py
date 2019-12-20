import ctypes
import sys
import traceback
from pathlib import Path

from PyQt5 import QtWidgets, QtCore, QtGui

import hub
from appinfo import APP, ORG, APPID
from settings import Settings

# https://stackoverflow.com/a/44352931
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', Path(__file__).absolute().parent)
    return str(base_path / relative_path)


class ExceptionHandler(QtCore.QObject):
    traceback_sig = QtCore.pyqtSignal(list)

    def __init__(self, output_file):
        super().__init__()
        self.path = output_file
        self.cleared = False

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

        self.traceback_sig.emit(exc)


if __name__ == "__main__":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APPID)
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(resource_path(Path("icons/icons_library.ico"))))
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
