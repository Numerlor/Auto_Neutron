# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from __future__ import annotations

import typing as t
from dataclasses import dataclass
from functools import partial

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.ship import Ship
from auto_neutron.workers import GameWorker

if t.TYPE_CHECKING:
    from auto_neutron.journal import Journal
    from auto_neutron.route_plots import Plotter, RouteList


class Location(t.NamedTuple):
    """Represents a location of a system and its name."""

    name: str

    x: float
    y: float
    z: float


@dataclass
class GameState:
    """
    Hold the current state of the game from the journal.

    The state can be updated through assignments on public attributes or using `update_from_loadout`.
    """

    ship = Ship()
    shut_down: t.Optional[bool] = None
    location: t.Optional[Location] = None


class PlotterState(QtCore.QObject):
    """Hold the state required for a plotter to function."""

    new_system_signal = QtCore.Signal(str, int)

    def __init__(self, game_state: GameState):
        super().__init__()
        self._game_state = game_state

        self._route_index = 0
        self.tail_worker: t.Optional[GameWorker] = None
        self._active_journal: t.Optional[Journal] = None
        self._active_route: t.Optional[list] = None
        self._plotter: t.Optional[Plotter] = None

    def create_worker_with_route(self, route: RouteList) -> None:
        """
        Set the `tail_worker`'s route to `route`.

        If the worker didn't exist yes, it is created without starting.
        """
        if self.tail_worker is None:
            self.tail_worker = GameWorker(route, self.journal)
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
        self._route_index = index
        self.new_system_signal.emit(self._active_route[index].system, index)

    @property
    def plotter(self) -> Plotter:
        """Return the active plotter instance."""
        return self._plotter

    @plotter.setter
    def plotter(self, plotter: Plotter) -> None:
        """
        Set the active plotter to `plotter`.

        If a previous plotter exists, stop it before replacing.
        The tail worker is started and has its `new_system_index_sig` connected to the plotter's `update_system` method.
        """
        if self._plotter is not None:
            self._plotter.stop()

        self._plotter = plotter
        self.new_system_signal.connect(self._plotter.update_system)

        self.tail_worker.start()
        self.tail_worker.new_system_index_sig.connect(
            partial(setattr, self, "route_index")
        )

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
            self._game_state.shut_down = False
            journal.shut_down_sig.connect(
                partial(setattr, self._game_state, "shut_down", True)
            )
            journal.system_sig.connect(partial(setattr, self._game_state, "location"))
            journal.loadout_sig.connect(self._game_state.ship.update_from_loadout)
            journal.reload()
            if self._plotter is not None:
                self.tail_worker.stop()
                self.tail_worker = GameWorker(self.tail_worker.route, self.journal)
                self.tail_worker.start()
                self.tail_worker.new_system_index_sig.connect(
                    self.tail_worker.new_system_index_sig.connect(
                        partial(setattr, self, "route_index")
                    )
                )
        self._active_journal = journal
