from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from geodetic_app.models.app_state import AppState
from geodetic_app.ui.tabs._shared import format_comma_decimal, parse_two_column_measurements


class InklinacjaTab(QWidget):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self.data_frame: pd.DataFrame | None = None
        self._avg_inclination_cc: float | None = None
        self._inclination_error_cc: float | None = None

        self.file_label = QLabel("Nie wybrano pliku")
        self.load_button = QPushButton("Wczytaj plik tekstowy")
        self.load_button.clicked.connect(self.load_file)

        self.results_label = QLabel("Ilość pomiarów: —")
        self.avg_inclination_label = QLabel("Inklinacja średnia: — cc")
        self.inclination_error_label = QLabel("Błąd inklinacji: — cc")
        self.avg_reading_label = QLabel("Średnia odcz: — cc")
        self.observation_error_label = QLabel("m odcz: — cc")

        self.c_value_input = QDoubleSpinBox()
        self.c_value_input.setRange(-1000.0, 1000.0)
        self.c_value_input.setDecimals(4)
        self.c_value_input.setValue(0.0)

        self.mc_value_input = QDoubleSpinBox()
        self.mc_value_input.setRange(0.0, 1000.0)
        self.mc_value_input.setDecimals(4)
        self.mc_value_input.setValue(0.0)

        self.z_value_input = QDoubleSpinBox()
        self.z_value_input.setRange(0.0, 399.9999)
        self.z_value_input.setDecimals(4)
        self.z_value_input.setValue(0.0)

        self.c_value_input.valueChanged.connect(self._recalculate_if_ready)
        self.mc_value_input.valueChanged.connect(self._recalculate_if_ready)
        self.z_value_input.valueChanged.connect(self._recalculate_if_ready)

        params_box = QGroupBox("Parametry")
        params_layout = QFormLayout(params_box)
        params_layout.setContentsMargins(12, 12, 12, 12)
        params_layout.setSpacing(8)
        params_layout.addRow("c [cc]", self.c_value_input)
        params_layout.addRow("mc [cc]", self.mc_value_input)
        params_layout.addRow("z [grad]", self.z_value_input)

        self.horiz_angle_input = QDoubleSpinBox()
        self.horiz_angle_input.setRange(0.0, 400.0)
        self.horiz_angle_input.setDecimals(4)
        self.horiz_angle_input.setValue(0.0)
        self.horiz_angle_input.valueChanged.connect(self._recompute_corrections_if_ready)

        self.vert_angle_input = QDoubleSpinBox()
        self.vert_angle_input.setRange(0.0, 400.0)
        self.vert_angle_input.setDecimals(4)
        self.vert_angle_input.setValue(100.0)
        self.vert_angle_input.valueChanged.connect(self._recompute_corrections_if_ready)

        self.compute_correction_button = QPushButton("Oblicz poprawione kąty")
        self.compute_correction_button.clicked.connect(self.compute_corrections)

        self.corrected_horiz_label = QLabel("Poprawiony kąt poziomy: — grad")
        self.corrected_horiz_error_label = QLabel("Poprawka pozioma: — ± — grad")
        self.corrected_vert_label = QLabel("Poprawiony kąt pionowy: — grad")
        self.corrected_vert_error_label = QLabel("Poprawka pionowa: — ± — grad")

        correction_box = QGroupBox("Korekta kątów")
        correction_layout = QVBoxLayout(correction_box)
        correction_layout.setContentsMargins(12, 12, 12, 12)
        correction_layout.setSpacing(10)

        correction_form = QFormLayout()
        correction_form.addRow("Kąt poziomy [grad]", self.horiz_angle_input)
        correction_form.addRow("Kąt pionowy [grad]", self.vert_angle_input)

        correction_layout.addLayout(correction_form)
        correction_layout.addWidget(self.compute_correction_button)
        correction_layout.addWidget(self.corrected_horiz_label)
        correction_layout.addWidget(self.corrected_horiz_error_label)
        correction_layout.addWidget(self.corrected_vert_label)
        correction_layout.addWidget(self.corrected_vert_error_label)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Odczyt I", "Odczyt II", "d [cc]", "v [cc]", "vv [cc^2]"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        main_layout.addWidget(self.file_label)
        main_layout.addWidget(self.load_button)
        main_layout.addWidget(params_box)
        main_layout.addWidget(self.avg_inclination_label)
        main_layout.addWidget(self.inclination_error_label)
        main_layout.addWidget(self.avg_reading_label)
        main_layout.addWidget(self.observation_error_label)
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

        self._calculate_inclination()

    def _recalculate_if_ready(self) -> None:
        if self.data_frame is not None and not self.data_frame.empty:
            self._calculate_inclination()

    def _recompute_corrections_if_ready(self) -> None:
        if self._avg_inclination_cc is not None and self._inclination_error_cc is not None:
            self.compute_corrections()

    def _calculate_inclination(self) -> None:
        if self.data_frame is None or len(self.data_frame) == 0:
            return

        odczyt_i = self.data_frame["Odczyt I"]
        odczyt_ii = self.data_frame["Odczyt II"]

        d_cc_values: list[float] = []

        for h_i, h_ii in zip(odczyt_i.tolist(), odczyt_ii.tolist()):
            delta = h_ii - h_i
            if delta < 0.0:
                delta += 400.0
            d_cc_values.append(((delta - 200.0) / 2.0) * 10000.0)

        d_cc_series = pd.Series(d_cc_values, index=self.data_frame.index, dtype=float)
        n = len(d_cc_series)
        avg_d_cc = float(d_cc_series.sum() / n)

        if n > 1:
            residuals_cc = d_cc_series - avg_d_cc
            vv_cc2 = residuals_cc**2
            vv_sum = float((residuals_cc**2).sum())
            observation_error_cc = math.sqrt(vv_sum / (n * (n - 1)))
        else:
            residuals_cc = pd.Series([0.0] * n, index=self.data_frame.index, dtype=float)
            vv_cc2 = pd.Series([0.0] * n, index=self.data_frame.index, dtype=float)
            observation_error_cc = 0.0

        c_value_cc = self.c_value_input.value()
        mc_value_cc = self.mc_value_input.value()
        z_value_grad = self.z_value_input.value()

        z_rad = z_value_grad * math.pi / 200.0
        tan_z = math.tan(z_rad)
        cos_z = math.cos(z_rad)
        if math.isclose(cos_z, 0.0):
            self._avg_inclination_cc = None
            self._inclination_error_cc = None
            self.results_label.setText("Wynik: błąd obliczeń dla podanego z")
            return

        avg_inclination_cc = avg_d_cc * tan_z - (c_value_cc / cos_z)
        inclination_error_cc = math.sqrt(
            (tan_z**2) * (observation_error_cc**2) + ((1.0 / (cos_z**2)) * (mc_value_cc**2))
        )

        self.table.setRowCount(len(self.data_frame))
        for row_idx, row_data in self.data_frame.iterrows():
            self.table.setItem(row_idx, 0, QTableWidgetItem(format_comma_decimal(row_data["Odczyt I"], 4)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(format_comma_decimal(row_data["Odczyt II"], 4)))
            self.table.setItem(row_idx, 2, QTableWidgetItem(format_comma_decimal(d_cc_series.iloc[row_idx], 2)))
            self.table.setItem(row_idx, 3, QTableWidgetItem(format_comma_decimal(residuals_cc.iloc[row_idx], 2)))
            self.table.setItem(row_idx, 4, QTableWidgetItem(format_comma_decimal(vv_cc2.iloc[row_idx], 2)))

        self.avg_reading_label.setText(f"Średnia odcz: {avg_d_cc:.2f} cc")
        self.observation_error_label.setText(f"Błąd odczytu to: {observation_error_cc:.2f} cc")
        self.avg_inclination_label.setText(f"Inklinacja średnia: {avg_inclination_cc:.2f} cc")
        self.inclination_error_label.setText(f"Błąd inklinacji: {inclination_error_cc:.2f} cc")
        self.results_label.setText(f"Ilość pomiarów: {len(self.data_frame)}")

        self._avg_inclination_cc = avg_inclination_cc
        self._inclination_error_cc = inclination_error_cc
        self.compute_corrections()

        result_frame = self.data_frame.copy()
        result_frame["d_cc"] = d_cc_series
        result_frame["v_cc"] = residuals_cc
        result_frame["vv_cc2"] = vv_cc2
        result_frame["c_cc"] = c_value_cc
        result_frame["mc_cc"] = mc_value_cc
        result_frame["z_grad"] = z_value_grad
        result_frame["avg_inclination_cc"] = avg_inclination_cc
        result_frame["inclination_error_cc"] = inclination_error_cc
        self.state.results = result_frame

    def compute_corrections(self) -> None:
        if self._avg_inclination_cc is None or self._inclination_error_cc is None:
            self.corrected_horiz_label.setText("Poprawiony kąt poziomy: brak danych do obliczeń")
            self.corrected_horiz_error_label.setText("Poprawka pozioma: brak danych")
            self.corrected_vert_label.setText("Poprawiony kąt pionowy: brak danych do obliczeń")
            self.corrected_vert_error_label.setText("Poprawka pionowa: brak danych")
            return

        c_value_cc = self.c_value_input.value()
        mc_value_cc = self.mc_value_input.value()
        i_value_cc = self._avg_inclination_cc
        mi_value_cc = self._inclination_error_cc

        z_corr_grad = self.vert_angle_input.value()
        z_corr_rad = z_corr_grad * math.pi / 200.0
        sin_z = math.sin(z_corr_rad)
        tan_z = math.tan(z_corr_rad)

        if math.isclose(sin_z, 0.0) or math.isclose(tan_z, 0.0):
            self.corrected_horiz_label.setText("Poprawiony kąt poziomy: błąd obliczeń")
            self.corrected_horiz_error_label.setText("Poprawka pozioma: błąd obliczeń")
            self.corrected_vert_label.setText("Poprawiony kąt pionowy: błąd obliczeń")
            self.corrected_vert_error_label.setText("Poprawka pionowa: błąd obliczeń")
            return

        horiz_input = self.horiz_angle_input.value()
        vert_input = self.vert_angle_input.value()

        horiz_corr_cc = (c_value_cc / sin_z) + (i_value_cc / tan_z)
        horiz_corr_grad = horiz_corr_cc / 10000.0
        horiz_err_cc = math.sqrt(((mc_value_cc / sin_z) ** 2) + ((mi_value_cc / tan_z) ** 2))
        horiz_err_grad = horiz_err_cc / 10000.0

        vert_corr_cc = i_value_cc
        vert_corr_grad = vert_corr_cc / 10000.0
        vert_err_grad = mi_value_cc / 10000.0

        corrected_horiz = horiz_input - horiz_corr_grad
        corrected_vert = vert_input - vert_corr_grad

        self.corrected_horiz_label.setText(f"Poprawiony kąt poziomy: {corrected_horiz:.5f} grad")
        self.corrected_horiz_error_label.setText(
            f"Poprawka pozioma: {horiz_corr_grad:.5f} ± {horiz_err_grad:.5f} grad"
        )
        self.corrected_vert_label.setText(f"Poprawiony kąt pionowy: {corrected_vert:.5f} grad")
        self.corrected_vert_error_label.setText(
            f"Poprawka pionowa: {vert_corr_grad:.5f} ± {vert_err_grad:.5f} grad"
        )
