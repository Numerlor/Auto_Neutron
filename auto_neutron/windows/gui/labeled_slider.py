# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

from PySide6 import QtCore, QtGui, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401


class LabeledSlider(QtWidgets.QSlider):
    """Slider that shows current value in a boxed label above the handle."""

    def __init__(
        self, orientation: QtCore.Qt.OtherFocusReason, parent: QtWidgets.QWidget
    ):
        super().__init__(orientation, parent)
        self._value_label = QtWidgets.QLabel(parent)
        self._value_label.frame_shape = QtWidgets.QFrame.StyledPanel
        self._value_label.frame_shadow = QtWidgets.QFrame.Raised
        self._value_label.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self._value_label.auto_fill_background = True
        self._value_label.hide()

        self._label_hide_timer = QtCore.QTimer(self)
        self._label_hide_timer.single_shot_ = True
        self._label_hide_timer.timeout.connect(self._hide_value_label_if_not_hover)

        self.sliderPressed.connect(self._on_press)
        self.sliderReleased.connect(self._on_release)

        self.mouse_tracking = True
        self._mouse_on_handle = False

    def slider_change(self, change: QtWidgets.QAbstractSlider.SliderChange) -> None:
        """Show the label above the slider's handle. If the user is not holding the slider, hide it in 1 second."""
        super().slider_change(change)
        if change == QtWidgets.QAbstractSlider.SliderChange.SliderValueChange:
            self._display_value_tooltip(start_hide_timer=True)

    def _display_value_tooltip(self, *, start_hide_timer: bool) -> None:
        """Display a value tooltip on top of the slider's handle."""
        option = QtWidgets.QStyleOptionSlider()
        self.init_style_option(option)

        handle_rect = self.style().sub_control_rect(
            QtWidgets.QStyle.CC_Slider,
            option,
            QtWidgets.QStyle.SC_SliderHandle,
            self,
        )
        self._value_label.text = str(self.value)
        self._value_label.adjust_size()
        new_rect = QtCore.QRect(
            self.map_to_parent(
                QtCore.QPoint(
                    handle_rect.left()
                    - (self._value_label.rect.width() - handle_rect.width()) / 2,
                    handle_rect.top() - self._value_label.rect.height(),
                )
            ),
            self.map_to_parent(
                QtCore.QPoint(
                    handle_rect.right()
                    + (self._value_label.rect.width() - handle_rect.width()) / 2,
                    handle_rect.top(),
                )
            ),
        )
        self._value_label.geometry = new_rect
        self._value_label.show()
        if start_hide_timer:
            self._label_hide_timer.interval = 1000
            self._label_hide_timer.start()

    def _on_press(self) -> None:
        """Set the slider as being pressed and stop the hide timer."""
        self._label_hide_timer.stop()
        self._display_value_tooltip(start_hide_timer=False)

    def _on_release(self) -> None:
        """Set the slider as being released and start the timer to hide the label in 500ms."""
        self._label_hide_timer.interval = 500
        self._label_hide_timer.start()

    def mouse_move_event(self, event: QtGui.QMouseEvent) -> None:
        """Show the value tooltip on hover."""
        super().mouse_move_event(event)
        option = QtWidgets.QStyleOptionSlider()
        self.init_style_option(option)

        handle_rect = self.style().sub_control_rect(
            QtWidgets.QStyle.CC_Slider,
            option,
            QtWidgets.QStyle.SC_SliderHandle,
            self,
        )

        on_handle = handle_rect.contains(event.pos())

        if on_handle and not self._mouse_on_handle:
            self._mouse_on_handle = True
            self._display_value_tooltip(start_hide_timer=False)
        elif not on_handle and self._mouse_on_handle:
            self._mouse_on_handle = False
            if not self._label_hide_timer.active:
                self._value_label.hide()

    def leave_event(self, event: QtCore.QEvent) -> None:
        """Hide the value label if the user was hovering over it and the hide timer is not active."""
        super().leave_event(event)
        if self._mouse_on_handle:
            self._mouse_on_handle = False
            if not self._label_hide_timer.active:
                self._value_label.hide()

    def _hide_value_label_if_not_hover(self) -> None:
        """Hide the value label if the cursor is not hovering over the handle."""
        if not self._mouse_on_handle:
            self._value_label.hide()
