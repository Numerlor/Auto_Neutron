import os
from pathlib import Path

from PyQt5 import QtWidgets, QtCore, QtGui

from auto_neutron import workers
from auto_neutron.constants import VERSION
from auto_neutron.settings import Settings


class BasePopUp(QtWidgets.QDialog):

    def __init__(self, parent, prompt: str):
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

    def setup_ui(self):
        self.main_layout.setContentsMargins(10, 20, 10, 10)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.info_label.setFont(font)
        self.main_layout.addWidget(self.info_label, alignment=QtCore.Qt.AlignCenter)
        self.main_layout.addSpacerItem(self.y_spacer)
        self.main_layout.addLayout(self.bottom_layout)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

    def add_widget(self, widget, alignment=QtCore.Qt.AlignCenter):
        self.bottom_layout.addWidget(widget, alignment)

    def add_layout(self, layout):
        self.bottom_layout.addLayout(layout)


class RouteFinishedPop(BasePopUp):
    close_signal = QtCore.pyqtSignal()
    new_route_signal = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent, "Route finished")
        self.quit_button = QtWidgets.QPushButton("Quit")
        self.new_route_button = QtWidgets.QPushButton("New route")
        self.button_layout = QtWidgets.QHBoxLayout()
        self.setup_ui()

    def setup_ui(self):
        super().setup_ui()
        self.button_layout.addWidget(self.new_route_button)
        self.button_layout.addSpacerItem(self.x_spacer)
        self.button_layout.addWidget(self.quit_button)

        self.add_layout(self.button_layout)

        self.quit_button.pressed.connect(QtWidgets.QApplication.instance().quit)
        self.new_route_button.pressed.connect(self.new_route_signal.emit)
        self.new_route_button.pressed.connect(self.close)

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QDialog, self).closeEvent(*args, **kwargs)
        self.close_signal.emit()


class QuitDialog(BasePopUp):
    def __init__(self, parent, prompt, modal):
        super().__init__(parent, prompt)

        self.pushButton = QtWidgets.QPushButton(text="Quit", parent=parent)
        self.modal = modal
        self.setup_ui()

    def setup_ui(self):
        super().setup_ui()
        self.pushButton.setMaximumWidth(95)
        self.pushButton.pressed.connect(QtWidgets.QApplication.instance().quit)
        self.add_widget(self.pushButton)

        self.setModal(self.modal)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)


class GameShutPop(BasePopUp):
    worker_signal = QtCore.pyqtSignal(list, Path, int)  # signal to start new worker
    # signal to disconnect all main window signals if app is not quit or new worker is not started
    close_signal = QtCore.pyqtSignal()

    def __init__(self, parent, settings, route, index):
        super().__init__(parent, "Game shut down")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.journal_combo = QtWidgets.QComboBox()
        self.journal_button = QtWidgets.QPushButton("Load journal")
        self.quit_button = QtWidgets.QPushButton("Quit")
        self.jour_ver = QtWidgets.QHBoxLayout()
        self.save_quit_lay = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("Save current route")
        self.route = route
        self.index = index
        self.settings = settings
        self.jpath = Path(self.settings.paths.journal)
        self.setup_ui()

    def setup_ui(self):
        super().setup_ui()
        self.jour_ver.addWidget(self.journal_button, alignment=QtCore.Qt.AlignLeft)
        self.jour_ver.addWidget(self.journal_combo, alignment=QtCore.Qt.AlignCenter)
        self.jour_ver.addSpacerItem(self.x_spacer)

        self.save_quit_lay.addWidget(self.save_button, alignment=QtCore.Qt.AlignRight)
        self.save_quit_lay.addWidget(self.quit_button, alignment=QtCore.Qt.AlignRight)

        self.horizontalLayout.addLayout(self.jour_ver)
        self.horizontalLayout.addLayout(self.save_quit_lay)
        self.add_layout(self.horizontalLayout)

        self.quit_button.pressed.connect(QtWidgets.QApplication.instance().quit)
        self.save_button.pressed.connect(self.save_route)
        self.journal_button.pressed.connect(self.load_journal)
        self.journal_button.pressed.connect(lambda: self.journal_button.setDisabled(True))

        self.populate_combo()

        self.setModal(True)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)

    def save_route(self):
        self.settings.last_route = (self.index, self.route)
        self.save_button.setDisabled(True)

    def populate_combo(self):
        self.journal_combo.addItems(["Last journal", "Second to last",
                                     "Third to last"][:len([file for file
                                                            in os.listdir(self.jpath)
                                                            if file.endswith(".log")])])

    def load_journal(self):
        journals = sorted([self.jpath / file for file
                           in os.listdir(self.jpath)
                           if file.endswith(".log")],
                          key=os.path.getctime, reverse=True)
        self.worker_signal.emit(self.route, journals[self.journal_combo.currentIndex()],
                                self.index)
        self.hide()

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QDialog, self).closeEvent(*args, **kwargs)
        self.close_signal.emit()


class CrashPop(BasePopUp):
    def __init__(self):
        super().__init__(None, "An unexpected error has occurred")
        self.text_browser = QtWidgets.QTextBrowser()
        self.quit_button = QtWidgets.QPushButton("Quit")
        self.layout = QtWidgets.QVBoxLayout()
        self.setup_ui()

    def setup_ui(self):
        super().setup_ui()
        self.quit_button.pressed.connect(QtWidgets.QApplication.instance().quit)
        self.quit_button.setMaximumWidth(125)
        self.layout.addWidget(self.text_browser)
        self.layout.addWidget(self.quit_button, alignment=QtCore.Qt.AlignCenter)
        self.add_layout(self.layout)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setModal(True)

    def add_traceback(self, traceback):
        for line in traceback:
            self.text_browser.append(line)


class LicensePop(QtWidgets.QDialog):
    close_signal = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(LicensePop, self).__init__(parent)
        self.text = QtWidgets.QTextBrowser()
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setup_ui()

    def setup_ui(self):
        self.setFixedSize(300, 125)
        self.setWindowTitle("Auto Neutron " + VERSION)
        self.text.setText("Auto Neutron Copyright (C) 2019 Numerlor\n"
                          "This program comes with ABSOLUTELY NO WARRANTY.\n"
                          "This is free software, and you are welcome to redistribute it")
        self.text.append('under certain conditions; <a href="https://www'
                         '.gnu.org/licenses/">click here</a> for details')
        self.main_layout.addWidget(self.text)
        self.text.setOpenExternalLinks(True)
        self.setLayout(self.main_layout)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QDialog, self).closeEvent(*args, **kwargs)
        self.close_signal.emit()


class Nearest(QtWidgets.QDialog):
    """GUI window for sending and displaying requests for nearest system."""
    RIGHT_ALIGN = QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter
    closed_signal = QtCore.pyqtSignal()
    destination_signal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
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

    def setup_ui(self):
        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.MinimumExpanding)
        right_align = QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter

        self.setFixedSize(250, 188)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.main_layout.setSpacing(10)
        self.submit_button.setFixedWidth(65)
        self.status.setSizeGripEnabled(False)

        self.system_result.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.system_result.setCursor(QtCore.Qt.IBeamCursor)
        self.system_result.mouseDoubleClickEvent = lambda _: self.destination_signal.emit(self.system_result.text())
        # Add spinbox/ label pairs for each coord to grid.
        for i, coord_name in zip(range(2, 5), "xyz"):
            layout = QtWidgets.QHBoxLayout()
            spinbox = QtWidgets.QDoubleSpinBox(alignment=self.RIGHT_ALIGN, minimum=-100000, maximum=100000)
            label = QtWidgets.QLabel(coord_name.upper(), alignment=self.RIGHT_ALIGN)

            spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            spinbox.valueChanged.connect(self.update_parameters)
            spinbox.setObjectName(coord_name)  # Set object name for identification when updating request params

            layout.addSpacerItem(spacer)
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

        self.main_layout.addWidget(self.submit_button, 5, 1, alignment=QtCore.Qt.AlignRight)

    def update_parameters(self, value):
        """Update parameters to reflect changed value."""
        self.parameters[self.sender().objectName()] = value

    def send_request(self):
        self.request_worker = workers.NearestRequest(self.parameters)
        self.request_worker.finished_signal.connect(self.process_response)
        self.request_worker.status_signal.connect(self.status.showMessage)
        self.request_worker.start()

    def process_response(self, system):
        self.request_worker.quit()
        self.status.clearMessage()
        self.system_result.setText(str(system['name']))
        self.distance_result.setText(f"{round(system['distance'], 2)} Ly")
        self.x_result.setText(str(round(system['x'], 2)))
        self.y_result.setText(str(round(system['y'], 2)))
        self.z_result.setText(str(round(system['z'], 2)))

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QDialog, self).closeEvent(*args, **kwargs)
        self.closed_signal.emit()


class SettingsPop(QtWidgets.QDialog):
    settings_signal = QtCore.pyqtSignal()
    close_signal = QtCore.pyqtSignal()

    def __init__(self, parent, settings: Settings):
        super(SettingsPop, self).__init__(parent)
        self.widget_save_layout = QtWidgets.QVBoxLayout()
        self.bottom_layout = QtWidgets.QHBoxLayout()

        self.main_bind_edit = QtWidgets.QLineEdit()
        self.script_edit = QtWidgets.QTextEdit()
        self.dark_check = QtWidgets.QCheckBox()
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.font_layout = QtWidgets.QHBoxLayout()
        self.font_combo = QtWidgets.QFontComboBox()
        self.font_size_combo = QtWidgets.QSpinBox()
        self.bold_check = QtWidgets.QCheckBox()
        self.save = QtWidgets.QPushButton()
        self.apply = QtWidgets.QPushButton()
        self.save_on_quit = QtWidgets.QCheckBox()
        self.copy_layout = QtWidgets.QHBoxLayout()
        self.ahk_button = QtWidgets.QPushButton()
        self.copy_check = QtWidgets.QCheckBox()
        self.autoscroll_check = QtWidgets.QCheckBox()

        self.alert_layout = QtWidgets.QHBoxLayout()
        self.threshold_layout = QtWidgets.QHBoxLayout()
        self.alert_threshold_spin = QtWidgets.QSpinBox()
        self.alert_threshold_label = QtWidgets.QLabel()
        self.alert_sound_check = QtWidgets.QCheckBox()
        self.alert_visual_check = QtWidgets.QCheckBox()
        self.alert_path_layout = QtWidgets.QHBoxLayout()
        self.alert_path = QtWidgets.QLineEdit()
        self.alert_dialog_button = QtWidgets.QToolButton()
        self.alert_path_label = QtWidgets.QLabel()

        self.settings = settings
        self.error_label = QtWidgets.QLabel()

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
        self.setup_ui()

    def setup_ui(self):
        self.resize(265, 371)
        self.main_bind_edit.setMaximumWidth(100)
        spacer = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding,
                                       QtWidgets.QSizePolicy.Expanding)

        self.bottom_layout.addWidget(self.error_label)
        self.bottom_layout.addWidget(self.save)
        self.bottom_layout.addWidget(self.apply)
        self.bottom_layout.setSpacing(5)

        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(4, 4, 4, 4)
        self.font_size_combo.setMaximumWidth(50)
        self.save.setMaximumWidth(75)
        self.apply.setMaximumWidth(75)
        self.save.pressed.connect(lambda: self.save_settings(close=True))
        self.apply.pressed.connect(self.save_settings)

        self.horizontalLayout.addWidget(self.selector)
        self.selector.addItems(("Appearance", "Behaviour", "Alerts", "AHK script"))
        self.selector.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.selector.setFixedWidth(self.selector.sizeHintForColumn(0) + 5)

        self.selector.currentRowChanged.connect(self.widget_selector.setCurrentIndex)
        self.widget_selector.addWidget(self.appearance)
        self.widget_selector.addWidget(self.behaviour)
        self.widget_selector.addWidget(self.alerts)
        self.widget_selector.addWidget(self.script)

        self.widget_save_layout.setContentsMargins(0, 0, 0, 0)
        self.widget_save_layout.addWidget(self.widget_selector)
        self.widget_save_layout.addLayout(self.bottom_layout)
        self.horizontalLayout.addLayout(self.widget_save_layout)

        self.font_layout.addWidget(self.font_combo)
        self.font_layout.addWidget(self.font_size_combo)

        self.appearance_layout.addLayout(self.font_layout)
        self.appearance_layout.addWidget(self.bold_check)
        self.appearance_layout.addWidget(self.dark_check)
        self.appearance_layout.addSpacerItem(spacer)
        self.appearance.setLayout(self.appearance_layout)

        self.script_layout.addWidget(self.main_bind_edit)
        self.script_layout.addWidget(self.script_edit)
        self.script.setLayout(self.script_layout)

        self.copy_layout.addWidget(self.copy_check)
        self.copy_layout.addWidget(self.ahk_button)
        self.behaviour_layout.addWidget(self.save_on_quit)

        self.behaviour_layout.addLayout(self.copy_layout)
        self.behaviour_layout.addWidget(self.autoscroll_check)
        self.behaviour_layout.addSpacerItem(spacer)
        self.behaviour.setLayout(self.behaviour_layout)

        self.alert_threshold_spin.setSuffix("%")
        self.alert_threshold_spin.setMaximum(300)
        self.alert_threshold_spin.setAccelerated(True)
        self.alert_threshold_label.setWordWrap(True)
        self.alert_dialog_button.pressed.connect(self.sound_path_dialog)
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
        self.retranslate_ui()

        # grab all settings and set the widget values to them
        self.main_bind_edit.setText(self.settings.bind)
        self.script_edit.setText(self.settings.script)
        self.alert_path.setText(self.settings.paths.alert)
        self.alert_threshold_spin.setValue(self.settings.alerts.threshold)
        self.dark_check.setChecked(self.settings.window.dark)
        self.font_combo.setCurrentFont(self.settings.font.font)
        self.font_size_combo.setValue(self.settings.font.size)
        self.bold_check.setChecked(self.settings.font.bold)
        self.save_on_quit.setChecked(self.settings.save_on_quit)
        self.copy_check.setChecked(self.settings.copy_mode)
        self.alert_sound_check.setChecked(self.settings.alerts.audio)
        self.alert_visual_check.setChecked(self.settings.alerts.visual)
        self.autoscroll_check.setChecked(self.settings.window.autoscroll)

        if not self.settings.paths.ahk:
            self.copy_check.setDisabled(True)

        self.ahk_button.pressed.connect(self.ahk_dialog)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.resize(self.width(), self.script_edit.height() / 2)

    def ahk_dialog(self):
        ahk_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            filter="AutoHotKey (AutoHotKey*.exe)",
            caption="Select AutoHotkey's executable",
            directory="C:/")

        if ahk_path:
            self.settings.paths.ahk = ahk_path
            self.copy_check.setDisabled(False)
        self.settings.sync()

    def sound_path_dialog(self):
        sound_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            caption="Notification audio file")
        if sound_path:
            self.alert_path.setText(sound_path)

    def save_settings(self, close=False):
        if "|SYSTEMDATA|" not in self.settings.script:
            self.error_label.setText('Script must include "|SYSTEMDATA|"')
        else:
            self.error_label.clear()
            self.settings.auto_sync = False
            self.settings.bind = self.main_bind_edit.text()
            self.settings.script = self.script_edit.toPlainText()
            self.settings.window.dark = self.dark_check.isChecked()
            self.settings.font.font = self.font_combo.currentFont()
            self.settings.font.size = self.font_size_combo.value()
            self.settings.font.bold = self.bold_check.isChecked()
            self.settings.save_on_quit = self.save_on_quit.isChecked()
            self.settings.copy_mode = self.copy_check.isChecked()
            self.settings.alerts.audio = self.alert_sound_check.isChecked()
            self.settings.alerts.visual = self.alert_visual_check.isChecked()
            self.settings.alerts.threshold = self.alert_threshold_spin.value()
            self.settings.paths.alert = self.alert_path.text()
            self.settings.auto_sync = True
            self.settings.window.autoscroll = self.autoscroll_check.isChecked()
            self.settings_signal.emit()
            if close:
                self.close()

    def retranslate_ui(self):
        self.setWindowTitle("Settings")
        self.dark_check.setText("Dark theme")
        self.bold_check.setText("Bold")
        self.save.setText("Ok")
        self.main_bind_edit.setToolTip(
            "Bind to trigger the script, # for win key, "
            "! for alt, ^ for control, + for shift")
        self.save_on_quit.setText("Save route on window close")
        self.copy_check.setText("Copy mode")
        self.ahk_button.setText("AHK Path")
        self.alert_visual_check.setText("Taskbar fuel alert")
        self.alert_sound_check.setText("Sound fuel alert")
        self.alert_threshold_label.setText("Threshold for warning in % of max fuel usage per jump")
        self.alert_dialog_button.setText("...")
        self.alert_path_label.setText("Custom sound alert file")
        self.autoscroll_check.setText("Auto scroll")
        self.apply.setText("Apply")

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QDialog, self).closeEvent(*args, **kwargs)
        self.close_signal.emit()
