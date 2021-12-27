# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

import typing as t
from functools import partial

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401


class _ReorderedCheckBox(QtWidgets.QCheckBox):
    """Checkbox with check states reordered so the partial state appears after both unchecked and checked."""

    _CHECK_STATES = [
        QtCore.Qt.CheckState.Unchecked,
        QtCore.Qt.CheckState.Checked,
        QtCore.Qt.CheckState.PartiallyChecked,
    ]

    def next_check_state(self) -> None:
        """Set the next state."""
        self.set_check_state(
            self._CHECK_STATES[(self._CHECK_STATES.index(self.check_state()) + 1) % 3]
        )


class SettingsWindowGUI(QtWidgets.QDialog):
    """Implement the basic settings GUI with multiple settings categories from the settings module."""

    def __init__(self, parent: t.Optional[QtWidgets.QWidget]):
        super().__init__(parent)
        self.set_attribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        # region layout/widget init
        self.appearance_widget = QtWidgets.QWidget(self)
        self.appearance_layout = QtWidgets.QVBoxLayout(self.appearance_widget)

        self.behaviour_widget = QtWidgets.QWidget(self)
        self.behaviour_layout = QtWidgets.QVBoxLayout(self.behaviour_widget)

        self.alerts_widget = QtWidgets.QWidget(self)
        self.alerts_layout = QtWidgets.QVBoxLayout(self.alerts_widget)

        self.script_widget = QtWidgets.QWidget(self)
        self.script_layout = QtWidgets.QVBoxLayout(self.script_widget)

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_c_layout = QtWidgets.QVBoxLayout()
        self.main_bottom_layout = QtWidgets.QHBoxLayout()
        # endregion
        # region main view
        self.group_selector = QtWidgets.QListWidget(self)
        self.widget_selector = QtWidgets.QStackedWidget(self)
        self.ok_button = QtWidgets.QPushButton("Ok", self)
        self.apply_button = QtWidgets.QPushButton("Apply", self)
        self.error_label = QtWidgets.QLabel(self)
        # region main layout init
        self.main_bottom_layout.add_widget(self.error_label)
        self.main_bottom_layout.add_widget(self.ok_button)
        self.main_bottom_layout.add_widget(self.apply_button)

        self.main_bottom_layout.set_spacing(5)

        self.main_c_layout.add_widget(self.widget_selector)
        self.main_c_layout.add_layout(self.main_bottom_layout)
        self.main_c_layout.contents_margins = QtCore.QMargins(0, 0, 0, 0)
        self.main_layout.add_widget(self.group_selector)
        self.main_layout.add_layout(self.main_c_layout)
        self.main_layout.contents_margins = QtCore.QMargins(4, 4, 4, 4)
        self.main_layout.set_spacing(0)
        # endregion
        self.widget_selector.add_widget(self.appearance_widget)
        self.widget_selector.add_widget(self.behaviour_widget)
        self.widget_selector.add_widget(self.alerts_widget)
        self.widget_selector.add_widget(self.script_widget)

        self.group_selector.add_items(
            ("Appearance", "Behaviour", "Alerts", "AHK script")
        )
        self.group_selector.horizontal_scroll_bar_policy = (
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.group_selector.set_fixed_width(
            self.group_selector.size_hint_for_column(0) + 5
        )

        self.ok_button.maximum_width = 75
        self.apply_button.maximum_width = 75
        # endregion
        # region appearance group
        self.font_chooser = QtWidgets.QFontComboBox(self.appearance_widget)
        self.font_size_chooser = QtWidgets.QSpinBox(self.appearance_widget)
        self.font_bold_checkbox = QtWidgets.QCheckBox("Bold", self.appearance_widget)
        self.dark_mode_checkbox = _ReorderedCheckBox(
            "Dark mode", self.appearance_widget
        )
        self.dark_mode_checkbox.tristate = True

        self.font_layout = QtWidgets.QHBoxLayout()
        self.font_layout.add_widget(self.font_chooser)
        self.font_layout.add_widget(self.font_size_chooser)
        self.appearance_layout.add_layout(self.font_layout)
        self.appearance_layout.add_widget(self.font_bold_checkbox)
        self.appearance_layout.add_widget(self.dark_mode_checkbox)
        self.appearance_layout.add_spacer_item(self.get_spacer())

        self.font_size_chooser.maximum_width = 50
        # endregion
        # region behaviour group
        self.plotter_options_layout = QtWidgets.QHBoxLayout()

        self.save_on_quit_checkbox = QtWidgets.QCheckBox(
            "Save route on window close", self.behaviour_widget
        )
        self.copy_mode_checkbox = QtWidgets.QCheckBox(
            "Copy mode", self.behaviour_widget
        )
        self.ahk_path_button = QtWidgets.QPushButton("AHK Path", self.behaviour_widget)
        self.auto_scroll_checkbox = QtWidgets.QCheckBox(
            "Auto scroll", self.behaviour_widget
        )

        self.plotter_options_layout.add_widget(self.copy_mode_checkbox)
        self.plotter_options_layout.add_widget(self.ahk_path_button)

        self.behaviour_layout.add_widget(self.save_on_quit_checkbox)
        self.behaviour_layout.add_layout(self.plotter_options_layout)
        self.behaviour_layout.add_widget(self.auto_scroll_checkbox)
        self.behaviour_layout.add_spacer_item(self.get_spacer())
        self.ahk_path_button.maximum_width = 75
        # endregion
        # region alert group
        self.alert_checkbox_layout = QtWidgets.QHBoxLayout()
        self.alert_path_layout = QtWidgets.QHBoxLayout()
        self.alert_threshold_layout = QtWidgets.QHBoxLayout()

        self.visual_alert_checkbox = QtWidgets.QCheckBox(
            "Taskbar fuel alert", self.alerts_widget
        )
        self.audio_alert_checkbox = QtWidgets.QCheckBox(
            "Sound fuel alert", self.alerts_widget
        )

        self.alert_path_label = QtWidgets.QLabel(
            "Custom sound alert file:", self.alerts_widget
        )
        self.alert_path_line_edit = QtWidgets.QLineEdit(self.alerts_widget)
        self.alert_path_button = QtWidgets.QPushButton("...", self.alerts_widget)

        self.alert_threshold_label = QtWidgets.QLabel(
            "% of maximum fuel usage left in tank before triggering alert",
            self.alerts_widget,
        )
        self.alert_threshold_spinbox = QtWidgets.QSpinBox(self.alerts_widget)

        self.alert_checkbox_layout.add_widget(self.visual_alert_checkbox)
        self.alert_checkbox_layout.add_widget(self.audio_alert_checkbox)

        self.alert_path_layout.add_widget(self.alert_path_line_edit)
        self.alert_path_layout.add_widget(self.alert_path_button)

        self.alert_threshold_layout.add_widget(self.alert_threshold_spinbox)
        self.alert_threshold_layout.add_widget(self.alert_threshold_label)

        self.alerts_layout.add_layout(self.alert_checkbox_layout)
        self.alerts_layout.add_widget(self.alert_path_label)
        self.alerts_layout.add_layout(self.alert_path_layout)
        self.alerts_layout.add_layout(self.alert_threshold_layout)
        self.alerts_layout.add_spacer_item(self.get_spacer())

        self.alert_path_button.set_fixed_size(QtCore.QSize(24, 23))
        # endregion
        # region script group
        self.ahk_bind_edit = QtWidgets.QLineEdit(self.script_widget)
        self.ahk_script_edit = QtWidgets.QTextEdit(self.script_widget)

        self.script_layout.add_widget(self.ahk_bind_edit)
        self.script_layout.add_widget(self.ahk_script_edit)

        self.ahk_bind_edit.maximum_width = 100
        self.ahk_bind_edit.tool_tip = "Bind to trigger the script, # for win key, ! for alt, ^ for control, + for shift"
        self.alert_threshold_spinbox.maximum = 300
        self.alert_threshold_spinbox.accelerated = True
        self.alert_threshold_spinbox.maximum_width = 75
        self.alert_threshold_spinbox.suffix = "%"
        self.alert_threshold_label.word_wrap = True

        # endregion
        self.window_title = "Settings"
        self.group_selector.currentRowChanged.connect(
            partial(setattr, self.widget_selector, "current_index")
        )

        for button in self.find_children(QtWidgets.QPushButton):
            button.auto_default = False

        self.show()

    def get_spacer(self) -> QtWidgets.QSpacerItem:
        """Get an expanding spacer item."""
        return QtWidgets.QSpacerItem(
            1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
