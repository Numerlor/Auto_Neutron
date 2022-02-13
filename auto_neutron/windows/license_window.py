# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import sys
import textwrap
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
        self.text.markdown = self.get_license_text()

    def get_license_text(self) -> str:
        """Create the license text to show to the user."""
        python_license_url = (base_path() / "resources/LICENSE_PYTHON.md").as_uri()
        mit_license_url = (base_path() / "resources/LICENSE_MIT.md").as_uri()
        bsd3_license_url = (base_path() / "resources/LICENSE_BSD_3_Clause.md").as_uri()
        gpl_license_url = (base_path() / "LICENSE.md").as_uri()

        return textwrap.dedent(
            _(
                """\
        Auto_Neutron Copyright (C) 2019 Numerlor\\
        This program comes with ABSOLUTELY NO WARRANTY.\\
        This is free software, and you are welcome to redistribute it
        under conditions of the {gplv3_hyperlink}, see {gnu_licenses_hyperlink} for more details.


        Auto_Neutron uses the following software:
        - PySide6 Copyright (C) 2015 The Qt Company Ltd. under the {gplv3_hyperlink}
        - tomli, and tomli-w under the {mit_hyperlink}
        - babel under the {bsd_3_clause_hyperlink}
        - Python and its associated software:

        {python_copyright_notice}
          Python is licensed under the {psf_license_agreement_hyperlink}, see {python_licenses_hyperlink} for more details
        """
            )
        ).format(
            gplv3_hyperlink=self.make_hyperlink(_("GPLv3 license"), gpl_license_url),
            gnu_licenses_hyperlink=self.make_hyperlink(
                _("gnu.org/licenses"), GNU_LICENSES_URL
            ),
            psf_license_agreement_hyperlink=self.make_hyperlink(
                _("PSF License Agreement"), python_license_url
            ),
            python_licenses_hyperlink=self.make_hyperlink(
                _("docs.python.org/license.html"), PYTHON_LICENSE_URL
            ),
            mit_hyperlink=self.make_hyperlink(_("MIT license"), mit_license_url),
            bsd_3_clause_hyperlink=self.make_hyperlink(
                _("3-Clause BSD license"), bsd3_license_url
            ),
            python_copyright_notice=textwrap.indent(sys.copyright.strip(), " " * 6),
        )

    def make_hyperlink(self, text: str, url: str) -> str:
        """Create a blue-styled hyperlink pointing to `url`, with `text`."""
        return f'<a href="{url}" style="color: #007bff">{text}</a>'
