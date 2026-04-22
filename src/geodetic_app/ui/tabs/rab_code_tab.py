from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


@dataclass(slots=True)
class RabStripe:
    n: int
    typ: str
    os_mm: float
    width_mm: float
    width_label: str

class RabCodePreview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._stripes: list[RabStripe] = []
        self._start_mm = 0.0
        self._view_mm = 300.0
        self._zoom = 1.0  # Каэфіцыент прыбліжэння
        self._base_px_per_mm = 2.0  # Базавая шчыльнасць (пікселяў на мм)
        
        self.setMinimumWidth(180)
        self.update_geometry()

    def update_geometry(self):
        # Вылічваем патрэбную вышыню і шырыню аджэта з улікам зуму
        new_height = int(self._view_mm * self._base_px_per_mm * self._zoom)
        new_width = int(400 * self._zoom) # Шырыня таксама можа расці
        self.setMinimumSize(new_width, new_height)
        self.update()

    def set_data(self, stripes: list[RabStripe], start_mm: float, view_mm: float) -> None:
        self._stripes = stripes
        self._start_mm = max(0.0, start_mm)
        self._view_mm = max(50.0, view_mm)
        self.update_geometry()

    def wheelEvent(self, event):  # noqa: N802
        # Прыбліжэнне праз Ctrl + кола мышы
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom = min(self._zoom + 0.2, 5.0) # Макс 5x
            else:
                self._zoom = max(self._zoom - 0.2, 0.5) # Мін 0.5x
            self.update_geometry()
            event.accept()
        else:
            super().wheelEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Агульная вобласць малявання (займае ўвесь аджэт)
        canvas = self.rect()
        painter.fillRect(canvas, QColor("#f1f1f1"))

        # Вызначаем прапорцыі: лата злева, памеры справа
        # Мы пакідаем 100 пікселяў справа пад надпісы (памнажаем на зум)
        right_margin = int(100 * self._zoom)
        strip_rect = canvas.adjusted(20, 10, -right_margin, -10)
        
        # Цела латы
        painter.fillRect(strip_rect, QColor("#d8c631"))
        painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawRect(strip_rect)

        if not self._stripes:
            return

        # Маштаб цяпер залежыць ад фізічнага памеру аджэта
        scale = strip_rect.height() / self._view_mm
        end_mm = self._start_mm + self._view_mm

        # 1. Малюем рыскі
        for stripe in self._stripes:
            y_top_mm = stripe.os_mm
            y_bottom_mm = stripe.os_mm + stripe.width_mm
            
            if y_bottom_mm < self._start_mm or y_top_mm > end_mm:
                continue

            y1 = strip_rect.top() + int((y_top_mm - self._start_mm) * scale)
            y2 = strip_rect.top() + int((y_bottom_mm - self._start_mm) * scale)
            h = max(1, y2 - y1)
            
            color = QColor("#000000")
            painter.fillRect(strip_rect.left() + 1, y1, strip_rect.width() - 2, h, color)

        # 2. Малюем шкалу (вось яна была праблемай)
        painter.setPen(QPen(QColor("#6a6a6a"), 1))
        # Лінія шкалы
        line_x = strip_rect.right() + 5
        painter.drawLine(line_x, strip_rect.top(), line_x, strip_rect.bottom())

        # Шрыфт таксама павінен трохі расці пры зуме
        font = painter.font()
        font.setPointSize(max(8, int(10 * self._zoom)))
        painter.setFont(font)

        painter.setPen(QColor("#4b4b8d"))
        step = 10
        first_tick = int(self._start_mm // step) * step
        for mm in range(first_tick, int(end_mm) + step, step):
            y = strip_rect.top() + int((mm - self._start_mm) * scale)
            if y < strip_rect.top() or y > strip_rect.bottom():
                continue
            
            painter.drawLine(line_x, y, line_x + int(8 * self._zoom), y)
            label = str(mm)
            # Малюем тэкст так, каб ён заўсёды быў бачны
            painter.drawText(line_x + int(12 * self._zoom), y + int(4 * self._zoom), label)

# class RabCodePreview(QWidget):
#     def __init__(self) -> None:
#         super().__init__()
#         self._stripes: list[RabStripe] = []
#         self._start_mm = 0.0
#         self._view_mm = 300.0
#         self.setMinimumWidth(260)
#         self.setMinimumHeight(680)

#     def set_data(self, stripes: list[RabStripe], start_mm: float, view_mm: float) -> None:
#         self._stripes = stripes
#         self._start_mm = max(0.0, start_mm)
#         self._view_mm = max(50.0, view_mm)
#         self.update()

#     def paintEvent(self, event) -> None:  # noqa: N802
#         super().paintEvent(event)
#         painter = QPainter(self)
#         painter.setRenderHint(QPainter.Antialiasing, True)

#         # 1. Малюем агульнае палатно
#         canvas = self.rect().adjusted(10, 10, -10, -10)
#         painter.fillRect(canvas, QColor("#f1f1f1"))

#         # 2. Малюем цела латы (жоўтая аснова)
#         strip_rect = canvas.adjusted(20, 10, -110, -10)
#         painter.fillRect(strip_rect, QColor("#d8c631"))
#         painter.setPen(QPen(QColor("#555555"), 1))
#         painter.drawRect(strip_rect)

#         if not self._stripes:
#             painter.setPen(QColor("#333333"))
#             painter.drawText(canvas, Qt.AlignCenter, "Brak danych. Kliknij Generuj.")
#             return

#         # 3. Настройка маштабу
#         scale = strip_rect.height() / self._view_mm
#         end_mm = self._start_mm + self._view_mm

#         # 4. МАЛЯВАННЕ РЫСАК (Тут галоўныя змены)
#         for stripe in self._stripes:
#             y_top_mm = stripe.os_mm
#             y_bottom_mm = stripe.os_mm + stripe.width_mm
            
#             # Праверка, ці трапляе рыска ў зону бачнасці
#             if y_bottom_mm < self._start_mm or y_top_mm > end_mm:
#                 continue

#             # Пералік міліметраў у пікселі
#             y1 = strip_rect.top() + int((y_top_mm - self._start_mm) * scale)
#             y2 = strip_rect.top() + int((y_bottom_mm - self._start_mm) * scale)
#             h = max(1, y2 - y1)
            
#             # Выбар колеру ў залежнасці ад тыпу (для нагляднасці)
#             if stripe.typ == "R":
#                 color = QColor("#000000") # Рэферэнтныя — самыя чорныя
#             else:
#                 color = QColor("#2f2f2f") # Астатнія — цёмна-шэрыя
                
#             painter.fillRect(strip_rect.left() + 1, y1, strip_rect.width() - 2, h, color)

#         # 5. МАЛЯВАННЕ ШКАЛЫ (Твой арыгінальны код, ён добры)
#         painter.setPen(QPen(QColor("#6a6a6a"), 1))
#         painter.drawLine(strip_rect.right() + 8, strip_rect.top(), strip_rect.right() + 8, strip_rect.bottom())

#         painter.setPen(QColor("#4b4b8d"))
#         step = 10
#         first_tick = int(self._start_mm // step) * step
#         for mm in range(first_tick, int(end_mm) + step, step):
#             y = strip_rect.top() + int((mm - self._start_mm) * scale)
#             if y < strip_rect.top() or y > strip_rect.bottom():
#                 continue
#             painter.drawLine(strip_rect.right() + 8, y, strip_rect.right() + 16, y)
#             label = str(mm)
#             painter.drawText(strip_rect.right() + 20, y + 4, label)


class RabCodeTab(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.start_input = QLineEdit("0")
        self.view_input = QLineEdit("300")
        self.generate_button = QPushButton("Generuj")

        self.preview = RabCodePreview()
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setWidget(self.preview)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["n", "Typ", "Os [mm]", "Szerokość [mm]"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(8)
        form.addRow("Wysokość start (mm):", self.start_input)
        form.addRow("Długość widoku (mm):", self.view_input)

        top_controls = QHBoxLayout()
        top_controls.addLayout(form)
        top_controls.addWidget(self.generate_button)
        top_controls.addStretch()

        left_layout = QVBoxLayout()
        left_layout.addLayout(top_controls)
        left_layout.addWidget(self.preview_scroll)

        left_panel = QWidget()
        left_panel.setLayout(left_layout)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Tabela Parametrów"))
        right_layout.addWidget(self.table)

        right_panel = QWidget()
        right_panel.setLayout(right_layout)
        right_panel.setMinimumWidth(320)
        right_panel.setMaximumWidth(360)

        content_layout = QHBoxLayout(self)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(12)
        content_layout.addWidget(left_panel, 1)
        content_layout.addWidget(right_panel)

        self.generate_button.clicked.connect(self.generate)
        self.generate()

    def generate(self) -> None:
        start_mm = self._parse_positive_float(self.start_input.text(), default=0.0)
        view_mm = self._parse_positive_float(self.view_input.text(), default=300.0)
        stripes = self._build_stripes(start_mm, view_mm)
        self._populate_table(stripes)
        self.preview.set_data(stripes, start_mm, view_mm)

    def _build_stripes(self, start_mm: float, view_mm: float) -> list[RabStripe]:
        stripes: list[RabStripe] = []
        end_mm = start_mm + view_mm + 120

        i = 0
        os_mm = 0.0
        while os_mm <= end_mm:
            stripes.append(RabStripe(n=i, typ="R", os_mm=os_mm, width_mm=8.0, width_label="Wzór 8mm"))

            width_a = self._width_a_mm(i)
            stripes.append(RabStripe(n=i, typ="A", os_mm=os_mm + 10.0, width_mm=width_a, width_label=f"{width_a:.3f}"))

            width_b = self._width_b_mm(i)
            stripes.append(RabStripe(n=i, typ="B", os_mm=os_mm + 20.0, width_mm=width_b, width_label=f"{width_b:.3f}"))

            i += 1
            os_mm += 30.0

        return stripes

    def _populate_table(self, stripes: list[RabStripe]) -> None:
        self.table.setRowCount(len(stripes))
        for row, stripe in enumerate(stripes):
            values = [
                str(stripe.n),
                stripe.typ,
                f"{stripe.os_mm:.1f}",
                stripe.width_label,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()

    def _width_a_mm(self, n: int) -> float:
        angle = 2.0 * pi * ((30.0 * n + 21.25) / 330.0)
        return round(5.0 + 4.0 * cos(angle), 3)

    def _width_b_mm(self, n: int) -> float:
        angle = 2.0 * pi * ((30.0 * n + 35.0) / 300.0)
        return round(5.0 + 4.0 * cos(angle), 3)

    @staticmethod
    def _parse_positive_float(text: str, default: float) -> float:
        normalized = text.replace(",", ".").strip()
        if not normalized:
            return default
        try:
            value = float(normalized)
        except ValueError:
            return default
        return max(0.0, value)
