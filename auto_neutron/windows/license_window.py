# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import sys
import typing as t

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.utils.file import base_path
from auto_neutron.windows.gui.license_window import LicenseWindowGUI

PYTHON_LICENSE_URL = "https://docs.python.org/3.10/license.html"
GNU_LICENSES_URL = "https://www.gnu.org/licenses/"


class LicenseWindow(LicenseWindowGUI):
    """License window displaying the project's and Qt's copyright."""

    def __init__(self, parent: t.Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.about_qt_button.pressed.connect(QtWidgets.QApplication.instance().about_qt)
        self.back_button.pressed.connect(self.retranslate)

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslate()

    def retranslate(self) -> None:
        """Set the text browser text."""
        super().retranslate()
        python_license_file_url = QtCore.QUrl.from_local_file(
            str(base_path() / "LICENSE_PYTHON.md")
        ).url()
        gpl_license_file_url = QtCore.QUrl.from_local_file(
            str(base_path() / "LICENSE.md")
        ).url()
        # fmt: off
        self.text.set_text(
            _("This program uses PySide6:<br>")
            + _("PySide6 Copyright (C) 2015 The Qt Company Ltd.") + "<br><br>"
            + _("This program uses Python and its associated software:<br>")
            + sys.copyright.replace("\n", "<br>") + "<br>"
            + _("Python is licensed under the ") + self.make_hyperlink(_("PSF License Agreement"), python_license_file_url)
            + _(", see ") + self.make_hyperlink(_("docs.python.org/license.html"), PYTHON_LICENSE_URL) + " for more details.<br><br>"
            + _("Auto_Neutron Copyright (C) 2019 Numerlor") + "<br>"
            + _("Auto_Neutron comes with ABSOLUTELY NO WARRANTY).") + "<br>"
            + _("This is free software, and you are welcome to redistribute it under the conditions of the ")
            + self.make_hyperlink("GPLv3 License", gpl_license_file_url) + _(", ") + self.make_hyperlink(_("click here"), GNU_LICENSES_URL) + _(" for more details.")
        )
        # fmt: on

    def make_hyperlink(self, text: str, url: str) -> str:
        """Create a blue-styled hyperlink pointing to `url`, with `text`."""
        return f'<a href="{url}" style="color: #007bff">{text}</a>'
