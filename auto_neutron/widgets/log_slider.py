# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

import math

from PySide6 import QtCore, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401


class LogSlider(QtWidgets.QSlider):
    """
    A logarithmic slider.

    The `valueChanged` signal is emitted with the current step instead of the log adjusted value.
    """

    log_value_changed = QtCore.Signal(int)

    def __init__(self, *args, steps: int = 500, **kwargs):
        super().__init__(*args, **kwargs)
        self._log_min = 0
        self._log_max = 1_000_000
        self._log_value = 0
        self._manual_set = False
        self._last_val = None

        self.minimum = 0
        self.maximum = steps
        self.valueChanged.connect(self._on_value_changed)

    @property
    def log_value(self) -> int:
        """The current value selected by the slider."""  # noqa: D401
        if self._last_val != self.value:
            # Update value if the slider's position changed.
            # The class can't rely purely on the valueChanged connection
            # because this may run between the update and when the event loop actually handles the slots.
            self._log_value = self._log_value_from_slider_pos()
        self._last_val = self.value
        return self._log_value

    @log_value.setter
    def log_value(self, value: int) -> None:
        """Set the current value to `value`."""
        # Prevent slider's valueChanged from rewriting `log_value` when `log_value` is set,
        # as it'll be emitted after self.value is assigned here.
        self._manual_set = True
        self._log_value = value
        log_min = math.log1p(self._log_min)
        log_max = math.log1p(self._log_max)

        scale = (log_max - log_min) / self.steps
        self.value = self._last_val = round((math.log1p(value) - log_min) / scale)

    @property
    def log_maximum(self) -> int:
        """The maximum value on the slider."""  # noqa: D401
        return self._log_max

    @log_maximum.setter
    def log_maximum(self, value: int) -> None:
        """
        Set the maximum value to `value`.

        If the set value differs from the new one, emit the log_value_changed signal.
        """
        if self.log_maximum != value:
            self._log_max = value
            self.log_value = self.log_value
            self._on_value_changed()

    @property
    def log_minimum(self) -> int:
        """The minimum value on the slider."""  # noqa: D401
        return self._log_min

    @log_minimum.setter
    def log_minimum(self, value: int) -> None:
        """
        Set the minimum value to `value`.

        If the set value differs from the new one, emit the log_value_changed signal.
        """
        if self.log_minimum != value:
            self._log_min = value
            self.log_value = self.log_value
            self._on_value_changed()

    @property
    def steps(self) -> int:
        """Number of steps on the slider."""  # noqa: D401
        return self.maximum

    @steps.setter
    def steps(self, step_count: int) -> None:
        """Set the number of steps on the slider."""
        self.maximum = step_count

    def _log_value_from_slider_pos(self) -> int:
        log_min = math.log1p(self._log_min)
        log_max = math.log1p(self._log_max)

        scale = (log_max - log_min) / self.steps

        return round(math.e ** (log_min + scale * self.value) - 1)

    def _on_value_changed(self) -> None:
        if not self._manual_set:
            # Only update from slider position if the slider was moved, not when assigned directly to `log_value`.
            self._log_value = self._log_value_from_slider_pos()
        self._manual_set = False
        self.log_value_changed.emit(self._log_value)
