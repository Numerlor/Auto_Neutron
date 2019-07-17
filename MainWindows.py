import csv
import json
import os
import sys

from PyQt5 import QtWidgets, QtCore, QtGui

import popups
import workers
from appinfo import SHIP_STATS


class SpinBoxDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, QStyleOptionViewItem, QModelIndex):
        editor = QtWidgets.QSpinBox(parent)
        editor.setFrame(False)
        editor.setMinimum(0)
        editor.setMaximum(10_000)
        editor.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        return editor

    def setEditorData(self, QWidget, QModelIndex):
        value = int(QModelIndex.model().data(QModelIndex, QtCore.Qt.EditRole))

        QWidget.setValue(value)

    def setModelData(self, QWidget, QAbstractItemModel, QModelIndex):
        QWidget.interpretText()
        value = QWidget.value()
        QAbstractItemModel.setData(QModelIndex, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, QWidget, QStyleOptionViewItem, QModelIndex):
        QWidget.setGeometry(QStyleOptionViewItem.rect)


class DoubleSpinBoxDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, QStyleOptionViewItem, QModelIndex):
        editor = QtWidgets.QDoubleSpinBox(parent)
        editor.setFrame(False)
        editor.setMinimum(0)
        editor.setMaximum(1_000_000)
        editor.setDecimals(2)
        editor.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        return editor

    def setEditorData(self, QWidget, QModelIndex):
        value = float(QModelIndex.model().data(QModelIndex, QtCore.Qt.EditRole))
        QWidget.setValue(value)

    def setModelData(self, QWidget, QAbstractItemModel, QModelIndex):
        value = QWidget.text()
        QAbstractItemModel.setData(QModelIndex, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, QWidget, QStyleOptionViewItem, QModelIndex):
        QWidget.setGeometry(QStyleOptionViewItem.rect)


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

        self.spin_delegate = SpinBoxDelegate()
        self.double_spin_delegate = DoubleSpinBoxDelegate()
        self.last_index = 0
        self.total_jumps = 0
        self.max_fuel = 9999999999

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
        for i in range(4):
            item = QtWidgets.QTableWidgetItem()
            self.MainTable.setHorizontalHeaderItem(i, item)

        self.MainTable.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.MainTable.setAlternatingRowColors(True)
        self.MainTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.MainTable.verticalHeader().setVisible(False)

        header = self.MainTable.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Fixed)
        header.setHighlightSections(False)
        header.disconnect()

        self.MainTable.setItemDelegateForColumn(1, self.double_spin_delegate)
        self.MainTable.setItemDelegateForColumn(2, self.double_spin_delegate)
        self.MainTable.setItemDelegateForColumn(3, self.spin_delegate)

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
            self.MainTable.resizeColumnToContents(0)
            self.edit_signal.emit(item.row(), item.text())
        elif item.column() == 3:
            self.update_jumps(self.last_index)

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
        ui.data_signal.connect(self.pop_table)
        ui.fuel_signal.connect(self.set_max_fuel)
        ui.setupUi()

    def pop_table(self, journal, table_data, index):
        try:
            self.MainTable.itemChanged.disconnect()
        except TypeError:
            pass
        self.start_worker(journal, table_data, index)
        self.update_jumps(0)
        for row in table_data:
            self.insert_row(row)

        self.MainTable.resizeColumnToContents(0)
        self.MainTable.resizeRowsToContents()
        self.MainTable.itemChanged.connect(self.send_changed)

    def start_worker(self, journal, data_values, index):
        self.worker = workers.AhkWorker(self, journal, data_values, self.settings, index)
        self.worker.sys_signal.connect(self.grayout)
        self.worker.route_finished_signal.connect(self.end_route_pop)
        self.worker.game_shut_signal.connect(self.restart_worker)
        self.worker.start()

        status_file = (f"{os.environ['userprofile']}/Saved Games/"
                       f"Frontier Developments/Elite Dangerous/Status.json")
        self.sound_worker = workers.FuelAlert(self.max_fuel, status_file, self)
        self.sound_worker.start()

    def set_max_fuel(self, value):
        self.max_fuel = value

    def restart_worker(self, route_data, route_index):
        self.worker.quit()
        while not self.worker.isFinished():
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
        total_jumps = sum(
            int(self.MainTable.item(i, 3).text()) for i in
            range(self.MainTable.rowCount()))

        if total_jumps != 0:
            remaining_jumps = sum(
                int(self.MainTable.item(i, 3).text()) for i in
                range(index, self.MainTable.rowCount()))

            self.MainTable.horizontalHeaderItem(3).setText(
                f"Jumps {remaining_jumps}/{total_jumps}")
            self.MainTable.resizeColumnToContents(3)
        else:
            self.MainTable.horizontalHeaderItem(3).setText("Jumps")

    def new_route(self):
        self.quit_worker_signal.emit()
        try:
            self.worker.quit()
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
        self.MainTable.resizeColumnToContents(0)
        self.MainTable.resizeColumnToContents(3)
        self.MainTable.resizeRowsToContents()

    def write_default_settings(self):
        if not self.settings.value("paths/journal"):
            self.resize(800, 600)
            self.move(300, 300)
            self.settings.setValue("paths/journal",
                                   (f"{os.environ['userprofile']}/Saved Games/"
                                    f"Frontier Developments/Elite Dangerous/"))
            self.jpath = (f"{os.environ['userprofile']}/Saved Games/"
                          f"Frontier Developments/Elite Dangerous/")
            self.settings.setValue("paths/ahk",
                                   (f"{os.environ['PROGRAMW6432']}/"
                                    f"AutoHotkey/AutoHotkey.exe"))
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
                                              ";navigate to second map tab "
                                              "and focus on search field\n"
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
            ahk_path = QtWidgets.QFileDialog.getOpenFileName(
                filter="AutoHotKey (AutoHotKey*.exe)",
                caption="Select AutoHotkey's executable "
                        "if you wish to use it, cancel for copy mode",
                directory="C:/")

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
        self.cargo = QtWidgets.QSlider(orientation=QtCore.Qt.Horizontal)
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
        self.cargo.valueChanged.connect(self.update_range)

        self.gridLayout_4.addWidget(self.source, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.destination, 1, 0, 1, 1)
        self.gridLayout_4.addWidget(self.cargo_label, 2, 0, 1, 1)
        self.gridLayout_4.addWidget(self.cargo, 3, 0, 1, 1)
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
        self.show()
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
            loadout = next(lines[i] for i in range(len(lines) - 1, -1, -1)
                           if lines[i]['event'] == "Loadout"
                           and lines[i]['MaxJumpRange'] != 0)
            ship_cargo = next(lines[i] for i in range(len(lines) - 1, -1, -1)
                              if lines[i]['event'] == "Cargo"
                              and lines[i]['Vessel'] == "Ship")['Count']
            self.cargo.setDisabled(False)
            cargo_cap = loadout['CargoCapacity']
            fuel = loadout['FuelCapacity']['Main']
            mass = loadout['UnladenMass']
            modules = (i for i in loadout['Modules']
                       if i['Slot'] == "FrameShiftDrive"
                       or "fsdbooster" in i['Item'])
            boost = 0
            for item in modules:
                if item['Slot'] == "FrameShiftDrive":
                    (max_fuel, optimal_mass, size_const,
                     class_const) = SHIP_STATS['FSD'][item['Item']]

                    if 'Engineering' in item.keys():
                        for blueprint in item['Engineering']['Modifiers']:
                            if blueprint['Label'] == "FSDOptimalMass":
                                optimal_mass = blueprint['Value']
                            elif blueprint['Label'] == "MaxFuelPerJump":
                                max_fuel = blueprint['Value']
                if "fsdbooster" in item['Item']:
                    boost = SHIP_STATS['Booster'][item['Item']]

            def jump_range(cargo):
                return (boost + optimal_mass * (1000 * max_fuel / class_const)
                        ** (1 / size_const) / (mass + fuel + cargo))

            self.jump_range = jump_range
            self.fuel_signal.emit(max_fuel)
            self.ran_spinbox.setValue(self.jump_range(ship_cargo))
            self.cargo.setMaximum(cargo_cap)
            self.cargo.setValue(ship_cargo)

        except StopIteration:
            self.ran_spinbox.setValue(50)
            self.cargo.setDisabled(True)

    def update_range(self, cargo):
        self.ran_spinbox.setValue(self.jump_range(cargo))

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
        if os.stat(cpath).st_size > 2_097_152:
            self.status.showMessage("File too large")
            self.cs_submit.setEnabled(True)
        else:
            try:
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
                        self.data_signal.emit(self.journals[self.cs_comb.currentIndex()], data, -1)
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
