# This file is part of Auto_Neutron.
# Copyright (C) 2019-2020  Numerlor

import os
from pathlib import Path

from PyQt5 import QtCore, QtWidgets, QtGui

from auto_neutron import main_windows
from auto_neutron import popups
from auto_neutron import workers
from auto_neutron.constants import SHIP_STATS
from auto_neutron.settings import Settings


class Hub(QtCore.QObject):
    script_settings = QtCore.pyqtSignal(tuple)  # worker settings from SettingsPop
    script_mode_signal = QtCore.pyqtSignal(bool)
    window_quit_signal = QtCore.pyqtSignal(bool)  # if window was closed, close ahk script
    worker_set_ahk_signal = QtCore.pyqtSignal()
    quit_worker_signal = QtCore.pyqtSignal()

    stop_alert_worker_signal = QtCore.pyqtSignal()
    alert_fuel_signal = QtCore.pyqtSignal(int, int)

    def __init__(self, settings: Settings, crash_handler):
        super().__init__()

        crash_handler.traceback_sig.connect(self.show_exception)
        self.settings = settings
        self.application = QtWidgets.QApplication.instance()
        self.total_jumps = 0
        self.max_fuel = 0
        self.workers_started = False
        self.alert_worker_started = False

        self.main_window = main_windows.MainWindow(self)
        self.crash_window = popups.CrashPop()

    def startup(self):
        self.set_theme()
        self.double_signal = self.main_window.double_signal
        self.edit_signal = self.main_window.edit_signal
        self.next_jump_signal = self.main_window.next_jump_signal
        self.show_window()
        self.initial_pop()

    def new_route(self):
        if self.workers_started:
            self.quit_worker_signal.emit()
            self.worker.quit()
            if any((self.visual_alert, self.sound_alert)):
                self.stop_alert_worker()
        self.main_window.reset_table()
        self.initial_pop()

    def show_window(self):
        self.main_window.restoreGeometry(self.settings.window.geometry)
        font = self.settings.font.font
        font.setPointSize(self.settings.font.size)
        font.setBold(self.settings.font.bold)
        autoscroll = self.settings.window.autoscroll
        self.main_window.change_settings(font, self.settings.window.dark, autoscroll)
        self.main_window.show()

    def start_alert_worker(self):
        self.player = workers.SoundPlayer(self.settings.paths.alert)
        status_file = (Path(os.environ['userprofile'])
                       / "Saved Games/Frontier Developments/Elite Dangerous/Status.json")
        self.sound_worker = workers.FuelAlert(self, self.max_fuel, status_file, self.settings.alerts.threshold)
        self.sound_worker.alert_signal.connect(self.fuel_alert)
        self.sound_worker.start()
        self.alert_worker_started = True

    def stop_alert_worker(self):
        if self.alert_worker_started:
            self.stop_alert_worker_signal.emit()
            self.sound_worker.quit()
            try:
                self.sound_worker.alert_signal.disconnect()
            except TypeError:
                pass

    def set_max_fuel(self, value):
        self.max_fuel = value

    def fuel_alert(self):
        if self.visual_alert:
            self.application.alert(self.main_window.centralwidget, 5000)
        if self.sound_alert:
            if self.sound_path:
                self.player.play()
            else:
                self.application.beep()

    def start_worker(self, data_values, journal, index):
        settings = (self.settings.script, self.settings.bind,
                    self.settings.copy_mode,
                    self.settings.paths.ahk)
        self.worker = workers.AhkWorker(self, journal, data_values, settings, index)
        self.worker.sys_signal.connect(self.main_window.index_change)
        self.worker.route_finished_signal.connect(self.end_route_pop)
        self.worker.game_shut_signal.connect(self.restart_worker)
        self.worker.fuel_signal.connect(self.get_max_fuel)
        self.worker.start()

        if self.settings.alerts.audio or self.settings.alerts.visual:
            self.start_alert_worker()
        self.workers_started = True

    def restart_worker(self, route_data, route_index):
        self.worker.quit()
        if self.settings.alerts.audio or self.settings.alerts.visual:
            self.stop_alert_worker()
        while not self.worker.isFinished():
            self.thread().sleep(1)
        w = popups.GameShutPop(self.main_window, self.settings, route_data, route_index)
        w.show()
        w.worker_signal.connect(self.start_worker)
        w.close_signal.connect(self.main_window.disconnect_signals)

    def get_max_fuel(self, json):
        fsd = next(item for item in json['Modules'] if item['Slot'] == "FrameShiftDrive")
        self.max_fuel = SHIP_STATS['FSD'][fsd['Item']][0]
        if 'Engineering' in fsd:
            for blueprint in fsd['Engineering']['Modifiers']:
                if blueprint['Label'] == 'MaxFuelPerJump':
                    self.max_fuel = blueprint['Value']

        self.alert_fuel_signal.emit(self.max_fuel, self.settings.alerts.threshold)

    def set_theme(self):
        """Set dark/default theme depending on user setting"""
        if self.settings.window.dark:
            change_to_dark()
        else:
            change_to_default()

    def initial_pop(self):
        w = main_windows.PlotStartDialog(self.main_window, self.settings)
        w.fuel_signal.connect(self.set_max_fuel)
        w.data_signal.connect(self.main_window.pop_table)
        w.data_signal.connect(self.start_worker)
        w.setup_ui()
        w.show()
        w.after_show()

    def end_route_pop(self):
        w = popups.RouteFinishedPop(self.main_window)
        w.show()
        w.close_signal.connect(self.main_window.disconnect_signals)
        w.new_route_signal.connect(self.new_route)

    def licenses_pop(self):
        w = popups.LicensePop(self.main_window)
        w.show()
        w.close_signal.connect(lambda:
                               self.main_window.about_action.setEnabled(True))
        self.main_window.about_action.setDisabled(True)

    def sett_pop(self):
        w = popups.SettingsPop(self.main_window, self.settings)
        w.show()
        w.settings_signal.connect(self.change_editable_settings)
        w.close_signal.connect(lambda:
                               self.main_window.settings_action.setEnabled(True))
        self.main_window.settings_action.setDisabled(True)

    def change_editable_settings(self):
        self.script_mode_signal.emit(self.settings.copy_mode)
        self.script_settings.emit(self.settings.bind, self.settings.script)

        self.set_theme()

        if self.settings.alerts.audio or self.settings.alerts.visual:
            self.start_alert_worker()
        else:
            self.stop_alert_worker()
        if any((self.sound_alert, self.visual_alert)):
            self.stop_alert_worker()
            self.start_alert_worker()

        self.alert_fuel_signal.emit(self.max_fuel, self.settings.alerts.threshold)

        self.player = workers.SoundPlayer(self.paths.alert)

        font = self.settings.font.font
        font.setPointSize(self.settings.font.size)
        font.setBold(self.settings.font.bold)
        self.main_window.change_settings(font, self.settings.window.dark, self.window.auto_scroll)

    def save_route(self):
        self.settings.last_route = (self.worker.route_index, self.worker.route.data)

    def show_exception(self, exc):
        self.crash_window.add_traceback(exc)
        self.crash_window.show()

    def quit(self, geometry):
        self.settings.window.geometry = geometry
        if self.settings.save_on_quit:
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
