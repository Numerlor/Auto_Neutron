# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import sys
import textwrap

from PySide6 import QtCore, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron.utils.file import base_path

from ..utils.utils import get_application
from .gui.license_window import LicenseWindowGUI

PYTHON_LICENSE_URL = "https://docs.python.org/3.10/license.html"
PYSIDE6_LICENSES_URL = "https://doc.qt.io/qtforpython/licenses.html"
QT_LICENSING_URL = "https://www.qt.io/licensing/"
GNU_LICENSES_URL = "https://www.gnu.org/licenses/"


class LicenseWindow(LicenseWindowGUI):
    """License window displaying the project's and Qt's copyright."""

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.about_qt_button.pressed.connect(get_application().about_qt)
        self.back_button.pressed.connect(self.retranslate)
        self.back_button.pressed.connect(
            lambda: setattr(self.back_button, "enabled", False)  # noqa: B010
        )
        self.text.sourceChanged.connect(
            lambda: setattr(self.back_button, "enabled", True)  # noqa: B010
        )

        self.back_button.enabled = False

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.retranslate()

    @QtCore.Slot()
    def retranslate(self) -> None:
        """Set the text browser text."""
        super().retranslate()
        self.text.markdown = self.get_license_text()

    def get_license_text(self) -> str:
        """Create the license text to show to the user."""
        python_license_url = (
            base_path() / "third_party_licenses/LICENSE_Python.md"
        ).as_uri()
        tomli_w_license_url = (
            base_path() / "third_party_licenses/LICENSE_tomli-w.md"
        ).as_uri()
        babel_license_url = (
            base_path() / "third_party_licenses/LICENSE_babel.md"
        ).as_uri()
        breeze_license_url = (
            base_path() / "third_party_licenses/LICENSE_breeze-icons.md"
        ).as_uri()
        pyside_license_url = (
            base_path() / "third_party_licenses/LICENSE_PySide6.md"
        ).as_uri()
        more_itertools_license_url = (
            base_path() / "third_party_licenses/LICENSE_more-itertools.md"
        ).as_uri()
        auto_neutron_license_url = (base_path() / "LICENSE.md").as_uri()

        return textwrap.dedent(
            _(
                """\
        Auto_Neutron Copyright (C) 2019 Numerlor\\
        This program comes with ABSOLUTELY NO WARRANTY.\\
        This is free software, and you are welcome to redistribute it
        under conditions of the {auto_neutron_hyperlink}, see {gnu_licenses_hyperlink} for more details.


        Auto_Neutron uses the following software:
        -   PySide6 Copyright (C) 2015 The Qt Company Ltd. under the {pyside_hyperlink}, see {pyside_licenses_hyperlink} and {qt_licenses_hyperlink} for more details.
        - Qt6, click the "About Qt" button for more details.
        - tomli-w licensed under the {tomli_w_hyperlink}
        - more-itertools licensed under the {more_itertools_hyperlink}
        - babel licensed under the {babel_hyperlink}
        - Python and its associated software:

        {python_copyright_notice}
          Python is licensed under the {psf_license_agreement_hyperlink}, see {python_licenses_hyperlink} for more details.

        And The Breeze Icons Theme Copyright (C) 2014 Uri Herrera <uri_herrera@nitrux.in> and others, licensed under the {breeze_hyperlink}.
        """
            )
        ).format(
            auto_neutron_hyperlink=self.make_hyperlink(
                _("GPLv3 license"), auto_neutron_license_url
            ),
            gnu_licenses_hyperlink=self.make_hyperlink(
                _("gnu.org/licenses"), GNU_LICENSES_URL
            ),
            pyside_hyperlink=self.make_hyperlink(
                _("GPLv3 license"), pyside_license_url
            ),
            pyside_licenses_hyperlink=self.make_hyperlink(
                _("doc.qt.io/qtforpython/licenses.html"), PYSIDE6_LICENSES_URL
            ),
            qt_licenses_hyperlink=self.make_hyperlink(
                _("qt.io/licensing/"), QT_LICENSING_URL
            ),
            tomli_w_hyperlink=self.make_hyperlink(
                _("MIT license"), tomli_w_license_url
            ),
            more_itertools_hyperlink=self.make_hyperlink(
                _("MIT license"), more_itertools_license_url
            ),
            babel_hyperlink=self.make_hyperlink(
                _("3-Clause BSD license"), babel_license_url
            ),
            psf_license_agreement_hyperlink=self.make_hyperlink(
                _("PSF License Agreement"), python_license_url
            ),
            python_licenses_hyperlink=self.make_hyperlink(
                _("docs.python.org/license.html"), PYTHON_LICENSE_URL
            ),
            breeze_hyperlink=self.make_hyperlink(
                _("LGPLv3 license"), breeze_license_url
            ),
            python_copyright_notice=textwrap.indent(sys.copyright.strip(), " " * 6),
        )

    def make_hyperlink(self, text: str, url: str) -> str:
        """Create a hyperlink pointing to `url`, with `text`."""
        return f"[{text}]({url})"
