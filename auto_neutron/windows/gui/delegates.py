# This file is part of Auto_Neutron. See the main.py file for more details.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class SpinBoxDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate for a table to use cells as `SpinBox`es."""

    def create_editor(  # noqa: D102
        self,
        parent: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> QtWidgets.QWidget:
        editor = QtWidgets.QSpinBox(parent)
        editor.setFrame(False)
        editor.setMinimum(1)
        editor.setMaximum(10_000)
        editor.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
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
        editor.setFrame(False)
        editor.setMinimum(0)
        editor.setMaximum(1_000_000)
        editor.setDecimals(2)
        editor.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
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
        palette.setColor(
            QtGui.QPalette.ColorRole.Text, option.palette().highlightedText().color()
        )
        palette.setColor(
            QtGui.QPalette.ColorRole.Window, option.palette().highlightedText().color()
        )
        editor.setPalette(palette)
        return editor

    def updateEditorGeometry(
        self,
        editor: QtWidgets.QWidget,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> None:
        """Move the editor to the middle."""
        editor.setGeometry(self.getCheckboxRect(option))

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

        check_box_style_option.rect = self.getCheckboxRect(option)
        if option.state & QtWidgets.QStyle.StateFlag.State_HasFocus:
            self.drawFocusRect(painter, option)
            check_box_style_option.palette.setColor(
                QtGui.QPalette.ColorRole.Text,
                option.palette().highlightedText().color(),
            )

        elif (
            foreground_brush := index.data(QtCore.Qt.ItemDataRole.ForegroundRole)
        ) is not None:
            check_box_style_option.palette.setColor(
                QtGui.QPalette.ColorRole.Text, foreground_brush.color()
            )

        check_box_style_option.palette.setColor(
            QtGui.QPalette.ColorRole.Window, QtGui.QColor(100, 100, 0, 0)
        )
        check_box_style_option.palette.setColor(
            QtGui.QPalette.ColorRole.Base, QtGui.QColor(100, 100, 0, 0)
        )

        QtWidgets.QApplication.style().drawControl(
            QtWidgets.QStyle.ControlElement.CE_CheckBox, check_box_style_option, painter
        )

    def drawFocusRect(
        self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem
    ) -> None:
        """Draw a rectangle over the table item indicating it is in focus."""
        focus_option = QtWidgets.QStyleOptionFocusRect()
        focus_option.state = option.state
        focus_option.rect = option.rect
        focus_option.state |= QtWidgets.QStyle.StateFlag.State_KeyboardFocusChange
        focus_option.state |= QtWidgets.QStyle.StateFlag.State_Item
        focus_option.setPalette(option.palette())
        QtWidgets.QApplication.style().drawPrimitive(
            QtWidgets.QStyle.PrimitiveElement.PE_FrameFocusRect,
            focus_option,
            painter,
            None,
        )

    def getCheckboxRect(self, option: QtWidgets.QStyleOptionViewItem) -> QtCore.QRect:
        """Get the rect for a checkbox in the item's center."""
        check_box_style_option = QtWidgets.QStyleOptionButton()
        check_box_rect = QtWidgets.QApplication.style().subElementRect(
            QtWidgets.QStyle.SubElement.SE_CheckBoxIndicator,
            check_box_style_option,
            None,
        )
        check_box_point = QtCore.QPoint(
            option.rect.x() + option.rect.width() / 2 - check_box_rect.width() / 2,
            option.rect.y() + option.rect.height() / 2 - check_box_rect.height() / 2,
        )
        return QtCore.QRect(check_box_point, check_box_rect.size())
