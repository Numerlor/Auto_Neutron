# This file is part of Auto_Neutron.
# Copyright (C) 2019  Numerlor

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets
from __feature__ import snake_case, true_property  # noqa: F401


class PlainTextScroller(QtWidgets.QWidget):
    """
    A plain text display widget, which scrolls horizontally on hover if the entire text cannot fit into its size.

    The `fade_width` argument can be used to control the width of the fade-in and fade-out gradients.
    `scroll_step` defines how much the text moves for each scroll interval.
    `scroll_interval` controls the scroll interval, in ms.

    The widget's palette's Window color role is used as the color for the fade-out gradients.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        *,
        text: str = "",
        fade_width: int = 30,
        scroll_step: float = 1 / 4,
        scroll_interval: int = 4,
    ):
        super().__init__(parent)
        self._fade_width = fade_width
        self._scroll_pos = 0
        self.scroll_step = scroll_step
        self._scroll_interval = scroll_interval

        self._static_text = QtGui.QStaticText(text)
        self._static_text.set_text_format(QtCore.Qt.PlainText)

        self._fade_in_image, self._fade_out_image = self._create_fade_images()

        self._scroll_timer = QtCore.QTimer(self)
        self._scroll_timer.interval = scroll_interval
        self._scroll_timer.timer_type = QtCore.Qt.TimerType.PreciseTimer
        self._scroll_timer.timeout.connect(self._reposition)

        self._reset_timer = QtCore.QTimer(self)
        self._reset_timer.interval = 2000
        self._reset_timer.single_shot_ = True
        self._reset_timer.timeout.connect(self._reset_pos)

        self._delay_scroll_start_timer = QtCore.QTimer(self)
        self._delay_scroll_start_timer.interval = 750
        self._delay_scroll_start_timer.single_shot_ = True
        self._delay_scroll_start_timer.timeout.connect(self._scroll_timer.start)

    @property
    def text(self) -> str:
        """Return the widget's text."""
        return self._static_text.text()

    @text.setter
    def text(self, text: str) -> None:
        """Set widget's text to `text`."""
        self._static_text.set_text(text)
        self.update_geometry()
        self.update()

    @property
    def font(self) -> QtGui.QFont:
        """Return the widget's font."""
        return super().font()

    @font.setter
    def font(self, font: QtGui.QFont) -> None:
        """Set the widget's font."""
        super(self.__class__, self.__class__).font.__set__(self, font)
        self._fade_in_image, self._fade_out_image = self._create_fade_images()

    @property
    def fade_width(self) -> int:
        """Return the fade rect width."""
        return self._fade_width

    @fade_width.setter
    def fade_width(self, width: int) -> None:
        """Set the fade rect width to `width`."""
        self._fade_width = width
        self._fade_in_image, self._fade_out_image = self._create_fade_images()

    @property
    def scroll_interval(self) -> int:
        """Return the current scroll interval."""
        return self._scroll_interval

    @scroll_interval.setter
    def scroll_interval(self, interval: int) -> None:
        """Set a new scroll interval."""
        self._scroll_timer.interval = interval
        self._scroll_interval = interval

    @property
    def size_hint(self) -> QtCore.QSize:
        """
        Return the size hint.

        Equal to the text's size.
        """
        return self._text_size

    @property
    def minimum_size_hint(self) -> QtCore.QSize:
        """
        Return the minimum size hint.

        Height is equal to the text's, width is the text's width with a minimum of 40.
        """
        text_size = self._text_size
        return QtCore.QSize(max(40, text_size.width()), text_size.height())

    def enter_event(self, event: QtGui.QEnterEvent) -> None:
        """Start scrolling if text doesn't fit on entry."""
        super().enter_event(event)
        if self._text_size.width() > self.size.width():
            self._delay_scroll_start_timer.interval = 500
            self._delay_scroll_start_timer.start()

    def leave_event(self, event: QtCore.QEvent) -> None:
        """Cancel any scrolling on leave."""
        super().leave_event(event)
        self._scroll_pos = 0
        self._scroll_timer.stop()
        self._reset_timer.stop()
        self._delay_scroll_start_timer.stop()
        self.update()

    def _reposition(self) -> None:
        """
        Move the text and redraw.

        If the text is not at the end, move the text to the left, otherwise stop moving and start the reset timer.
        """
        if self._text_size.width() - self._scroll_pos < self.width:
            # Reached end of text.
            self._scroll_timer.stop()
            self._reset_timer.start()
        else:
            self._scroll_pos += self.scroll_step
        self.update()

    def _reset_pos(self) -> None:
        """Reset the text to its initial position, and start the scroll timer which will start scrolling in 750ms."""
        self._scroll_pos = 0
        self.update()
        self._delay_scroll_start_timer.interval = 750
        self._delay_scroll_start_timer.start()

    def paint_event(self, paint_event: QtGui.QPaintEvent) -> None:
        """Paint the text at its current scroll position with the fade-out gradients on both sides."""
        text_y = (self.height - self._text_size.height()) // 2

        painter = QtGui.QPainter(self)

        painter.set_clip_rect(
            QtCore.QRect(
                QtCore.QPoint(0, text_y),
                self._text_size,
            )
        )

        painter.draw_static_text(
            QtCore.QPointF(-self._scroll_pos, text_y),
            self._static_text,
        )
        # Show more transparent half of gradient immediately to prevent text from appearing cut-off.
        if self._scroll_pos == 0:
            fade_in_width = 0
        else:
            fade_in_width = min(
                self._scroll_pos + self.fade_width // 2, self.fade_width
            )

        painter.draw_image(
            -self.fade_width + fade_in_width,
            text_y,
            self._fade_in_image,
        )

        fade_out_width = self._text_size.width() - self.width - self._scroll_pos
        if fade_out_width > 0:
            fade_out_width = min(self.fade_width, fade_out_width + self.fade_width // 2)

        painter.draw_image(
            self.width - fade_out_width,
            text_y,
            self._fade_out_image,
        )

    def _create_fade_images(self) -> tuple[QtGui.QImage, QtGui.QImage]:
        """Return a fade-in image and a fade-out image of `self.fade_width` width."""
        fade_in_image = QtGui.QImage(
            self.fade_width,
            self._text_size.height(),
            QtGui.QImage.Format_ARGB32_Premultiplied,
        )
        if fade_in_image.is_null():
            raise MemoryError("Unable to allocate QImage.")
        fade_out_image = QtGui.QImage(
            self.fade_width,
            self._text_size.height(),
            QtGui.QImage.Format_ARGB32_Premultiplied,
        )
        if fade_out_image.is_null():
            raise MemoryError("Unable to allocate QImage.")

        # FIXME: use actual transparency instead of using the background color
        background_color = self.palette.window().color().get_rgb()[:-1]
        opaque_color = QtGui.QColor(*background_color, 255)

        fade_in_image.fill(QtCore.Qt.transparent)
        fade_out_image.fill(QtCore.Qt.transparent)

        gradient = QtGui.QLinearGradient(
            QtCore.QPointF(0, 0), QtCore.QPointF(self.fade_width, 0)
        )

        painter = QtGui.QPainter(fade_in_image)
        painter.set_pen(QtCore.Qt.NoPen)

        gradient.set_color_at(0, opaque_color)
        gradient.set_color_at(1, QtCore.Qt.transparent)

        painter.fill_rect(fade_in_image.rect(), gradient)
        painter.end()

        painter.begin(fade_out_image)
        painter.set_pen(QtCore.Qt.NoPen)

        gradient.set_color_at(0, QtCore.Qt.transparent)
        gradient.set_color_at(1, opaque_color)

        painter.fill_rect(fade_out_image.rect(), gradient)

        return fade_in_image, fade_out_image

    def change_event(self, event: QtCore.QEvent) -> None:
        """Update the fade images if the palette changed."""
        if event.type() == QtCore.QEvent.PaletteChange:
            self._fade_in_image, self._fade_out_image = self._create_fade_images()
        super().change_event(event)

    @property
    def _text_size(self) -> QtCore.QSize:
        return QtCore.QSize(
            self.font_metrics().horizontal_advance(self.text),
            self.font_metrics().height(),
        )
