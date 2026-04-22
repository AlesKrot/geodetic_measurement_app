from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from geodetic_app.calculations.horizontal_distance import EARTH_RADIUS_M
from geodetic_app.models.app_state import AppState
from geodetic_app.ui.tabs._shared import LinePlotWidget


class ArcVsChordTab(QWidget):
    EFFECTIVE_RADIUS_M = 8.0 * EARTH_RADIUS_M

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

        self.generate_button = QPushButton("Wygeneruj tabelę i wykres (1-100 km)")
        self.info_label = QLabel("Krzywizna fali: Δc = c - d = -d^3/(24r^2), r = 8R_Ziemi")
        self.plot = LinePlotWidget()
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["d [km]", "c [km]", "Δc = c - d [mm]"])

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
            d_m = distance_km * 1000.0
            delta_c_m = -(d_m**3) / (24.0 * (self.EFFECTIVE_RADIUS_M**2))
            c_m = d_m + delta_c_m
            rows.append(
                {
                    "distance_km": distance_km,
                    "chord_km": c_m / 1000.0,
                    "delta_c_mm": delta_c_m * 1000.0,
                }
            )

        frame = pd.DataFrame(rows)
        self.state.results = frame

        self.table.setRowCount(len(frame.index))
        for row_index, row in enumerate(frame.itertuples(index=False)):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row.distance_km)))
            self.table.setItem(row_index, 1, QTableWidgetItem(f"{row.chord_km:.9f}"))
            self.table.setItem(row_index, 2, QTableWidgetItem(f"{row.delta_c_mm:.5f}"))

        self.plot.set_series(
            frame["distance_km"].tolist(),
            frame["delta_c_mm"].tolist(),
            "Δc = c - d [mm] vs d [km]",
        )

        min_value = frame["delta_c_mm"].min()
        self.info_label.setText(
            f"Wygenerowano {len(frame)} wierszy. Największa (ujemna) wartość Δc: {min_value:.5f} mm"
        )
