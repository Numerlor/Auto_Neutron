# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

import typing as t

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401

from .tooltip_slider import TooltipSlider


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
        TooltipSlider,
    ]:
        """Create a layout that holds the top system text edits and cargo slider."""
        layout = QtWidgets.QVBoxLayout()

        source_system_edit = QtWidgets.QLineEdit(parent)
        target_system_edit = QtWidgets.QLineEdit(parent)

        source_system_edit.placeholder_text = "Source system"
        target_system_edit.placeholder_text = "Destination system"

        cargo_label = QtWidgets.QLabel("Cargo", parent)
        cargo_slider = TooltipSlider(QtCore.Qt.Orientation.Horizontal, parent)

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
            999  # static value because ship may come from outside source
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
        self.focus_policy = QtCore.Qt.FocusPolicy.ClickFocus

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
