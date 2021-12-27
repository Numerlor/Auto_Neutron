import enum

from PySide6 import QtNetwork

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401

network_mgr: QtNetwork.QNetworkAccessManager = None


class Theme(enum.IntEnum):
    """The theme to be used by the app."""

    LIGHT_THEME = 0
    OS_THEME = 1
    DARK_THEME = 2
