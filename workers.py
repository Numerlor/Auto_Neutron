import itertools
import json
from contextlib import suppress
from math import ceil

import requests
from PyQt5 import QtCore, QtMultimedia
from ahk import Hotkey, AHK
from pyperclip import copy as set_clip


class AhkWorker(QtCore.QThread):
    sys_signal = QtCore.pyqtSignal(int)  # signal to update gui to index
    route_finished_signal = QtCore.pyqtSignal()  # route end reached signal
    game_shut_signal = QtCore.pyqtSignal(list, int)  # signal for game shutdown
    fuel_signal = QtCore.pyqtSignal(dict)
    save_signal = QtCore.pyqtSignal(int, list)

    def __init__(self, parent, journal, data_values, settings, start_index):
        super(AhkWorker, self).__init__(parent)
        self.hub = parent
        self.journal = journal
        self.data_values = data_values
        self.systems = [data[0].casefold() for data in data_values]
        self.script, self.bind, self.copy, ahk_path = settings

        if not self.copy:
            self.ahk = AHK(executable_path=ahk_path)
        self.loop = True
        # set index according to last saved route or new plot, default index 1
        self.route_index = start_index if start_index != -1 else 1

        # connect parent signals
        parent.double_signal.connect(self.set_index)
        parent.edit_signal.connect(self.update_sys)
        parent.script_settings.connect(self.update_script)
        parent.window_quit_signal.connect(self.exit_and_save)
        parent.save_route_signal.connect(self.save_route)
        parent.quit_worker_signal.connect(self.quit_loop)
        parent.script_mode_signal.connect(self.set_copy)

    def run(self):
        if self.check_shutdown():
            self.game_shut_signal.emit(self.data_values, self.route_index)
            return

        self.set_output_system()
        self.sys_signal.emit(self.route_index)
        for line in self.follow_file(self.journal):
            loaded = json.loads(line)

            if (loaded['event'] == "FSDJump" and
                    loaded['StarSystem'].casefold() in self.systems[self.route_index:]):
                self.route_index = self.systems.index(loaded['StarSystem'].casefold()) + 1
                # if index is last, stop
                if self.route_index == len(self.data_values):
                    self.close_ahk()
                    self.route_finished_signal.emit()
                    break
                self.set_output_system()
                self.sys_signal.emit(self.route_index)

            elif loaded['event'] == "Loadout":
                # update max fuel for alerts
                self.fuel_signal.emit(loaded)

            elif loaded['event'] == "Shutdown":
                self.game_shut_signal.emit(self.data_values, self.route_index)
                self.close_ahk()
                break

    def check_shutdown(self):
        with self.journal.open('rb') as f:
            f.seek(-13, 2)
            return b"Shutdown" == f.read(8)

    def set_index(self, index):
        self.route_index = index
        self.set_output_system()
        self.sys_signal.emit(self.route_index)

    def set_output_system(self):
        if self.copy:
            set_clip(self.systems[self.route_index])
        else:
            self.reset_ahk()

    def update_sys(self, index, new_sys):
        self.data_values[index][0] = new_sys
        self.systems[index] = new_sys.casefold()
        if self.route_index == index:
            self.set_output_system()

    def update_script(self, bind, script):
        if self.bind != bind or self.script != script:
            self.bind = bind
            self.script = script
            if not self.copy:
                self.reset_ahk()

    def set_copy(self, setting):
        if setting is not self.copy:
            self.copy = setting
            if self.copy:
                self.close_ahk()
                set_clip(self.systems[self.route_index])
            else:
                self.ahk = AHK(executable_path=self.hub.get_ahk_path())
                self.reset_ahk()

    def reset_ahk(self):
        self.close_ahk()
        self.hotkey = Hotkey(
            self.ahk,
            self.bind,
            self.script.replace("|SYSTEMDATA|", self.systems[self.route_index])
        )
        self.hotkey.start()

    def close_ahk(self):
        with suppress(RuntimeError, AttributeError):
            self.hotkey.stop()

    def exit_and_save(self, save_route):
        if save_route:
            self.save_route()
        self.close_ahk()

    def save_route(self):
        self.save_signal.emit(self.route_index, self.data_values)

    def quit_loop(self):
        self.loop = False
        self.close_ahk()

    def follow_file(self, filepath):
        with filepath.open(encoding="utf-8") as file:
            file.seek(0, 2)
            while self.loop:
                loopline = file.readline()
                if not loopline:
                    self.sleep(1)
                    continue
                yield loopline


class FuelAlert(QtCore.QThread):
    alert_signal = QtCore.pyqtSignal()

    def __init__(self, parent, max_fuel, file, modifier):
        super(FuelAlert, self).__init__(parent)
        self.file = file
        self.loop = True
        self.alert = False

        self.set_jump_fuel(max_fuel, modifier)
        parent.stop_alert_worker_signal.connect(self.stop_loop)
        parent.next_jump_signal.connect(self.change_alert)
        parent.alert_fuel_signal.connect(self.set_jump_fuel)

    def run(self):
        self.main(self.file)

    def main(self, path):
        hold = False
        for line in self.follow_file(path):
            if line:
                loaded = json.loads(line)
                with suppress(KeyError):
                    # notify when fuel is low,
                    # fsd is in cooldown and ship in supercruise
                    binflag = f"{loaded['Flags']:b}"
                    if (
                            not hold
                            and self.alert
                            and loaded['Fuel']['FuelMain'] < self.jump_fuel
                            and binflag[-19] == "1"
                            and binflag[-5] == "1"
                    ):
                        hold = True
                        self.alert_signal.emit()
                    elif loaded['Fuel']['FuelMain'] > self.jump_fuel:
                        hold = False

    def set_jump_fuel(self, max_fuel, modifier):
        self.jump_fuel = max_fuel * modifier / 100

    def change_alert(self, status):
        self.alert = status

    def stop_loop(self):
        self.loop = False

    def follow_file(self, filepath):
        with filepath.open(encoding="utf-8") as file:
            while self.loop:
                file.seek(0, 0)
                loopline = file.readline()
                yield loopline
                self.sleep(2)


class SpanshPlot(QtCore.QThread):
    finished_signal = QtCore.pyqtSignal(list)  # signal containing output
    status_signal = QtCore.pyqtSignal(str)  # signal for updating statusbar

    def __init__(self, efficiency, jrange, source, to, parent=None):
        super(SpanshPlot, self).__init__(parent)
        self.efficiency = efficiency
        self.jrange = jrange
        self.source = source
        self.to = to

    def run(self):
        self.plot(self.efficiency, self.jrange, self.source, self.to)

    def plot(self, efficiency, jrange, source, to):
        try:
            job_request = requests.get("https://spansh.co.uk/api/route",
                                       params={
                                           "efficiency": efficiency,
                                           "range": jrange,
                                           "from": source,
                                           "to": to
                                       })
        except requests.exceptions.ConnectionError:
            self.status_signal.emit("Cannot establish a connection to Spansh")
        else:
            job_json = job_request.json()
            try:
                if job_json['error'] == "Could not find starting system":
                    self.status_signal.emit("Source system invalid")
                elif job_json['error'] == "Could not find finishing system":
                    self.status_signal.emit("Destination system invalid")
                else:
                    self.status_signal.emit("An error has occurred when contacting Spansh's API")

            except KeyError:
                job_id = job_json['job']
                self.status_signal.emit("Plotting")

                for sleep_base in itertools.count(1, 5):
                    job_json = requests.get("https://spansh.co.uk/api/results/" + job_id).json()

                    if job_json['status'] == "queued":
                        # 1, 1, 2, 2, 3, 4, 6, 7, 9, 12, 15, 17, 20, 24, 27, 30, 30, 30, …
                        self.sleep(min(ceil(ceil((sleep_base / 10) ** 2) / 1.9), 30))
                    else:
                        self.finished_signal.emit(
                            [[data['system'],
                              round(float(data['distance_jumped']), 2),
                              round(float(data['distance_left']), 2),
                              int(data['jumps'])]
                             for data in job_json['result']['system_jumps']])
                        break


class NearestRequest(QtCore.QThread):
    REQUEST_URL = "https://spansh.co.uk/api/nearest"
    finished_signal = QtCore.pyqtSignal(dict)  # output signal
    status_signal = QtCore.pyqtSignal(str)  # statusbar change signal

    def __init__(self, params, parent=None):
        super(NearestRequest, self).__init__(parent)
        self.params = params

    def run(self):
        self.request(self.params)

    def request(self, parameters):
        try:
            self.status_signal.emit("Waiting for spansh")
            job_request = requests.get(self.REQUEST_URL, params=parameters)
        except requests.exceptions.ConnectionError:
            self.status_signal.emit("Unable to establish a connection to Spansh")
        else:
            if job_request.ok:
                response = job_request.json()
                self.finished_signal.emit(response['system'])
            else:
                self.status_signal.emit(
                    "An error has occurred while communicating with Spansh's API")


class SoundPlayer:
    def __init__(self, path):
        self.sound_file = QtMultimedia.QMediaPlayer()
        self.sound_file.setMedia(QtMultimedia.QMediaContent(
            QtCore.QUrl.fromLocalFile(str(path))))
        self.sound_file.setVolume(100)

    def play(self):
        self.sound_file.play()
