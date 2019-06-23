import json

import requests
from PyQt5 import QtCore
from ahk import Hotkey, AHK


class AhkWorker(QtCore.QThread):
    sys_signal = QtCore.pyqtSignal(int, bool)  # signal to move grayout to index
    route_finished_signal = QtCore.pyqtSignal()  # route end reached signal
    game_shut_signal = QtCore.pyqtSignal(list, int)  # signal for game shutdown

    def __init__(self, parent, journal, data_values, settings, start_index):
        super(AhkWorker, self).__init__()
        self.journal = journal
        self.data_values = data_values
        self.settings = settings
        self.ahk = AHK(executable_path=self.settings.value("paths/AHK"))
        self.script = self.settings.value("script")
        self.bind = self.settings.value("bind")
        self.dark = self.settings.value("window/dark", type=bool)
        self.start_index = start_index
        self.loop = True
        # set index according to last saved route or new plot, default index 1
        if start_index > 0:
            self.list_index = start_index
        elif len(self.data_values) != 1:
            self.list_index = 1
        else:
            self.list_index = 0
        # connect parent signals
        parent.double_signal.connect(self.set_index)
        parent.edit_signal.connect(self.update_sys)
        parent.script_settings.connect(self.update_script)
        parent.window_quit_signal.connect(self.exit_and_save)
        parent.save_route_signal.connect(self.save_route)
        parent.quit_worker_signal.connect(self.quit_loop)

    def main(self):
        shutdown = False
        # search file for shutdown event, do not continue and send signal if it's found
        with open(self.journal, encoding='utf-8') as f:
            for l in f:
                j = json.loads(l)
                if j['event'] == "Shutdown":
                    shutdown = True
                    self.game_shut_signal.emit(self.data_values, self.list_index)
        if not shutdown:
            self.hotkey = Hotkey(self.ahk, self.bind,
                                 self.script.replace("|SYSTEMDATA|", self.data_values[self.list_index][0]))
            self.sys_signal.emit(self.list_index, self.dark)
            self.hotkey.start()
            for line in self.follow_file(open(self.journal, encoding='utf-8')):
                self.script = self.settings.value("script")
                self.bind = self.settings.value("bind")
                loaded = json.loads(line)
                if loaded['event'] == "FSDJump" and loaded['StarSystem'] == self.data_values[self.list_index][0]:
                    self.close_ahk()
                    self.list_index += 1
                    if self.list_index == len(self.data_values):
                        self.close_ahk()
                        self.route_finished_signal.emit()
                        break
                    self.hotkey = Hotkey(self.ahk, self.bind,
                                         self.script.replace("|SYSTEMDATA|", self.data_values[self.list_index][0]))
                    self.hotkey.start()
                    self.sys_signal.emit(self.list_index, self.dark)
                elif loaded['event'] == "Shutdown":
                    self.game_shut_signal.emit(self.data_values, self.list_index)
                    self.close_ahk()
                    break

    def set_index(self, index):
        self.list_index = index
        self.close_ahk()
        hotkey = Hotkey(self.ahk, self.bind, self.script.replace("|SYSTEMDATA|", self.data_values[self.list_index][0]))
        hotkey.start()
        self.sys_signal.emit(self.list_index, self.dark)

    def update_sys(self, index, new_sys):
        self.data_values[index][0] = new_sys
        if self.list_index == index:
            self.close_ahk()
            self.hotkey = Hotkey(self.ahk, self.bind,
                                 self.script.replace("|SYSTEMDATA|", self.data_values[self.list_index][0]))
            self.hotkey.start()

    def update_script(self, tup):
        self.bind = tup[0]
        self.script = tup[1]
        self.dark = tup[2]

        self.close_ahk()
        self.hotkey = Hotkey(self.ahk, self.bind,
                             self.script.replace("|SYSTEMDATA|", self.data_values[self.list_index][0]))
        self.hotkey.start()
        
    def close_ahk(self):
        try:
            self.hotkey.stop()
        except RuntimeError:
            pass

    def exit_and_save(self, save_route):
        if save_route:
            self.save_route()
        self.close_ahk()

    def save_route(self):
        self.settings.setValue("last_route", (self.list_index, self.data_values))

    def quit_loop(self):
        self.loop = False
        self.close_ahk()

    def follow_file(self, file):
        file.seek(0, 2)
        while self.loop:
            loopline = file.readline()
            if not loopline:
                self.sleep(1)
                continue
            yield loopline


class SpanshPlot(QtCore.QThread):
    finished_signal = QtCore.pyqtSignal(list)  # signal containing output
    status_signal = QtCore.pyqtSignal(str)  # signal for updating statusbar

    def __init__(self):
        super(SpanshPlot, self).__init__()

    def plot(self, efficiency, jrange, source, to):
        try:
            job_request = requests.get("https://spansh.co.uk/api/route",
                                       params=f"efficiency={efficiency}&range={jrange}"
                                       f"&from={source}&to={to}")
        except requests.exceptions.ConnectionError:
            self.status_signal.emit("Cannot establish a connection to Spansh")
        else:
            job_json = json.loads(job_request.content.decode())
            try:
                if job_json['error'] == "Could not find starting system":
                    self.status_signal.emit("Source system invalid")
                elif job_json['error'] == "Could not find finishing system":
                    self.status_signal.emit("Destination system invalid")
                else:
                    self.status_signal.emit("An error has occured when contacting Spansh's API")
            except KeyError:
                job_id = job_json['job']
                self.status_signal.emit("Plotting")
                for _ in range(20):
                    encodedjob = requests.get("https://spansh.co.uk/api/results/" + job_id)
                    decodedjob = encodedjob.content.decode()
                    job_json = json.loads(decodedjob)
                    if job_json['status'] == "queued":
                        self.sleep(1)
                    else:
                        data = []
                        valid = False
                        for stuff in job_json['result']['system_jumps']:
                            tlist = []
                            tlist.append(stuff['system'])
                            tlist.append(round(float(stuff['distance_jumped']), 2))
                            tlist.append(round(float(stuff['distance_left']), 2))
                            tlist.append(int(stuff['jumps']))
                            data.append(tlist)
                            valid = True
                        if valid:
                            self.finished_signal.emit(data)
                            break
                entered = False
                while job_json['status'] == "queued":
                    entered = True
                    self.sleep(4)
                    encodedjob = requests.get("https://spansh.co.uk/api/results/" + job_id)
                    decodedjob = encodedjob.content.decode()
                    job_json = json.loads(decodedjob)
                if entered:
                    data = []
                    valid = False
                    for stuff in job_json['result']['system_jumps']:
                        tlist = []
                        tlist.append(stuff['system'])
                        tlist.append(round(float(stuff['distance_jumped']), 2))
                        tlist.append(round(float(stuff['distance_left']), 2))
                        tlist.append(int(stuff['jumps']))
                        data.append(tlist)
                        valid = True
                    if valid:
                        self.finished_signal.emit(data)


class NearestRequest(QtCore.QThread):
    finished_signal = QtCore.pyqtSignal(dict)  # output signal
    status_signal = QtCore.pyqtSignal(str)  # statusbar change signal

    def __init__(self):
        super(NearestRequest, self).__init__()

    def request(self, request_link, parameters):
        try:
            self.status_signal.emit("Waiting for spansh")
            job_request = requests.get(request_link, params=parameters)
        except requests.exceptions.ConnectionError:
            self.status_signal.emit("Unable to establish a connection to spansh")
        else:
            response = json.loads(job_request.content.decode())
            self.finished_signal.emit(response['system'])

