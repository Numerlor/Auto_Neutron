from __future__ import annotations

import typing as t
from contextlib import suppress
from dataclasses import dataclass
from functools import partial

from PySide6 import QtCore

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron.journal import Journal
from auto_neutron.utils import ExceptionHandler
from auto_neutron.workers import Plotter
from QTest import MainWindow


@dataclass
class ExactPlotRow:
    """One row entry of an exact plot from the Spansh Galaxy Plotter."""

    system: str
    dist: float
    dist_rem: float
    fuel_left: t.Optional[float]
    fuel_used: t.Optional[float]
    refuel: t.Optional[bool]
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
    neutron_star: bool
    jumps: int

    def __eq__(self, other: t.Union[NeutronPlotRow, str]):
        if isinstance(other, str):
            return self.system.lower() == other.lower()
        return super().__eq__(other)


RouteList = t.Union[list[ExactPlotRow], list[NeutronPlotRow]]


class GameWorker(QtCore.QObject):
    """Handle dispatching route signals from the journal's tailer."""

    next_system_sig = QtCore.Signal(str, int)
    route_end_sig = QtCore.Signal()

    def __init__(self, route: RouteList, journal: Journal):
        super().__init__()
        self._generator = journal.tail()
        self._timer = QtCore.QTimer()
        self._timer.interval = 250
        self._timer.timeout.connect(partial(next, self._generator))
        self._stopped = False
        self.route = route
        journal.system_sig.connect(self._emit_next_system)

    def _emit_next_system(self, system_name: str) -> None:
        """Emit the next system in the route and its index, or end of route."""
        with suppress(ValueError):
            new_system_index = self.route.index(system_name) + 1
            try:
                self.next_system_sig.emit(
                    self.route[new_system_index], new_system_index
                )
            except IndexError:
                self.route_end_sig.emit()

    def start(self) -> None:
        """Start the worker to tail the journal file."""
        if self._stopped:
            raise RuntimeError("Can't restart a stopped worker.")
        self._timer.start()

    def stop(self) -> None:
        """Stop the worker from tailing the journal file."""
        self._timer.stop()
        self._generator.close()
        self._stopped = True


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
        self.window.show()
        self.plotter_state = PlotterState()
