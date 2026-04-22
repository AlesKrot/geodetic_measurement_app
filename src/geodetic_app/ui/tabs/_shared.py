from __future__ import annotations

import math
import re

import pandas as pd
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


def parse_two_column_measurements(content: str) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith(("odczyt", "Odczyt", "#")):
            continue
        line = line.replace(",", ".")
        parts = line.split()
        if len(parts) >= 2:
            try:
                val1 = float(parts[0])
                val2 = float(parts[1])
                rows.append({"Odczyt I": val1, "Odczyt II": val2})
            except ValueError:
                continue

    return pd.DataFrame(rows)


def format_comma_decimal(value: float, decimals: int = 4) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


class LinePlotWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._points: list[QPointF] = []
        self._title = ""
        self.setMinimumHeight(260)

    def set_series(self, x_values: list[float], y_values: list[float], title: str) -> None:
        self._points = [QPointF(x, y) for x, y in zip(x_values, y_values)]
        self._title = title
        self.update()

    def paintEvent(self, _) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        if not self._points:
            painter.setPen(QPen(QColor("#555555"), 1))
            painter.drawText(self.rect(), Qt.AlignCenter, "No data to plot")
            return

        margin_left = 52
        margin_right = 20
        margin_top = 34
        margin_bottom = 34

        plot_w = max(1, self.width() - margin_left - margin_right)
        plot_h = max(1, self.height() - margin_top - margin_bottom)

        x_values = [point.x() for point in self._points]
        y_values = [point.y() for point in self._points]
        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)

        if math.isclose(min_x, max_x):
            max_x = min_x + 1.0
        if math.isclose(min_y, max_y):
            max_y = min_y + 1.0

        painter.setPen(QPen(QColor("#cccccc"), 1))
        for idx in range(6):
            y = margin_top + int(plot_h * idx / 5)
            painter.drawLine(margin_left, y, margin_left + plot_w, y)

        painter.setPen(QPen(QColor("#111111"), 1.5))
        painter.drawLine(margin_left, margin_top + plot_h, margin_left + plot_w, margin_top + plot_h)
        painter.drawLine(margin_left, margin_top, margin_left, margin_top + plot_h)

        painter.setPen(QPen(QColor("#0a7e8c"), 2.0))
        last = None
        for point in self._points:
            px = margin_left + ((point.x() - min_x) / (max_x - min_x)) * plot_w
            py = margin_top + (1.0 - (point.y() - min_y) / (max_y - min_y)) * plot_h
            if last is not None:
                painter.drawLine(last, QPointF(px, py))
            last = QPointF(px, py)

        painter.setPen(QPen(QColor("#111111"), 1))
        painter.drawText(8, 18, self._title)
        painter.drawText(margin_left, self.height() - 8, f"{min_x:.0f}")
        painter.drawText(self.width() - margin_right - 30, self.height() - 8, f"{max_x:.0f}")
        painter.drawText(8, margin_top + 8, f"{max_y:.2f}")
        painter.drawText(8, margin_top + plot_h, f"{min_y:.2f}")
