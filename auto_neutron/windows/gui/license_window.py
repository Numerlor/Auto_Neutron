# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import typing as t

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.constants import VERSION


class LicenseWindow(QtWidgets.QDialog):
    """Window for license information."""

    def __init__(self, parent: t.Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.set_fixed_size(350, 175)
        self.set_window_flag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.set_attribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.window_title = "Auto Neutron " + VERSION

        self.text = QtWidgets.QTextBrowser(self)
        self.text.open_external_links = True

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.contents_margins = QtCore.QMargins(0, 0, 0, 0)
        self.main_layout.add_widget(self.text)
        self.set_layout(self.main_layout)

        self.text.insert_html(
            "PySide6 Copyright (C) 2015 The Qt Company Ltd.<br><br>"
            "Auto_Neutron Copyright (C) 2019, 2021 Numerlor<br><br>"
            "Auto_Neutron comes with ABSOLUTELY NO WARRANTY.<br>"
            "This is free software, and you are welcome to redistribute it under certain conditions; "
            '<a href="https://www.gnu.org/licenses/" style="color: #007bff">click here</a> for details.'
        )

        self.show()