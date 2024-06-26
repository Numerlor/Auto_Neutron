# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron.widgets import LogSlider

_SPINBOX_BORDER_STYLESHEET = "border:none;border:1px solid {border_color};border-radius:3px;background:palette(base);"


class _TooltipSliderBase(QtWidgets.QSlider):
    """
    Slider that shows current value in an editable tooltip above the handle.

    `slider_value`, `tooltip_maximum`, and `tooltip_minimum` properties have to be implemented.
    """

    def __init__(self, orientation: QtCore.Qt.Orientation, parent: QtWidgets.QWidget):
        self._finished_init = False
        super().__init__(orientation, parent)
        self._value_spinbox = QtWidgets.QSpinBox(parent)
        self._set_up_spinbox()

        self._tooltip_hide_timer = QtCore.QTimer(self)
        self._tooltip_hide_timer.single_shot_ = True
        self._tooltip_hide_timer.timeout.connect(self._hide_value_tooltip_if_not_hover)

        self.sliderPressed.connect(self._on_press)
        self.sliderReleased.connect(self._on_release)

        self.mouse_tracking = True
        self._mouse_on_handle = False
        self._finished_init = True

    @property
    def slider_value(self) -> int:
        """The value of the slider used for the tooltip."""  # noqa: D401
        raise NotImplementedError

    @slider_value.setter
    def slider_value(self, value: int) -> None:
        """Set the slider's value from the tooltip."""
        raise NotImplementedError

    @property
    def tooltip_maximum(self) -> int:
        """The maximum value for the tooltip."""  # noqa: D401
        raise NotImplementedError

    @property
    def tooltip_minimum(self) -> int:
        """The minimum value for the tooltip."""  # noqa: D401
        raise NotImplementedError

    def _set_up_spinbox(self) -> None:
        """Set up the value spinbox and hide it."""
        self._value_spinbox.install_event_filter(self)

        self._value_spinbox.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._value_spinbox.button_symbols = (
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._value_spinbox.minimum = self.tooltip_minimum
        self._value_spinbox.maximum = self.tooltip_maximum
        self._value_spinbox.style_sheet = _SPINBOX_BORDER_STYLESHEET.format(
            border_color=self.palette.window().color().darker(140).name()
        )
        self._value_spinbox.adjust_size()

        self._value_spinbox.valueChanged.connect(partial(setattr, self, "slider_value"))
        self._value_spinbox.hide()

    def slider_change(self, change: QtWidgets.QAbstractSlider.SliderChange) -> None:
        """Show the tooltip above the slider's handle. If the user is not holding the slider, hide it in 1 second."""
        super().slider_change(change)
        if (
            self._finished_init
            and not self._value_spinbox.focus
            and self.visible
            and change == QtWidgets.QAbstractSlider.SliderChange.SliderValueChange
        ):
            self._display_value_tooltip(start_hide_timer=True)

    def _display_value_tooltip(self, *, start_hide_timer: bool) -> None:
        """Display a value tooltip on top of the slider's handle."""
        option = QtWidgets.QStyleOptionSlider()
        self.init_style_option(option)

        handle_rect = self._handle_rect()
        self._value_spinbox.value = self.slider_value

        mapped_pos = self.map_to_parent(
            QtCore.QPoint(
                handle_rect.left()
                - (self._value_spinbox.rect.width() - handle_rect.width()) / 2,
                handle_rect.top() - self._value_spinbox.rect.height() + 1,
            )
        )
        if mapped_pos.x() < 0:
            mapped_pos.set_x(0)
        elif (
            parent := self.parent_widget()
        ) is not None and mapped_pos.x() + self._value_spinbox.width > parent.width:
            mapped_pos.set_x(self.parent_widget().width - self._value_spinbox.width)

        self._value_spinbox.pos = mapped_pos
        self._value_spinbox.show()
        self._value_spinbox.raise_()
        if start_hide_timer:
            self._tooltip_hide_timer.interval = 1000
            self._tooltip_hide_timer.start()

    def mouse_move_event(self, event: QtGui.QMouseEvent) -> None:
        """Show the value tooltip on hover."""
        super().mouse_move_event(event)
        on_handle = self._handle_rect().contains(event.position().to_point())

        if on_handle and not self._mouse_on_handle:
            self._mouse_on_handle = True
            self._display_value_tooltip(start_hide_timer=False)
        elif not on_handle and self._mouse_on_handle:
            self._mouse_on_handle = False
            if not self._value_spinbox.focus and not self._tooltip_hide_timer.active:
                self._hide_value_tooltip_if_not_hover()

    def leave_event(self, event: QtCore.QEvent) -> None:
        """Hide the value tooltip if the user was hovering over it and the hide timer is not active."""
        super().leave_event(event)
        if self._mouse_on_handle:
            self._mouse_on_handle = False
            if not self._value_spinbox.focus and not self._tooltip_hide_timer.active:
                self._hide_value_tooltip_if_not_hover()

    @QtCore.Slot()
    def _hide_value_tooltip_if_not_hover(self) -> None:
        """Hide the value tooltip if the cursor is not hovering over the handle or the spinbox."""
        mouse_pos = self.map_to_parent(self.map_from_global(QtGui.QCursor.pos()))
        if (
            not self._mouse_on_handle
            and not self._value_spinbox.geometry.contains(mouse_pos)
            and not self.slider_down
        ):
            self._value_spinbox.hide()

    def change_event(self, event: QtCore.QEvent) -> None:
        """Update the tooltip's colors when the palette changes."""
        if event.type() == QtCore.QEvent.Type.PaletteChange:
            self._value_spinbox.style_sheet = _SPINBOX_BORDER_STYLESHEET.format(
                border_color=self.palette.window().color().darker(140).name()
            )
        super().change_event(event)

    @QtCore.Slot()
    def _on_press(self) -> None:
        """Stop the hide timer."""
        self._tooltip_hide_timer.stop()
        self._display_value_tooltip(start_hide_timer=False)

    @QtCore.Slot()
    def _on_release(self) -> None:
        """Start the timer to hide the tooltip in 500ms."""
        self._tooltip_hide_timer.interval = 500
        self._tooltip_hide_timer.start()

    def event_filter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Correctly hide the spinbox on its events."""
        if watched is self._value_spinbox:
            event_type = event.type()
            if event_type is QtCore.QEvent.Type.Leave:
                cursor_pos = QtGui.QCursor.pos()
                handle_rect = self._handle_rect()
                if (
                    not self._value_spinbox.focus
                    and not handle_rect.contains(self.map_from_global(cursor_pos))
                    and not self._tooltip_hide_timer.active
                ):
                    self._value_spinbox.hide()

            elif event_type is QtCore.QEvent.Type.FocusOut:
                self._value_spinbox.hide()

            elif event_type is QtCore.QEvent.Type.KeyRelease:
                key = t.cast("QtGui.QKeyEvent", event).key()
                if key in {QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter}:
                    self._value_spinbox.clear_focus()
                    self._value_spinbox.hide()

        return False

    def _handle_rect(self) -> QtCore.QRect:
        """Get the rect of the handle's current position."""
        option = QtWidgets.QStyleOptionSlider()
        self.init_style_option(option)

        return self.style().sub_control_rect(
            QtWidgets.QStyle.ComplexControl.CC_Slider,
            option,
            QtWidgets.QStyle.SubControl.SC_SliderHandle,
            self,
        )


class TooltipSlider(_TooltipSliderBase):
    """A plain slider with a tooltip."""

    @property
    def slider_value(self) -> int:  # noqa: D102
        return self.value

    @slider_value.setter
    def slider_value(self, value: int) -> None:  # noqa: D102
        self.value = value

    @property
    def tooltip_maximum(self) -> int:  # noqa: D102
        return self.maximum

    @property
    def tooltip_minimum(self) -> int:  # noqa: D102
        return self.minimum

    @property
    def maximum(self) -> int:
        """Return the slider's maximum value."""
        return super().maximum

    @maximum.setter
    def maximum(self, value: int) -> None:
        """Set the slider's maximum value, and update the tooltip's max to the same."""
        super(TooltipSlider, self.__class__).maximum.__set__(self, value)
        self._value_spinbox.maximum = value
        self._value_spinbox.adjust_size()

    @property
    def minimum(self) -> int:
        """Return the slider's minimum value."""
        return super().minimum

    @minimum.setter
    def minimum(self, value: int) -> None:
        """Set the slider's minimum value, and update the tooltip's min to the same."""
        super(TooltipSlider, self.__class__).minimum.__set__(self, value)
        self._value_spinbox.minimum = value


class LogTooltipSlider(_TooltipSliderBase, LogSlider):
    """Logarithmic slider with a tooltip."""

    @property
    def slider_value(self) -> int:  # noqa: D102
        return self.log_value

    @slider_value.setter
    def slider_value(self, value: int) -> None:  # noqa: D102
        self.log_value = value

    @property
    def tooltip_maximum(self) -> int:  # noqa: D102
        return self.log_maximum

    @property
    def tooltip_minimum(self) -> int:  # noqa: D102
        return self.log_minimum

    @property
    def log_maximum(self) -> int:
        """Return the slider's log_maximum value."""
        return super().log_maximum

    @log_maximum.setter
    def log_maximum(self, value: int) -> None:
        """Set the slider's log_maximum value, and update the tooltip's max to the same."""
        super(LogTooltipSlider, self.__class__).log_maximum.fset(self, value)
        self._value_spinbox.maximum = value

    @property
    def log_minimum(self) -> int:
        """Return the slider's log_minimum value."""
        return super().log_minimum

    @log_minimum.setter
    def log_minimum(self, value: int) -> None:
        """Set the slider's log_minimum value, and update the tooltip's min to the same."""
        super(LogTooltipSlider, self.__class__).log_minimum.fset(self, value)
        self._value_spinbox.minimum = value
