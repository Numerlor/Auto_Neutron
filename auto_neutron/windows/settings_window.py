# This file is part of Auto_Neutron.
# Copyright (C) 2021  Numerlor

import typing as t
from operator import attrgetter

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron import settings
from auto_neutron.windows.gui.settings_window import SettingsWindowGUI


class SettingsWindow(SettingsWindowGUI):
    """Implement the settings functionality."""

    settings_applied = QtCore.Signal()

    def __init__(self, parent: t.Optional[QtWidgets.QWidget]):
        super().__init__(parent)
        # pairs of widgets that we can assign directly to settings and the relevant settings
        self.settings_pairs = (
            (self.dark_mode_checkbox, ("Window", "dark_mode")),
            (self.auto_scroll_checkbox, ("Window", "autoscroll")),
            (self.alert_threshold_spinbox, ("Alerts", "threshold")),
            (self.visual_alert_checkbox, ("Alerts", "visual")),
            (self.audio_alert_checkbox, ("Alerts", "audio")),
            (self.alert_path_line_edit, ("Paths", "alert_sound")),
            (self.ahk_bind_edit, ("General", "bind")),
            (self.ahk_script_edit, ("General", "script")),
            (self.save_on_quit_checkbox, ("General", "save_on_quit")),
            (self.copy_mode_checkbox, ("General", "copy_mode")),
        )
        self.refresh_widgets()
        self.apply_button.pressed.connect(self.save_settings)
        self.apply_button.pressed.connect(self.settings_applied)
        self.ok_button.pressed.connect(self.settings_applied)
        self.ok_button.pressed.connect(self.save_settings)
        self.ok_button.pressed.connect(self.close)

    def refresh_widgets(self) -> None:
        """Refresh the state of the widgets to reflect the current settings."""
        for widget, (setting_group, setting_name) in self.settings_pairs:
            setting_value = attrgetter(f"{setting_group}.{setting_name}")(settings)
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.checked = setting_value
            elif isinstance(widget, QtWidgets.QLineEdit):
                widget.text = (
                    str(setting_value) if setting_value is not None else ""
                )  # Sometimes this is a Path
            elif isinstance(widget, QtWidgets.QTextEdit):
                widget.plain_text = setting_value
            else:
                widget.value = setting_value

        font = settings.Window.font
        self.font_bold_checkbox.checked = font.bold()
        self.font_size_chooser.value = font.point_size()
        self.font_chooser.current_font = font

    def save_settings(self) -> None:
        """Save the settings from the widgets."""
        for widget, (setting_group, setting_name) in self.settings_pairs:
            settings_category = getattr(settings, setting_group)
            if isinstance(widget, QtWidgets.QCheckBox):
                setattr(settings_category, setting_name, widget.checked)
            elif isinstance(widget, QtWidgets.QLineEdit):
                setattr(settings_category, setting_name, widget.text)
            elif isinstance(widget, QtWidgets.QTextEdit):
                setattr(settings_category, setting_name, widget.plain_text)
            else:
                setattr(settings_category, setting_name, widget.value)

        font = self.font_chooser.current_font
        font.set_point_size(self.font_size_chooser.value)
        font.set_bold(self.font_bold_checkbox.checked)
        settings.Window.font = font
