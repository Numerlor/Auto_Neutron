import csv
import json
from os import environ, listdir
from os.path import getctime

from PyQt5 import QtWidgets, QtCore, QtGui

import popups
import workers


# TODO selectable copy mode/ forced if ahk path wasn't provided/is invalid

class Ui_MainWindow(QtWidgets.QMainWindow):
    double_signal = QtCore.pyqtSignal(int)  # double click signal to set worker to new clicked row
    edit_signal = QtCore.pyqtSignal(int, str)  # send edited system to worker if changed
    script_settings = QtCore.pyqtSignal(tuple)  # worker settings from SettingsPop
    script_mode_signal = QtCore.pyqtSignal(bool)
    window_quit_signal = QtCore.pyqtSignal(bool)  # if window was closed, close ahk script
    worker_set_ahk_signal = QtCore.pyqtSignal()
    save_route_signal = QtCore.pyqtSignal()  # signal to save current route
    quit_worker_signal = QtCore.pyqtSignal()

    def __init__(self, settings, application):
        super(Ui_MainWindow, self).__init__()
        self.centralwidget = QtWidgets.QWidget(self)
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.MainTable = QtWidgets.QTableWidget(self.centralwidget)
        self.settings = settings
        self.application = application

        self.jpath = self.settings.value("paths/journal")
        self.dark = self.settings.value("window/dark", type=bool)

        self.change_action = QtWidgets.QAction("Edit", self)
        self.save_action = QtWidgets.QAction("Save route", self)
        self.copy_action = QtWidgets.QAction("Copy", self)
        self.new_route_action = QtWidgets.QAction("Start a new route", self)
        self.settings_action = QtWidgets.QAction("Settings", self)
        self.about_action = QtWidgets.QAction("About", self)
        self.save_on_quit = self.settings.value("save_on_quit", type=bool)

        self.last_index = 0
        self.total_jumps = 0

    def setupUi(self):
        self.resize(self.settings.value("window/size", type=QtCore.QSize))
        self.move(self.settings.value("window/pos", type=QtCore.QPoint))

        # connect and add actions
        self.setup_actions()
        # set context menus to custom
        self.MainTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.MainTable.customContextMenuRequested.connect(self.table_context)
        self.customContextMenuRequested.connect(self.main_context)

        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        # build table
        self.MainTable.setGridStyle(QtCore.Qt.NoPen)
        self.MainTable.setColumnCount(4)
        item = QtWidgets.QTableWidgetItem()
        self.MainTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.MainTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.MainTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.MainTable.setHorizontalHeaderItem(3, item)
        self.MainTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.MainTable.setAlternatingRowColors(True)
        self.MainTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.MainTable.verticalHeader().setVisible(False)

        header = self.MainTable.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        header.disconnect()
        self.MainTable.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.gridLayout.addWidget(self.MainTable, 0, 0, 1, 1)
        self.setCentralWidget(self.centralwidget)
        # write settings if not defined, check ahk path
        self.write_default_settings()

        # font of table
        font = self.settings.value("font/font", type=QtGui.QFont)
        font.setPointSize(self.settings.value("font/size", type=int))
        font.setBold(self.settings.value("font/bold", type=bool))
        self.MainTable.setFont(font)
        self.MainTable.doubleClicked.connect(self.table_click)
        # color management
        p = self.MainTable.palette()
        p.setColor(QtGui.QPalette.Highlight, QtGui.QColor(255, 255, 255, 0))
        p.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 123, 255))
        self.MainTable.setPalette(p)

        if self.dark:
            change_to_dark(self.application)
        else:
            change_to_default(self.application)
        self.retranslateUi()

        self.show()
        # show initial popup
        self.show_w()

    def setup_actions(self):
        self.copy_action.triggered.connect(self.copy)
        self.change_action.triggered.connect(self.change_item_text)
        self.save_action.triggered.connect(self.save_route_signal.emit)
        self.settings_action.triggered.connect(self.sett_pop)
        self.about_action.triggered.connect(self.licenses_pop)
        self.new_route_action.triggered.connect(self.new_route)

    def main_context(self, location):
        menu = QtWidgets.QMenu()
        menu.addAction(self.new_route_action)
        menu.addSeparator()
        menu.addAction(self.save_action)
        menu.addAction(self.settings_action)
        menu.addAction(self.about_action)
        menu.exec_(self.mapToGlobal(location))

    def table_context(self, location):
        menu = QtWidgets.QMenu()
        menu.addAction(self.copy_action)
        menu.addAction(self.change_action)
        menu.addAction(self.save_action)
        menu.addSeparator()
        menu.addAction(self.new_route_action)
        menu.addAction(self.settings_action)
        menu.addAction(self.about_action)
        menu.exec_(self.MainTable.viewport().mapToGlobal(location))

    def send_changed(self, item):
        if item.column() == 0:
            self.edit_signal.emit(item.row(), item.text())

    def sett_pop(self):
        w = popups.SettingsPop(self, self.settings)
        w.setupUi()
        w.settings_signal.connect(self.change_editable_settings)

    def copy(self):
        if self.MainTable.currentItem() is not None:
            QtWidgets.QApplication.clipboard().setText(self.MainTable.currentItem().text())

    def change_item_text(self):
        item = self.MainTable.currentItem()
        self.MainTable.editItem(item)

    def insert_row(self, data):
        col_count = self.MainTable.columnCount()
        if len(data) != col_count:
            raise ValueError("Insert must contain the same amount of values in "
                             "an interable as there are columns in the table")
        row_pos = self.MainTable.rowCount()
        self.MainTable.setRowCount(row_pos + 1)
        for i in range(0, col_count):
            item = QtWidgets.QTableWidgetItem(str(data[i]))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.MainTable.setItem(row_pos, i, item)

    def show_w(self):
        ui = PlotStartDialog(self, self.settings)
        ui.setupUi()
        ui.data_signal.connect(self.pop_table)

    def pop_table(self, journal, table_data, index):
        try:
            self.MainTable.itemChanged.disconnect()
        except TypeError:
            pass
        self.start_worker(journal, table_data, index)
        self.total_jumps = sum(jum[3] for jum in table_data)
        self.MainTable.horizontalHeaderItem(3).setText(f"Jumps ({self.total_jumps}/{self.total_jumps})")
        for row in table_data:
            self.insert_row(row)

        self.MainTable.itemChanged.connect(self.send_changed)

    def start_worker(self, journal, data_values, index):
        self.thread = QtCore.QThread()
        self.worker = workers.AhkWorker(self, journal, data_values, self.settings, index)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.main)
        self.worker.sys_signal.connect(self.grayout)
        self.worker.route_finished_signal.connect(self.end_route_pop)
        self.worker.game_shut_signal.connect(self.restart_worker)
        self.thread.start()

    def restart_worker(self, route_data, route_index):
        self.thread.quit()
        while not self.thread.isFinished():
            QtCore.QThread.sleep(1)
        rw = popups.GameShutPop(self, self.settings, route_data, route_index)
        rw.setupUi()
        rw.worker_signal.connect(self.start_worker)
        rw.close_signal.connect(self.disconnect_signals)

    def disconnect_signals(self):
        try:
            self.disconnect()
            self.MainTable.disconnect()
            self.change_action.disconnect()
        except TypeError:
            pass

    def grayout(self, index, dark):
        self.update_jumps(index)
        self.last_index = index
        try:
            self.MainTable.itemChanged.disconnect()
        except TypeError:
            pass

        if dark:
            text_color = QtGui.QColor(240, 240, 240)
        else:
            text_color = QtGui.QColor(0, 0, 0)

        for row in range(0, index):
            for i in range(0, 4):
                self.MainTable.item(row, i).setForeground(QtGui.QColor(150, 150, 150))
        for row in range(index, self.MainTable.rowCount()):
            for i in range(0, 4):
                self.MainTable.item(row, i).setForeground(text_color)
        self.MainTable.itemChanged.connect(self.send_changed)

    def table_click(self, c):
        self.double_signal.emit(c.row())

    def quit_pop(self, prompt, modal):
        d = popups.QuitDialog(self, prompt, modal)
        d.setupUi()

    def end_route_pop(self):
        w = popups.RouteFinishedPop(self)
        w.setup()
        w.close_signal.connect(self.disconnect_signals)
        w.new_route_signal.connect(self.new_route)

    def licenses_pop(self):
        w = popups.LicensePop(self)
        w.setup()

    def update_jumps(self, index):
        remaining_jumps = sum(int(self.MainTable.item(i, 3).text()) for i in range(index, self.MainTable.rowCount()))
        if self.total_jumps != 0:
            self.MainTable.horizontalHeaderItem(3).setText(f"Jumps ({remaining_jumps}/{self.total_jumps})")

    def new_route(self):
        self.quit_worker_signal.emit()
        try:
            self.thread.quit()
        except AttributeError:
            pass
        self.MainTable.horizontalHeaderItem(3).setText("Jumps")
        self.MainTable.clearContents()
        self.MainTable.setRowCount(0)
        self.show_w()

    def retranslateUi(self):
        self.setWindowTitle("Auto Neutron")
        item = self.MainTable.horizontalHeaderItem(0)
        item.setText("System Name")
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        item = self.MainTable.horizontalHeaderItem(1)
        item.setText("Distance")
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        item = self.MainTable.horizontalHeaderItem(2)
        item.setText("Remaining")
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        item = self.MainTable.horizontalHeaderItem(3)
        item.setText("Jumps")
        item.setTextAlignment(QtCore.Qt.AlignCenter)

    def change_editable_settings(self, values):
        self.script_mode_signal.emit(values[7])
        self.script_settings.emit((values[0], values[1], values[2]))
        if values[2]:
            self.dark = True
            change_to_dark(self.application)
            self.grayout(self.last_index, True)
        else:
            self.dark = False
            change_to_default(self.application)
            self.grayout(self.last_index, False)

        self.save_on_quit = values[6]

        font = values[3]
        font.setPointSize(values[4])
        font.setBold(values[5])
        self.MainTable.setFont(font)

    def write_default_settings(self):
        if not self.settings.value("paths/journal"):
            self.resize(800, 600)
            self.move(300, 300)
            self.settings.setValue("paths/journal",
                                   f"{environ['userprofile']}/Saved Games/Frontier Developments/Elite Dangerous/")
            self.jpath = f"{environ['userprofile']}/Saved Games/Frontier Developments/Elite Dangerous/"
            self.settings.setValue("paths/ahk", environ['PROGRAMW6432'] + "\\AutoHotkey\\AutoHotkey.exe")
            self.settings.setValue("save_on_quit", True)
            self.settings.setValue("paths/csv", "")
            self.settings.setValue("window/size", QtCore.QSize(800, 600))
            self.settings.setValue("window/pos", QtCore.QPoint(100, 100))
            self.settings.setValue("window/dark", False)
            self.settings.setValue("window/font_size", 11)
            self.settings.setValue("font/font", QtGui.QFont())
            self.settings.setValue("font/size", 11)
            self.settings.setValue("font/bold", False)
            self.settings.setValue("bind", "F5")
            self.settings.setValue("script", ("SetKeyDelay, 50, 50\n"
                                              ";bind to open map\n"
                                              "send, {Numpad7}\n"
                                              "; wait for map to open\n"
                                              "sleep, 850\n"
                                              ";navigate to second map tab and focus on search field\n"
                                              "send, e\n"
                                              "send, {Space}\n"
                                              "ClipOld := ClipboardAll\n"
                                              'Clipboard := "|SYSTEMDATA|"\n'
                                              "sleep, 100\n"
                                              "Send, ^v\n"
                                              "Clipboard := ClipOld\n"
                                              "ClipOld ="
                                              "SetKeyDelay, 1, 2\n"
                                              "send, {enter}\n"))
            self.settings.setValue("last_route", ())
            self.settings.sync()
            self.write_ahk_path()

    def write_ahk_path(self):
        try:
            open(self.settings.value("paths/ahk")).close()
        except FileNotFoundError:
            ahk_path = QtWidgets.QFileDialog.getOpenFileName(filter="AutoHotKey (AutoHotKey*.exe)",
                                                             caption="Select AutoHotkey's executable "
                                                                     "if you wish to use AHK")
            if len(ahk_path[0]) == 0:
                self.settings.setValue("copy_mode", True)
                self.settings.setValue("paths/AHK", "")
            else:
                self.settings.setValue("paths/AHK", ahk_path[0])
                self.settings.setValue("copy_mode", False)
            self.settings.sync()

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).closeEvent(*args, **kwargs)
        self.settings.setValue("window/size", self.size())
        self.settings.setValue("window/pos", self.pos())
        self.settings.sync()
        self.window_quit_signal.emit(self.save_on_quit)


class PlotStartDialog(QtWidgets.QDialog):
    data_signal = QtCore.pyqtSignal(str, list, int)

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
        self.sp_comb = QtWidgets.QComboBox(self.tab_2)
        self.sp_submit = QtWidgets.QPushButton(self.tab_2, enabled=False)
        self.eff_spinbox = QtWidgets.QSpinBox(self.tab_2)
        self.range = QtWidgets.QLabel(self.tab_2)
        self.ran_spinbox = QtWidgets.QDoubleSpinBox(self.tab_2)
        self.efficiency = QtWidgets.QLabel(self.tab_2)
        self.destination = QtWidgets.QLineEdit(self.tab_2)
        self.status_layout = QtWidgets.QVBoxLayout(self)
        self.status = QtWidgets.QStatusBar()

    def setupUi(self):
        self.setMinimumSize(233, 241)
        self.resize(233, 241)
        self.tabWidget.addTab(self.tab, "")
        self.tabWidget.addTab(self.tab_2, "")
        self.tabWidget.addTab(self.tab_3, "")

        self.gridLayout.setContentsMargins(4, 6, 2, 2)
        self.gridLayout.setSpacing(0)
        self.gridLayout.addWidget(self.tabWidget)
        self.gridLayout.addLayout(self.status_layout, 1, 0, 1, 1)
        self.status_layout.addWidget(self.status)

        # CSV
        self.path_button.setMaximumWidth(95)
        if len(self.cpath) > 0:
            self.cs_submit.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(self.cs_comb.sizePolicy().hasHeightForWidth())
        self.cs_comb.setSizePolicy(sizePolicy)
        self.cs_comb.setMaximumWidth(95)
        self.cs_submit.setMaximumWidth(65)
        self.path_label.setWordWrap(True)

        self.cs_submit.pressed.connect(lambda: self.cs_submit_act(self.cpath))
        self.path_button.pressed.connect(self.change_path)

        self.horizontalLayout.addWidget(self.path_button, alignment=QtCore.Qt.AlignLeft)
        spacerItem = QtWidgets.QSpacerItem(30, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout_2.addLayout(self.horizontalLayout, 2, 0, 1, 1)
        self.horizontalLayout_2.addWidget(self.cs_comb, alignment=QtCore.Qt.AlignLeft)
        self.horizontalLayout_2.addWidget(self.cs_submit, alignment=QtCore.Qt.AlignRight)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 4, 0, 1, 1)
        self.gridLayout_2.addWidget(self.path_label, 1, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
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

        self.gridLayout_4.addWidget(self.ran_spinbox, 3, 0, 1, 1)
        self.gridLayout_4.addWidget(self.efficiency, 4, 0, 1, 1)
        self.gridLayout_4.addWidget(self.destination, 1, 0, 1, 1)
        self.gridLayout_4.addWidget(self.sp_comb, 7, 0, 1, 1)
        self.gridLayout_4.addWidget(self.range, 2, 0, 1, 1)
        self.gridLayout_4.addWidget(self.source, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.nearest, 5, 1, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_4.addItem(spacerItem2, 6, 0, 1, 1)
        self.gridLayout_4.addWidget(self.eff_spinbox, 5, 0, 1, 1)
        self.gridLayout_4.addWidget(self.sp_submit, 7, 1, 1, 1)

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
        self.show()

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

    def button_on_filled_fields(self):
        if len(self.destination.text()) > 0 and len(self.source.text()) > 0:
            self.sp_submit.setEnabled(True)
        else:
            self.sp_submit.setEnabled(False)

    def change_path(self):
        file_dialog = QtWidgets.QFileDialog()
        fpath = file_dialog.getOpenFileName(filter="csv (*.csv)")
        if len(fpath[0]) > 0:
            self.cpath = fpath[0]
            self.path_label.setText("Current path: " + fpath[0])
            self.settings.setValue("paths/csv", fpath[0])
            self.settings.sync()
            self.cs_submit.setEnabled(True)
        else:
            self.cs_submit.setEnabled(False)

    def get_journals(self):
        try:
            self.journals = sorted([self.jpath + file for file in listdir(self.jpath) if file.endswith(".log")],
                                   key=getctime, reverse=True)
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
                self.update_source(0)
                self.current_range(0)

    def update_source(self, index):
        # set source system to last visited in currently selected journal
        with open(self.journals[index], encoding='utf-8') as f:
            lines = [json.loads(line) for line in f]
        try:
            self.source.setText(next(lines[i]['StarSystem'] for i in range(len(lines) - 1, -1, -1)
                                     if lines[i]['event'] == "FSDJump" or lines[i]['event'] == "Location"))
        except StopIteration:
            self.source.clear()

    def current_range(self, index):
        with open(self.journals[index], encoding='utf-8') as f:
            lines = [json.loads(line) for line in f]
        try:
            self.ran_spinbox.setValue(next(round(float(lines[i]['MaxJumpRange']), 2)
                                           for i in range(len(lines) - 1, -1, -1) if lines[i]['event'] == "Loadout"))
        except StopIteration:
            self.ran_spinbox.setValue(5)

    def update_destination(self, system):
        self.destination.setText(system)

    def sp_submit_act(self):
        self.plotter = workers.SpanshPlot(self.eff_spinbox.value(), self.ran_spinbox.value(),
                                          self.source.text(), self.destination.text())
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
            with open(cpath, encoding='utf-8') as f:

                data = []
                valid = True
                for stuff in csv.DictReader(f, delimiter=','):
                    tlist = []
                    tlist.append(stuff['System Name'])
                    if stuff is None:
                        valid = False
                        break
                    try:
                        tlist.append(round(float(stuff['Distance To Arrival']), 2))
                    except (ValueError, KeyError):
                        valid = False
                        break

                    try:
                        tlist.append(round(float(stuff['Distance Remaining']), 2))
                    except (ValueError, KeyError):
                        valid = False
                        break
                    try:
                        tlist.append(int(stuff['Jumps']))
                    except (ValueError, KeyError):
                        valid = False
                        break
                    data.append(tlist)
                if valid:
                    self.data_signal.emit(self.journals[self.cs_comb.currentIndex()], data, -1)
                    self.close()
                else:
                    self.status.showMessage("Error loading csv file")
                    self.cs_submit.setEnabled(True)

        except FileNotFoundError:
            self.status.showMessage("Invalid path to CSV file")

    def last_submit_act(self):
        last_route = self.settings.value("last_route")
        if last_route is None or len(last_route) == 0:
            self.status.showMessage("No last route found")
        else:
            if last_route[0] == len(last_route[1]):
                self.data_signal.emit(self.journals[self.last_comb.currentIndex()], last_route[1], 1)
                self.close()
            else:
                self.data_signal.emit(self.journals[self.last_comb.currentIndex()], last_route[1], last_route[0])
                self.close()

    def show_nearest(self):
        self.nearest.setEnabled(False)
        n_win = popups.Nearest(self)
        n_win.setupUi()
        n_win.closed_signal.connect(self.enable_button)
        n_win.destination_signal.connect(self.update_destination)

    def enable_button(self):
        self.nearest.setEnabled(True)


def change_to_dark(application):
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
    application.setStyle("Fusion")
    application.setPalette(p)


def change_to_default(application):
    application.setStyle("Fusion")
    application.setPalette(application.style().standardPalette())
