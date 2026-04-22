from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from geodetic_app.models.app_state import AppState
from geodetic_app.ui.tabs._shared import LinePlotWidget


class Ng0Tab(QWidget):
    STANDARD_TEMPERATURE_C = 15.0
    STANDARD_PRESSURE_MMHG = 760.0

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

        self.info_label = QLabel(
            "Obliczenie Ng0 oraz ΔD=(Ngs-Ngr) [ppm] dla długości fali 400-1600 nm (krok 10 nm)"
        )
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(-40.0, 60.0)
        self.temperature_input.setDecimals(2)
        self.temperature_input.setValue(5.0)

        self.pressure_input = QDoubleSpinBox()
        self.pressure_input.setRange(500.0, 900.0)
        self.pressure_input.setDecimals(2)
        self.pressure_input.setValue(760.0)

        self.generate_button = QPushButton("Wygeneruj tabelę i wykres")
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            [
                "Długość fali [nm]",
                "N_g0 [ppm]",
                "Ng0",
                "N_gs [ppm]",
                "N_gr [ppm]",
                "ΔD = N_gs - N_gr [ppm]",
            ]
        )
        self.refractivity_plot = LinePlotWidget()

        self.generate_button.clicked.connect(self.generate)

        form = QFormLayout()
        form.addRow("Temperatura rzeczywista [st C]", self.temperature_input)
        form.addRow("Ciśnienie rzeczywiste [mmHg]", self.pressure_input)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(self.info_label)
        layout.addLayout(form)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.refractivity_plot)
        layout.addWidget(self.table)
        layout.addStretch()

    def generate(self) -> None:
        wavelengths = sorted(set(range(400, 1601, 10)) | {633})
        rows = []
        real_temperature_c = self.temperature_input.value()
        real_pressure_mmhg = self.pressure_input.value()

        standard_factor = (
            self.STANDARD_PRESSURE_MMHG / self.STANDARD_PRESSURE_MMHG
        ) * (273.15 / (273.15 + self.STANDARD_TEMPERATURE_C))
        real_factor = (real_pressure_mmhg / self.STANDARD_PRESSURE_MMHG) * (
            273.15 / (273.15 + real_temperature_c)
        )

        for wavelength_nm in wavelengths:
            wavelength_um = wavelength_nm / 1000.0
            sigma2 = (1.0 / wavelength_um) ** 2
            refractivity = 287.6155 + (4.8866 * sigma2) + (0.0680 * sigma2 * sigma2)
            ng0 = 1.0 + refractivity * 1e-6
            n_gs = refractivity * standard_factor
            n_gr = refractivity * real_factor
            delta_d_ppm = n_gs - n_gr
            rows.append(
                {
                    "wavelength_nm": wavelength_nm,
                    "N_g0": refractivity,
                    "Ng0": ng0,
                    "N_gs": n_gs,
                    "N_gr": n_gr,
                    "delta_d_ppm": delta_d_ppm,
                }
            )

        frame = pd.DataFrame(rows)
        self.state.results = frame

        self.table.setRowCount(len(frame.index))
        for row_index, row in enumerate(frame.itertuples(index=False)):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row.wavelength_nm)))
            self.table.setItem(row_index, 1, QTableWidgetItem(f"{row.N_g0:.5f}"))
            self.table.setItem(row_index, 2, QTableWidgetItem(f"{row.Ng0:.9f}"))
            self.table.setItem(row_index, 3, QTableWidgetItem(f"{row.N_gs:.5f}"))
            self.table.setItem(row_index, 4, QTableWidgetItem(f"{row.N_gr:.5f}"))
            self.table.setItem(row_index, 5, QTableWidgetItem(f"{row.delta_d_ppm:.5f}"))

        self.refractivity_plot.set_series(
            frame["wavelength_nm"].tolist(),
            frame["N_g0"].tolist(),
            "N_g0 [ppm] vs długość fali",
        )
        sample_633 = frame.loc[frame["wavelength_nm"] == 633]
        if not sample_633.empty:
            n_633 = sample_633.iloc[0]["N_g0"]
            self.info_label.setText(
                f"Wygenerowano {len(frame)} wierszy. Dla 633 nm: N_g0={n_633:.2f} ppm"
            )
        else:
            self.info_label.setText(f"Wygenerowano {len(frame)} wierszy")
