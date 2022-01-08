# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t

from PySide6 import QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.windows.gui.license_window import LicenseWindowGUI


class LicenseWindow(LicenseWindowGUI):
    """License window displaying the project's and Qt's copyright."""

    def __init__(self, parent: t.Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.about_qt_button.pressed.connect(QtWidgets.QApplication.instance().about_qt)
