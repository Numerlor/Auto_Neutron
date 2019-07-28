import csv
import json
import os
import sys

from PyQt5 import QtWidgets, QtCore, QtGui

import popups
import workers
from appinfo import SHIP_STATS


class PlotStartDialog(QtWidgets.QDialog):
    data_signal = QtCore.pyqtSignal(str, list, int)
    fuel_signal = QtCore.pyqtSignal(int)

    def __init__(self, parent, settings):
        super(PlotStartDialog, self).__init__(parent)
        self.settings = settings
        self.jpath = self.settings.value("paths/journal")
        self.cpath = self.settings.value("paths/CSV")
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.tabWidget = QtWidgets.QTabWidget(self)
        self.tab = QtWidgets.QWidget()
        self.tab_2 = QtWidgets.QWidget()
        self.tab_3 = QtWidgets.QWidget()
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.path_button = QtWidgets.QPushButton(self.tab)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.last_main_layout = QtWidgets.QVBoxLayout(self.tab_3)
        self.last_comsub_layout = QtWidgets.QHBoxLayout(self.tab_3)
        self.last_label = QtWidgets.QLabel(self.tab_3)
        self.last_comb = QtWidgets.QComboBox(self.tab_3)
        self.last_submit = QtWidgets.QPushButton(self.tab_3)
        self.cs_comb = QtWidgets.QComboBox(self.tab)
        self.cs_submit = QtWidgets.QPushButton(self.tab, enabled=False)
        self.path_label = QtWidgets.QLabel(self.tab)
        self.gridLayout_4 = QtWidgets.QGridLayout(self.tab_2)
        self.source = QtWidgets.QLineEdit(self.tab_2)
        self.nearest = QtWidgets.QPushButton(self.tab_2)
        self.cargo_slider = QtWidgets.QSlider(orientation=QtCore.Qt.Horizontal)
        self.cargo_label = QtWidgets.QLabel()
        self.sp_comb = QtWidgets.QComboBox(self.tab_2)
        self.sp_submit = QtWidgets.QPushButton(self.tab_2, enabled=False)
        self.eff_spinbox = QtWidgets.QSpinBox(self.tab_2)
        self.range = QtWidgets.QLabel(self.tab_2)
        self.ran_spinbox = QtWidgets.QDoubleSpinBox(self.tab_2)
        self.efficiency = QtWidgets.QLabel(self.tab_2)
        self.destination = QtWidgets.QLineEdit(self.tab_2)
        self.status_layout = QtWidgets.QVBoxLayout(self)
        self.status = QtWidgets.QStatusBar()

        self.setup_ui()

    def setup_ui(self):
        self.setMinimumSize(233, 241)
        self.resize(233, 241)
        self.tabWidget.addTab(self.tab, "")
        self.tabWidget.addTab(self.tab_2, "")
        self.tabWidget.addTab(self.tab_3, "")

        self.gridLayout.setContentsMargins(4, 6, 2, 2)
        self.gridLayout.setSpacing(0)
        self.gridLayout.addWidget(self.tabWidget)
        self.gridLayout.addLayout(self.status_layout, 1, 0, 1, 1)
        self.status.setSizeGripEnabled(False)
        self.status_layout.addWidget(self.status)

        # CSV
        self.path_button.setMaximumWidth(95)
        if len(self.cpath) > 0:
            self.cs_submit.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(self.cs_comb.sizePolicy().hasHeightForWidth())
        self.cs_comb.setSizePolicy(sizePolicy)
        self.cs_comb.setMaximumWidth(95)
        self.cs_submit.setMaximumWidth(65)
        self.path_label.setWordWrap(True)

        self.cs_submit.pressed.connect(lambda: self.cs_submit_act(self.cpath))
        self.path_button.pressed.connect(self.change_path)

        self.horizontalLayout.addWidget(self.path_button, alignment=QtCore.Qt.AlignLeft)
        spacerItem = QtWidgets.QSpacerItem(30, 20, QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout_2.addLayout(self.horizontalLayout, 2, 0, 1, 1)
        self.horizontalLayout_2.addWidget(self.cs_comb, alignment=QtCore.Qt.AlignLeft)
        self.horizontalLayout_2.addWidget(self.cs_submit, alignment=QtCore.Qt.AlignRight)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 4, 0, 1, 1)
        self.gridLayout_2.addWidget(self.path_label, 1, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum,
                                            QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem1, 3, 0, 1, 1)

        # Spansh
        self.sp_comb.setMaximumWidth(95)
        self.sp_submit.setMaximumWidth(65)
        self.eff_spinbox.setMaximumWidth(50)
        self.eff_spinbox.setRange(1, 100)
        self.eff_spinbox.setValue(60)
        self.eff_spinbox.setAccelerated(True)
        self.ran_spinbox.setMaximumWidth(50)
        self.ran_spinbox.setAccelerated(True)
        self.ran_spinbox.setRange(10, 100)
        self.ran_spinbox.setSingleStep(0.01)

        self.source.textChanged.connect(self.button_on_filled_fields)
        self.destination.textChanged.connect(self.button_on_filled_fields)
        self.nearest.pressed.connect(self.show_nearest)
        self.sp_submit.pressed.connect(self.sp_submit_act)
        self.sp_comb.currentIndexChanged.connect(self.update_source)
        self.sp_comb.currentIndexChanged.connect(self.current_range)
        self.cargo_slider.valueChanged.connect(self.update_range)

        self.gridLayout_4.addWidget(self.source, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.destination, 1, 0, 1, 1)
        self.gridLayout_4.addWidget(self.cargo_label, 2, 0, 1, 1)
        self.gridLayout_4.addWidget(self.cargo_slider, 3, 0, 1, 1)
        self.gridLayout_4.addWidget(self.range, 4, 0, 1, 1)
        self.gridLayout_4.addWidget(self.ran_spinbox, 5, 0, 1, 1)
        self.gridLayout_4.addWidget(self.efficiency, 6, 0, 1, 1)
        self.gridLayout_4.addWidget(self.nearest, 7, 1, 1, 1)
        self.gridLayout_4.addWidget(self.eff_spinbox, 7, 0, 1, 1)
        self.gridLayout_4.addWidget(self.sp_comb, 9, 0, 1, 1)
        self.gridLayout_4.addWidget(self.sp_submit, 9, 1, 1, 1)

        spacerItem2 = QtWidgets.QSpacerItem(
            20, 40,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding)

        self.gridLayout_4.addItem(spacerItem2, 6, 0, 1, 1)

        # Last
        font = QtGui.QFont()
        font.setPointSize(12)
        self.last_label.setFont(font)

        self.last_submit.pressed.connect(self.last_submit_act)

        self.last_main_layout.addWidget(self.last_label, alignment=QtCore.Qt.AlignCenter)
        self.last_main_layout.addLayout(self.last_comsub_layout)
        self.last_comsub_layout.addWidget(self.last_comb, alignment=QtCore.Qt.AlignLeft)
        self.last_comsub_layout.addWidget(self.last_submit, alignment=QtCore.Qt.AlignRight)

        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.retranslateUi()
        self.get_journals()
        self.setModal(True)
        self.check_dropped_files()

    def retranslateUi(self):
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), "CSV")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), "Spansh")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), "Last")
        self.last_label.setText("Use last saved route")
        self.last_submit.setText("Submit")
        self.setWindowTitle("Select a route")
        self.path_button.setText("Change path")
        self.cs_submit.setText("Submit")
        self.path_label.setText("Current path: " + self.cpath)
        self.source.setPlaceholderText("Source System")
        self.nearest.setText("Nearest")
        self.sp_submit.setText("Submit")
        self.range.setText("Range")
        self.efficiency.setText("Efficiency")
        self.destination.setPlaceholderText("Destination System")
        self.cargo_label.setText("Cargo")

    def button_on_filled_fields(self):
        if len(self.destination.text()) > 0 and len(self.source.text()) > 0:
            self.sp_submit.setEnabled(True)
        else:
            self.sp_submit.setEnabled(False)

    def change_path(self):
        file_dialog = QtWidgets.QFileDialog()
        fpath = file_dialog.getOpenFileName(filter="csv (*.csv)",
                                            directory=self.cpath[:self.cpath.rfind("/")])
        if len(fpath[0]) > 0:
            self.cpath = fpath[0]
            self.path_label.setText("Current path: " + fpath[0])
            self.settings.setValue("paths/csv", fpath[0])
            self.settings.sync()
            self.cs_submit.setEnabled(True)
        else:
            if not self.cpath:
                self.cs_submit.setEnabled(False)

    def get_journals(self):
        try:
            self.journals = sorted(
                [self.jpath + file for file in os.listdir(self.jpath)
                 if file.endswith(".log")],
                key=os.path.getctime, reverse=True)
        except FileNotFoundError:
            d = popups.QuitDialog(self, "Journal folder not detected")
            d.setupUi()
        else:
            options = ["Last journal", "Second to last", "Third to last"][:len(self.journals)]
            if len(options) == 0:
                d = popups.QuitDialog(self, "No journals detected", False)
                d.setupUi()
                self.sp_submit.setEnabled(False)
                self.cs_submit.setEnabled(False)
                self.last_submit.setEnabled(False)
                self.source.setDisabled(True)
                self.destination.setDisabled(True)
            else:
                self.cs_comb.addItems(options)
                self.sp_comb.addItems(options)
                self.last_comb.addItems(options)

    def update_source(self, index):
        # set source system to last visited in currently selected journal
        with open(self.journals[index], encoding='utf-8') as f:
            lines = [json.loads(line) for line in f]
        try:
            self.source.setText(next(lines[i]['StarSystem'] for i
                                     in range(len(lines) - 1, -1, -1)
                                     if lines[i]['event'] == "FSDJump"
                                     or lines[i]['event'] == "Location"))
        except StopIteration:
            self.source.clear()

    def current_range(self, index):
        with open(self.journals[index], encoding='utf-8') as f:
            lines = [json.loads(line) for line in f]
        try:
            # get last loadout event line
            loadout = next(lines[i] for i in range(len(lines) - 1, -1, -1)
                           if lines[i]['event'] == "Loadout"
                           and lines[i]['MaxJumpRange'] != 0)
            # get last cargo event line
            ship_cargo = next(lines[i] for i in range(len(lines) - 1, -1, -1)
                              if lines[i]['event'] == "Cargo"
                              and lines[i]['Vessel'] == "Ship")['Count']

        except StopIteration:
            self.ran_spinbox.setValue(50)
            self.cargo_slider.setDisabled(True)

        else:
            # both loadout and cargo found, enable cargo_slider slider
            self.cargo_slider.setDisabled(False)
            # grab ship stats
            cargo_cap = loadout['CargoCapacity']
            self.fuel = loadout['FuelCapacity']['Main']
            self.mass = loadout['UnladenMass']
            # get FSD and FSD booster
            modules = (i for i in loadout['Modules']
                       if i['Slot'] == "FrameShiftDrive"
                       or "fsdbooster" in i['Item'])
            self.boost = 0
            for item in modules:
                if item['Slot'] == "FrameShiftDrive":
                    (self.max_fuel, self.optimal_mass, self.size_const,
                     self.class_const) = SHIP_STATS['FSD'][item['Item']]

                    if 'Engineering' in item.keys():
                        for blueprint in item['Engineering']['Modifiers']:
                            if blueprint['Label'] == "FSDOptimalMass":
                                self.optimal_mass = blueprint['Value']
                            elif blueprint['Label'] == "MaxFuelPerJump":
                                self.max_fuel = blueprint['Value']

                if "fsdbooster" in item['Item']:
                    self.boost = SHIP_STATS['Booster'][item['Item']]

            self.fuel_signal.emit(self.max_fuel)
            self.ran_spinbox.setValue(self.calculate_range(ship_cargo))
            self.cargo_slider.setMaximum(cargo_cap)
            self.cargo_slider.setValue(ship_cargo)

    def calculate_range(self, cargo):
        return (self.boost + self.optimal_mass *
                (1000 * self.max_fuel / self.class_const)
                ** (1 / self.size_const) / (self.mass + self.fuel + cargo))

    def update_range(self, cargo):
        self.ran_spinbox.setValue(self.calculate_range(cargo))

    def update_destination(self, system):
        self.destination.setText(system)

    def check_dropped_files(self):
        files = [file for file in sys.argv if file.endswith("csv")]
        if len(files) > 0:
            self.cs_submit_act(files[0])

    def sp_submit_act(self):
        self.plotter = workers.SpanshPlot(self.eff_spinbox.value(),
                                          self.ran_spinbox.value(),
                                          self.source.text(),
                                          self.destination.text(), self)
        self.plotter.status_signal.connect(self.change_status)
        self.plotter.finished_signal.connect(self.sp_finish_act)
        self.plotter.start()

    def sp_finish_act(self, data):
        self.data_signal.emit(self.journals[self.sp_comb.currentIndex()], data, -1)
        self.plotter.quit()
        self.close()

    def change_status(self, message):
        self.status.showMessage(message)

    def cs_submit_act(self, cpath):
        self.cs_submit.setEnabled(False)

        try:
            if os.stat(cpath).st_size > 2_097_152:
                self.status.showMessage("File too large")
                self.cs_submit.setEnabled(True)
            else:
                with open(cpath, encoding='utf-8') as f:
                    data = []
                    valid = True
                    for stuff in csv.DictReader(f, delimiter=','):
                        if stuff is None:
                            valid = False
                            break
                        else:
                            try:
                                tlist = [
                                    stuff['System Name'],
                                    round(float(stuff['Distance To Arrival']), 2),
                                    round(float(stuff['Distance Remaining']), 2),
                                    int(stuff['Jumps'])
                                ]
                            except (ValueError, KeyError):
                                valid = False
                                break

                            data.append(tlist)
                    if valid:
                        self.data_signal.emit(
                            self.journals[self.cs_comb.currentIndex()],
                            data,
                            -1)
                        self.close()
                    else:
                        self.status.showMessage("Error loading csv file")
                        self.cs_submit.setEnabled(True)

        except FileNotFoundError:
            self.status.showMessage("Invalid path to CSV file")

    def last_submit_act(self):
        self.last_submit.setEnabled(False)
        last_route = self.settings.value("last_route")
        if last_route is None or len(last_route) == 0:
            self.status.showMessage("No last route found")
            self.last_submit.setEnabled(True)
        else:
            if last_route[0] == len(last_route[1]):
                self.data_signal.emit(self.journals[self.last_comb.currentIndex()],
                                      last_route[1], 1)
                self.close()
            else:
                self.data_signal.emit(self.journals[self.last_comb.currentIndex()],
                                      last_route[1], last_route[0])
                self.close()

    def show_nearest(self):
        self.nearest.setEnabled(False)
        n_win = popups.Nearest(self)
        n_win.setupUi()
        n_win.closed_signal.connect(self.enable_button)
        n_win.destination_signal.connect(self.update_destination)

    def enable_button(self):
        self.nearest.setEnabled(True)
