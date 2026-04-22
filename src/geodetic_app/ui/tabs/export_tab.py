from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import QFileDialog, QGroupBox, QLabel, QPushButton, QVBoxLayout, QWidget

from geodetic_app.models.app_state import AppState


class ExportTab(QWidget):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self._converter_source: Path | None = None

        self.converter_label = QLabel("Nie wybrano pliku do konwersji")
        self.choose_converter_file_button = QPushButton("Wybierz plik do konwersji")
        self.convert_to_txt_button = QPushButton("Konwertuj do TXT")
        self.converter_status_label = QLabel("Konwerter: gotowy")

        self.choose_converter_file_button.clicked.connect(self.choose_converter_source)
        self.convert_to_txt_button.clicked.connect(self.convert_selected_file_to_txt)

        converter_box = QGroupBox("Konwerter plików do TXT (CSV / JSON / PDF)")
        converter_layout = QVBoxLayout(converter_box)
        converter_layout.setContentsMargins(12, 12, 12, 12)
        converter_layout.setSpacing(8)
        converter_layout.addWidget(self.converter_label)
        converter_layout.addWidget(self.choose_converter_file_button)
        converter_layout.addWidget(self.convert_to_txt_button)
        converter_layout.addWidget(self.converter_status_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(converter_box)
        layout.addStretch()

    def set_results(self, frame) -> None:
        _ = frame
        # Zakładka uproszczona: obsługuje tylko konwersję plików do TXT.

    def choose_converter_source(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik do konwersji",
            "",
            "Wspierane pliki (*.csv *.json *.pdf);;Wszystkie pliki (*)",
        )
        if not file_path:
            return
        self._converter_source = Path(file_path)
        self.converter_label.setText(f"Plik źródłowy: {self._converter_source}")
        self.converter_status_label.setText("Konwerter: plik wybrany")

    def convert_selected_file_to_txt(self) -> None:
        if self._converter_source is None:
            self.converter_status_label.setText("Konwerter: najpierw wybierz plik")
            return

        target_default = f"{self._converter_source.stem}.txt"
        target_path, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz plik TXT",
            target_default,
            "Pliki tekstowe (*.txt);;Wszystkie pliki (*)",
        )
        if not target_path:
            return

        try:
            converted_text = self._convert_file_content_to_text(self._converter_source)
            Path(target_path).write_text(converted_text, encoding="utf-8")
        except Exception as exc:
            self.converter_status_label.setText(f"Konwerter: błąd ({exc})")
            return

        self.converter_status_label.setText(f"Konwerter: zapisano {Path(target_path).name}")

    def _convert_file_content_to_text(self, source: Path) -> str:
        suffix = source.suffix.lower()

        if suffix == ".csv":
            frame = pd.read_csv(source)
            return frame.to_string(index=False)

        if suffix == ".tsv":
            frame = pd.read_csv(source, sep="\t")
            return frame.to_string(index=False)

        if suffix == ".json":
            data = json.loads(source.read_text(encoding="utf-8", errors="ignore"))
            return json.dumps(data, indent=2, ensure_ascii=False)

        if suffix in {".xlsx", ".xls"}:
            frame = pd.read_excel(source)
            return frame.to_string(index=False)

        if suffix == ".pdf":
            pypdf_error: Exception | None = None
            try:
                from pypdf import PdfReader  # type: ignore[import-not-found]

                reader = PdfReader(str(source))
                pages_text: list[str] = []
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    pages_text.append(page_text.strip())
                return "\n\n".join(pages_text).strip()
            except Exception as exc:
                pypdf_error = exc

            pypdf2_error: Exception | None = None
            try:
                from PyPDF2 import PdfReader as PdfReader2  # type: ignore[import-not-found]

                reader = PdfReader2(str(source))
                pages_text = []
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    pages_text.append(page_text.strip())
                return "\n\n".join(pages_text).strip()
            except Exception as exc:
                pypdf2_error = exc

            # Fallback for systems with poppler installed.
            try:
                result = subprocess.run(
                    ["pdftotext", "-layout", str(source), "-"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout.strip()
            except Exception:
                pass

            raise RuntimeError(
                "Nie można odczytać PDF. Zainstaluj zależności: pip install -r requirements.txt "
                "(lub pip install pypdf)."
            ) from (pypdf2_error or pypdf_error)

        return source.read_text(encoding="utf-8", errors="ignore")
