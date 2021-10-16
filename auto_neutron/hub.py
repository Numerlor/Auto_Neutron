# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t
from dataclasses import dataclass
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron import settings
from auto_neutron.journal import Journal
from auto_neutron.route_plots import Plotter, RouteList
from auto_neutron.ship import Ship
from auto_neutron.utils.utils import ExceptionHandler
from auto_neutron.workers import GameWorker
from QTest import MainWindow


@dataclass
class GameState:
    """
    Hold the current state of the game from the journal.

    The state can be updated through assignments on public attributes or using `update_from_loadout`.
    """

    ship = Ship()
    shut_down: bool = None
    location: str = None


class PlotterState:
    """Hold the state required for a plotter to function."""

    def __init__(self, game_state: GameState):
        self._game_state = game_state

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
                self.tail_worker.next_system_sig.connect(self._plotter.update_system)
        self._active_journal = journal


class Hub(QtCore.QObject):
    """Manage windows and communication between them and workers."""

    def __init__(self, exception_handler: ExceptionHandler):
        super().__init__()
        self.window = MainWindow()
        self.window.insert_row([1, 1, 1, 1])
        self.window.show()
        self.game_state = GameState()

        self.plotter_state = PlotterState(self.game_state)

        set_theme()


def set_theme() -> None:
    """Set the app's theme depending on the user's preferences."""
    app = QtWidgets.QApplication.instance()

    if settings.Window.dark_mode:
        p = QtGui.QPalette()
        p.set_color(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
        p.set_color(QtGui.QPalette.WindowText, QtGui.QColor(247, 247, 247))
        p.set_color(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        p.set_color(QtGui.QPalette.Text, QtGui.QColor(247, 247, 247))
        p.set_color(QtGui.QPalette.Button, QtGui.QColor(60, 60, 60))
        p.set_color(QtGui.QPalette.AlternateBase, QtGui.QColor(45, 45, 45))
        p.set_color(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        p.set_color(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        p.set_color(
            QtGui.QPalette.Disabled, QtGui.QPalette.Light, QtGui.QColor(0, 0, 0)
        )
        p.set_color(
            QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(110, 110, 100)
        )
    else:
        p = app.style().standardPalette()
    app.set_palette(p)
