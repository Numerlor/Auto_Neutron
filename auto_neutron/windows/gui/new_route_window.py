# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401
from auto_neutron.utils.forbid_uninitialized import ForbidUninitialized

from .tooltip_slider import TooltipSlider


class TabBase(QtWidgets.QWidget):
    """Provide the base for a tab with convenience methods."""

    system_cargo_layout = ForbidUninitialized()
    source_edit = ForbidUninitialized()
    target_edit = ForbidUninitialized()
    cargo_label = ForbidUninitialized()
    cargo_slider = ForbidUninitialized()

    def __init__(self, parent: QtWidgets.QWidget, *, create_cargo: bool):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.has_cargo = create_cargo
        if create_cargo:
            (
                self.system_cargo_layout,
                self.source_edit,
                self.target_edit,
                self.cargo_label,
                self.cargo_slider,
            ) = self.create_system_and_cargo_layout(self)
        (
            self.journal_submit_layout,
            self.journal_combo,
            self.submit_button,
        ) = self.create_journal_and_submit_layout(self)

    def create_journal_and_submit_layout(
        self, widget_parent: QtWidgets.QWidget
    ) -> tuple[QtWidgets.QHBoxLayout, QtWidgets.QComboBox, QtWidgets.QPushButton]:
        """Create a layout that holds the bottom journal combo box and submit button."""
        journal_submit_layout = QtWidgets.QHBoxLayout()

        journal_combo = QtWidgets.QComboBox(widget_parent)

        submit_button = QtWidgets.QPushButton(widget_parent)
        submit_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum
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

        cargo_label = QtWidgets.QLabel(parent)
        cargo_slider = TooltipSlider(QtCore.Qt.Orientation.Horizontal, parent)

        layout.add_widget(source_system_edit)
        layout.add_widget(target_system_edit)

        layout.add_widget(cargo_label, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        layout.add_widget(cargo_slider, alignment=QtCore.Qt.AlignmentFlag.AlignTop)

        return layout, source_system_edit, target_system_edit, cargo_label, cargo_slider

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        if self.has_cargo:
            self.source_edit.placeholder_text = _("Source system")
            self.target_edit.placeholder_text = _("Destination system")

            self.cargo_label.text = _("Cargo")

        self.submit_button.text = _("Submit")
        index = self.journal_combo.current_index
        self.journal_combo.clear()
        self.journal_combo.add_items(
            [_("Last journal"), _("Second to last"), _("Third to last")]
        )
        self.journal_combo.current_index = index


class NeutronTab(TabBase):
    """The neutron plotter tab."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent, create_cargo=True)

        self.range_label = QtWidgets.QLabel(self)
        self.range_spin = QtWidgets.QDoubleSpinBox(self)
        self.range_spin.accelerated = True
        self.range_spin.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self.efficiency_label = QtWidgets.QLabel(self)
        self.efficiency_spin = QtWidgets.QSpinBox(self)
        self.efficiency_spin.maximum = 100
        self.efficiency_spin.suffix = "%"
        self.efficiency_spin.accelerated = True
        self.efficiency_spin.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        self.eff_nearest_layout = QtWidgets.QHBoxLayout()
        self.nearest_button = QtWidgets.QPushButton(self)
        self.nearest_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.eff_nearest_layout.add_widget(
            self.efficiency_spin, alignment=QtCore.Qt.AlignmentFlag.AlignLeft
        )
        self.eff_nearest_layout.add_widget(self.nearest_button)

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

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.range_label.text = _("Range")
        self.efficiency_label.text = _("Efficiency")
        self.nearest_button.text = _("Nearest")


class ExactTab(TabBase):
    """The exact plotter tab."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent, create_cargo=True)
        self.cargo_slider.maximum = (
            999  # static value because ship may come from outside source
        )

        self.is_supercharged_checkbox = QtWidgets.QCheckBox(self)
        self.supercarge_checkbox = QtWidgets.QCheckBox(self)
        self.fsd_injections_checkbox = QtWidgets.QCheckBox(self)
        self.exclude_secondary_checkbox = QtWidgets.QCheckBox(self)

        self.use_clipboard_and_nearest_layout = QtWidgets.QHBoxLayout()

        self.use_clipboard_checkbox = QtWidgets.QCheckBox(self)
        self.nearest_button = QtWidgets.QPushButton(self)
        self.nearest_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.use_clipboard_and_nearest_layout.add_widget(
            self.use_clipboard_checkbox, QtCore.Qt.AlignmentFlag.AlignLeft
        )
        self.use_clipboard_and_nearest_layout.add_widget(self.nearest_button)

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

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.is_supercharged_checkbox.text = _("Already supercharged")
        self.supercarge_checkbox.text = _("Use supercharge")
        self.fsd_injections_checkbox.text = _("Use FSD injections")
        self.exclude_secondary_checkbox.text = _("Exclude secondary stars")
        self.use_clipboard_checkbox.text = _("Use ship from clipboard")
        self.nearest_button.text = _("Nearest")


class CSVTab(TabBase):
    """The CSV plotter tab."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent, create_cargo=False)

        self.path_layout = QtWidgets.QHBoxLayout()

        self.path_edit = QtWidgets.QLineEdit(self)

        self.path_popup_button = QtWidgets.QPushButton("...", self)
        self.path_popup_button.maximum_width = 24

        self.path_layout.add_widget(self.path_edit)
        self.path_layout.add_widget(self.path_popup_button)

        self.main_layout.add_layout(self.path_layout)
        self.main_layout.add_spacer_item(
            QtWidgets.QSpacerItem(
                1, 1, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
            )
        )
        self.main_layout.add_layout(self.journal_submit_layout)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.path_edit.placeholder_text = "CSV path"


class LastTab(TabBase):
    """The last route plot tab."""

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent, create_cargo=False)

        self.source_label = QtWidgets.QLabel(self)
        self.location_label = QtWidgets.QLabel(self)
        self.destination_label = QtWidgets.QLabel(self)

        self.main_layout.add_widget(self.source_label)
        self.main_layout.add_widget(self.location_label)
        self.main_layout.add_widget(self.destination_label)

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

        self.tab_widget.add_tab(self.csv_tab, "")
        self.tab_widget.add_tab(self.spansh_neutron_tab, "")
        self.tab_widget.add_tab(self.spansh_exact_tab, "")
        self.tab_widget.add_tab(self.last_route_tab, "")

        self.status_bar = QtWidgets.QStatusBar(self)

        self.main_layout.add_widget(self.tab_widget)
        self.main_layout.add_widget(self.status_bar)

        for button in self.find_children(QtWidgets.QPushButton):
            button.auto_default = False

        self.csv_tab.journal_combo.adjust_size()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.csv_tab.retranslate()
        self.spansh_neutron_tab.retranslate()
        self.spansh_exact_tab.retranslate()
        self.last_route_tab.retranslate()
        self.tab_widget.set_tab_text(0, _("CSV"))
        self.tab_widget.set_tab_text(1, _("Neutron plotter"))
        self.tab_widget.set_tab_text(2, _("Galaxy plotter"))
        self.tab_widget.set_tab_text(3, _("Saved route"))
