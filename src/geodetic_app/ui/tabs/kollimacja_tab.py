from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QVBoxLayout,
    QWidget,
)

from geodetic_app.models.app_state import AppState
from geodetic_app.ui.tabs._shared import format_comma_decimal, parse_two_column_measurements


class KollimacjaTab(QWidget):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self.data_frame: pd.DataFrame | None = None

        self.file_label = QLabel("Nie wybrano pliku")
        self.load_button = QPushButton("Wczytaj plik tekstowy")
        self.load_button.clicked.connect(self.load_file)

        self.results_label = QLabel("Ilość pomiarów: —")
        self.avg_collimation_label = QLabel("Kolimacja średnia: — cc")
        self.collimation_error_label = QLabel("Błąd kolimacji: — cc")

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Odczyt I", "Odczyt II", "d [cc]", "v [cc]", "vv [cc^2]"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.horiz_circle_input = QDoubleSpinBox()
        self.horiz_circle_input.setRange(0.0, 400.0)
        self.horiz_circle_input.setDecimals(4)
        self.horiz_circle_input.setValue(0.0)
        self.horiz_circle_input.valueChanged.connect(self._recompute_correction_if_ready)

        self.compute_correction_button = QPushButton("Oblicz poprawiony odczyt")
        self.compute_correction_button.clicked.connect(self.compute_correction)

        self.corrected_horiz_label = QLabel("Poprawiony kąt poziomy: — grad")
        self.correction_error_label = QLabel("Użyta poprawka: — ± — grad")
        self.corrected_range_label = QLabel("Zakres poprawionego kąta poziomego: — grad")

        correction_box = QGroupBox("Korekta odczytu")
        correction_layout = QVBoxLayout(correction_box)
        correction_layout.setContentsMargins(12, 12, 12, 12)
        correction_layout.setSpacing(10)

        form_layout = QFormLayout()
        form_layout.addRow("Kąt poziomy (grad):", self.horiz_circle_input)
        correction_layout.addLayout(form_layout)
        correction_layout.addWidget(self.compute_correction_button)
        correction_layout.addWidget(self.corrected_horiz_label)
        correction_layout.addWidget(self.correction_error_label)
        correction_layout.addWidget(self.corrected_range_label)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        main_layout.addWidget(self.file_label)
        main_layout.addWidget(self.load_button)
        main_layout.addWidget(self.avg_collimation_label)
        main_layout.addWidget(self.collimation_error_label)
        main_layout.addWidget(self.results_label)
        main_layout.addWidget(self.table)
        main_layout.addWidget(correction_box)
        main_layout.addStretch()

    def load_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load measurements", "", "Text files (*.txt *.csv);;All files (*)"
        )
        if not file_path:
            return

        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        self.file_label.setText(f"File: {file_path}")

        self.data_frame = parse_two_column_measurements(content)
        if self.data_frame.empty:
            self.results_label.setText("Wynik: brak poprawnych danych w pliku")
            self.state.results = None
            return

        self._calculate_collimation()

    def _calculate_collimation(self) -> None:
        if self.data_frame is None or len(self.data_frame) == 0:
            return

        odczyt_i = self.data_frame["Odczyt I"]
        odczyt_ii = self.data_frame["Odczyt II"]
        differences_grad = pd.Series(index=self.data_frame.index, dtype=float)

        mask_i_over_200 = odczyt_i > 200.0
        mask_ii_over_200 = odczyt_ii > 200.0
        mask_normal = ~mask_i_over_200 & ~mask_ii_over_200

        differences_grad.loc[mask_normal] = (odczyt_ii[mask_normal] - odczyt_i[mask_normal]) / 2.0
        differences_grad.loc[mask_ii_over_200 & ~mask_i_over_200] = (
            odczyt_ii[mask_ii_over_200 & ~mask_i_over_200] - (odczyt_i[mask_ii_over_200 & ~mask_i_over_200] + 200.0)
        ) / 2.0
        differences_grad.loc[mask_i_over_200 & ~mask_ii_over_200] = (
            (odczyt_ii[mask_i_over_200 & ~mask_ii_over_200] + 200.0) - odczyt_i[mask_i_over_200 & ~mask_ii_over_200]
        ) / 2.0
        differences_grad.loc[mask_i_over_200 & mask_ii_over_200] = (
            odczyt_ii[mask_i_over_200 & mask_ii_over_200] - odczyt_i[mask_i_over_200 & mask_ii_over_200]
        ) / 2.0

        differences_cc = differences_grad * 10000.0
        n = len(differences_cc)
        avg_collimation_cc = float(differences_cc.sum() / n)

        if n > 1:
            residuals_cc = differences_cc - avg_collimation_cc
            vv_cc2 = residuals_cc**2
            vv_sum = float((residuals_cc**2).sum())
            collimation_error = math.sqrt(vv_sum / (n * (n - 1)))
        else:
            residuals_cc = pd.Series([0.0] * n, index=self.data_frame.index, dtype=float)
            vv_cc2 = pd.Series([0.0] * n, index=self.data_frame.index, dtype=float)
            collimation_error = 0.0

        self.table.setRowCount(len(self.data_frame))
        for row_idx, row_data in self.data_frame.iterrows():
            self.table.setItem(row_idx, 0, QTableWidgetItem(format_comma_decimal(row_data["Odczyt I"], 4)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(format_comma_decimal(row_data["Odczyt II"], 4)))
            self.table.setItem(row_idx, 2, QTableWidgetItem(format_comma_decimal(differences_cc.iloc[row_idx], 2)))
            self.table.setItem(row_idx, 3, QTableWidgetItem(format_comma_decimal(residuals_cc.iloc[row_idx], 2)))
            self.table.setItem(row_idx, 4, QTableWidgetItem(format_comma_decimal(vv_cc2.iloc[row_idx], 2)))

        self.avg_collimation_label.setText(f"Kolimacja średnia: {avg_collimation_cc:.2f} cc")
        self.collimation_error_label.setText(f"Błąd kolimacji: {collimation_error:.2f} cc")
        self.results_label.setText(f"Ilość pomiarów: {len(self.data_frame)}")

        result_frame = self.data_frame.copy()
        result_frame["d_cc"] = differences_cc
        result_frame["v_cc"] = residuals_cc
        result_frame["vv_cc2"] = vv_cc2
        self.state.results = result_frame
        self._avg_collimation_cc = avg_collimation_cc
        self._collimation_error_cc = collimation_error
        self.compute_correction()

    def _recompute_correction_if_ready(self) -> None:
        if hasattr(self, "_avg_collimation_cc"):
            self.compute_correction()

    def compute_correction(self) -> None:
        if self.data_frame is None or not hasattr(self, "_avg_collimation_cc"):
            self.corrected_horiz_label.setText("poprawiony odczyt koła poziomego: brak danych do obliczeń")
            self.correction_error_label.setText("użyta poprawka: brak danych")
            self.corrected_range_label.setText("zakres poprawionego odczytu: brak danych")
            return

        horiz_reading = self.horiz_circle_input.value()
        correction_grad = self._avg_collimation_cc / 10000.0
        error_grad = getattr(self, "_collimation_error_cc", 0.0) / 10000.0
        corrected_horiz = horiz_reading - correction_grad
        corrected_min = corrected_horiz - error_grad
        corrected_max = corrected_horiz + error_grad

        self.corrected_horiz_label.setText(f"Poprawiony odczyt koła poziomego: {corrected_horiz:.5f} grad")
        self.correction_error_label.setText(f"użyta poprawka: {correction_grad:.5f} ± {error_grad:.5f} grad")
        self.corrected_range_label.setText(
            f"zakres poprawionego odczytu: {corrected_min:.5f} ... {corrected_max:.5f} grad"
        )
