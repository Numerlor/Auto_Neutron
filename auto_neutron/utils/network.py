# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import json
import logging
import typing as t
import urllib.parse
from functools import partial

from PySide6 import QtCore, QtNetwork

import auto_neutron
from auto_neutron.constants import APP, VERSION

if t.TYPE_CHECKING:
    import collections.abc

log = logging.getLogger(__name__)


class NetworkError(Exception):
    """Raised for Qt network errors."""

    def __init__(
        self,
        error_type: QtNetwork.QNetworkReply.NetworkError,
        qt_error: str,
        reply_error: str | None,
    ):
        self.error_message = qt_error
        self.reply_error = reply_error
        self.error_type = error_type
        super().__init__(qt_error, reply_error)


def make_network_request(
    url: str,
    *,
    params: collections.abc.Mapping = {},  # noqa: B006
    finished_callback: collections.abc.Callable[[QtNetwork.QNetworkReply], t.Any],
) -> QtNetwork.QNetworkReply:
    """Make a network request to `url` with a `params` query and connect its reply to `finished_callback`."""
    log.debug(f"Sending request to {url} with {params=}")
    if params:
        url += "?" + urllib.parse.urlencode(params)
    qurl = QtCore.QUrl(url)
    request = QtNetwork.QNetworkRequest(qurl)
    request.setHeader(
        QtNetwork.QNetworkRequest.KnownHeaders.UserAgentHeader, f"{APP}/{VERSION}"
    )
    reply = auto_neutron.network_mgr.get(request)
    reply.finished.connect(partial(finished_callback, reply))

    return reply


def post_request(
    url: str,
    *,
    json_: collections.abc.Mapping = {},  # noqa: B006
    finished_callback: collections.abc.Callable[[QtNetwork.QNetworkReply], t.Any],
) -> QtNetwork.QNetworkReply:
    """Make a post request to `url` with `json_` as its body. Connect its reply to `finished_callback`."""
    qurl = QtCore.QUrl(url)
    request = QtNetwork.QNetworkRequest(qurl)
    request.setHeader(
        QtNetwork.QNetworkRequest.KnownHeaders.UserAgentHeader, f"{APP}/{VERSION}"
    )
    request.setHeader(
        QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
    )
    reply = auto_neutron.network_mgr.post(
        request,
        json.dumps(json_).encode(),
    )
    reply.finished.connect(partial(finished_callback, reply))

    return reply


def json_from_network_req(
    reply: QtNetwork.QNetworkReply, *, json_error_key: str | None = None
) -> dict:
    """Decode bytes from the `QNetworkReply` object or raise an error on failed requests."""
    try:
        if reply.error() is QtNetwork.QNetworkReply.NetworkError.NoError:
            return json.loads(reply.readAll().data())

        elif (
            reply.error() is QtNetwork.QNetworkReply.NetworkError.OperationCanceledError
        ):
            raise NetworkError(reply.error(), reply.errorString(), None)

        else:
            text_response = reply.readAll().data()
            if text_response:
                if json_error_key is not None:
                    reply_error = json.loads(text_response)[json_error_key]
                else:
                    reply_error = text_response
            else:
                reply_error = None
            raise NetworkError(reply.error(), reply.errorString(), reply_error)
    finally:
        reply.deleteLater()
