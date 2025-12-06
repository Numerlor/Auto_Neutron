# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class _ReorderedCheckBox(QtWidgets.QCheckBox):
    """Checkbox with check states reordered so the partial state appears after both unchecked and checked."""

    _CHECK_STATES = [
        QtCore.Qt.CheckState.Unchecked,
        QtCore.Qt.CheckState.Checked,
        QtCore.Qt.CheckState.PartiallyChecked,
    ]

    def nextCheckState(self) -> None:
        """Set the next state."""
        self.setCheckState(
            self._CHECK_STATES[(self._CHECK_STATES.index(self.checkState()) + 1) % 3]
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
        self.language_combo.setSizeAdjustPolicy(
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents
        )

        self.dark_mode_checkbox = _ReorderedCheckBox(self)
        self.dark_mode_checkbox.setTristate(True)

        self.font_layout = QtWidgets.QHBoxLayout()
        self.font_layout.addWidget(self.font_chooser)
        self.font_layout.addWidget(self.font_size_chooser)
        self.language_layout = QtWidgets.QHBoxLayout()
        self.language_layout.addWidget(self.language_label)
        self.language_layout.addWidget(self.language_combo)
        self.main_layout.addLayout(self.font_layout)
        self.main_layout.addLayout(self.language_layout)
        self.main_layout.addWidget(self.font_bold_checkbox)
        self.main_layout.addWidget(self.dark_mode_checkbox)
        self.main_layout.addSpacerItem(get_spacer())

        self.font_size_chooser.setMaximumWidth(50)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.font_bold_checkbox.setText(_("Bold"))
        self.language_label.setText(_("Language"))
        self.dark_mode_checkbox.setText(_("Dark mode"))


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
        self.loop_routes_checkbox = QtWidgets.QCheckBox(self)

        self.plotter_options_layout.addWidget(self.copy_mode_checkbox)
        self.plotter_options_layout.addWidget(self.ahk_path_button)

        self.main_layout.addWidget(self.save_on_quit_checkbox)
        self.main_layout.addLayout(self.plotter_options_layout)
        self.main_layout.addWidget(self.auto_scroll_checkbox)
        self.main_layout.addWidget(self.loop_routes_checkbox)
        self.main_layout.addSpacerItem(get_spacer())
        self.ahk_path_button.setMaximumWidth(75)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.save_on_quit_checkbox.setText(_("Save route on window close"))
        self.copy_mode_checkbox.setText(_("Copy Mode"))
        self.ahk_path_button.setText(_("AHK Path"))
        self.auto_scroll_checkbox.setText(_("Auto scroll"))
        self.loop_routes_checkbox.setText(_("Loop routes"))


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
        self.alert_threshold_label.setWordWrap(True)

        self.alert_threshold_spinbox = QtWidgets.QSpinBox(self)
        self.alert_threshold_spinbox.setMaximum(300)
        self.alert_threshold_spinbox.setAccelerated(True)
        self.alert_threshold_spinbox.setMaximumWidth(75)
        self.alert_threshold_spinbox.setSuffix("%")

        self.alert_checkbox_layout.addWidget(self.visual_alert_checkbox)
        self.alert_checkbox_layout.addWidget(self.audio_alert_checkbox)

        self.alert_path_layout.addWidget(self.alert_path_line_edit)
        self.alert_path_layout.addWidget(self.alert_path_button)

        self.alert_threshold_layout.addWidget(self.alert_threshold_spinbox)
        self.alert_threshold_layout.addWidget(self.alert_threshold_label)

        self.main_layout.addLayout(self.alert_checkbox_layout)
        self.main_layout.addWidget(self.alert_path_label)
        self.main_layout.addLayout(self.alert_path_layout)
        self.main_layout.addLayout(self.alert_threshold_layout)
        self.main_layout.addSpacerItem(get_spacer())

        self.alert_path_button.setFixedSize(QtCore.QSize(24, 23))

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.visual_alert_checkbox.setText(_("Taskbar fuel alert"))
        self.audio_alert_checkbox.setText(_("Sound fuel alert"))
        self.alert_path_label.setText(_("Custom sound alert file:"))
        # Escape % for translation
        self.alert_threshold_label.setText(
            _("%% of maximum fuel usage left in tank before triggering alert").replace(
                "%%", "%"
            )
        )


class SimpleScriptWidget(QtWidgets.QWidget):
    """Widget containing options used to configured the AHK simple mode."""

    def __init__(self, parent: QtWidgets.QWidget | None):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))

        self._reference_label = QtWidgets.QLabel(self)
        self._reference_label.setOpenExternalLinks(True)

        self._map_open_key_label = QtWidgets.QLabel(self)
        self.map_open_key_edit = QtWidgets.QLineEdit(self)
        self.map_open_key_edit.setMaximumWidth(100)

        self._map_open_wait_label = QtWidgets.QLabel(self)
        self.map_open_wait_spinbox = QtWidgets.QSpinBox(self)
        self.map_open_wait_spinbox.setMaximumWidth(100)
        self.map_open_wait_spinbox.setMaximum(10_000)
        self.map_open_wait_spinbox.setAccelerated(True)

        self._navigate_right_key_label = QtWidgets.QLabel(self)
        self.navigate_right_key_edit = QtWidgets.QLineEdit(self)
        self.navigate_right_key_edit.setMaximumWidth(100)

        self._focus_key_label = QtWidgets.QLabel(self)
        self.focus_key_edit = QtWidgets.QLineEdit(self)
        self.focus_key_edit.setMaximumWidth(100)

        self._submit_key_label = QtWidgets.QLabel(self)
        self.submit_key_edit = QtWidgets.QLineEdit(self)
        self.submit_key_edit.setMaximumWidth(100)

        self.main_layout.addWidget(self._reference_label)
        self.main_layout.addWidget(self._map_open_key_label)
        self.main_layout.addWidget(self.map_open_key_edit)
        self.main_layout.addWidget(self._map_open_wait_label)
        self.main_layout.addWidget(self.map_open_wait_spinbox)
        self.main_layout.addWidget(self._navigate_right_key_label)
        self.main_layout.addWidget(self.navigate_right_key_edit)
        self.main_layout.addWidget(self._focus_key_label)
        self.main_layout.addWidget(self.focus_key_edit)
        self.main_layout.addWidget(self._submit_key_label)
        self.main_layout.addWidget(self.submit_key_edit)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self._map_open_key_label.setText(_("Galaxy map open key"))
        self._map_open_wait_label.setText(_("Time to wait for galaxy map to open"))
        self._navigate_right_key_label.setText(
            _("Key to use to navigate right in the map")
        )
        self._focus_key_label.setText(
            _("Key to use to focus onto the system input field")
        )
        self._submit_key_label.setText(_("Key to submit the entered system"))
        self._reference_label.setText(
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
        self.ahk_bind_edit.setMaximumWidth(100)

        self.ahk_script_edit = QtWidgets.QTextEdit(self.switch_widget)
        self.switch_widget.addWidget(self.ahk_script_edit)

        self.simple_mode_widget = SimpleScriptWidget(self)
        self.switch_widget.addWidget(self.simple_mode_widget)

        self.main_layout.addWidget(self.simple_mode_checkbox)
        self.main_layout.addWidget(self.ahk_bind_edit)
        self.main_layout.addWidget(self.switch_widget)

    @QtCore.Slot(int)
    def set_mode_widget_from_checkbox(self, state: int) -> None:
        """
        Set the current index of the switch widget from the checkbox's state.

        If the checkbox is not checked, set the index to 0, otherwise set it to 1.
        """
        if state == 2:
            # checked
            state = 1
        self.switch_widget.setCurrentIndex(state)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.simple_mode_widget.retranslate()
        self.ahk_bind_edit.setToolTip(
            _(
                "Bind to trigger the script, # for win key, ! for alt, ^ for control, + for shift"
            )
        )
        self.simple_mode_checkbox.setText(_("Simple mode"))
        self.simple_mode_checkbox.setToolTip(
            _(
                "With Simple mode enabled, a default script filled with the specified settings is used, "
                "if simple mode is not enabled, the script can be fully customized."
            )
        )


class SettingsWindowGUI(QtWidgets.QDialog):
    """Implement the basic settings GUI with multiple settings categories from the settings module."""

    def __init__(self, parent: QtWidgets.QWidget | None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
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
        self.main_bottom_layout.addWidget(self.error_label)
        self.main_bottom_layout.addWidget(self.ok_button)
        self.main_bottom_layout.addWidget(self.apply_button)

        self.main_bottom_layout.setSpacing(5)

        self.main_c_layout.addWidget(self.widget_selector)
        self.main_c_layout.addLayout(self.main_bottom_layout)
        self.main_c_layout.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))
        self.main_layout.addWidget(self.group_selector)
        self.main_layout.addLayout(self.main_c_layout)
        self.main_layout.setContentsMargins(QtCore.QMargins(4, 4, 4, 4))
        self.main_layout.setSpacing(0)
        # endregion
        self.widget_selector.addWidget(self.appearance_widget)
        self.widget_selector.addWidget(self.behaviour_widget)
        self.widget_selector.addWidget(self.alerts_widget)
        self.widget_selector.addWidget(self.script_widget)

        self.group_selector.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.ok_button.setMaximumWidth(75)
        self.apply_button.setMaximumWidth(75)
        # endregion
        self.group_selector.currentRowChanged.connect(
            self.widget_selector.setCurrentIndex
        )

        for button in self.findChildren(QtWidgets.QPushButton):
            button.setAutoDefault(False)

    def retranslate(self) -> None:
        """Retranslate text that is always on display."""
        self.appearance_widget.retranslate()
        self.behaviour_widget.retranslate()
        self.alerts_widget.retranslate()
        self.script_widget.retranslate()

        self.ok_button.setText(_("Ok"))
        self.apply_button.setText(_("Apply"))
        index = self.group_selector.currentIndex()
        self.group_selector.clear()
        self.group_selector.addItems(
            (_("Appearance"), _("Behaviour"), _("Alerts"), _("AHK script"))
        )
        self.group_selector.setCurrentIndex(index)
        self.group_selector.setFixedWidth(self.group_selector.sizeHintForColumn(0) + 5)
        self.setWindowTitle(_("Settings"))


def get_spacer() -> QtWidgets.QSpacerItem:
    """Get an expanding spacer item."""
    return QtWidgets.QSpacerItem(
        1,
        1,
        QtWidgets.QSizePolicy.Policy.Expanding,
        QtWidgets.QSizePolicy.Policy.Expanding,
    )
