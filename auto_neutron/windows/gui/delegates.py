# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401


class SpinBoxDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for a table to use cells as `SpinBox`es."""

    def create_editor(  # noqa: D102
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> QtWidgets.QWidget:
        editor = QtWidgets.QSpinBox(parent)
        editor.frame = False
        editor.minimum = 1
        editor.maximum = 10_000
        editor.button_symbols = QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        return editor


class DoubleSpinBoxDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for a table to use cells as `DoubleSpinBox`es."""

    def create_editor(  # noqa: D102
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> QtWidgets.QWidget:
        editor = QtWidgets.QDoubleSpinBox(parent)
        editor.frame = False
        editor.minimum = 0
        editor.maximum = 1_000_000
        editor.decimals = 2
        editor.button_symbols = QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        return editor


class CheckBoxDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for a table to use cells as `CheckBox`es."""

    def create_editor(  # noqa: D102
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> QtWidgets.QWidget:
        editor = QtWidgets.QCheckBox(parent)
        palette = QtGui.QPalette()
        palette.set_color(
            QtGui.QPalette.ColorRole.Text, option.palette.highlighted_text().color()
        )
        palette.set_color(
            QtGui.QPalette.ColorRole.Window, option.palette.highlighted_text().color()
        )
        editor.palette = palette
        return editor

    def update_editor_geometry(
        self,
        editor: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        """Move the editor to the middle."""
        editor.geometry = self.get_checkbox_rect(option)

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        """Pain the checkbox in the center."""
        check_box_style_option = QtWidgets.QStyleOptionButton()

        if index.data():  # checked
            check_box_style_option.state |= QtWidgets.QStyle.StateFlag.State_On
        else:
            check_box_style_option.state |= QtWidgets.QStyle.StateFlag.State_Off

        check_box_style_option.rect = self.get_checkbox_rect(option)
        if option.state & QtWidgets.QStyle.StateFlag.State_HasFocus:
            self.draw_focus_rect(painter, option)
            check_box_style_option.palette.set_color(
                QtGui.QPalette.ColorRole.Text, option.palette.highlighted_text().color()
            )

        elif (
            foreground_brush := index.data(QtCore.Qt.ItemDataRole.ForegroundRole)
        ) is not None:
            check_box_style_option.palette.set_color(
                QtGui.QPalette.ColorRole.Text, foreground_brush.color()
            )

        check_box_style_option.palette.set_color(
            QtGui.QPalette.ColorRole.Window, QtGui.QColor(100, 100, 0, 0)
        )
        check_box_style_option.palette.set_color(
            QtGui.QPalette.ColorRole.Base, QtGui.QColor(100, 100, 0, 0)
        )

        QtWidgets.QApplication.style().draw_control(
            QtWidgets.QStyle.ControlElement.CE_CheckBox, check_box_style_option, painter
        )

    def draw_focus_rect(
        self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem
    ) -> None:
        """Draw a rectangle over the table item indicating it is in focus."""
        focus_option = QtWidgets.QStyleOptionFocusRect()
        focus_option.state = option.state
        focus_option.rect = option.rect
        focus_option.state |= QtWidgets.QStyle.StateFlag.State_KeyboardFocusChange
        focus_option.state |= QtWidgets.QStyle.StateFlag.State_Item
        focus_option.palette = option.palette
        QtWidgets.QApplication.style().draw_primitive(
            QtWidgets.QStyle.PrimitiveElement.PE_FrameFocusRect,
            focus_option,
            painter,
            None,
        )

    def get_checkbox_rect(self, option: QtWidgets.QStyleOptionViewItem) -> QtCore.QRect:
        """Get the rect for a checkbox in the item's center."""
        check_box_style_option = QtWidgets.QStyleOptionButton()
        check_box_rect = QtWidgets.QApplication.style().sub_element_rect(
            QtWidgets.QStyle.SubElement.SE_CheckBoxIndicator,
            check_box_style_option,
            None,
        )
        check_box_point = QtCore.QPoint(
            option.rect.x() + option.rect.width() / 2 - check_box_rect.width() / 2,
            option.rect.y() + option.rect.height() / 2 - check_box_rect.height() / 2,
        )
        return QtCore.QRect(check_box_point, check_box_rect.size())
