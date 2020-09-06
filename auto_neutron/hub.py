# This file is part of Auto_Neutron.
# Copyright (C) 2019-2020  Numerlor

from PyQt5 import QtCore, QtGui, QtWidgets

from auto_neutron import main_windows
from auto_neutron import popups
from auto_neutron import settings
from auto_neutron import workers
from auto_neutron.constants import LAST_JOURNALS_TEXT, SHIP_STATS
from auto_neutron.utils import get_journals


class Hub(QtCore.QObject):
    settings_changed = QtCore.pyqtSignal()  # worker settings from SettingsPop
    window_quit_signal = QtCore.pyqtSignal(bool)  # if window was closed, close ahk script
    worker_set_ahk_signal = QtCore.pyqtSignal()
    quit_worker_signal = QtCore.pyqtSignal()

    stop_alert_worker_signal = QtCore.pyqtSignal()
    alert_fuel_signal = QtCore.pyqtSignal(int)

    def __init__(self, crash_handler):
        super().__init__()
        self.application = QtWidgets.QApplication.instance()
        self.total_jumps = 0
        self.max_fuel = 0
        self.workers_started = False
        self.alert_worker_started = False

        self.main_window = main_windows.MainWindow(self)
        self.crash_window = popups.CrashPop()
        crash_handler.triggered.connect(self.crash_window.show)
        self.player = workers.SoundPlayer(self.settings_changed)

    def startup(self):
        self.set_theme()
        self.double_signal = self.main_window.double_signal
        self.edit_signal = self.main_window.edit_signal
        self.next_jump_signal = self.main_window.next_jump_signal
        self.main_window.show()
        self.start_alert_worker()
        self.initial_pop()

    def new_route(self):
        if self.workers_started:
            self.quit_worker_signal.emit()
            self.worker.quit()
        self.main_window.reset_table()
        self.initial_pop()

    def start_alert_worker(self):
        self.alert_worker = workers.FuelAlert(self, self.max_fuel)
        self.alert_worker.alert_signal.connect(self.fuel_alert)
        self.alert_worker.start()

    def set_max_fuel(self, value):
        self.max_fuel = value

    def fuel_alert(self):
        if settings.Alerts.visual:
            self.application.alert(self.main_window.centralwidget, 5000)
        if settings.Alerts.audio:
            if settings.Paths.alert_sound:
                self.player.play()
            else:
                self.application.beep()

    def start_worker(self, data_values, journal, index):
        self.worker = workers.AhkWorker(self, journal, data_values, index)
        self.worker.sys_signal.connect(self.main_window.index_change)
        self.worker.route_finished_signal.connect(self.end_route_pop)
        self.worker.game_shut_signal.connect(self.on_game_shutdown)
        self.worker.fuel_signal.connect(self.get_max_fuel)
        self.worker.start()

        self.workers_started = True

    def on_game_shutdown(self):
        journals = get_journals(3)
        w = popups.GameShutPop(self.main_window, LAST_JOURNALS_TEXT[:len(journals)])
        w.show()
        w.journal_button.pressed.connect(
            lambda: self.start_worker(
                self.worker.route,
                journals[w.journal_combo.currentIndex()],
                self.worker.route_index)
        )
        w.save_button.pressed.connect(self.save_route)

    def get_max_fuel(self, json):
        fsd = next(item for item in json['Modules'] if item['Slot'] == "FrameShiftDrive")
        self.max_fuel = SHIP_STATS['FSD'][fsd['Item']][0]
        if 'Engineering' in fsd:
            for blueprint in fsd['Engineering']['Modifiers']:
                if blueprint['Label'] == 'MaxFuelPerJump':
                    self.max_fuel = blueprint['Value']

        self.alert_fuel_signal.emit(self.max_fuel)

    def set_theme(self):
        """Set dark/default theme depending on user setting"""
        if settings.Window.dark_mode:
            change_to_dark()
        else:
            change_to_default()

    def initial_pop(self):
        w = main_windows.PlotStartDialog(self.main_window)
        w.fuel_signal.connect(self.set_max_fuel)
        w.data_signal.connect(self.main_window.pop_table)
        w.data_signal.connect(self.start_worker)
        w.setup_ui()
        w.show()
        w.after_show()

    def end_route_pop(self):
        w = popups.RouteFinishedPop(self.main_window)
        w.show()
        w.new_route_signal.connect(self.new_route)

    def licenses_pop(self):
        w = popups.LicensePop(self.main_window)
        w.show()
        w.close_signal.connect(lambda: self.main_window.about_action.setEnabled(True))
        self.main_window.about_action.setDisabled(True)

    def sett_pop(self):
        w = popups.SettingsPop(self.main_window)
        w.show()
        w.settings_signal.connect(self.change_editable_settings)
        w.close_signal.connect(lambda: self.main_window.settings_action.setEnabled(True))
        self.main_window.settings_action.setDisabled(True)

    def change_editable_settings(self):
        self.set_theme()
        self.settings_changed.emit()

    def save_route(self):
        settings.General.last_route = (self.worker.route_index, self.worker.route.data)

    def quit(self, geometry):
        settings.Window.geometry = geometry
        if self.workers_started and settings.General.save_on_quit:
            self.save_route()


def change_to_dark():
    p = QtGui.QPalette()
    p.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    p.setColor(QtGui.QPalette.WindowText, QtGui.QColor(247, 247, 247))
    p.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
    p.setColor(QtGui.QPalette.Text, QtGui.QColor(247, 247, 247))
    p.setColor(QtGui.QPalette.Button, QtGui.QColor(60, 60, 60))
    p.setColor(QtGui.QPalette.Background, QtGui.QColor(35, 35, 35))
    p.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(45, 45, 45))
    p.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    p.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    p.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Light, QtGui.QColor(0, 0, 0))
    p.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(110, 110, 100))
    app = QtWidgets.QApplication.instance()
    app.setStyle("Fusion")
    app.setPalette(p)


def change_to_default():
    app = QtWidgets.QApplication.instance()
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())
