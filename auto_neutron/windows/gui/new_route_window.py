# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    import collections.abc

from PySide6 import QtCore, QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

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
        journal_combo.size_adjust_policy = (
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents
        )

        submit_button = QtWidgets.QPushButton(self)
        submit_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum
        )
        abort_button = QtWidgets.QPushButton(self)
        abort_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum
        )
        abort_button.hide()
        refresh_button = QtWidgets.QPushButton(self)
        refresh_button.icon = QtGui.QIcon(self.get_refresh_icon(is_dark()))

        journal_submit_layout.add_widget(journal_combo)
        journal_submit_layout.add_widget(refresh_button)
        journal_submit_layout.add_spacer_item(
            QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding)
        )
        journal_submit_layout.add_widget(submit_button)
        journal_submit_layout.add_widget(abort_button)

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

    def change_event(self, event: QtCore.QEvent) -> None:
        """Update the tooltip's colors when the palette changes."""
        if event.type() == QtCore.QEvent.Type.PaletteChange:
            self.refresh_button.icon = self.get_refresh_icon(is_dark())

        super().change_event(event)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.submit_button.text = _("Submit")
        self.abort_button.text = _("Abort")
        self.abort_button.tool_tip = _("Cancel the current route plot")
        self.refresh_button.tool_tip = _("Refresh journals")


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
        self.nearest_button.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        submit_nearest_layout = QtWidgets.QVBoxLayout()
        submit_nearest_layout.add_spacer_item(
            QtWidgets.QSpacerItem(
                1,
                1,
                QtWidgets.QSizePolicy.Fixed,
                QtWidgets.QSizePolicy.Expanding,
            )
        )
        submit_nearest_layout.add_widget(self.nearest_button)
        submit_nearest_layout.add_widget(self.submit_button)
        submit_nearest_layout.add_widget(self.abort_button)

        self.journal_submit_layout.add_widget(
            self.journal_combo,
            alignment=QtCore.Qt.AlignmentFlag.AlignBottom,
        )
        self.journal_submit_layout.add_widget(
            self.refresh_button,
            alignment=QtCore.Qt.AlignmentFlag.AlignBottom,
        )
        self.journal_submit_layout.add_spacer_item(
            QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding)
        )
        spacer = QtWidgets.QSpacerItem(
            45,
            1,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        self.journal_submit_layout.add_spacer_item(spacer)
        self.journal_submit_layout.add_layout(submit_nearest_layout)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.nearest_button.text = _("Nearest")
        self.source_edit.placeholder_text = _("Source system")
        self.target_edit.placeholder_text = _("Destination system")

        self.cargo_label.text = _("Cargo")

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

        layout.add_widget(source_system_edit)
        layout.add_widget(target_system_edit)

        layout.add_widget(cargo_label, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        layout.add_widget(cargo_slider, alignment=QtCore.Qt.AlignmentFlag.AlignTop)

        return layout, source_system_edit, target_system_edit, cargo_label, cargo_slider


class NeutronTabGUI(SpanshTabGUIBase):
    """The neutron plotter tab."""

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)

        self.range_label = QtWidgets.QLabel(self)
        self.range_spin = QtWidgets.QDoubleSpinBox(self)
        self.range_spin.suffix = " Ly"
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

        self.main_layout.add_layout(self.system_cargo_layout)
        self.main_layout.add_widget(self.range_label)
        self.main_layout.add_widget(self.range_spin)
        self.main_layout.add_widget(self.efficiency_label)
        self.main_layout.add_widget(self.efficiency_spin)
        self.main_layout.add_spacer_item(
            QtWidgets.QSpacerItem(
                1,
                1,
                QtWidgets.QSizePolicy.Fixed,
                QtWidgets.QSizePolicy.Expanding,
            )
        )
        self.main_layout.add_layout(self.journal_submit_layout)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.range_label.text = _("Range")
        self.efficiency_label.text = _("Efficiency")


class ExactTabGUI(SpanshTabGUIBase):
    """The exact plotter tab."""

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self.cargo_slider.maximum = (
            999  # static value because ship may come from outside source
        )

        self.is_supercharged_checkbox = QtWidgets.QCheckBox(self)
        self.supercarge_checkbox = QtWidgets.QCheckBox(self)
        self.fsd_injections_checkbox = QtWidgets.QCheckBox(self)
        self.exclude_secondary_checkbox = QtWidgets.QCheckBox(self)

        self.use_clipboard_checkbox = QtWidgets.QCheckBox(self)

        self.main_layout.add_layout(self.system_cargo_layout)
        self.main_layout.add_widget(self.is_supercharged_checkbox)
        self.main_layout.add_widget(self.supercarge_checkbox)
        self.main_layout.add_widget(self.fsd_injections_checkbox)
        self.main_layout.add_widget(self.exclude_secondary_checkbox)
        self.main_layout.add_widget(self.use_clipboard_checkbox)
        self.main_layout.add_spacer_item(
            QtWidgets.QSpacerItem(
                1,
                1,
                QtWidgets.QSizePolicy.Fixed,
                QtWidgets.QSizePolicy.Expanding,
            )
        )
        self.main_layout.add_layout(self.journal_submit_layout)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.is_supercharged_checkbox.text = _("Already supercharged")
        self.supercarge_checkbox.text = _("Use supercharge")
        self.fsd_injections_checkbox.text = _("Use FSD injections")
        self.exclude_secondary_checkbox.text = _("Exclude secondary stars")
        self.use_clipboard_checkbox.text = _("Use ship from clipboard")


class RoadToRichesTabGUI(SpanshTabGUIBase):
    """The road to riches plotter tab."""

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self.main_layout.contents_margins = QtCore.QMargins(
            0, 0, 0, 0
        )  # Holds only the scroll area.

        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.frame_shape = QtWidgets.QFrame.Shape.NoFrame
        self.scroll_area.horizontal_scroll_bar_policy = (
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Ignored,
        )
        self.scroll_area.widget_resizable = True
        # The widget in the scroll area renders its background with the Window color even with
        # auto_fill_background set to False, and changing the Window role color affects how child widgets are rendered.
        # Because the tab widget this is in has its own background color,
        # and to avoid having to set a palette on all the children created here, the scroll area is forced to use
        # a an otherwise unused role for the color.
        palette = self.scroll_area.palette
        palette.set_color(palette.Shadow, QtGui.QColor(0, 0, 0, 0))
        self.scroll_area.palette = palette
        self.scroll_area.set_background_role(palette.Shadow)

        self.scroll_widget = QtWidgets.QWidget(self)
        self.scroll_area.set_widget(self.scroll_widget)
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_widget)

        self.range_label = QtWidgets.QLabel(self.scroll_widget)
        self.range_spinbox = QtWidgets.QDoubleSpinBox(self.scroll_widget)
        self.range_spinbox.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.range_spinbox.maximum = 100
        self.range_spinbox.accelerated = True
        self.range_spinbox.suffix = " Ly"

        self.radius_label = QtWidgets.QLabel(self.scroll_widget)
        self.radius_spinbox = QtWidgets.QSpinBox(self.scroll_widget)
        self.radius_spinbox.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.radius_spinbox.accelerated = True
        self.radius_spinbox.suffix = " Ly"

        self.max_systems_label = QtWidgets.QLabel(self.scroll_widget)
        self.max_systems_spinbox = QtWidgets.QSpinBox(self.scroll_widget)
        self.max_systems_spinbox.size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.max_systems_spinbox.accelerated = True
        self.max_systems_spinbox.maximum = 500

        self.use_mapping_value_checkbox = QtWidgets.QCheckBox(self.scroll_widget)
        self.loop_checkbox = QtWidgets.QCheckBox(self.scroll_widget)

        self.maximum_distance_label = QtWidgets.QLabel(self.scroll_widget)
        self.max_distance_slider = TooltipSlider(
            QtCore.Qt.Orientation.Horizontal, self.scroll_widget
        )
        self.max_distance_slider.maximum = 1_000_000

        self.minimum_scan_label = QtWidgets.QLabel(self.scroll_widget)
        self.minimum_scan_slider = TooltipSlider(
            QtCore.Qt.Orientation.Horizontal, self.scroll_widget
        )
        self.minimum_scan_slider.minimum = 100
        self.minimum_scan_slider.maximum = 1_000_000

        self.scroll_layout.add_layout(self.system_cargo_layout)
        self.scroll_layout.add_widget(self.range_label)
        self.scroll_layout.add_widget(self.range_spinbox)
        self.scroll_layout.add_widget(self.radius_label)
        self.scroll_layout.add_widget(self.radius_spinbox)
        self.scroll_layout.add_widget(self.max_systems_label)
        self.scroll_layout.add_widget(self.max_systems_spinbox)
        self.scroll_layout.add_widget(self.use_mapping_value_checkbox)
        self.scroll_layout.add_widget(self.loop_checkbox)
        self.scroll_layout.add_widget(self.maximum_distance_label)
        self.scroll_layout.add_widget(self.max_distance_slider)
        self.scroll_layout.add_widget(self.minimum_scan_label)
        self.scroll_layout.add_widget(self.minimum_scan_slider)
        self.scroll_layout.add_spacer_item(
            QtWidgets.QSpacerItem(
                1,
                1,
                QtWidgets.QSizePolicy.Fixed,
                QtWidgets.QSizePolicy.Expanding,
            )
        )
        self.scroll_layout.add_layout(self.journal_submit_layout)
        self.main_layout.add_widget(self.scroll_area)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        super().retranslate()
        self.range_label.text = _("Range")
        self.radius_label.text = _("Radius")
        self.max_systems_label.text = _("Maximum systems")
        self.use_mapping_value_checkbox.text = _("Use mapping value")
        self.loop_checkbox.text = _("Loop back to start")
        self.maximum_distance_label.text = _("Maximum distance to arrival")
        self.minimum_scan_label.text = _("Minimum scan value")


class CSVTabGUI(TabGUIBase):
    """The CSV plotter tab."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        self.path_edit.placeholder_text = _("CSV path")


class LastTabGUI(TabGUIBase):
    """The last route plot tab."""

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)

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

    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        *,
        tabs: collections.abc.Sequence[tuple[TabGUIBase, str]],
    ):
        super().__init__(parent)
        self.set_attribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.focus_policy = QtCore.Qt.FocusPolicy.ClickFocus

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.set_spacing(1)
        self.main_layout.contents_margins = QtCore.QMargins(3, 6, 3, 3)

        self.tab_widget = QtWidgets.QTabWidget(self)

        self.tabs = []
        self.tab_names = []
        for tab, tab_name in tabs:
            self.tabs.append(tab)
            self.tab_names.append(tab_name)
            self.tab_widget.add_tab(tab, "")

        self.status_layout = QtWidgets.QHBoxLayout()
        self.status_widget = ScrolledStatus(self)
        # FIXME: layout with spacer won't be necessary after PySide6 is fixed to properly call the widget's size hint
        self.status_layout.add_widget(self.status_widget)
        self.status_layout.add_spacer_item(
            QtWidgets.QSpacerItem(
                0, 16, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
            )
        )

        self.main_layout.add_widget(self.tab_widget)
        self.main_layout.add_layout(self.status_layout)

    def switch_submit_abort(self) -> None:
        """Switches the currently appearing submit/abort buttons for the other one."""
        abort_hidden = self.tabs[0].abort_button.is_hidden()
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
            self.tab_widget.set_tab_text(tab_pos, _(tab_title))
