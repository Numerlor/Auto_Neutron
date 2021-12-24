# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401


class TooltipSlider(QtWidgets.QSlider):
    """Slider that shows current value in an editable tooltip above the handle."""

    def __init__(self, orientation: QtCore.Qt.Orientation, parent: QtWidgets.QWidget):
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

    def _set_up_spinbox(self) -> None:
        """Set up the value spinbox and hide it."""
        self._value_spinbox.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self._value_spinbox.button_symbols = QtWidgets.QAbstractSpinBox.NoButtons
        self._value_spinbox.minimum = self.minimum
        self._value_spinbox.maximum = self.maximum
        self._value_spinbox.style_sheet = (
            "border:none;border:1px solid #282828;border-radius:3px;background:#181818;"
        )
        self._value_spinbox.adjust_size()
        self._value_spinbox.hide()

        base_leave_event = self._value_spinbox.leave_event

        def hide_on_leave(event: QtCore.QEvent) -> None:
            base_leave_event(event)
            cursor_pos = QtGui.QCursor.pos()
            handle_rect = self._handle_rect()
            if not self._value_spinbox.focus and not handle_rect.contains(
                self.map_from_global(cursor_pos)
            ):
                self._value_spinbox.hide()

        self._value_spinbox.leave_event = hide_on_leave

        base_key_release_event = self._value_spinbox.key_release_event

        def hide_on_confirm(event: QtGui.QKeyEvent) -> None:
            key = event.key()
            if key == QtCore.Qt.Key.Key_Return or key == QtCore.Qt.Key.Key_Enter:
                self._value_spinbox.clear_focus()
                self._value_spinbox.hide()
            else:
                base_key_release_event(event)

        self._value_spinbox.key_release_event = hide_on_confirm

        base_focus_out_event = self._value_spinbox.focus_out_event

        def hide_on_focus_out(event: QtGui.QFocusEvent) -> None:
            base_focus_out_event(event)
            self._value_spinbox.hide()

        self._value_spinbox.focus_out_event = hide_on_focus_out

        self._value_spinbox.valueChanged.connect(partial(setattr, self, "value"))

    def slider_change(self, change: QtWidgets.QAbstractSlider.SliderChange) -> None:
        """Show the tooltip above the slider's handle. If the user is not holding the slider, hide it in 1 second."""
        super().slider_change(change)
        if (
            not self._value_spinbox.focus
            and change == QtWidgets.QAbstractSlider.SliderChange.SliderValueChange
        ):
            self._display_value_tooltip(start_hide_timer=True)

    def _display_value_tooltip(self, *, start_hide_timer: bool) -> None:
        """Display a value tooltip on top of the slider's handle."""
        option = QtWidgets.QStyleOptionSlider()
        self.init_style_option(option)

        handle_rect = self._handle_rect()
        self._value_spinbox.value = self.value
        self._value_spinbox.pos = self.map_to_parent(
            QtCore.QPoint(
                handle_rect.left()
                - (self._value_spinbox.rect.width() - handle_rect.width()) / 2,
                handle_rect.top() - self._value_spinbox.rect.height() + 1,
            )
        )
        self._value_spinbox.show()
        if start_hide_timer:
            self._tooltip_hide_timer.interval = 1000
            self._tooltip_hide_timer.start()

    def mouse_move_event(self, event: QtGui.QMouseEvent) -> None:
        """Show the value tooltip on hover."""
        super().mouse_move_event(event)
        on_handle = self._handle_rect().contains(event.pos())

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

    def _hide_value_tooltip_if_not_hover(self) -> None:
        """Hide the value tooltip if the cursor is not hovering over the handle or the spinbox."""
        mouse_pos = self.map_to_parent(self.map_from_global(QtGui.QCursor.pos()))
        if not self._mouse_on_handle and not self._value_spinbox.geometry.contains(
            mouse_pos
        ):
            self._value_spinbox.hide()

    def _on_press(self) -> None:
        """Stop the hide timer."""
        self._tooltip_hide_timer.stop()
        self._display_value_tooltip(start_hide_timer=False)

    def _on_release(self) -> None:
        """Start the timer to hide the tooltip in 500ms."""
        self._tooltip_hide_timer.interval = 500
        self._tooltip_hide_timer.start()

    def _handle_rect(self) -> QtCore.QRect:
        """Get the rect of the handle's current position."""
        option = QtWidgets.QStyleOptionSlider()
        self.init_style_option(option)

        return self.style().sub_control_rect(
            QtWidgets.QStyle.CC_Slider,
            option,
            QtWidgets.QStyle.SC_SliderHandle,
            self,
        )

    @property
    def maximum(self) -> int:
        """Return the slider's maximum value."""
        return super().maximum

    @maximum.setter
    def maximum(self, value: int) -> None:
        """Set the slider's maximum value."""
        super(self.__class__, self.__class__).maximum.__set__(self, value)
        self._value_spinbox.maximum = value
        self._value_spinbox.adjust_size()

    @property
    def minimum(self) -> int:
        """Return the slider's minimum value."""
        return super().minimum

    @minimum.setter
    def minimum(self, value: int) -> None:
        """Set the slider's minimum value."""
        super(self.__class__, self.__class__).minimum.__set__(self, value)
        self._value_spinbox.minimum = value
