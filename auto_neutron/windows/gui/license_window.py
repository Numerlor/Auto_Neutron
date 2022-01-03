# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

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
        self.window_title = "Auto_Neutron " + VERSION

        self.text = QtWidgets.QTextBrowser(self)
        self.text.open_external_links = True

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.contents_margins = QtCore.QMargins(0, 0, 0, 0)
        self.main_layout.add_widget(self.text)
        self.set_layout(self.main_layout)

        self.retranslate()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.text.clear()
        # fmt: off
        self.text.insert_html(
            _("PySide6 Copyright (C) 2015 The Qt Company Ltd.") + "<br><br>"
            + _("Auto_Neutron Copyright (C) 2019 Numerlor") + "<br>"
            + _("Auto_Neutron comes with ABSOLUTELY NO WARRANTY).") + "<br>"
            + _("This is free software, and you are welcome to redistribute it under certain conditions; ")
            + '<a href="https://www.gnu.org/licenses/" style="color: #007bff">click here</a> for details.'
        )
        # fmt: on

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslate()
