# This file is part of Auto_Neutron.
# Copyright (C) 2019-2020  Numerlor
from pathlib import Path
from typing import List, Optional, Union

from PyQt5 import QtCore, QtGui, QtWidgets

from auto_neutron import settings, workers
from auto_neutron.constants import VERSION


class BasePopUp(QtWidgets.QDialog):
    """Base window for simple dialog popups."""

    def __init__(self, parent: Optional[QtWidgets.QWidget], prompt: str):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.info_label = QtWidgets.QLabel(prompt)
        self.x_spacer = QtWidgets.QSpacerItem(
            1, 1,
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.Fixed)
        self.y_spacer = QtWidgets.QSpacerItem(
            1, 1,
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.MinimumExpanding)

    def setup_ui(self) -> None:  # noqa D102
        self.main_layout.setContentsMargins(10, 20, 10, 10)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.info_label.setFont(font)
        self.main_layout.addWidget(self.info_label, alignment=QtCore.Qt.AlignCenter)
        self.main_layout.addSpacerItem(self.y_spacer)
        self.main_layout.addLayout(self.bottom_layout)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

    def add_widget(
            self,
            widget: QtWidgets.QWidget,
            alignment: Union[QtCore.Qt.Alignment, QtCore.Qt.AlignmentFlag] = QtCore.Qt.AlignCenter
    ) -> None:
        """Add `widget` to bottom of window."""
        self.bottom_layout.addWidget(widget, alignment)

    def add_layout(self, layout: QtWidgets.QLayout) -> None:
        """Add `layout` to bottom of window."""
        self.bottom_layout.addLayout(layout)


class RouteFinishedPop(BasePopUp):
    """
    Popup for finished route.

    Contains two buttons:
                          `quit_button` for exiting the app
                          `new_route_button` for starting a new route
    """

    close_signal = QtCore.pyqtSignal()
    new_route_signal = QtCore.pyqtSignal()

    def __init__(self, parent: Optional[QtWidgets.QWidget]):
        super().__init__(parent, "Route finished")
        self.quit_button = QtWidgets.QPushButton("Quit")
        self.new_route_button = QtWidgets.QPushButton("New route")
        self.button_layout = QtWidgets.QHBoxLayout()
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:  # noqa D102
        super().setup_ui()
        self.button_layout.addWidget(self.new_route_button)
        self.button_layout.addSpacerItem(self.x_spacer)
        self.button_layout.addWidget(self.quit_button)

        self.add_layout(self.button_layout)

    def connect_signals(self) -> None:  # noqa D102
        self.quit_button.pressed.connect(QtWidgets.QApplication.instance().quit)
        self.new_route_button.pressed.connect(self.new_route_signal.emit)
        self.new_route_button.pressed.connect(self.close)

    def closeEvent(self, *args, **kwargs) -> None:
        """Emit `close_signal` when window is closed."""
        super().closeEvent(*args, **kwargs)
        self.close_signal.emit()


class QuitDialog(BasePopUp):
    """
    Popup wth the option to quit the app.

    Contains one button:
                          `quit_button` for exiting the app
    If `modal` is True, the window is modal and user is forced to quit.
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget], prompt: str, modal: bool):
        super().__init__(parent, prompt)

        self.quit_button = QtWidgets.QPushButton(text="Quit", parent=parent)
        self.modal = modal
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:  # noqa D102
        super().setup_ui()
        self.quit_button.setMaximumWidth(95)
        self.add_widget(self.quit_button)
        self.setModal(self.modal)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

    def connect_signals(self) -> None:  # noqa D102
        self.quit_button.pressed.connect(QtWidgets.QApplication.instance().quit)


class GameShutPop(BasePopUp):
    """
    Popup for when the game is shut down.

    Contains three buttons:
                            `quit_button` for exiting the app
                            `journal_button` for continuing the route with
                                             a new journal file
                            `save_button` for saving the route
    """

    close_signal = QtCore.pyqtSignal()

    def __init__(self, parent: Optional[QtWidgets.QWidget], combo_items: List[str]):
        super().__init__(parent, "Game shut down")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.journal_combo = QtWidgets.QComboBox()
        self.journal_button = QtWidgets.QPushButton("Load journal")
        self.quit_button = QtWidgets.QPushButton("Quit")
        self.jour_ver = QtWidgets.QHBoxLayout()
        self.save_quit_lay = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("Save current route")

        self.combo_items = combo_items
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:  # noqa D102
        super().setup_ui()
        self.jour_ver.addWidget(self.journal_button, alignment=QtCore.Qt.AlignLeft)
        self.jour_ver.addWidget(self.journal_combo, alignment=QtCore.Qt.AlignCenter)
        self.jour_ver.addSpacerItem(self.x_spacer)

        self.save_quit_lay.addWidget(self.save_button, alignment=QtCore.Qt.AlignRight)
        self.save_quit_lay.addWidget(self.quit_button, alignment=QtCore.Qt.AlignRight)

        self.horizontalLayout.addLayout(self.jour_ver)
        self.horizontalLayout.addLayout(self.save_quit_lay)
        self.add_layout(self.horizontalLayout)

        self.journal_combo.addItems(self.combo_items)

        self.setModal(True)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

    def connect_signals(self) -> None:  # noqa D102
        self.quit_button.pressed.connect(QtWidgets.QApplication.instance().quit)
        self.journal_button.pressed.connect(self.close)

    def closeEvent(self, *args, **kwargs) -> None:
        """Emit `close_signal` when window is closed."""
        super().closeEvent(*args, **kwargs)
        self.close_signal.emit()


class CrashPop(BasePopUp):
    """
    Popup for showing an exception.

    Shows an exception text and forces user to quit through `quit_button`.
    """

    def __init__(self):
        super().__init__(None, "An unexpected error has occurred")
        self.text_browser = QtWidgets.QTextBrowser()
        self.quit_button = QtWidgets.QPushButton("Quit")
        self.layout = QtWidgets.QVBoxLayout()
        self.setup_ui()

    def setup_ui(self):  # noqa D102
        super().setup_ui()
        self.quit_button.pressed.connect(QtWidgets.QApplication.instance().quit)
        self.quit_button.setMaximumWidth(125)
        issues_html = "https://github.com/Numerlor/Auto_Neutron/issues/new"
        log_path = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)
        self.text_browser.insertHtml(
            f'Please make sure to report the bug at <br>'
            f'<a href="{issues_html}" style="color: #007bff">{issues_html}</a>,<br>'
            f'including the latest log file from<br>'
            f' <a href="{log_path}" style="color: #007bff">{log_path}</a>'
        )
        self.text_browser.setOpenExternalLinks(True)

        self.layout.addWidget(self.text_browser)
        self.layout.addWidget(self.quit_button, alignment=QtCore.Qt.AlignCenter)
        self.add_layout(self.layout)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setModal(True)


class LicensePop(QtWidgets.QDialog):
    """Window for license information."""

    close_signal = QtCore.pyqtSignal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super(LicensePop, self).__init__(parent)
        self.text = QtWidgets.QTextBrowser()
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setup_ui()

    def setup_ui(self) -> None:  # noqa D102
        self.setFixedSize(300, 125)
        self.setWindowTitle("Auto Neutron " + VERSION)
        self.text.insertHtml(
            'Auto_Neutron Copyright (C) 2019-2020 Numerlor<br><br>'
            'Auto_Neutron comes with ABSOLUTELY NO WARRANTY.<br>'
            'This is free software, and you are welcome to redistribute it under certain conditions; '
            '<a href="https://www.gnu.org/licenses/" style="color: #007bff">click here</a> '
            'for details'
        )
        self.main_layout.addWidget(self.text)
        self.text.setOpenExternalLinks(True)
        self.setLayout(self.main_layout)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def closeEvent(self, *args, **kwargs) -> None:
        """Emit `close_signal` when window is closed."""
        super().closeEvent(*args, **kwargs)
        self.close_signal.emit()


class Nearest(QtWidgets.QDialog):
    """GUI window for sending and displaying requests for nearest system."""

    RIGHT_ALIGN = QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter
    closed_signal = QtCore.pyqtSignal()
    destination_signal = QtCore.pyqtSignal(str)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent=parent)
        self.parameters = dict.fromkeys("xyz", 0)
        self.main_layout = QtWidgets.QGridLayout(self)
        self.status = QtWidgets.QStatusBar()

        self.system_label = QtWidgets.QLabel("System name", alignment=self.RIGHT_ALIGN)
        self.distance_label = QtWidgets.QLabel("Distance", alignment=self.RIGHT_ALIGN)

        self.distance_result = QtWidgets.QLabel()
        self.system_result = QtWidgets.QLabel()
        self.x_result = QtWidgets.QLabel()
        self.y_result = QtWidgets.QLabel()
        self.z_result = QtWidgets.QLabel()

        self.submit_button = QtWidgets.QPushButton("Send")
        self.setup_ui()

    def setup_ui(self) -> None:  # noqa D102
        self.setFixedSize(250, 188)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.main_layout.setSpacing(10)
        self.submit_button.setFixedWidth(65)
        self.status.setSizeGripEnabled(False)

        self.system_result.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.system_result.setCursor(QtCore.Qt.IBeamCursor)
        self.system_result.mouseDoubleClickEvent = lambda _: (
            self.destination_signal.emit(self.system_result.text())
        )
        # Add spinbox/ label pairs for each coord to grid.
        for i, coord_name in zip(range(2, 5), "xyz"):
            layout = QtWidgets.QHBoxLayout()
            spinbox = QtWidgets.QDoubleSpinBox(
                alignment=self.RIGHT_ALIGN,
                minimum=-100000,
                maximum=100000
            )
            label = QtWidgets.QLabel(coord_name.upper(), alignment=self.RIGHT_ALIGN)

            spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            spinbox.valueChanged.connect(self.update_parameters)
            # Set object name for identification when updating request params
            spinbox.setObjectName(coord_name)

            layout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding))
            layout.addWidget(spinbox)
            layout.addWidget(label)
            self.main_layout.addLayout(layout, i, 0)

        self.main_layout.addWidget(self.system_label, 0, 0)
        self.main_layout.addWidget(self.distance_label, 1, 0)

        self.main_layout.addWidget(self.system_result, 0, 1)
        self.main_layout.addWidget(self.distance_result, 1, 1)
        self.main_layout.addWidget(self.x_result, 2, 1)
        self.main_layout.addWidget(self.y_result, 3, 1)
        self.main_layout.addWidget(self.z_result, 4, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.submit_button.pressed.connect(self.send_request)
        self.main_layout.addWidget(self.status, 5, 0, 1, 2)

        self.main_layout.addWidget(self.submit_button, 5, 1, alignment=self.RIGHT_ALIGN)

    def update_parameters(self, value: int) -> None:
        """Update coordinate parameters with new value from spinboxes."""
        self.parameters[self.sender().objectName()] = value

    def send_request(self) -> None:
        """Create and start NearestWorker for getting coordinates from spansh."""
        self.request_worker = workers.NearestRequest(*self.parameters.values())
        self.request_worker.finished_signal.connect(self.set_target_values)
        self.request_worker.status_signal.connect(self.status.showMessage)
        self.request_worker.start()

    def set_target_values(self, system: str, distance: str, x: str, y: str, z: str) -> None:
        """Clear status bar and set target system values."""
        self.status.clearMessage()
        self.system_result.setText(system)
        self.distance_result.setText(f"{distance} Ly")
        self.x_result.setText(x)
        self.y_result.setText(y)
        self.z_result.setText(z)

    def closeEvent(self, *args, **kwargs) -> None:
        """Emit `close_signal` when window is closed."""
        super().closeEvent(*args, **kwargs)
        self.closed_signal.emit()


class SettingsPop(QtWidgets.QDialog):
    """
    UI window for editing settings.

    `settings_signal` is emitted when settings are changed.
    """

    settings_signal = QtCore.pyqtSignal()
    close_signal = QtCore.pyqtSignal()

    def __init__(self, parent: Optional[QtWidgets.QWidget]):
        super().__init__(parent)

        self.selector = QtWidgets.QListWidget(self)
        self.widget_selector = QtWidgets.QStackedWidget(self)
        self.appearance_layout = QtWidgets.QVBoxLayout()
        self.appearance = QtWidgets.QWidget()
        self.behaviour_layout = QtWidgets.QVBoxLayout()
        self.behaviour = QtWidgets.QWidget()
        self.alerts_layout = QtWidgets.QVBoxLayout()
        self.alerts = QtWidgets.QWidget()
        self.script_layout = QtWidgets.QVBoxLayout()
        self.script = QtWidgets.QWidget()

        self.widget_save_layout = QtWidgets.QVBoxLayout()
        self.bottom_layout = QtWidgets.QHBoxLayout()

        self.save = QtWidgets.QPushButton("Ok")
        self.apply = QtWidgets.QPushButton("Apply")
        self.error_label = QtWidgets.QLabel()

        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.font_layout = QtWidgets.QHBoxLayout()
        self.font_combo = QtWidgets.QFontComboBox()
        self.font_size_combo = QtWidgets.QSpinBox()
        self.bold_check = QtWidgets.QCheckBox("Bold")
        self.dark_check = QtWidgets.QCheckBox("Dark theme")

        self.save_on_quit = QtWidgets.QCheckBox("Save route on window close")
        self.copy_layout = QtWidgets.QHBoxLayout()
        self.ahk_button = QtWidgets.QPushButton("AHK Path")
        self.copy_check = QtWidgets.QCheckBox("Copy mode")
        self.autoscroll_check = QtWidgets.QCheckBox("Auto scroll")

        self.alert_layout = QtWidgets.QHBoxLayout()
        self.threshold_layout = QtWidgets.QHBoxLayout()
        self.alert_threshold_spin = QtWidgets.QSpinBox()
        self.alert_threshold_label = QtWidgets.QLabel()
        self.alert_sound_check = QtWidgets.QCheckBox("Sound fuel alert")
        self.alert_visual_check = QtWidgets.QCheckBox("Taskbar fuel alert")
        self.alert_path_layout = QtWidgets.QHBoxLayout()
        self.alert_path = QtWidgets.QLineEdit(str(settings.Paths.alert_sound))
        self.alert_dialog_button = QtWidgets.QPushButton("...")
        self.alert_path_label = QtWidgets.QLabel("Custom sound alert file")

        self.main_bind_edit = QtWidgets.QLineEdit(settings.General.bind)
        self.script_edit = QtWidgets.QTextEdit()

        self.ahk_path = settings.Paths.ahk
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:  # noqa D102
        self.setWindowTitle("Settings")

        self.bottom_layout.setSpacing(5)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(4, 4, 4, 4)
        self.widget_save_layout.setContentsMargins(0, 0, 0, 0)

        self.save.setMaximumWidth(75)
        self.apply.setMaximumWidth(75)
        self.font_size_combo.setMaximumWidth(50)
        self.ahk_button.setMaximumWidth(75)
        self.alert_dialog_button.setFixedSize(24, 23)
        self.main_bind_edit.setMaximumWidth(100)

        self.main_bind_edit.setToolTip(
            "Bind to trigger the script, # for win key, ! for alt, ^ for control, + for shift"
        )
        self.selector.addItems(("Appearance", "Behaviour", "Alerts", "AHK script"))
        self.selector.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.selector.setFixedWidth(self.selector.sizeHintForColumn(0) + 5)

        self.alert_threshold_spin.setSuffix("%")
        self.alert_threshold_spin.setMaximum(300)
        self.alert_threshold_spin.setAccelerated(True)
        self.alert_threshold_spin.setMaximumWidth(75)
        self.alert_threshold_label.setWordWrap(True)

        # Grab remaining settings and set the widget values to them
        self.script_edit.setText(settings.General.script)
        self.save_on_quit.setChecked(settings.General.save_on_quit)
        self.copy_check.setChecked(settings.General.copy_mode)

        self.dark_check.setChecked(settings.Window.dark_mode)
        self.autoscroll_check.setChecked(settings.Window.autoscroll)
        self.font_combo.setCurrentFont(settings.Window.font)
        self.font_size_combo.setValue(settings.Window.font.pointSize())
        self.bold_check.setChecked(settings.Window.font.bold())

        self.alert_threshold_spin.setValue(settings.Alerts.threshold)
        self.alert_sound_check.setChecked(settings.Alerts.audio)
        self.alert_visual_check.setChecked(settings.Alerts.visual)
        if not settings.Paths.ahk:
            self.copy_check.setDisabled(True)

        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.build_layouts()

    def build_layouts(self) -> None:
        """Add widgets and layouts to layouts. Separated from setup_ui for readability."""
        spacer = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding,
                                       QtWidgets.QSizePolicy.Expanding)
        self.widget_selector.addWidget(self.appearance)
        self.widget_selector.addWidget(self.behaviour)
        self.widget_selector.addWidget(self.alerts)
        self.widget_selector.addWidget(self.script)

        self.bottom_layout.addWidget(self.error_label)
        self.bottom_layout.addWidget(self.save)
        self.bottom_layout.addWidget(self.apply)

        self.widget_save_layout.addWidget(self.widget_selector)
        self.widget_save_layout.addLayout(self.bottom_layout)

        self.horizontalLayout.addWidget(self.selector)
        self.horizontalLayout.addLayout(self.widget_save_layout)

        self.font_layout.addWidget(self.font_combo)
        self.font_layout.addSpacerItem(QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding))
        self.font_layout.addWidget(self.font_size_combo)

        self.appearance_layout.addLayout(self.font_layout)
        self.appearance_layout.addWidget(self.bold_check)
        self.appearance_layout.addWidget(self.dark_check)
        self.appearance_layout.addSpacerItem(spacer)
        self.appearance.setLayout(self.appearance_layout)

        self.copy_layout.addWidget(self.copy_check)
        self.copy_layout.addWidget(self.ahk_button)
        self.behaviour_layout.addWidget(self.save_on_quit)

        self.behaviour_layout.addLayout(self.copy_layout)
        self.behaviour_layout.addWidget(self.autoscroll_check)
        self.behaviour_layout.addSpacerItem(spacer)
        self.behaviour.setLayout(self.behaviour_layout)

        self.alert_path_layout.addWidget(self.alert_path)
        self.alert_path_layout.addWidget(self.alert_dialog_button)
        self.alert_layout.addWidget(self.alert_visual_check)
        self.alert_layout.addWidget(self.alert_sound_check)
        self.alerts_layout.addLayout(self.alert_layout)
        self.threshold_layout.addWidget(self.alert_threshold_label)
        self.threshold_layout.addWidget(self.alert_threshold_spin)
        self.alerts_layout.addWidget(self.alert_path_label)
        self.alerts_layout.addLayout(self.alert_path_layout)
        self.alerts_layout.addLayout(self.threshold_layout)
        self.alerts_layout.addSpacerItem(spacer)
        self.alerts.setLayout(self.alerts_layout)

        self.script_layout.addWidget(self.main_bind_edit)
        self.script_layout.addWidget(self.script_edit)
        self.script.setLayout(self.script_layout)

    def connect_signals(self) -> None:  # noqa D102
        self.save.pressed.connect(lambda: self.save_settings(close=True))
        self.apply.pressed.connect(lambda: self.save_settings(close=False))
        self.ahk_button.pressed.connect(self.enable_copy_mode)
        self.selector.currentRowChanged.connect(self.widget_selector.setCurrentIndex)
        self.alert_dialog_button.pressed.connect(self.sound_path_dialog)

    def enable_copy_mode(self) -> None:
        """Allow use of ahk mode after a valid path was set."""
        ahk_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            filter="AutoHotkey (AutoHotkey*.exe)",
            caption="Select AutoHotkey's executable.",
            directory="C:/")

        if ahk_path:
            self.ahk_path = Path(ahk_path)
            self.copy_check.setEnabled(True)
        else:
            self.ahk_path = None
            self.copy_check.setChecked(True)
            self.copy_check.setEnabled(False)

    def sound_path_dialog(self) -> None:
        """Open a file dialog, set `self.alert_path`'s text to file if one was selected."""
        sound_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            caption="Notification audio file")
        if sound_path:
            self.alert_path.setText(sound_path)

    def save_settings(self, *, close: bool) -> None:
        """
        Write current states of all settings widgets to settings.

        Error is displayed if ahk script doesn't include |SYSTEMDATA|-
        If `close` is True the settings window is closed.
        """
        if "|SYSTEMDATA|" not in self.script_edit.toPlainText():
            self.error_label.setText('Script must include "|SYSTEMDATA|"')
        else:
            self.error_label.clear()

            settings.General.bind = self.main_bind_edit.text()
            settings.General.script = self.script_edit.toPlainText()
            settings.General.save_on_quit = self.save_on_quit.isChecked()
            settings.General.copy_mode = self.copy_check.isChecked()

            settings.Window.dark_mode = self.dark_check.isChecked()
            font = self.font_combo.currentFont()
            font.setBold(self.bold_check.isChecked())
            font.setPointSize(self.font_size_combo.value())
            settings.Window.font = font
            settings.Window.autoscroll = self.autoscroll_check.isChecked()

            settings.Alerts.audio = self.alert_sound_check.isChecked()
            settings.Alerts.visual = self.alert_visual_check.isChecked()
            settings.Alerts.threshold = self.alert_threshold_spin.value()

            settings.Paths.alert_sound = self.alert_path.text()
            settings.Paths.ahk = self.ahk_path
            self.settings_signal.emit()
            if close:
                self.close()

    def closeEvent(self, *args, **kwargs) -> None:
        """Emit `close_signal` when window is closed."""
        super(QtWidgets.QDialog, self).closeEvent(*args, **kwargs)
        self.close_signal.emit()
