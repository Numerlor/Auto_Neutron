# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t

from auto_neutron.widgets.tooltip_slider import LogTooltipSlider

if t.TYPE_CHECKING:
    import collections.abc

from PySide6 import QtCore, QtGui, QtWidgets

from auto_neutron.dark_theme import is_dark
from auto_neutron.utils.file import base_path
from auto_neutron.widgets import ScrolledStatus, TooltipSlider


class TabGUIBase(QtWidgets.QWidget):
    """Provide the base for plot tabs, with a journal selector and submit/abort buttons on bottom."""

    def __init__(
        self,
        *args: object,
        **kwargs: object,
    ):
        super().__init__()
        self.main_layout = QtWidgets.QVBoxLayout(self)
        (
            self.journal_submit_layout,
            self.journal_combo,
            self.refresh_button,
            self.submit_button,
            self.abort_button,
        ) = self._create_journal_and_submit_layout()
        self.submit_button.default = True
        self.abort_button.default = True

    def _create_journal_and_submit_layout(
        self,
    ) -> tuple[
        QtWidgets.QHBoxLayout,
        QtWidgets.QComboBox,
        QtWidgets.QPushButton,
        QtWidgets.QPushButton,
        QtWidgets.QPushButton,
    ]:
        """Create a layout that holds the bottom journal combo box and submit button."""
        journal_submit_layout = QtWidgets.QHBoxLayout()

        journal_combo = QtWidgets.QComboBox(self)
        journal_combo.setSizeAdjustPolicy(
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents
        )

        submit_button = QtWidgets.QPushButton(self)
        submit_button.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Maximum,
                QtWidgets.QSizePolicy.Policy.Maximum,
            )
        )
        abort_button = QtWidgets.QPushButton(self)
        abort_button.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Maximum,
                QtWidgets.QSizePolicy.Policy.Maximum,
            )
        )
        abort_button.hide()
        refresh_button = QtWidgets.QPushButton(self)
        refresh_button.setIcon(QtGui.QIcon(self.get_refresh_icon(is_dark())))

        journal_submit_layout.addWidget(journal_combo)
        journal_submit_layout.addWidget(refresh_button)
        journal_submit_layout.addSpacerItem(
            QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Policy.Expanding)
        )
        journal_submit_layout.addWidget(submit_button)
        journal_submit_layout.addWidget(abort_button)

        return (
            journal_submit_layout,
            journal_combo,
            refresh_button,
            submit_button,
            abort_button,
        )

    def get_refresh_icon(self, dark: bool) -> QtGui.QIcon:
        """Get an appropriately coloured refresh icon."""
        if dark:
            path = base_path() / "resources/refresh-dark.svg"
        else:
            path = base_path() / "resources/refresh.svg"
        return QtGui.QIcon(str(path))

    def changeEvent(self, event: QtCore.QEvent) -> None:
        """Update the tooltip's colors when the palette changes."""
        if event.type() == QtCore.QEvent.Type.PaletteChange:
            self.refresh_button.setIcon(self.get_refresh_icon(is_dark()))

        super().changeEvent(event)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.submit_button.setText(_("Submit"))
        self.abort_button.setText(_("Abort"))
        self.abort_button.setToolTip(_("Cancel the current route plot"))
        self.refresh_button.setToolTip(_("Refresh journals"))


class SpanshTabGUIBase(TabGUIBase):
    """Base Spansh layout with the source/target sys inputs, cargo slider and nearest button above submit."""

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        (
            self.system_cargo_layout,
            self.source_edit,
            self.target_edit,
            self.cargo_label,
            self.cargo_slider,
        ) = self._create_system_and_cargo_layout()

        self.journal_submit_layout = QtWidgets.QHBoxLayout()

        self.nearest_button = QtWidgets.QPushButton(self)
        self.nearest_button.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
            )
        )
        submit_nearest_layout = QtWidgets.QVBoxLayout()
        submit_nearest_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                1,
                1,
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )
        submit_nearest_layout.addWidget(self.nearest_button)
        submit_nearest_layout.addWidget(self.submit_button)
        submit_nearest_layout.addWidget(self.abort_button)

        self.journal_submit_layout.addWidget(
            self.journal_combo,
            alignment=QtCore.Qt.AlignmentFlag.AlignBottom,
        )
        self.journal_submit_layout.addWidget(
            self.refresh_button,
            alignment=QtCore.Qt.AlignmentFlag.AlignBottom,
        )
        self.journal_submit_layout.addSpacerItem(
            QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Policy.Expanding)
        )
        spacer = QtWidgets.QSpacerItem(
            45,
            1,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.journal_submit_layout.addSpacerItem(spacer)
        self.journal_submit_layout.addLayout(submit_nearest_layout)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.nearest_button.setText(_("Nearest"))
        self.source_edit.setPlaceholderText(_("Source system"))
        self.target_edit.setPlaceholderText(_("Destination system"))

        self.cargo_label.setText(_("Cargo"))

    def _create_system_and_cargo_layout(
        self,
    ) -> tuple[
        QtWidgets.QVBoxLayout,
        QtWidgets.QLineEdit,
        QtWidgets.QLineEdit,
        QtWidgets.QLabel,
        TooltipSlider,
    ]:
        """Create a layout that holds the top system text edits and cargo slider."""
        layout = QtWidgets.QVBoxLayout()

        source_system_edit = QtWidgets.QLineEdit(self)
        target_system_edit = QtWidgets.QLineEdit(self)

        cargo_label = QtWidgets.QLabel(self)
        cargo_slider = TooltipSlider(QtCore.Qt.Orientation.Horizontal, self)

        layout.addWidget(source_system_edit)
        layout.addWidget(target_system_edit)

        layout.addWidget(cargo_label, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        layout.addWidget(cargo_slider, alignment=QtCore.Qt.AlignmentFlag.AlignTop)

        return layout, source_system_edit, target_system_edit, cargo_label, cargo_slider


class NeutronTabGUI(SpanshTabGUIBase):
    """The neutron plotter tab."""

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)

        self.range_label = QtWidgets.QLabel(self)
        self.range_spin = QtWidgets.QDoubleSpinBox(self)
        self.range_spin.setSuffix(" Ly")
        self.range_spin.setAccelerated(True)
        self.range_spin.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
            )
        )

        self.efficiency_label = QtWidgets.QLabel(self)
        self.efficiency_spin = QtWidgets.QSpinBox(self)
        self.efficiency_spin.setMaximum(100)
        self.efficiency_spin.setSuffix("%")
        self.efficiency_spin.setAccelerated(True)
        self.efficiency_spin.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
            )
        )

        self.main_layout.addLayout(self.system_cargo_layout)
        self.main_layout.addWidget(self.range_label)
        self.main_layout.addWidget(self.range_spin)
        self.main_layout.addWidget(self.efficiency_label)
        self.main_layout.addWidget(self.efficiency_spin)
        self.main_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                1,
                1,
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )
        self.main_layout.addLayout(self.journal_submit_layout)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.range_label.setText(_("Range"))
        self.efficiency_label.setText(_("Efficiency"))


class ExactTabGUI(SpanshTabGUIBase):
    """The exact plotter tab."""

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self.cargo_slider.setMaximum(
            999  # static value because ship may come from outside source
        )

        self.is_supercharged_checkbox = QtWidgets.QCheckBox(self)
        self.supercarge_checkbox = QtWidgets.QCheckBox(self)
        self.fsd_injections_checkbox = QtWidgets.QCheckBox(self)
        self.exclude_secondary_checkbox = QtWidgets.QCheckBox(self)

        self.use_clipboard_checkbox = QtWidgets.QCheckBox(self)

        self.main_layout.addLayout(self.system_cargo_layout)
        self.main_layout.addWidget(self.is_supercharged_checkbox)
        self.main_layout.addWidget(self.supercarge_checkbox)
        self.main_layout.addWidget(self.fsd_injections_checkbox)
        self.main_layout.addWidget(self.exclude_secondary_checkbox)
        self.main_layout.addWidget(self.use_clipboard_checkbox)
        self.main_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                1,
                1,
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )
        self.main_layout.addLayout(self.journal_submit_layout)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.is_supercharged_checkbox.setText(_("Already supercharged"))
        self.supercarge_checkbox.setText(_("Use supercharge"))
        self.fsd_injections_checkbox.setText(_("Use FSD injections"))
        self.exclude_secondary_checkbox.setText(_("Exclude secondary stars"))
        self.use_clipboard_checkbox.setText(_("Use ship from clipboard"))


class RoadToRichesTabGUI(SpanshTabGUIBase):
    """The road to riches plotter tab."""

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Holds only the scroll area.

        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            (QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        )
        self.scroll_area.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Ignored,
                QtWidgets.QSizePolicy.Policy.Ignored,
            )
        )
        self.scroll_area.setWidgetResizable(True)
        # The widget in the scroll area renders its background with the Window color even with
        # auto_fill_background set to False, and changing the Window role color affects how child widgets are rendered.
        # Because the tab widget this is in has its own background color,
        # and to avoid having to set a palette on all the children created here, the scroll area is forced to use
        # a an otherwise unused role for the color.
        palette = self.scroll_area.palette()
        palette.setColor(QtGui.QPalette.ColorRole.Shadow, QtGui.QColor(0, 0, 0, 0))
        self.scroll_area.setPalette(palette)
        self.scroll_area.setBackgroundRole(QtGui.QPalette.ColorRole.Shadow)

        self.scroll_widget = QtWidgets.QWidget(self)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_widget)

        self.range_label = QtWidgets.QLabel(self.scroll_widget)
        self.range_spinbox = QtWidgets.QDoubleSpinBox(self.scroll_widget)
        self.range_spinbox.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
        )
        self.range_spinbox.setMaximum(100)
        self.range_spinbox.setAccelerated(True)
        self.range_spinbox.setSuffix(" Ly")

        self.radius_label = QtWidgets.QLabel(self.scroll_widget)
        self.radius_spinbox = QtWidgets.QSpinBox(self.scroll_widget)
        self.radius_spinbox.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
        )
        self.radius_spinbox.setAccelerated(True)
        self.radius_spinbox.setSuffix(" Ly")
        self.radius_spinbox.setValue(25)

        self.max_systems_label = QtWidgets.QLabel(self.scroll_widget)
        self.max_systems_spinbox = QtWidgets.QSpinBox(self.scroll_widget)
        self.max_systems_spinbox.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
        )
        self.max_systems_spinbox.setAccelerated(True)
        self.max_systems_spinbox.setMaximum(500)
        self.max_systems_spinbox.setValue(50)

        self.use_mapping_value_checkbox = QtWidgets.QCheckBox(self.scroll_widget)
        self.loop_checkbox = QtWidgets.QCheckBox(self.scroll_widget)

        self.maximum_distance_label = QtWidgets.QLabel(self.scroll_widget)
        self.max_distance_slider = LogTooltipSlider(
            QtCore.Qt.Orientation.Horizontal, self.scroll_widget
        )
        self.max_distance_slider.log_maximum = 1_000_000
        self.max_distance_slider.log_value = 10_000

        self.minimum_scan_label = QtWidgets.QLabel(self.scroll_widget)
        self.minimum_scan_slider = LogTooltipSlider(
            QtCore.Qt.Orientation.Horizontal, self.scroll_widget
        )
        self.minimum_scan_slider.log_minimum = 100
        self.minimum_scan_slider.log_maximum = 1_000_000
        self.minimum_scan_slider.log_value = 100_000

        # Scroll area's role messed up text color
        for label in (
            self.cargo_label,
            self.range_label,
            self.radius_label,
            self.max_systems_label,
            self.maximum_distance_label,
            self.minimum_scan_label,
        ):
            label.setBackgroundRole(QtGui.QPalette.ColorRole.Base)

        self.scroll_layout.addLayout(self.system_cargo_layout)
        self.scroll_layout.addWidget(self.range_label)
        self.scroll_layout.addWidget(self.range_spinbox)
        self.scroll_layout.addWidget(self.radius_label)
        self.scroll_layout.addWidget(self.radius_spinbox)
        self.scroll_layout.addWidget(self.max_systems_label)
        self.scroll_layout.addWidget(self.max_systems_spinbox)
        self.scroll_layout.addWidget(self.use_mapping_value_checkbox)
        self.scroll_layout.addWidget(self.loop_checkbox)
        self.scroll_layout.addWidget(self.maximum_distance_label)
        self.scroll_layout.addWidget(self.max_distance_slider)
        self.scroll_layout.addWidget(self.minimum_scan_label)
        self.scroll_layout.addWidget(self.minimum_scan_slider)
        self.scroll_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                1,
                1,
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )
        self.scroll_layout.addLayout(self.journal_submit_layout)
        self.main_layout.addWidget(self.scroll_area)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.range_label.setText(_("Range"))
        self.radius_label.setText(_("Radius"))
        self.max_systems_label.setText(_("Maximum systems"))
        self.use_mapping_value_checkbox.setText(_("Use mapping value"))
        self.loop_checkbox.setText(_("Loop back to start"))
        self.maximum_distance_label.setText(_("Maximum distance to arrival"))
        self.minimum_scan_label.setText(_("Minimum scan value"))


class CSVTabGUI(TabGUIBase):
    """The CSV plotter tab."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.path_layout = QtWidgets.QHBoxLayout()

        self.path_edit = QtWidgets.QLineEdit(self)

        self.path_popup_button = QtWidgets.QPushButton("...", self)
        self.path_popup_button.setMaximumWidth(24)

        self.path_layout.addWidget(self.path_edit)
        self.path_layout.addWidget(self.path_popup_button)

        self.main_layout.addLayout(self.path_layout)
        self.main_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                1,
                1,
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )
        self.main_layout.addLayout(self.journal_submit_layout)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.path_edit.setPlaceholderText(_("CSV path"))


class LastTabGUI(TabGUIBase):
    """The last route plot tab."""

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)

        self.source_label = QtWidgets.QLabel(self)
        self.location_label = QtWidgets.QLabel(self)
        self.destination_label = QtWidgets.QLabel(self)

        self.main_layout.addWidget(self.source_label)
        self.main_layout.addWidget(self.location_label)
        self.main_layout.addWidget(self.destination_label)

        self.main_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                1,
                1,
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )
        self.main_layout.addLayout(self.journal_submit_layout)


class NewRouteWindowGUI(QtWidgets.QDialog):
    """Provide the base GUI for the new route window in the form of tabs for each plotter."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        *,
        tabs: collections.abc.Sequence[tuple[TabGUIBase, str]],
    ):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setSpacing(1)
        self.main_layout.setContentsMargins(QtCore.QMargins(3, 6, 3, 3))

        self.tab_widget = QtWidgets.QTabWidget(self)

        self.tabs = []
        self.tab_names = []
        for tab, tab_name in tabs:
            self.tabs.append(tab)
            self.tab_names.append(tab_name)
            self.tab_widget.addTab(tab, "")

        self.status_layout = QtWidgets.QHBoxLayout()
        self.status_widget = ScrolledStatus(self)
        # FIXME: layout with spacer won't be necessary after PySide6 is fixed to properly call the widget's size hint
        self.status_layout.addWidget(self.status_widget)
        self.status_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                0,
                16,
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
        )

        self.main_layout.addWidget(self.tab_widget)
        self.main_layout.addLayout(self.status_layout)

    @QtCore.Slot()
    def switch_submit_abort(self) -> None:
        """Switches the currently appearing submit/abort buttons for the other one."""
        abort_hidden = self.tabs[0].abort_button.isHidden()
        for tab in self.tabs:
            if abort_hidden:
                tab.abort_button.show()
                tab.submit_button.hide()
            else:
                tab.abort_button.hide()
                tab.submit_button.show()

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        for tab_pos, (tab, tab_title) in enumerate(zip(self.tabs, self.tab_names)):
            tab.retranslate()
            self.tab_widget.setTabText(tab_pos, _(tab_title))
