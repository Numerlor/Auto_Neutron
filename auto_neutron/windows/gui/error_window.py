# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401


class ErrorWindowGUI(QtWidgets.QDialog):
    """Display basic information to informate user on how to report bug after an error has occurred."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.info_label = QtWidgets.QLabel("An unexpected error has occurred")
        font = QtGui.QFont()
        font.set_point_size(15)
        self.info_label.font = font

        self.text_browser = QtWidgets.QTextBrowser()
        issues_html = "https://github.com/Numerlor/Auto_Neutron/issues/new"
        log_path = QtCore.QStandardPaths.writable_location(
            QtCore.QStandardPaths.AppConfigLocation
        )
        self.text_browser.insert_html(
            f"Please make sure to report the bug at <br>"
            f'<a href="{issues_html}" style="color: #007bff">{issues_html}</a>,<br>'
            f"including the latest log file from<br>"
            f' <a href="{Path(log_path)}" style="color: #007bff">{log_path}</a>'
        )
        self.text_browser.open_external_links = True

        self.button_layout = QtWidgets.QHBoxLayout()
        self.quit_button = QtWidgets.QPushButton("Quit")
        self.save_button = QtWidgets.QPushButton("Save route")
        self.quit_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.save_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self.button_layout.add_widget(self.save_button)
        self.button_layout.add_widget(self.quit_button)

        self.main_layout.add_widget(self.info_label)
        self.main_layout.add_widget(self.text_browser)
        self.main_layout.add_layout(self.button_layout)
        self.set_modal(True)
