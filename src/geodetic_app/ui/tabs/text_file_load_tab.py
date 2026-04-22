from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from geodetic_app.calculations.atmospheric_corrections import atmospheric_correction_from_wet_dry


class TextFileLoadTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.file_label = QLabel("Nie wybrano pliku")
        self.load_button = QPushButton("Wczytaj plik tekstowy")
        self.table = QTableWidget(0, 0)
        self.table.verticalHeader().setVisible(False)

        self.load_button.clicked.connect(self.load_file)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(self.file_label)
        layout.addWidget(self.load_button)
        layout.addWidget(self.table)
        layout.addStretch()

    def load_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wczytaj plik tekstowy",
            "",
            "Pliki tekstowe (*.txt *.csv);;Wszystkie pliki (*)",
        )
        if not file_path:
            return

        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        self.file_label.setText(f"Plik: {file_path}")
        processed = self._append_corrected_length_column(content)
        self._fill_table_from_text(processed)

    def _fill_table_from_text(self, content: str) -> None:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if len(lines) < 2:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        headers = [token.strip() for token in lines[0].split(";") if token.strip()]
        rows: list[list[str]] = []
        for line in lines[1:]:
            tokens = [token.strip() for token in line.split(";") if token.strip()]
            if tokens:
                rows.append(tokens)

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            for col_idx in range(len(headers)):
                value = row[col_idx] if col_idx < len(row) else ""
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()

    def _append_corrected_length_column(self, content: str) -> str:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if len(lines) < 2:
            return content

        header_tokens = [token.strip() for token in lines[0].split(";") if token.strip()]
        lower_header = [token.lower() for token in header_tokens]

        def find_col(pattern: str) -> int | None:
            for idx, name in enumerate(lower_header):
                if re.search(pattern, name):
                    return idx
            return None

        ts_idx = find_col(r"\bts\b|such")
        tm_idx = find_col(r"\btm\b|mokr")
        p_idx = find_col(r"\bp\b|ciś|cisn")
        dist_idx = find_col(r"d[łl]ugo.*mierz|distance|dyst")
        if None in (ts_idx, tm_idx, p_idx, dist_idx):
            return content

        new_header = header_tokens + ["długość poprawiona"]
        output_lines = ["; ".join(new_header) + ";"]

        for raw_line in lines[1:]:
            tokens = [token.strip() for token in raw_line.split(";") if token.strip()]
            if len(tokens) <= max(ts_idx, tm_idx, p_idx, dist_idx):
                output_lines.append(raw_line)
                continue

            try:
                ts = float(tokens[ts_idx].replace(",", "."))
                tm = float(tokens[tm_idx].replace(",", "."))
                p = float(tokens[p_idx].replace(",", "."))
                distance = float(tokens[dist_idx].replace(",", "."))
            except ValueError:
                output_lines.append(raw_line)
                continue

            _, _, corrected_distance_m, _ = atmospheric_correction_from_wet_dry(
                distance_m=distance,
                wavelength_nm=633.0,
                dry_temperature_c=ts,
                wet_temperature_c=tm,
                pressure_hpa=p,
            )
            corrected_text = f"{corrected_distance_m:.4f}".replace(".", ",")
            output_lines.append(raw_line.rstrip("; ") + f"; {corrected_text};")

        return "\n".join(output_lines)
