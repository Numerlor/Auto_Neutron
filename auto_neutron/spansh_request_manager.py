# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import collections.abc
import logging
import typing as t
from functools import partial

from PySide6 import QtCore, QtNetwork

from auto_neutron.constants import SPANSH_API_URL
from auto_neutron.route import Route
from auto_neutron.utils.network import (
    NetworkError,
    json_from_network_req,
    make_network_request,
)

log = logging.getLogger(__name__)


class SpanshRequestManager:
    """Track the current reply from Spansh to allow termination."""

    def __init__(self, parent: QtCore.QObject):
        self._current_reply = None
        self._delay_timer = QtCore.QTimer(parent)
        self._delay_timer.setSingleShot(True)
        self._timer_connection = None

    def _reply_callback(
        self,
        reply: QtNetwork.QNetworkReply,
        *,
        result_callback: collections.abc.Callable[[Route], t.Any],
        error_callback: collections.abc.Callable[[str], t.Any],
        delay_iterator: collections.abc.Iterator[float],
        result_decode_func: collections.abc.Callable[[dict], t.Any],
    ) -> None:
        """
        Handle a Spansh job reply, wait until a response is available and then return `result_decode_func` applied to it.

        When re-requesting for status, wait for `delay` seconds,
        where `delay` is the next value from the `delay_iterator`
        """
        self._reset_reply()
        try:
            job_response = json_from_network_req(reply, json_error_key="error")
        except NetworkError as e:
            if (
                e.error_type
                is QtNetwork.QNetworkReply.NetworkError.OperationCanceledError
            ):
                return

            if e.reply_error is not None:
                error_callback(
                    _("Received error from Spansh: {}").format(e.reply_error)
                )
            else:
                error_callback(
                    e.error_message
                )  # Fall back to Qt error message if spansh didn't respond
        except Exception as e:
            error_callback(str(e))
            log.error(e)
        else:
            if job_response.get("status") == "queued":
                sec_delay = next(delay_iterator)
                log.debug(f"Re-requesting queued job result in {sec_delay} seconds.")
                self._delay_timer.setInterval(sec_delay * 1000)
                self._timer_connection = self._delay_timer.timeout.connect(
                    partial(
                        self.make_request,
                        SPANSH_API_URL + "/results/" + job_response["job"],
                        finished_callback=partial(
                            self._reply_callback,
                            result_callback=result_callback,
                            error_callback=error_callback,
                            delay_iterator=delay_iterator,
                            result_decode_func=result_decode_func,
                        ),
                    ),
                )
                self._delay_timer.start()
            elif job_response.get("result") is not None:
                log.debug("Received finished neutron job.")
                result_callback(result_decode_func(job_response["result"]))
            else:
                error_callback(_("Received invalid response from Spansh."))

    def route_decode_callback(
        self,
        *args: t.Any,
        route_type: type[Route],
        **kwargs: t.Any,
    ) -> None:
        """Callback to call the result callback with an ExactPlotRow list."""  # noqa: D401
        self._reply_callback(*args, **kwargs, result_decode_func=route_type.from_json)

    def make_request(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Make a network request and store the result reply."""
        self.abort()
        self._current_reply = make_network_request(*args, **kwargs)

    def abort(self) -> None:
        """Abort the current request."""
        if self._current_reply is not None:
            log.debug("Aborting route plot request.")
            self._current_reply.abort()
        self._delay_timer.stop()

    def _reset_reply(self) -> None:
        """Reset the reply and disconnect the timer from the old make_request."""
        self._current_reply = None
        if self._timer_connection is not None:
            self._delay_timer.disconnect(self._timer_connection)
