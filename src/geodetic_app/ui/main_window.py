from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget

from geodetic_app.models.app_state import AppState
from geodetic_app.services.connection_service import ConnectionService
from geodetic_app.ui.tabs.arc_vs_chord_tab import ArcVsChordTab
from geodetic_app.ui.tabs.atmospheric_correction_tab import AtmosphericCorrectionTab
from geodetic_app.ui.tabs.connection_tab import ConnectionTab
from geodetic_app.ui.tabs.export_tab import ExportTab
from geodetic_app.ui.tabs.inklinacja_tab import InklinacjaTab
from geodetic_app.ui.tabs.kollimacja_tab import KollimacjaTab
from geodetic_app.ui.tabs.ng0_tab import Ng0Tab
from geodetic_app.ui.tabs.rab_code_tab import RabCodeTab
from geodetic_app.ui.tabs.text_file_load_tab import TextFileLoadTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Geodetic Measurement App")
        self.resize(1200, 800)

        self.state = AppState()
        self.connection_service = ConnectionService()

        self.tabs = QTabWidget()
        self.kollimacja_tab = KollimacjaTab(self.state)
        self.inklinacja_tab = InklinacjaTab(self.state)
        self.ng0_tab = Ng0Tab(self.state)
        self.atmospheric_correction_tab = AtmosphericCorrectionTab(self.state)
        self.file_load_tab = TextFileLoadTab()
        self.arc_vs_chord_tab = ArcVsChordTab(self.state)
        self.rab_code_tab = RabCodeTab()
        self.connection_tab = ConnectionTab(self.state, self.connection_service)
        self.export_tab = ExportTab(self.state)

        self.tabs.addTab(self.kollimacja_tab, "Obliczenie kolimacji")
        self.tabs.addTab(self.inklinacja_tab, "Obliczenie inklinacji")
        self.tabs.addTab(self.ng0_tab, "Obliczenie Ng0 (400-1600 nm)")
        self.tabs.addTab(self.atmospheric_correction_tab, "Obliczenie poprawki atmosferycznej")
        self.tabs.addTab(self.file_load_tab, "Wczytanie pliku tekstowego")
        self.tabs.addTab(self.arc_vs_chord_tab, "Różnica łuk-cięciwa (mm)")
        self.tabs.addTab(self.rab_code_tab, "Generator kodu Topcon (RAB-Code)")
        self.tabs.addTab(self.connection_tab, "Connection")
        self.tabs.addTab(self.export_tab, "Export")

        self.setCentralWidget(self.tabs)
