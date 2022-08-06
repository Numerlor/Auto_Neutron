# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

import logging
from operator import attrgetter
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401

from auto_neutron import settings
from auto_neutron.constants import AHK_PATH
from auto_neutron.locale import code_from_locale, get_available_locales
from auto_neutron.settings import delay_sync

from .gui.settings_window import SettingsWindowGUI

log = logging.getLogger(__name__)


class SettingsWindow(SettingsWindowGUI):
    """Implement the settings functionality."""

    settings_applied = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None):
        super().__init__(parent)
        # pairs of widgets that we can assign directly to settings and the relevant settings
        self.settings_pairs = (
            (self.appearance_widget.dark_mode_checkbox, ("Window", "dark_mode")),
            (self.behaviour_widget.auto_scroll_checkbox, ("Window", "autoscroll")),
            (self.alerts_widget.alert_threshold_spinbox, ("Alerts", "threshold")),
            (self.alerts_widget.visual_alert_checkbox, ("Alerts", "visual")),
            (self.alerts_widget.audio_alert_checkbox, ("Alerts", "audio")),
            (self.alerts_widget.alert_path_line_edit, ("Paths", "alert_sound")),
            (self.script_widget.ahk_bind_edit, ("AHK", "bind")),
            (self.script_widget.ahk_script_edit, ("AHK", "user_script")),
            (self.script_widget.simple_mode_checkbox, ("AHK", "simple_mode")),
            (
                self.script_widget.simple_mode_widget.map_open_key_edit,
                ("AHK", "map_open_key"),
            ),
            (
                self.script_widget.simple_mode_widget.map_open_wait_spinbox,
                ("AHK", "map_open_wait_delay"),
            ),
            (
                self.script_widget.simple_mode_widget.navigate_right_key_edit,
                ("AHK", "navigate_right_key"),
            ),
            (
                self.script_widget.simple_mode_widget.focus_key_edit,
                ("AHK", "focus_key"),
            ),
            (
                self.script_widget.simple_mode_widget.submit_key_edit,
                ("AHK", "submit_key"),
            ),
            (self.behaviour_widget.save_on_quit_checkbox, ("General", "save_on_quit")),
            (self.behaviour_widget.copy_mode_checkbox, ("General", "copy_mode")),
        )
        self.refresh_widgets()

        if settings.Paths.ahk is None or not settings.Paths.ahk.exists():
            self.behaviour_widget.copy_mode_checkbox.enabled = False
            self.behaviour_widget.copy_mode_checkbox.checked = True

        self.behaviour_widget.ahk_path_button.pressed.connect(self.get_ahk_path)
        self.alerts_widget.alert_path_button.pressed.connect(self.get_sound_path)

        self.apply_button.pressed.connect(self.save_settings)
        self.apply_button.pressed.connect(self.settings_applied)
        self.ok_button.pressed.connect(self.settings_applied)
        self.ok_button.pressed.connect(self.save_settings)
        self.ok_button.pressed.connect(self.close)
        self.retranslate()

        locales = get_available_locales()
        active_locale_index = [code_from_locale(locale) for locale in locales].index(
            settings.General.locale
        )
        self.appearance_widget.language_combo.add_items(
            [locale.get_display_name() for locale in locales]
        )
        self.appearance_widget.language_combo.current_index = active_locale_index

    def get_ahk_path(self) -> None:
        """Ask the user for the AHK executable file path and save it to the setting."""
        path, __ = QtWidgets.QFileDialog.get_open_file_name(
            self,
            _("Select AHK executable"),
            str(AHK_PATH),
            filter=_("Executable files (*.exe)"),
        )
        if path:
            settings.Paths.ahk = Path(path)
            log.info(f"Setting ahk path to {path}")
            self.behaviour_widget.copy_mode_checkbox.enabled = True

    def get_sound_path(self) -> None:
        """Ask the user for the alert file path and save it to the line edit."""
        path, __ = QtWidgets.QFileDialog.get_open_file_name(
            self,
            _("Select alert file"),
            "",
            filter=_("Audio files (*.wav *.mp3);;All types (*.*)"),
        )
        if path:
            self.alerts_widget.alert_path_line_edit.text = str(Path(path))
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
        self.appearance_widget.font_bold_checkbox.checked = font.bold()
        self.appearance_widget.font_size_chooser.value = font.point_size()
        self.appearance_widget.font_chooser.current_font = font

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

            font = self.appearance_widget.font_chooser.current_font
            font.set_point_size(self.appearance_widget.font_size_chooser.value)
            font.set_bold(self.appearance_widget.font_bold_checkbox.checked)
            settings.Window.font = font

            settings.General.locale = code_from_locale(
                get_available_locales()[
                    self.appearance_widget.language_combo.current_index
                ]
            )

    def change_event(self, event: QtCore.QEvent) -> None:
        """Retranslate the GUI when a language change occurs."""
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslate()
