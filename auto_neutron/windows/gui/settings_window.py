# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

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


class AppearanceWidget(QtWidgets.QWidget):
    """Widget containing options for configuring the appearance of the app."""

    def __init__(self, parent: QtWidgets.QWidget | None):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.font_chooser = QtWidgets.QFontComboBox(self)
        self.font_size_chooser = QtWidgets.QSpinBox(self)
        self.font_bold_checkbox = QtWidgets.QCheckBox(self)

        self.language_label = QtWidgets.QLabel(self)
        self.language_combo = QtWidgets.QComboBox(self)
        self.language_combo.size_adjust_policy = (
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents
        )

        self.dark_mode_checkbox = _ReorderedCheckBox(self)
        self.dark_mode_checkbox.tristate = True

        self.font_layout = QtWidgets.QHBoxLayout()
        self.font_layout.add_widget(self.font_chooser)
        self.font_layout.add_widget(self.font_size_chooser)
        self.language_layout = QtWidgets.QHBoxLayout()
        self.language_layout.add_widget(self.language_label)
        self.language_layout.add_widget(self.language_combo)
        self.main_layout.add_layout(self.font_layout)
        self.main_layout.add_layout(self.language_layout)
        self.main_layout.add_widget(self.font_bold_checkbox)
        self.main_layout.add_widget(self.dark_mode_checkbox)
        self.main_layout.add_spacer_item(get_spacer())

        self.font_size_chooser.maximum_width = 50

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.font_bold_checkbox.text = _("Bold")
        self.language_label.text = _("Language")
        self.dark_mode_checkbox.text = _("Dark mode")


class BehaviourWidget(QtWidgets.QWidget):
    """Widget containing options for configuring the behaviour of the app."""

    def __init__(self, parent: QtWidgets.QWidget | None):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.plotter_options_layout = QtWidgets.QHBoxLayout()

        self.save_on_quit_checkbox = QtWidgets.QCheckBox(self)
        self.copy_mode_checkbox = QtWidgets.QCheckBox(self)
        self.ahk_path_button = QtWidgets.QPushButton(self)
        self.auto_scroll_checkbox = QtWidgets.QCheckBox(self)

        self.plotter_options_layout.add_widget(self.copy_mode_checkbox)
        self.plotter_options_layout.add_widget(self.ahk_path_button)

        self.main_layout.add_widget(self.save_on_quit_checkbox)
        self.main_layout.add_layout(self.plotter_options_layout)
        self.main_layout.add_widget(self.auto_scroll_checkbox)
        self.main_layout.add_spacer_item(get_spacer())
        self.ahk_path_button.maximum_width = 75

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.save_on_quit_checkbox.text = _("Save route on window close")
        self.copy_mode_checkbox.text = _("Copy Mode")
        self.ahk_path_button.text = _("AHK Path")
        self.auto_scroll_checkbox.text = _("Auto scroll")


class AlertsWidget(QtWidgets.QWidget):
    """Widget containing options for configuring the alert system."""

    def __init__(self, parent: QtWidgets.QWidget | None):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.alert_checkbox_layout = QtWidgets.QHBoxLayout()
        self.alert_path_layout = QtWidgets.QHBoxLayout()
        self.alert_threshold_layout = QtWidgets.QHBoxLayout()

        self.visual_alert_checkbox = QtWidgets.QCheckBox(self)
        self.audio_alert_checkbox = QtWidgets.QCheckBox(self)

        self.alert_path_label = QtWidgets.QLabel(self)
        self.alert_path_line_edit = QtWidgets.QLineEdit(self)
        self.alert_path_button = QtWidgets.QPushButton("...", self)

        self.alert_threshold_label = QtWidgets.QLabel(
            self,
        )
        self.alert_threshold_label.word_wrap = True

        self.alert_threshold_spinbox = QtWidgets.QSpinBox(self)
        self.alert_threshold_spinbox.maximum = 300
        self.alert_threshold_spinbox.accelerated = True
        self.alert_threshold_spinbox.maximum_width = 75
        self.alert_threshold_spinbox.suffix = "%"

        self.alert_checkbox_layout.add_widget(self.visual_alert_checkbox)
        self.alert_checkbox_layout.add_widget(self.audio_alert_checkbox)

        self.alert_path_layout.add_widget(self.alert_path_line_edit)
        self.alert_path_layout.add_widget(self.alert_path_button)

        self.alert_threshold_layout.add_widget(self.alert_threshold_spinbox)
        self.alert_threshold_layout.add_widget(self.alert_threshold_label)

        self.main_layout.add_layout(self.alert_checkbox_layout)
        self.main_layout.add_widget(self.alert_path_label)
        self.main_layout.add_layout(self.alert_path_layout)
        self.main_layout.add_layout(self.alert_threshold_layout)
        self.main_layout.add_spacer_item(get_spacer())

        self.alert_path_button.set_fixed_size(QtCore.QSize(24, 23))

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.visual_alert_checkbox.text = _("Taskbar fuel alert")
        self.audio_alert_checkbox.text = _("Sound fuel alert")
        self.alert_path_label.text = _("Custom sound alert file:")
        # Escape % for translation
        self.alert_threshold_label.text = _(
            "%% of maximum fuel usage left in tank before triggering alert"
        ).replace("%%", "%")


class SimpleScriptWidget(QtWidgets.QWidget):
    """Widget containing options used to configured the AHK simple mode."""

    def __init__(self, parent: QtWidgets.QWidget | None):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.contents_margins = QtCore.QMargins(0, 0, 0, 0)

        self._reference_label = QtWidgets.QLabel(self)
        self._reference_label.open_external_links = True

        self._map_open_key_label = QtWidgets.QLabel(self)
        self.map_open_key_edit = QtWidgets.QLineEdit(self)
        self.map_open_key_edit.maximum_width = 100

        self._map_open_wait_label = QtWidgets.QLabel(self)
        self.map_open_wait_spinbox = QtWidgets.QSpinBox(self)
        self.map_open_wait_spinbox.maximum_width = 100
        self.map_open_wait_spinbox.maximum = 10_000
        self.map_open_wait_spinbox.accelerated = True

        self._navigate_right_key_label = QtWidgets.QLabel(self)
        self.navigate_right_key_edit = QtWidgets.QLineEdit(self)
        self.navigate_right_key_edit.maximum_width = 100

        self._focus_key_label = QtWidgets.QLabel(self)
        self.focus_key_edit = QtWidgets.QLineEdit(self)
        self.focus_key_edit.maximum_width = 100

        self._submit_key_label = QtWidgets.QLabel(self)
        self.submit_key_edit = QtWidgets.QLineEdit(self)
        self.submit_key_edit.maximum_width = 100

        self.main_layout.add_widget(self._reference_label)
        self.main_layout.add_widget(self._map_open_key_label)
        self.main_layout.add_widget(self.map_open_key_edit)
        self.main_layout.add_widget(self._map_open_wait_label)
        self.main_layout.add_widget(self.map_open_wait_spinbox)
        self.main_layout.add_widget(self._navigate_right_key_label)
        self.main_layout.add_widget(self.navigate_right_key_edit)
        self.main_layout.add_widget(self._focus_key_label)
        self.main_layout.add_widget(self.focus_key_edit)
        self.main_layout.add_widget(self._submit_key_label)
        self.main_layout.add_widget(self.submit_key_edit)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self._map_open_key_label.text = _("Galaxy map open key")
        self._map_open_wait_label.text = _("Time to wait for galaxy map to open")
        self._navigate_right_key_label.text = _(
            "Key to use to navigate right in the map"
        )
        self._focus_key_label.text = _(
            "Key to use to focus onto the system input field"
        )
        self._submit_key_label.text = _("Key to submit the entered system")
        self._reference_label.text = (
            '<a href="https://www.autohotkey.com/docs/commands/Send.htm#Parameters">'
            + _("AutoHotKey key reference")
            + "</a>"
        )


class ScriptWidget(QtWidgets.QWidget):
    """Widget containing options for configuring the AHK script."""

    def __init__(self, parent: QtWidgets.QWidget | None):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.switch_widget = QtWidgets.QStackedWidget(self)

        self.simple_mode_checkbox = QtWidgets.QCheckBox(self)
        self.simple_mode_checkbox.stateChanged.connect(
            self.set_mode_widget_from_checkbox
        )

        self.ahk_bind_edit = QtWidgets.QLineEdit(self)
        self.ahk_bind_edit.maximum_width = 100

        self.ahk_script_edit = QtWidgets.QTextEdit(self.switch_widget)
        self.switch_widget.add_widget(self.ahk_script_edit)

        self.simple_mode_widget = SimpleScriptWidget(self)
        self.switch_widget.add_widget(self.simple_mode_widget)

        self.main_layout.add_widget(self.simple_mode_checkbox)
        self.main_layout.add_widget(self.ahk_bind_edit)
        self.main_layout.add_widget(self.switch_widget)

    def set_mode_widget_from_checkbox(self, state: int) -> None:
        """
        Set the current index of the switch widget from the checkbox's state.

        If the checkbox is not checked, set the index to 0, otherwise set it to 1.
        """
        if state == 2:
            # checked
            state = 1
        self.switch_widget.current_index = state

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.simple_mode_widget.retranslate()
        self.ahk_bind_edit.tool_tip = _(
            "Bind to trigger the script, # for win key, ! for alt, ^ for control, + for shift"
        )
        self.simple_mode_checkbox.text = _("Simple mode")
        self.simple_mode_checkbox.tool_tip = _(
            "With Simple mode enabled, a default script filled with the specified settings is used, "
            "if simple mode is not enabled, the script can be fully customized."
        )


class SettingsWindowGUI(QtWidgets.QDialog):
    """Implement the basic settings GUI with multiple settings categories from the settings module."""

    def __init__(self, parent: QtWidgets.QWidget | None):
        super().__init__(parent)
        self.set_attribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        # region layout/widget init
        self.appearance_widget = AppearanceWidget(self)
        self.behaviour_widget = BehaviourWidget(self)
        self.alerts_widget = AlertsWidget(self)
        self.script_widget = ScriptWidget(self)

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_c_layout = QtWidgets.QVBoxLayout()
        self.main_bottom_layout = QtWidgets.QHBoxLayout()
        # endregion
        # region main view
        self.group_selector = QtWidgets.QListWidget(self)
        self.widget_selector = QtWidgets.QStackedWidget(self)
        self.ok_button = QtWidgets.QPushButton(self)
        self.apply_button = QtWidgets.QPushButton(self)
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

        self.group_selector.horizontal_scroll_bar_policy = (
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.ok_button.maximum_width = 75
        self.apply_button.maximum_width = 75
        # endregion
        self.group_selector.currentRowChanged.connect(
            partial(setattr, self.widget_selector, "current_index")
        )

        for button in self.find_children(QtWidgets.QPushButton):
            button.auto_default = False

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.appearance_widget.retranslate()
        self.behaviour_widget.retranslate()
        self.alerts_widget.retranslate()
        self.script_widget.retranslate()

        self.ok_button.text = _("Ok")
        self.apply_button.text = _("Apply")
        index = self.group_selector.current_index()
        self.group_selector.clear()
        self.group_selector.add_items(
            (_("Appearance"), _("Behaviour"), _("Alerts"), _("AHK script"))
        )
        self.group_selector.set_current_index(index)
        self.group_selector.set_fixed_width(
            self.group_selector.size_hint_for_column(0) + 5
        )
        self.window_title = _("Settings")


def get_spacer() -> QtWidgets.QSpacerItem:
    """Get an expanding spacer item."""
    return QtWidgets.QSpacerItem(
        1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
    )
