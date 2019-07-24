import os

from PyQt5 import QtWidgets, QtCore, QtGui

import popups
import workers
from route_chooser import PlotStartDialog


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

    stop_sound_worker_signal = QtCore.pyqtSignal()
    next_jump_signal = QtCore.pyqtSignal(bool)

    def __init__(self, settings, application: QtWidgets):
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

        self.sound_alert = self.settings.value("alerts/audio", type=bool)
        self.visual_alert = self.settings.value("alerts/visual", type=bool)
        self.sound_path = self.settings.value("paths/alert")
        self.modifier = self.settings.value("alerts/threshold", type=int)

        self.spin_delegate = SpinBoxDelegate()
        self.double_spin_delegate = DoubleSpinBoxDelegate()
        self.last_index = 0
        self.total_jumps = 0
        self.max_fuel = 9999999999
        self.workers_started = False

    def setupUi(self):
        self.resize(self.settings.value("window/size", type=QtCore.QSize))
        self.move(self.settings.value("window/pos", type=QtCore.QPoint))

        # connect and add actions
        self.connect_signals()
        # set context menus to custom
        self.MainTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

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
        # color management
        p = self.MainTable.palette()
        p.setColor(QtGui.QPalette.Highlight, QtGui.QColor(255, 255, 255, 0))
        p.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 123, 255))
        self.MainTable.setPalette(p)
        self.set_theme()
        self.retranslateUi()
        self.show()
        # show initial popup
        self.show_w()

    def connect_signals(self):
        self.MainTable.customContextMenuRequested.connect(self.table_context)
        self.customContextMenuRequested.connect(self.main_context)
        self.MainTable.doubleClicked.connect(self.table_click)
        # actions
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

    def set_theme(self):
        if self.dark:
            change_to_dark(self.application)
        else:
            change_to_default(self.application)

    def sett_pop(self):
        w = popups.SettingsPop(self, self.settings)
        w.setupUi()
        w.settings_signal.connect(self.change_editable_settings)

    def copy(self):
        if self.MainTable.currentItem() is not None:
            self.application.clipboard().setText(self.MainTable.currentItem().text())

    def change_item_text(self):
        item = self.MainTable.currentItem()
        self.MainTable.editItem(item)

    def table_click(self, c):
        self.double_signal.emit(c.row())

    def insert_row(self, data):
        col_count = self.MainTable.columnCount()
        row_pos = self.MainTable.rowCount()
        self.MainTable.setRowCount(row_pos + 1)
        for i in range(0, col_count):
            item = QtWidgets.QTableWidgetItem(str(data[i]))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.MainTable.setItem(row_pos, i, item)

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
        if self.workers_started:
            self.quit_worker_signal.emit()
            self.worker.quit()
            if any((self.visual_alert, self.sound_alert)):
                self.stop_sound_worker()

        self.MainTable.horizontalHeaderItem(3).setText("Jumps")
        self.MainTable.clearContents()
        self.MainTable.setRowCount(0)
        self.show_w()

    def start_worker(self, journal, data_values, index):
        self.worker = workers.AhkWorker(self, journal, data_values, self.settings, index)
        self.worker.sys_signal.connect(self.grayout)
        self.worker.route_finished_signal.connect(self.end_route_pop)
        self.worker.game_shut_signal.connect(self.restart_worker)
        self.worker.start()

        if self.visual_alert or self.sound_alert:
            self.start_sound_worker()
        self.workers_started = True

    def restart_worker(self, route_data, route_index):
        self.worker.quit()
        if self.sound_alert or self.visual_alert:
            self.stop_sound_worker()
        while not self.worker.isFinished():
            QtCore.QThread.sleep(1)
        rw = popups.GameShutPop(self, self.settings, route_data, route_index)
        rw.setupUi()
        rw.worker_signal.connect(self.start_worker)
        rw.close_signal.connect(self.disconnect_signals)

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

    def send_changed(self, item):
        if item.column() == 0:
            self.MainTable.resizeColumnToContents(0)
            self.edit_signal.emit(item.row(), item.text())
        elif item.column() == 3:
            self.update_jumps(self.last_index)

    def disconnect_signals(self):
        try:
            self.disconnect()
            self.MainTable.disconnect()
            self.change_action.disconnect()
        except TypeError:
            pass

    def grayout(self, index, dark):
        self.update_jumps(index)
        self.next_jump_signal.emit(
            self.MainTable.item(index, 3).text() == "1")
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

    def start_sound_worker(self):
        self.player = workers.SoundPlayer(self.sound_path)
        status_file = (f"{os.environ['userprofile']}/Saved Games/"
                       f"Frontier Developments/Elite Dangerous/Status.json")
        self.sound_worker = workers.FuelAlert(self.max_fuel, status_file, self, self.modifier)
        self.sound_worker.flash_signal.connect(self.fuel_alert)
        self.sound_worker.start()

    def stop_sound_worker(self):
        self.stop_sound_worker_signal.emit()
        self.sound_worker.quit()
        try:
            self.sound_worker.flash_signal.disconnect()
        except TypeError:
            pass

    def set_max_fuel(self, value):
        self.max_fuel = value

    def fuel_alert(self):
        if self.visual_alert:
            self.application.alert(self.centralwidget, 5000)
        if self.sound_alert:
            if self.sound_path:
                self.player.play()
            else:
                self.application.beep()

    def show_w(self):
        ui = PlotStartDialog(self, self.settings)
        ui.data_signal.connect(self.pop_table)
        ui.fuel_signal.connect(self.set_max_fuel)
        ui.setupUi()

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

        self.dark = values[2]
        self.set_theme()
        if self.MainTable.rowCount() != 0:
            self.grayout(self.last_index, self.dark)

        if (values[8] or values[9]
                and not any((self.sound_alert, self.visual_alert))):
            self.start_sound_worker()
        elif not values[8] and not values[9]:
            self.stop_sound_worker()
        self.sound_alert = values[8]
        self.visual_alert = values[9]

        self.save_on_quit = values[6]
        if self.modifier != values[10] and any((self.sound_alert, self.visual_alert)):
            self.stop_sound_worker()
            self.modifier = values[10]
            self.start_sound_worker()
        else:
            self.modifier = values[10]

        self.sound_path = values[11]
        self.player = workers.SoundPlayer(values[11])
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
            self.settings.setValue("alerts/audio", False)
            self.settings.setValue("alerts/visual", False)
            self.settings.setValue("alerts/threshold", 150)
            self.settings.setValue("paths/alert", "")
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
