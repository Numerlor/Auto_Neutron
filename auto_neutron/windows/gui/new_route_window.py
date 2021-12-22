# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import typing as t

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


class TabBase(QtWidgets.QWidget):
    """Provide the base for a tab with convenience methods."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)

    def create_journal_and_submit_layout(
        self, widget_parent: QtWidgets.QWidget
    ) -> tuple[QtWidgets.QHBoxLayout, QtWidgets.QComboBox, QtWidgets.QPushButton]:
        """Create a layout that holds the bottom journal combo box and submit button."""
        journal_submit_layout = QtWidgets.QHBoxLayout()

        journal_combo = QtWidgets.QComboBox(widget_parent)
        journal_combo.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        journal_combo.add_items(["Last journal", "Second to last", "Third to last"])

        submit_button = QtWidgets.QPushButton("Submit", widget_parent)
        submit_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        journal_submit_layout.add_widget(
            journal_combo, alignment=QtCore.Qt.AlignmentFlag.AlignLeft
        )
        journal_submit_layout.add_widget(submit_button)

        return journal_submit_layout, journal_combo, submit_button

    def create_system_and_cargo_layout(
        self, parent: QtWidgets.QWidget
    ) -> tuple[
        QtWidgets.QVBoxLayout,
        QtWidgets.QLineEdit,
        QtWidgets.QLineEdit,
        QtWidgets.QLabel,
        LabeledSlider,
    ]:
        """Create a layout that holds the top system text edits and cargo slider."""
        layout = QtWidgets.QVBoxLayout()

        source_system_edit = QtWidgets.QLineEdit(parent)
        target_system_edit = QtWidgets.QLineEdit(parent)

        source_system_edit.placeholder_text = "Source system"
        target_system_edit.placeholder_text = "Destination system"

        cargo_label = QtWidgets.QLabel("Cargo", parent)
        cargo_slider = LabeledSlider(QtCore.Qt.Orientation.Horizontal, parent)

        layout.add_widget(source_system_edit)
        layout.add_widget(target_system_edit)

        layout.add_widget(cargo_label, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        layout.add_widget(cargo_slider, alignment=QtCore.Qt.AlignmentFlag.AlignTop)

        return layout, source_system_edit, target_system_edit, cargo_label, cargo_slider


class NeutronTab(TabBase):
    """The neutron plotter tab."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        (
            self.system_cargo_layout,
            self.source_edit,
            self.target_edit,
            self.cargo_label,
            self.cargo_slider,
        ) = self.create_system_and_cargo_layout(self)

        self.range_label = QtWidgets.QLabel("Range", self)
        self.range_spin = QtWidgets.QDoubleSpinBox(self)
        self.range_spin.accelerated = True
        self.range_spin.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self.efficiency_label = QtWidgets.QLabel("Efficiency", self)
        self.efficiency_spin = QtWidgets.QSpinBox(self)
        self.efficiency_spin.maximum = 100
        self.efficiency_spin.suffix = "%"
        self.efficiency_spin.accelerated = True
        self.efficiency_spin.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self.eff_nearest_layout = QtWidgets.QHBoxLayout()
        self.nearest_button = QtWidgets.QPushButton("Nearest", self)
        self.nearest_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.eff_nearest_layout.add_widget(
            self.efficiency_spin, alignment=QtCore.Qt.AlignmentFlag.AlignLeft
        )
        self.eff_nearest_layout.add_widget(self.nearest_button)

        (
            self.journal_submit_layout,
            self.journal_combo,
            self.submit_button,
        ) = self.create_journal_and_submit_layout(self)

        self.main_layout.add_layout(self.system_cargo_layout)
        self.main_layout.add_spacer_item(
            QtWidgets.QSpacerItem(
                1, 1, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
            )
        )
        self.main_layout.add_widget(self.range_label)
        self.main_layout.add_widget(self.range_spin)
        self.main_layout.add_widget(self.efficiency_label)
        self.main_layout.add_layout(self.eff_nearest_layout)
        self.main_layout.add_layout(self.journal_submit_layout)


class ExactTab(TabBase):
    """The exact plotter tab."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        (
            self.system_cargo_layout,
            self.source_edit,
            self.target_edit,
            self.cargo_label,
            self.cargo_slider,
        ) = self.create_system_and_cargo_layout(self)

        self.cargo_slider.maximum = (
            1000  # static value because ship may come from outside source
        )

        self.is_supercharged_checkbox = QtWidgets.QCheckBox(
            "Already Supercharged", self
        )
        self.supercarge_checkbox = QtWidgets.QCheckBox("Use Supercharge", self)
        self.fsd_injections_checkbox = QtWidgets.QCheckBox("Use FSD injections", self)
        self.exclude_secondary_checkbox = QtWidgets.QCheckBox(
            "Exclude secondary stars", self
        )

        self.use_clipboard_and_nearest_layout = QtWidgets.QHBoxLayout()

        self.use_clipboard_checkbox = QtWidgets.QCheckBox(
            "Use ship from clipboard", self
        )
        self.nearest_button = QtWidgets.QPushButton("Nearest", self)
        self.nearest_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.use_clipboard_and_nearest_layout.add_widget(
            self.use_clipboard_checkbox, QtCore.Qt.AlignmentFlag.AlignLeft
        )
        self.use_clipboard_and_nearest_layout.add_widget(self.nearest_button)

        (
            self.journal_submit_layout,
            self.journal_combo,
            self.submit_button,
        ) = self.create_journal_and_submit_layout(self)

        self.main_layout.add_layout(self.system_cargo_layout)
        self.main_layout.add_spacer_item(
            QtWidgets.QSpacerItem(
                1, 1, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
            )
        )
        self.main_layout.add_widget(self.is_supercharged_checkbox)
        self.main_layout.add_widget(self.supercarge_checkbox)
        self.main_layout.add_widget(self.fsd_injections_checkbox)
        self.main_layout.add_widget(self.exclude_secondary_checkbox)
        self.main_layout.add_layout(self.use_clipboard_and_nearest_layout)
        self.main_layout.add_layout(self.journal_submit_layout)


class CSVTab(TabBase):
    """The CSV plotter tab."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        self.path_layout = QtWidgets.QHBoxLayout()

        self.path_edit = QtWidgets.QLineEdit(self)
        self.path_edit.placeholder_text = "CSV path"

        self.path_popup_button = QtWidgets.QPushButton("...", self)
        self.path_popup_button.maximum_width = 24

        self.path_layout.add_widget(self.path_edit)
        self.path_layout.add_widget(self.path_popup_button)

        (
            self.journal_submit_layout,
            self.journal_combo,
            self.submit_button,
        ) = self.create_journal_and_submit_layout(self)

        self.main_layout.add_layout(self.path_layout)
        self.main_layout.add_spacer_item(
            QtWidgets.QSpacerItem(
                1, 1, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
            )
        )
        self.main_layout.add_layout(self.journal_submit_layout)


class LastTab(TabBase):
    """The last route plot tab."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        (
            self.journal_submit_layout,
            self.journal_combo,
            self.submit_button,
        ) = self.create_journal_and_submit_layout(self)

        self.main_layout.add_spacer_item(
            QtWidgets.QSpacerItem(
                1, 1, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
            )
        )
        self.main_layout.add_layout(self.journal_submit_layout)


class NewRouteWindowGUI(QtWidgets.QDialog):
    """Provide the base GUI for the new route window in the form of tabs for each plotter."""

    def __init__(self, parent: t.Optional[QtWidgets.QWidget]):
        super().__init__(parent)
        self.set_attribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.set_spacing(0)
        self.main_layout.contents_margins = QtCore.QMargins(4, 6, 2, 2)

        self.tab_widget = QtWidgets.QTabWidget(self)

        self.csv_tab = CSVTab(self.tab_widget)
        self.spansh_neutron_tab = NeutronTab(self.tab_widget)
        self.spansh_exact_tab = ExactTab(self.tab_widget)
        self.last_route_tab = LastTab(self.tab_widget)

        self.tab_widget.add_tab(self.csv_tab, "CSV")
        self.tab_widget.add_tab(self.spansh_neutron_tab, "Neutron plotter")
        self.tab_widget.add_tab(self.spansh_exact_tab, "Galaxy plotter")
        self.tab_widget.add_tab(self.last_route_tab, "Saved route")

        self.status_bar = QtWidgets.QStatusBar(self)

        self.main_layout.add_widget(self.tab_widget)
        self.main_layout.add_widget(self.status_bar)

        self.show()
