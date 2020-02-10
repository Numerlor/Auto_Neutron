# This file is part of Auto_Neutron.
# Copyright (C) 2019-2020  Numerlor

import csv
import json
import os
import sys
from pathlib import Path

from PyQt5 import QtWidgets, QtCore, QtGui
from pyperclip import copy as set_clip

from auto_neutron import popups
from auto_neutron import workers
from auto_neutron.constants import SHIP_STATS


# TODO clean up th mess of PlotStartDialog

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


class MainWindow(QtWidgets.QMainWindow):
    double_signal = QtCore.pyqtSignal(int)  # double click signal to set worker to new clicked row
    edit_signal = QtCore.pyqtSignal(int, str)  # send edited system to worker if changed
    next_jump_signal = QtCore.pyqtSignal(bool)

    def __init__(self, hub):
        super(MainWindow, self).__init__()
        self.hub = hub
        self.centralwidget = QtWidgets.QWidget(self)
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.MainTable = QtWidgets.QTableWidget(self.centralwidget)
        self.spin_delegate = SpinBoxDelegate()
        self.double_spin_delegate = DoubleSpinBoxDelegate()

        self.change_action = QtWidgets.QAction("Edit", self)
        self.save_action = QtWidgets.QAction("Save route", self)
        self.copy_action = QtWidgets.QAction("Copy", self)
        self.new_route_action = QtWidgets.QAction("Start a new route", self)
        self.settings_action = QtWidgets.QAction("Settings", self)
        self.about_action = QtWidgets.QAction("About", self)

        self.last_index = 0

        self.setup_ui()

    def setup_ui(self):
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

        p = self.MainTable.palette()
        p.setColor(QtGui.QPalette.Highlight, QtGui.QColor(255, 255, 255, 0))
        p.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 123, 255))
        self.MainTable.setPalette(p)
        self.retranslateUi()

    def connect_signals(self):
        self.MainTable.customContextMenuRequested.connect(self.table_context)
        self.customContextMenuRequested.connect(self.main_context)
        self.MainTable.doubleClicked.connect(self.table_click)
        # actions
        self.copy_action.triggered.connect(self.copy)
        self.change_action.triggered.connect(self.change_item_text)

        self.save_action.triggered.connect(self.hub.save_route_signal.emit)
        self.settings_action.triggered.connect(self.hub.sett_pop)
        self.about_action.triggered.connect(self.hub.licenses_pop)
        self.new_route_action.triggered.connect(self.hub.new_route)

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

    def copy(self):
        if self.MainTable.currentItem() is not None:
            set_clip(self.MainTable.currentItem().text())

    def change_item_text(self):
        item = self.MainTable.currentItem()
        self.MainTable.editItem(item)

    def table_click(self, c):
        self.double_signal.emit(c.row())

    def update_jumps(self, index):
        """Update remaining jump count"""
        # sum all values in 4th column
        total_jumps = sum(
            int(self.MainTable.item(i, 3).text()) for i in
            range(self.MainTable.rowCount()))

        if total_jumps:
            remaining_jumps = sum(
                int(self.MainTable.item(i, 3).text()) for i in
                range(index, self.MainTable.rowCount()))

            self.MainTable.horizontalHeaderItem(3).setText(
                f"Jumps {remaining_jumps}/{total_jumps}")
        else:
            self.MainTable.horizontalHeaderItem(3).setText("Jumps")
        self.MainTable.resizeColumnToContents(3)

    def reset_table(self):
        self.MainTable.horizontalHeaderItem(3).setText("Jumps")
        self.MainTable.clearContents()
        self.MainTable.setRowCount(0)
        self.last_index = 0

    def pop_table(self, table_data, _, __):
        """Populate table with table_data"""

        # disconnect signal to not update things needlessly
        try:
            self.MainTable.itemChanged.disconnect()
        except TypeError:
            pass

        self.update_jumps(0)

        for row in table_data:
            self.insert_row(row)

        self.MainTable.resizeColumnToContents(0)
        self.MainTable.resizeRowsToContents()
        # reconnect signal
        self.MainTable.itemChanged.connect(self.manage_changed)

    def insert_row(self, data):
        """Creates a new row and inserts 4 items from data"""
        col_count = self.MainTable.columnCount()
        row_pos = self.MainTable.rowCount()
        self.MainTable.setRowCount(row_pos + 1)
        for i in range(0, col_count):
            item = QtWidgets.QTableWidgetItem(str(data[i]))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.MainTable.setItem(row_pos, i, item)

    def manage_changed(self, item):
        """Update relevant data in script if item was changed"""
        # if edited item was in first column, send it to worker and update column size
        if item.column() == 0:
            self.MainTable.resizeColumnToContents(0)
            self.edit_signal.emit(item.row(), item.text())
        elif item.column() == 3:
            self.update_jumps(self.last_index)

    def disconnect_signals(self):
        # disconnect all signals that interact
        try:
            self.disconnect()
            self.MainTable.disconnect()
            self.change_action.disconnect()
        except TypeError:
            pass

    def index_change(self, index):
        """Update table when index is changed"""

        self.update_jumps(index)
        self.next_jump_signal.emit(
            self.MainTable.item(index, 3).text() == "1")

        if (self.autoscroll and
                (self.MainTable.itemAt(QtCore.QPoint(1, 1)).row() == self.last_index
                 or self.last_index == 0)):
            self.MainTable.scrollToItem(self.MainTable.item(index, 0)
                                        , QtWidgets.QAbstractItemView.PositionAtTop)
        self.grayout(index, self.dark)
        self.last_index = index

    def grayout(self, index, dark):
        """Set all rows before index to grey, all rows after to black/white"""

        try:
            self.MainTable.itemChanged.disconnect()
        except TypeError:
            pass

        text_color = "#f0f0f0" if dark else "#000000"
        for row in range(0, index):
            for i in range(0, 4):
                self.MainTable.item(row, i).setForeground(QtGui.QColor(150, 150, 150))
        for row in range(index, self.MainTable.rowCount()):
            for i in range(0, 4):
                self.MainTable.item(row, i).setForeground(QtGui.QColor(text_color))
        self.MainTable.itemChanged.connect(self.manage_changed)

    def change_settings(self, font, dark, autoscroll):
        self.dark = dark
        self.autoscroll = autoscroll
        if self.MainTable.rowCount() != 0:
            self.grayout(self.last_index, self.dark)
        self.MainTable.setFont(font)
        self.MainTable.resizeColumnToContents(0)
        self.MainTable.resizeColumnToContents(3)
        self.MainTable.resizeRowsToContents()

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

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).closeEvent(*args, **kwargs)
        self.hub.quit(self.saveGeometry())


class PlotStartDialog(QtWidgets.QDialog):
    data_signal = QtCore.pyqtSignal(list, Path, int)
    fuel_signal = QtCore.pyqtSignal(int)

    def __init__(self, parent, settings):
        super(PlotStartDialog, self).__init__(parent)
        self.settings = settings
        self.jpath = Path(self.settings.paths.journal)
        cpath = self.settings.paths.csv
        self.cpath = Path(cpath) if cpath else cpath
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
        self.spansh_layout = QtWidgets.QVBoxLayout(self.tab_2)
        self.nearest_layout = QtWidgets.QHBoxLayout(self.tab_2)
        self.sp_submit_layout = QtWidgets.QHBoxLayout(self.tab_2)
        self.source = QtWidgets.QLineEdit(self.tab_2)
        self.nearest = QtWidgets.QPushButton(self.tab_2)
        self.cargo_slider = QtWidgets.QSlider(self.tab_2, orientation=QtCore.Qt.Horizontal)
        self.cargo_label = QtWidgets.QLabel(self.tab_2)
        self.sp_comb = QtWidgets.QComboBox(self.tab_2)
        self.sp_submit = QtWidgets.QPushButton(self.tab_2, enabled=False)
        self.eff_spinbox = QtWidgets.QSpinBox(self.tab_2)
        self.range = QtWidgets.QLabel(self.tab_2)
        self.ran_spinbox = QtWidgets.QDoubleSpinBox(self.tab_2)
        self.efficiency = QtWidgets.QLabel(self.tab_2)
        self.destination = QtWidgets.QLineEdit(self.tab_2)
        self.status_layout = QtWidgets.QVBoxLayout(self)
        self.status = QtWidgets.QStatusBar()

    def setup_ui(self):

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
        if self.cpath:
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
        self.nearest.setMaximumWidth(65)
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
        self.sp_comb.currentIndexChanged.connect(self.current_range)
        self.cargo_slider.valueChanged.connect(self.update_range)

        self.nearest_layout.addWidget(self.eff_spinbox, alignment=QtCore.Qt.AlignLeft)
        self.nearest_layout.addWidget(self.nearest, alignment=QtCore.Qt.AlignRight)

        self.sp_submit_layout.addWidget(self.sp_comb, alignment=QtCore.Qt.AlignLeft)
        self.sp_submit_layout.addWidget(self.sp_submit, alignment=QtCore.Qt.AlignRight)

        self.spansh_layout.addWidget(self.source)
        self.spansh_layout.addWidget(self.destination)
        self.spansh_layout.addWidget(self.cargo_label)
        self.spansh_layout.addWidget(self.cargo_slider)
        self.spansh_layout.addWidget(self.range)
        self.spansh_layout.addWidget(self.ran_spinbox)
        self.spansh_layout.addWidget(self.efficiency)
        self.spansh_layout.addLayout(self.nearest_layout)
        self.spansh_layout.addSpacerItem(spacerItem1)
        self.spansh_layout.addLayout(self.sp_submit_layout)
        self.set_order()

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

    def after_show(self):
        # delay connecting of singals to only open file once
        self.last_comb.currentIndexChanged.connect(self.set_max_fuel)
        self.cs_comb.currentIndexChanged.connect(self.set_max_fuel)
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
        self.path_label.setText("Current path: " + str(self.cpath))
        self.source.setPlaceholderText("Source System")
        self.nearest.setText("Nearest")
        self.sp_submit.setText("Submit")
        self.range.setText("Range")
        self.efficiency.setText("Efficiency")
        self.destination.setPlaceholderText("Destination System")
        self.cargo_label.setText("Cargo")

    def button_on_filled_fields(self):
        if self.destination.text() and self.source.text():
            self.sp_submit.setEnabled(True)
        else:
            self.sp_submit.setEnabled(False)

    def set_order(self):
        self.tab_2.setTabOrder(self, self.source)
        self.tab_2.setTabOrder(self.source, self.destination)
        self.tab_2.setTabOrder(self.destination, self.cargo_slider)
        self.tab_2.setTabOrder(self.cargo_slider, self.ran_spinbox)
        self.tab_2.setTabOrder(self.ran_spinbox, self.eff_spinbox)
        self.tab_2.setTabOrder(self.eff_spinbox, self.nearest)
        self.tab_2.setTabOrder(self.nearest, self.sp_comb)
        self.tab_2.setTabOrder(self.sp_comb, self.sp_submit)

    def change_path(self):
        file_dialog = QtWidgets.QFileDialog()
        fpath, _ = file_dialog.getOpenFileName(filter="csv (*.csv)",
                                               directory=str(self.cpath.parent)
                                               if self.cpath else "")
        if fpath:
            self.cpath = Path(fpath)
            self.path_label.setText("Current path: " + str(self.cpath))
            self.settings.paths.csv = str(self.cpath)
            self.cs_submit.setEnabled(True)
        else:
            if not self.cpath:
                self.cs_submit.setEnabled(False)

    def get_journals(self):
        try:
            self.journals = sorted(
                [self.jpath / file for file in os.listdir(self.jpath)
                 if file.endswith(".log")],
                key=os.path.getctime, reverse=True)
        except FileNotFoundError:
            w = popups.QuitDialog(self, "Journal folder not detected", True)
            w.show()
        else:
            options = ["Last journal", "Second to last", "Third to last"][:len(self.journals)]
            if not options:
                w = popups.QuitDialog(self, "No journals detected", False)
                w.show()
                self.sp_submit.setEnabled(False)
                self.cs_submit.setEnabled(False)
                self.last_submit.setEnabled(False)
                self.source.setDisabled(True)
                self.destination.setDisabled(True)
            else:
                self.cs_comb.addItems(options)
                self.sp_comb.addItems(options)
                self.last_comb.addItems(options)

    def current_range(self, index):
        with self.journals[index].open(encoding='utf-8') as f:
            lines = [json.loads(line) for line in f]
        try:
            self.source.setText(next(lines[i]['StarSystem'] for i
                                     in range(len(lines) - 1, -1, -1)
                                     if lines[i]['event'] == "FSDJump"
                                     or lines[i]['event'] == "Location"))
        except StopIteration:
            self.source.clear()

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
        # set text of source input widget to last visited sys

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

    def set_max_fuel(self, index):
        with self.journals[index].open(encoding='utf-8') as f:
            lines = [json.loads(line) for line in f]
        try:
            # get last loadout event line
            loadout = next(lines[i] for i in range(len(lines) - 1, -1, -1)
                           if lines[i]['event'] == "Loadout"
                           and lines[i]['MaxJumpRange'] != 0)
        except StopIteration:
            pass
        else:
            # get FSD
            fsd = next((i for i in loadout['Modules']
                        if i['Slot'] == "FrameShiftDrive"))
            max_fuel = SHIP_STATS['FSD'][fsd['Item']][0]
            if 'Engineering' in fsd:
                for blueprint in fsd['Engineering']['Modifiers']:
                    if blueprint['Label'] == 'MaxFuelPerJump':
                        max_fuel = blueprint['Value']
            self.fuel_signal.emit(max_fuel)

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
        if files:
            self.cs_submit_act(Path(files[0]))

    def sp_submit_act(self):
        self.plotter = workers.SpanshPlot(self.eff_spinbox.value(),
                                          self.ran_spinbox.value(),
                                          self.source.text().strip(),
                                          self.destination.text().strip(), self)
        self.plotter.status_signal.connect(self.change_status)
        self.plotter.finished_signal.connect(self.sp_finish_act)
        self.plotter.start()

    def sp_finish_act(self, data):
        self.data_signal.emit(data, self.journals[self.cs_comb.currentIndex()], -1)
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
                with cpath.open(encoding='utf-8') as f:
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
                            data,
                            self.journals[self.cs_comb.currentIndex()],
                            -1)
                        self.close()
                    else:
                        self.status.showMessage("Error loading csv file")
                        self.cs_submit.setEnabled(True)

        except FileNotFoundError:
            self.status.showMessage("Invalid path to CSV file")

    def last_submit_act(self):
        self.last_submit.setEnabled(False)
        last_route = self.settings.last_route
        if not last_route:
            self.status.showMessage("No last route found")
            self.last_submit.setEnabled(True)
        else:
            index = int(last_route[0])
            route = last_route[1]
            if index == route:
                self.data_signal.emit(route, self.journals[self.last_comb.currentIndex()], 1)
                self.close()
            else:
                self.data_signal.emit(route, self.journals[self.last_comb.currentIndex()], index)
                self.close()

    def show_nearest(self):
        self.nearest.setEnabled(False)
        n_win = popups.Nearest(self)
        n_win.show()
        n_win.closed_signal.connect(self.enable_button)
        n_win.destination_signal.connect(self.update_destination)

    def enable_button(self):
        self.nearest.setEnabled(True)
