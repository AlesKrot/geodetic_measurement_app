from __future__ import annotations

import math

import pandas as pd
from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from geodetic_app.calculations.horizontal_distance import EARTH_RADIUS_M
from geodetic_app.models.app_state import AppState
from geodetic_app.ui.tabs._shared import LinePlotWidget


class ArcVsChordTab(QWidget):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

        self.generate_button = QPushButton("Wygeneruj tabelę i wykres (1-100 km)")
        self.info_label = QLabel("Różnica łuk-cięciwa [mm] dla przedziału 1-100 km (co 1 km)")
        self.plot = LinePlotWidget()
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Odległość [km]", "Różnica łuk-cięciwa [mm]"])

        self.generate_button.clicked.connect(self.generate)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.info_label)
        layout.addWidget(self.plot)
        layout.addWidget(self.table)
        layout.addStretch()

    def generate(self) -> None:
        rows = []
        for distance_km in range(1, 101):
            arc_m = distance_km * 1000.0
            chord_m = 2.0 * EARTH_RADIUS_M * math.sin(arc_m / (2.0 * EARTH_RADIUS_M))
            diff_mm = (arc_m - chord_m) * 1000.0
            rows.append({"distance_km": distance_km, "arc_minus_chord_mm": diff_mm})

        frame = pd.DataFrame(rows)
        self.state.results = frame

        self.table.setRowCount(len(frame.index))
        for row_index, row in enumerate(frame.itertuples(index=False)):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row.distance_km)))
            self.table.setItem(row_index, 1, QTableWidgetItem(f"{row.arc_minus_chord_mm:.5f}"))

        self.plot.set_series(
            frame["distance_km"].tolist(),
            frame["arc_minus_chord_mm"].tolist(),
            "Różnica łuk-cięciwa [mm] vs odległość [km]",
        )

        max_value = frame["arc_minus_chord_mm"].max()
        self.info_label.setText(f"Wygenerowano {len(frame)} wierszy. Maksymalna różnica: {max_value:.5f} mm")
