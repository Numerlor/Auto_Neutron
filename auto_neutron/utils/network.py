# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import json
import logging
import typing as t
import urllib.parse
from functools import partial

from PySide6 import QtCore, QtNetwork

import auto_neutron

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401

if t.TYPE_CHECKING:
    import collections.abc

log = logging.getLogger(__name__)


class NetworkError(Exception):
    """Raised for Qt network errors."""

    def __init__(self, qt_error: str, reply_error: t.Optional[str]):
        self.error_message = qt_error
        self.reply_error = reply_error
        super().__init__(qt_error, reply_error)


def make_network_request(
    url: str,
    *,
    params: dict = {},  # noqa B006
    finished_callback: collections.abc.Callable[[QtNetwork.QNetworkReply], t.Any],
) -> QtNetwork.QNetworkReply:
    """Make a network request to `url` with a `params` query and connect its reply to `callback`."""
    log.debug(f"Sending request to {url} with {params=}")
    if params:
        url += "?" + urllib.parse.urlencode(params)
    qurl = QtCore.QUrl(url)
    request = QtNetwork.QNetworkRequest(qurl)
    reply = auto_neutron.network_mgr.get(request)
    reply.finished.connect(partial(finished_callback, reply))

    return reply


def json_from_network_req(
    reply: QtNetwork.QNetworkReply, *, json_error_key: str
) -> dict:
    """Decode bytes from the `QNetworkReply` object or raise an error on failed requests."""
    try:
        if reply.error() is QtNetwork.QNetworkReply.NetworkError.NoError:
            return json.loads(reply.read_all().data())
        else:
            text_response = reply.read_all().data()
            if text_response:
                reply_error = json.loads(text_response)[json_error_key]
            else:
                reply_error = None
            raise NetworkError(reply.error_string(), reply_error)
    finally:
        reply.delete_later()
