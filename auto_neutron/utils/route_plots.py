# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from __future__ import annotations

import collections.abc
import logging
import typing as t
from dataclasses import dataclass
from functools import partial

from PySide6 import QtCore, QtNetwork

# noinspection PyUnresolvedReferences
# Can't use true_property because QTimer's single_shot method turns into a property for is_single_shot
from __feature__ import snake_case  # noqa F401
from auto_neutron.constants import SPANSH_API_URL
from auto_neutron.utils.network import json_from_network_req, make_network_request

log = logging.getLogger(__name__)


@dataclass
class ExactPlotRow:
    """One row entry of an exact plot from the Spansh Galaxy Plotter."""

    system: str
    dist: float
    dist_rem: float
    refuel: bool
    neutron_star: bool

    def __eq__(self, other: t.Union[ExactPlotRow, str]):
        if isinstance(other, str):
            return self.system.lower() == other.lower()
        return super().__eq__(other)


@dataclass
class NeutronPlotRow:
    """One row entry of an exact plot from the Spansh Neutron Router."""

    system: str
    dist_to_arrival: float
    dist_rem: float
    jumps: int

    def __eq__(self, other: t.Union[NeutronPlotRow, str]):
        if isinstance(other, str):
            return self.system.lower() == other.lower()
        return super().__eq__(other)


RouteList = t.Union[list[ExactPlotRow], list[NeutronPlotRow]]


def _spansh_job_callback(
    reply: QtNetwork.QNetworkReply,
    *,
    result_callback: collections.abc.Callable[[list[NeutronPlotRow]], t.Any],
    delay_iterator: collections.abc.Iterator[float],
    result_decode_func: collections.abc.Callable[[dict], t.Any],
) -> None:
    """
    Handle a Spansh job reply, wait until a response is available and then return `result_decode_func` applied to it.

    When re-requesting for status, wait for `delay` seconds,
    where `delay` is the next value from the `delay_iterator`
    """
    job_response = json_from_network_req(reply)
    if job_response.get("status") == "queued":
        sec_delay = next(delay_iterator)
        log.debug(f"Re-requesting queued job result in {sec_delay} seconds.")
        QtCore.QTimer.single_shot(
            sec_delay * 1000,
            partial(
                make_network_request,
                SPANSH_API_URL + "/results/" + job_response["job"],
                reply_callback=partial(
                    _spansh_job_callback,
                    result_callback=result_callback,
                    delay_iterator=delay_iterator,
                    result_decode_func=result_decode_func,
                ),
            ),
        )
    elif job_response.get("result") is not None:
        log.debug("Received finished neutron job.")
        result_callback(result_decode_func(job_response["result"]))
    else:
        raise RuntimeError(
            "Received invalid JSON response from Spansh neutron route.",
            job_response,
        )


def _decode_neutron_result(result: dict) -> list[NeutronPlotRow]:
    return [
        NeutronPlotRow(
            row["system"],
            row["distance_jumped"],
            row["distance_left"],
            row["jumps"],
        )
        for row in result["system_jumps"]
    ]


spansh_neutron_callback = partial(
    _spansh_job_callback, result_decode_func=_decode_neutron_result
)
