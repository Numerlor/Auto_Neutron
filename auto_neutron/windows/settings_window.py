# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

import logging
import typing as t
from operator import attrgetter
from pathlib import Path

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa: F401
from auto_neutron import settings
from auto_neutron.constants import AHK_PATH
from auto_neutron.settings.category_meta import delay_sync
from auto_neutron.windows.gui.settings_window import SettingsWindowGUI

log = logging.getLogger(__name__)


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

        if settings.Paths.ahk is None or not settings.Paths.ahk.exists():
            self.copy_mode_checkbox.enabled = False
            self.copy_mode_checkbox.checked = True

        self.ahk_path_button.pressed.connect(self.get_ahk_path)
        self.alert_path_button.pressed.connect(self.get_sound_path)

        self.apply_button.pressed.connect(self.save_settings)
        self.apply_button.pressed.connect(self.settings_applied)
        self.ok_button.pressed.connect(self.settings_applied)
        self.ok_button.pressed.connect(self.save_settings)
        self.ok_button.pressed.connect(self.close)

    def get_ahk_path(self) -> None:
        """Ask the user for the AHK executable file path and save it to the setting."""
        path, _ = QtWidgets.QFileDialog.get_open_file_name(
            self,
            "Select AHK executable",
            str(AHK_PATH),
            filter="Executable files (*.exe)",
        )
        if path:
            settings.Paths.ahk = Path(path)
            log.info("Setting ahk path to {path}")
            self.copy_mode_checkbox.enabled = True

    def get_sound_path(self) -> None:
        """Ask the user for the alert file path and save it to the line edit."""
        path, _ = QtWidgets.QFileDialog.get_open_file_name(
            self,
            "Select alert file",
            "",
            filter="Audio files (*.wav *.mp3);;All types (*.*)",
        )
        if path:
            self.alert_path_line_edit.text = str(Path(path))
            settings.Paths.alert_sound = Path(path)

    def refresh_widgets(self) -> None:
        """Refresh the state of the widgets to reflect the current settings."""
        for widget, (setting_group, setting_name) in self.settings_pairs:
            setting_value = attrgetter(f"{setting_group}.{setting_name}")(settings)
            if isinstance(widget, QtWidgets.QCheckBox):
                if not widget.tristate and setting_value:
                    # We're saving bools but Qt has PartiallyChecked for 1 in the enum
                    setting_value = QtCore.Qt.CheckState.Checked
                widget.set_check_state(QtCore.Qt.CheckState(setting_value))
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
        with delay_sync():
            for widget, (setting_group, setting_name) in self.settings_pairs:
                settings_category = getattr(settings, setting_group)
                if isinstance(widget, QtWidgets.QCheckBox):
                    if widget.tristate:
                        converter = int
                    else:
                        converter = bool
                    setattr(
                        settings_category, setting_name, converter(widget.check_state())
                    )
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
