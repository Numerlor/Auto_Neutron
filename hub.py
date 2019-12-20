import os
from pathlib import Path

from PyQt5 import QtCore, QtWidgets, QtGui

import main_windows
import popups
import workers
from appinfo import SHIP_STATS


class Hub(QtCore.QObject):
    script_settings = QtCore.pyqtSignal(tuple)  # worker settings from SettingsPop
    script_mode_signal = QtCore.pyqtSignal(bool)
    window_quit_signal = QtCore.pyqtSignal(bool)  # if window was closed, close ahk script
    worker_set_ahk_signal = QtCore.pyqtSignal()
    save_route_signal = QtCore.pyqtSignal()  # signal to save current route
    quit_worker_signal = QtCore.pyqtSignal()

    stop_alert_worker_signal = QtCore.pyqtSignal()
    alert_fuel_signal = QtCore.pyqtSignal(int, int)

    def __init__(self, settings, crash_handler):
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
        self.write_default_settings()
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
        # check for old settings
        if (self.settings.value("window/geometry") is None
                and self.settings.value("window/pos", type=QtCore.QPoint)
                and self.settings.value("window/size", type=QtCore.QSize)):
            self.main_window.resize(self.settings.value("window/size", type=QtCore.QSize))
            self.main_window.move(self.settings.value("window/pos", type=QtCore.QPoint))
        else:
            self.main_window.restoreGeometry(self.settings.value("window/geometry"))
        font = self.settings.value("font/font", type=QtGui.QFont)
        font.setPointSize(self.settings.value("font/size", type=int))
        font.setBold(self.settings.value("font/bold", type=bool))
        autoscroll = self.settings.value("window/autoscroll", type=bool)
        self.main_window.change_settings(font, self.dark, autoscroll)
        self.main_window.show()

    def start_alert_worker(self):
        self.player = workers.SoundPlayer(self.sound_path)
        status_file = (Path(os.environ['userprofile'])
                       / "Saved Games/Frontier Developments/Elite Dangerous/Status.json")
        self.sound_worker = workers.FuelAlert(self, self.max_fuel, status_file, self.modifier)
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
        settings = (self.settings.value("script"), self.settings.value("bind"),
                    self.settings.value("copy_mode", type=bool),
                    self.settings.value("paths/AHK"))
        self.worker = workers.AhkWorker(self, journal, data_values, settings, index)
        self.worker.sys_signal.connect(self.main_window.index_change)
        self.worker.route_finished_signal.connect(self.end_route_pop)
        self.worker.game_shut_signal.connect(self.restart_worker)
        self.worker.fuel_signal.connect(self.get_max_fuel)
        self.worker.save_signal.connect(self.save_route)
        self.worker.start()

        if self.visual_alert or self.sound_alert:
            self.start_alert_worker()
        self.workers_started = True

    def restart_worker(self, route_data, route_index):
        self.worker.quit()
        if self.sound_alert or self.visual_alert:
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

        self.alert_fuel_signal.emit(self.max_fuel, self.modifier)

    def set_theme(self):
        """Set dark/default theme depending on user setting"""
        if self.dark:
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

    def change_editable_settings(self, values):
        self.script_mode_signal.emit(values[7])
        self.script_settings.emit(*values[:2])

        self.dark = values[2]
        self.set_theme()

        if (values[8] or values[9]
                and not any((self.sound_alert, self.visual_alert))):
            self.start_alert_worker()
        elif not values[8] and not values[9]:
            self.stop_alert_worker()
        self.sound_alert = values[8]
        self.visual_alert = values[9]

        self.save_on_quit = values[6]
        if any((self.sound_alert, self.visual_alert)):
            self.stop_alert_worker()
            self.start_alert_worker()

        self.modifier = values[10]
        self.alert_fuel_signal.emit(self.max_fuel, self.modifier)

        self.sound_path = values[11]
        self.player = workers.SoundPlayer(values[11])

        font = values[3]
        font.setPointSize(values[4])
        font.setBold(values[5])
        self.main_window.change_settings(font, self.dark, values[12])

    def save_route(self, index, data):
        self.settings.setValue("last_route", (index, data))

    def show_exception(self, exc):
        self.crash_window.add_traceback(exc)
        self.crash_window.show()

    def quit(self, geometry):
        self.settings.setValue("window/geometry", geometry)
        self.settings.sync()
        self.window_quit_signal.emit(self.save_on_quit)


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
