# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from functools import partial

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.constants import VERSION
from auto_neutron.settings import General
from auto_neutron.windows.gui.download_confirm_dialog import (
    VersionDownloadConfirmDialogGUI,
)


class VersionDownloadConfirmDialog(VersionDownloadConfirmDialogGUI):
    """
    Prompt the user to skip or download a new release.

    If the user chooses to download, `confirmed_signal` is downloaded.
    """

    confirmed_signal = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget, *, changelog: str, version: str):
        super().__init__(parent)
        self._changelog_browser.markdown = changelog
        self._new_version = version

        self._skip_button.pressed.connect(
            partial(setattr, General, "last_checked_release", version)
        )
        self._skip_button.pressed.connect(self.close)

        self._download_button.pressed.connect(self.confirmed_signal.emit)

        self.retranslate()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self._text_label.text = _("A new release is available: {} -> {}").format(
            VERSION, self._new_version
        )

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslate()
