from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from geodetic_app.models.app_state import AppState
from geodetic_app.ui.tabs._shared import LinePlotWidget


class Ng0Tab(QWidget):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

        self.info_label = QLabel("Obliczenie Ng0 dla długości fali 400-1600 nm (krok 10 nm)")
        self.generate_button = QPushButton("Wygeneruj tabelę i wykres")
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Długość fali [nm]", "Współczynnik refrakcji", "Ng0"])
        self.refractivity_plot = LinePlotWidget()
        # self.ng0_plot = LinePlotWidget()

        self.generate_button.clicked.connect(self.generate)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(self.info_label)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.refractivity_plot)
        # layout.addWidget(self.ng0_plot)
        layout.addWidget(self.table)
        layout.addStretch()

    def generate(self) -> None:
        wavelengths = list(range(400, 1601, 10))
        rows = []

        for wavelength_nm in wavelengths:
            wavelength_um = wavelength_nm / 1000.0
            sigma2 = (1.0 / wavelength_um) ** 2
            refractivity = 287.6155 + (4.8866 / (130.0 - sigma2)) + (0.0680 / (38.9 - sigma2))
            ng0 = 1.0 + refractivity * 1e-6
            rows.append(
                {
                    "wavelength_nm": wavelength_nm,
                    "refractivity": refractivity,
                    "Ng0": ng0,
                }
            )

        frame = pd.DataFrame(rows)
        self.state.results = frame

        self.table.setRowCount(len(frame.index))
        for row_index, row in enumerate(frame.itertuples(index=False)):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row.wavelength_nm)))
            self.table.setItem(row_index, 1, QTableWidgetItem(f"{row.refractivity:.5f}"))
            self.table.setItem(row_index, 2, QTableWidgetItem(f"{row.Ng0:.9f}"))

        self.refractivity_plot.set_series(
            frame["wavelength_nm"].tolist(),
            frame["refractivity"].tolist(),
            "Współczynnik refrakcji vs długość fali",
        )
        # self.ng0_plot.set_series(
        #     frame["wavelength_nm"].tolist(),
        #     frame["Ng0"].tolist(),
        #     "Ng0 vs długość fali",
        # )
        self.info_label.setText(f"Wygenerowano {len(frame)} wierszy")
