# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t
from dataclasses import dataclass

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.journal import GameState, Journal
from auto_neutron.utils.route_plots import RouteList
from auto_neutron.utils.utils import ExceptionHandler
from auto_neutron.workers import GameWorker, Plotter
from QTest import MainWindow


@dataclass
class PlotterState:
    """Hold the state required for a plotter to function."""

    tail_worker: t.Optional[GameWorker] = None
    _active_journal: t.Optional[Journal] = None
    _active_route: t.Optional[list] = None
    _plotter: t.Optional[Plotter] = None

    def create_worker_with_route(self, route: RouteList) -> None:
        """
        Set the `tail_worker`'s route to `route`.

        If the worker didn't exist yes, it is created without starting.
        """
        if self.tail_worker is None:
            self.tail_worker = GameWorker(route, self.journal)
        else:
            self.tail_worker.route = route

    @property
    def game_state(self) -> GameState:
        """Return the active journal's game state, or None if there is no journal."""
        return getattr(self.journal, "game_state", None)

    @property
    def plotter(self) -> Plotter:
        """Return the active plotter instance."""
        return self._plotter

    @plotter.setter
    def plotter(self, plotter: Plotter) -> None:
        """
        Set the active plotter to `plotter`.

        If a previous plotter exists, stop it before replacing.
        The tail worker is started and has its `next_system_sig` connected to the plotter's `update_system` method.
        """
        if self._plotter is not None:
            self._plotter.stop()

        self._plotter = plotter

        self.tail_worker.start()
        self.tail_worker.next_system_sig.connect(self._plotter.update_system)

    @property
    def journal(self) -> Journal:
        """Return the active journal instance."""
        return self._active_journal

    @journal.setter
    def journal(self, journal: t.Optional[Journal]) -> None:
        """
        Set or reset the active journal.

        If a `Journal` instance is passed, it is refreshed.
        In case a plotter is active, a new tail worker from the journal is created and connected to it.
        """
        if journal is not None:
            journal.reload()
            if self._plotter is not None:
                self.tail_worker.stop()
                self.tail_worker = GameWorker(self.tail_worker.route, self.journal)
                self.tail_worker.start()
                self.tail_worker.next_system_sig.connect(self._plotter.update_system)
        self._active_journal = journal


class Hub(QtCore.QObject):
    """Manage windows and communication between them and workers."""

    def __init__(self, exception_handler: ExceptionHandler):
        super().__init__()
        self.window = MainWindow()
        self.window.insert_row([1, 1, 1, 1])
        self.window.show()
        self.plotter_state = PlotterState()
