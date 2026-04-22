from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import QDoubleSpinBox, QFormLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from geodetic_app.calculations.atmospheric_corrections import atmospheric_correction_from_wet_dry
from geodetic_app.models.app_state import AppState


class AtmosphericCorrectionTab(QWidget):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

        self.wavelength_input = QDoubleSpinBox()
        self.wavelength_input.setRange(400.0, 1600.0)
        self.wavelength_input.setDecimals(1)
        self.wavelength_input.setSingleStep(10.0)
        self.wavelength_input.setValue(633.0)

        self.distance_input = QDoubleSpinBox()
        self.distance_input.setRange(0.0, 1_000_000.0)
        self.distance_input.setDecimals(3)
        self.distance_input.setValue(1000.0)

        self.temperature_dry_input = QDoubleSpinBox()
        self.temperature_dry_input.setRange(-60.0, 80.0)
        self.temperature_dry_input.setDecimals(2)
        self.temperature_dry_input.setValue(20.0)

        self.temperature_wet_input = QDoubleSpinBox()
        self.temperature_wet_input.setRange(-60.0, 80.0)
        self.temperature_wet_input.setDecimals(2)
        self.temperature_wet_input.setValue(18.0)

        self.pressure_input = QDoubleSpinBox()
        self.pressure_input.setRange(300.0, 1200.0)
        self.pressure_input.setDecimals(2)
        self.pressure_input.setValue(1013.25)

        input_width = 180
        for widget in (
            self.wavelength_input,
            self.temperature_dry_input,
            self.temperature_wet_input,
            self.pressure_input,
            self.distance_input,
        ):
            widget.setFixedWidth(input_width)

        self.compute_button = QPushButton("Oblicz poprawkę atmosferyczną")
        self.correction_per_km_label = QLabel("Poprawka na km: — mm/km")
        self.length_correction_label = QLabel("Poprawka do mierzonej długości: — mm")
        self.corrected_length_label = QLabel("Długość poprawiona: — m")
        self.estimated_humidity_label = QLabel("Wilgotność obliczona (z T suchej/mokrej): — %")

        self.compute_button.clicked.connect(self.compute)

        form = QFormLayout()
        form.addRow("Długość fali [nm]", self.wavelength_input)
        form.addRow("Temperatura sucha [st C]", self.temperature_dry_input)
        form.addRow("Temperatura mokra [st C]", self.temperature_wet_input)
        form.addRow("Ciśnienie [hPa]", self.pressure_input)
        form.addRow("Pomierzona długość [m]", self.distance_input)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addLayout(form)
        layout.addWidget(self.compute_button)
        layout.addWidget(self.correction_per_km_label)
        layout.addWidget(self.length_correction_label)
        layout.addWidget(self.corrected_length_label)
        layout.addWidget(self.estimated_humidity_label)
        layout.addStretch()

    def compute(self) -> None:
        wavelength_nm = self.wavelength_input.value()
        temperature_dry = self.temperature_dry_input.value()
        temperature_wet = self.temperature_wet_input.value()
        pressure = self.pressure_input.value()
        distance = self.distance_input.value()

        correction_per_km_m, correction_m, corrected_distance, estimated_humidity = atmospheric_correction_from_wet_dry(
            distance,
            wavelength_nm,
            temperature_dry,
            temperature_wet,
            pressure,
        )

        self.correction_per_km_label.setText(f"Poprawka na km: {correction_per_km_m * 1000.0:.3f} mm/km")
        self.length_correction_label.setText(
            f"Poprawka do mierzonej długości: {correction_m * 1000.0:.3f} mm ({correction_m:.6f} m)"
        )
        self.corrected_length_label.setText(f"Długość poprawiona: {corrected_distance:.6f} m")
        self.estimated_humidity_label.setText(
            f"Wilgotność obliczona (z T suchej/mokrej): {estimated_humidity:.2f} %"
        )

        self.state.results = pd.DataFrame(
            [
                {
                    "wavelength_nm": wavelength_nm,
                    "dry_temperature_c": temperature_dry,
                    "wet_temperature_c": temperature_wet,
                    "distance_m": distance,
                    "pressure_hpa": pressure,
                    "estimated_humidity_percent": estimated_humidity,
                    "correction_per_km_m": correction_per_km_m,
                    "correction_per_km_mm": correction_per_km_m * 1000.0,
                    "correction_m": correction_m,
                    "correction_mm": correction_m * 1000.0,
                    "corrected_distance_m": corrected_distance,
                }
            ]
        )
