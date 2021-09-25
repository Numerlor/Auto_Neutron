import abc
import typing as t

from PySide6 import QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401


class Plotter(abc.ABC):
    """Provide the base interface for a game plotter."""

    def __init__(self, start_system: t.Optional[str] = None):
        if start_system is not None:
            self.update_system(start_system)

    @abc.abstractmethod
    def update_system(self, system: str, system_index: t.Optional[int] = None) -> t.Any:
        """Update the plotter with the given system."""
        ...

    def stop(self) -> t.Any:
        """Stop the plotter."""
        ...


class CopyPlotter(Plotter):
    """Plot by copying given systems on the route into the clipboard."""

    def update_system(self, system: str, system_index: t.Optional[int] = None) -> None:
        """Set the system clipboard to `system`."""
        QtWidgets.QApplication.clipboard().set_text(system)
