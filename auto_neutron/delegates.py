# This file is part of Auto_Neutron.
# Copyright (C) 2019-2020  Numerlor
from typing import Union

from PySide6 import QtCore, QtWidgets

# noinspection PyUnresolvedReferences
from __feature__ import snake_case, true_property  # noqa F401


class SpinBoxDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for a table to use cells as `SpinBox`es."""

    def create_editor(  # noqa D102
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex],
    ) -> QtWidgets.QWidget:
        editor = QtWidgets.QSpinBox(parent)
        editor.frame = False
        editor.minimum = 1
        editor.maximum = 10_000
        editor.button_symbols = QtWidgets.QAbstractSpinBox.NoButtons
        return editor


class DoubleSpinBoxDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for a table to use cells as `DoubleSpinBox`es."""

    def create_editor(  # noqa D102
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex],
    ) -> QtWidgets.QWidget:
        editor = QtWidgets.QDoubleSpinBox(parent)
        editor.frame = False
        editor.minimum = 0
        editor.maximum = 1_000_000
        editor.decimals = 2
        editor.button_symbols = QtWidgets.QAbstractSpinBox.NoButtons
        return editor
