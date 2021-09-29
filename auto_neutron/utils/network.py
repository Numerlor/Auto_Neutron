# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import collections.abc
import typing as t
import urllib.parse
from functools import partial

from PySide6 import QtCore, QtNetwork

import auto_neutron

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401


class NetworkError(Exception):
    """Raised for Qt network errors."""


def make_network_request(
    url: str,
    *,
    params: dict = {},  # noqa B006
    callback: collections.abc.Callable[[QtNetwork.QNetworkReply], t.Any],
) -> None:
    """Make a network request to `url` with a `params` query and connect its reply to `callback`."""
    if params:
        url += "?" + urllib.parse.urlencode(params)
    qurl = QtCore.QUrl(url)
    request = QtNetwork.QNetworkRequest(qurl)
    reply = auto_neutron.network_mgr.get(request)
    reply.finished.connect(partial(callback, reply))


def data_from_network_req(reply: QtNetwork.QNetworkReply) -> bytes:
    """Decode bytes from the `QNetworkReply` object or raise an error on failed requests."""
    try:
        if reply.error() is QtNetwork.QNetworkReply.NetworkError.NoError:
            return reply.read_all().data()
        else:
            raise NetworkError(reply.error_string())
    finally:
        reply.delete_later()
