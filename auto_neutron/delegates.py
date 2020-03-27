from PyQt5 import QtWidgets
from PyQt5 import QtCore


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
