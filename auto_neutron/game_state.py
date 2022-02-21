# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import logging
import typing as t
from functools import partial

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.workers import GameWorker

if t.TYPE_CHECKING:
    from auto_neutron.journal import Journal
    from auto_neutron.route_plots import Plotter, RouteList

log = logging.getLogger(__name__)


class Location(t.NamedTuple):
    """Represents a location of a system and its name."""

    name: str

    x: float
    y: float
    z: float


class PlotterState(QtCore.QObject):
    """Hold the state required for a plotter to function."""

    new_system_signal = QtCore.Signal(str, int)
    route_end_signal = QtCore.Signal(int)
    shut_down_signal = QtCore.Signal()

    def __init__(self, parent: QtCore.QObject):
        super().__init__(parent)
        self._route_index = 0
        self.tail_worker: GameWorker | None = None
        self._active_journal: Journal | None = None
        self._active_route: list | None = None
        self._plotter: Plotter | None = None

    def create_worker_with_route(self, route: RouteList) -> None:
        """
        Set the `tail_worker`'s route to `route`.

        If the worker didn't exist yes, it is created without starting.
        """
        assert self.journal is not None, "Journal must be set first."
        if self.tail_worker is None:
            self.tail_worker = GameWorker(self, route, self.journal)
            if self.plotter is not None:
                self.tail_worker.new_system_index_sig.connect(
                    partial(setattr, self, "route_index")
                )
                self.tail_worker.route_end_sig.connect(self.route_end_signal.emit)
        else:
            self.tail_worker.route = route
        self._active_route = route

    @property
    def route_index(self) -> int:
        """Return the current route index."""
        return self._route_index

    @route_index.setter
    def route_index(self, index: int) -> None:
        """Set the current route index and emit `self.new_system_signal` with the system at it, and the index itself."""
        log.info(f"Setting route_{index=}.")
        self._route_index = index
        self.new_system_signal.emit(self._active_route[index].system, index)

    @property
    def route(self) -> RouteList | None:
        """Return the active route."""
        return self._active_route

    @route.setter
    def route(self, route: RouteList) -> None:
        """Set the active route and update the worker."""
        log.info("Setting new route.")
        self._active_route = route
        self.tail_worker.route = route

    @property
    def plotter(self) -> Plotter | None:
        """Return the active plotter instance."""
        return self._plotter

    @plotter.setter
    def plotter(self, plotter: Plotter) -> None:
        """
        Set the active plotter to `plotter`.

        If a previous plotter exists, stop it before replacing.
        The tail worker is started and has its `new_system_index_sig` connected to the plotter's `update_system` method.
        """
        assert self.journal is not None, "Journal must be set first."
        log.info("Setting new plotter.")
        if self._plotter is not None:
            self._plotter.stop()

        self._plotter = plotter
        self.new_system_signal.connect(self._plotter.update_system)

        if self.tail_worker is not None:
            self.tail_worker.start()
            self.tail_worker.new_system_index_sig.connect(
                partial(setattr, self, "route_index")
            )
            self.tail_worker.route_end_sig.connect(self.route_end_signal.emit)

    @property
    def journal(self) -> Journal | None:
        """Return the active journal instance."""
        return self._active_journal

    @journal.setter
    def journal(self, journal: Journal | None) -> None:
        """
        Set or reset the active journal.

        If a `Journal` instance is passed, it is refreshed.
        In case a plotter is active, a new tail worker from the journal is created and connected to it.
        """
        self._active_journal = journal
        log.info("Setting new journal.")
        if journal is not None:
            journal.shut_down_sig.connect(self.shut_down_signal.emit)
            journal.parse()

            if self._plotter is not None:
                self.tail_worker.stop()
                self.tail_worker = GameWorker(self, self.route, self.journal)
                self.tail_worker.start()
                self.tail_worker.new_system_index_sig.connect(
                    partial(setattr, self, "route_index")
                )
                self.tail_worker.route_end_sig.connect(self.route_end_signal.emit)
        else:
            if self.tail_worker is not None:
                self.tail_worker.stop()
