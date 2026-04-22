from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
import re

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from geodetic_app.models.app_state import AppState
from geodetic_app.models.device_config import DeviceConfig
from geodetic_app.services.connection_service import ConnectionService


class ConnectionTab(QWidget):
    def __init__(self, state: AppState, connection_service: ConnectionService) -> None:
        super().__init__()
        self.state = state
        self.connection_service = connection_service

        self.transport_combo = QComboBox()
        self.transport_combo.addItems([
            "RS-232",
            "RS-485",
            "RS-423A",
            "RS-422A",
            "CAN",
            "USB",
            "Bluetooth",
        ])

        self.device_name_input = QLineEdit()
        self.address_input = QLineEdit()
        self.scan_ble_button = QPushButton("Scan BLE")
        self.port_input = QComboBox()
        self.port_input.setEditable(True)
        self.port_input.setInsertPolicy(QComboBox.NoInsert)
        self.port_input.addItem("auto")
        self.port_input.setCurrentText("auto")
        self.refresh_ports_button = QPushButton("Refresh ports")

        self.baud_rate_input = QComboBox()
        self.baud_rate_input.setEditable(True)
        self.baud_rate_input.addItems([
            "1200",
            "2400",
            "4800",
            "9600",
            "19200",
            "38400",
            "57600",
            "115200",
            "230400",
        ])
        self.baud_rate_input.setCurrentText("9600")

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["ASCII", "Binary", "Modbus RTU", "CAN frame"]) 

        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(["5", "6", "7", "8"])
        self.data_bits_combo.setCurrentText("8")

        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])

        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(["1", "1.5", "2"])

        self.flow_control_combo = QComboBox()
        self.flow_control_combo.addItems(["None", "RTS/CTS", "XON/XOFF"])

        self.terminator_combo = QComboBox()
        self.terminator_combo.addItems(["None", "CR", "LF", "CRLF"])
        self.terminator_combo.setCurrentText("CRLF")

        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(50, 120000)
        self.timeout_input.setValue(1000)

        self.can_bitrate_input = QSpinBox()
        self.can_bitrate_input.setRange(10000, 1000000)
        self.can_bitrate_input.setSingleStep(10000)
        self.can_bitrate_input.setValue(500000)

        self.can_identifier_input = QLineEdit("0x100")
        self.can_extended_checkbox = QCheckBox("Extended CAN ID (29-bit)")
        self.ble_characteristic_input = QLineEdit()
        self.ble_characteristic_input.setPlaceholderText("e.g. 0000ffe1-0000-1000-8000-00805f9b34fb")

        self.status_label = QLabel("Disconnected")
        self.log_label = QLabel("Ready")
        self.stream_console = QTextEdit()
        self.stream_console.setReadOnly(True)
        self.stream_console.setPlaceholderText("Incoming device data will appear here after connection...")
        self.stream_console.setMinimumWidth(480)

        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.read_sample_button = QPushButton("Read sample")
        self.save_data_button = QPushButton("Save device data")
        self.save_structured_csv_button = QPushButton("Save structured CSV")

        self.connect_button.clicked.connect(self.connect_device)
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.refresh_ports_button.clicked.connect(self.refresh_ports)
        self.read_sample_button.clicked.connect(self.read_sample)
        self.save_data_button.clicked.connect(self.save_recorded_data)
        self.save_structured_csv_button.clicked.connect(self.save_structured_measurements_csv)
        self.scan_ble_button.clicked.connect(self.scan_ble_devices)

        form = QFormLayout()
        form.addRow("Interface", self.transport_combo)
        form.addRow("Device name", self.device_name_input)
        address_controls = QHBoxLayout()
        address_controls.addWidget(self.address_input)
        address_controls.addWidget(self.scan_ble_button)
        form.addRow("Address", address_controls)
        port_controls = QHBoxLayout()
        port_controls.addWidget(self.port_input)
        port_controls.addWidget(self.refresh_ports_button)
        form.addRow("Port", port_controls)
        form.addRow("Baud rate", self.baud_rate_input)
        form.addRow("Protocol", self.protocol_combo)
        form.addRow("Data bits", self.data_bits_combo)
        form.addRow("Parity", self.parity_combo)
        form.addRow("Stop bits", self.stop_bits_combo)
        form.addRow("Flow control", self.flow_control_combo)
        form.addRow("Line terminator", self.terminator_combo)
        form.addRow("Timeout (ms)", self.timeout_input)
        form.addRow("CAN bitrate", self.can_bitrate_input)
        form.addRow("CAN ID", self.can_identifier_input)
        form.addRow("", self.can_extended_checkbox)
        form.addRow("BLE char UUID", self.ble_characteristic_input)

        controls = QHBoxLayout()
        controls.addWidget(self.connect_button)
        controls.addWidget(self.disconnect_button)
        controls.addWidget(self.read_sample_button)
        controls.addWidget(self.save_data_button)
        controls.addWidget(self.save_structured_csv_button)

        settings_box = QGroupBox("Connection settings")
        settings_layout = QVBoxLayout(settings_box)
        settings_layout.addLayout(form)
        settings_layout.addLayout(controls)
        settings_layout.addWidget(self.status_label)
        settings_layout.addWidget(self.log_label)
        settings_layout.addStretch(1)

        stream_box = QGroupBox("Incoming data")
        stream_layout = QVBoxLayout(stream_box)
        stream_layout.addWidget(self.stream_console)

        splitter = QSplitter()
        splitter.addWidget(settings_box)
        splitter.addWidget(stream_box)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([430, 770])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(splitter)

        self.connection_service.connection_changed.connect(self._on_connection_changed)
        self.connection_service.log_message.connect(self.log_label.setText)
        self.connection_service.raw_data_received.connect(self._on_raw_data_received)
        self.connection_service.measurement_received.connect(self._on_measurement_received)
        self.refresh_ports()

    def _build_config(self) -> DeviceConfig:
        baud_rate_text = self.baud_rate_input.currentText().strip()
        baud_rate = int(baud_rate_text) if baud_rate_text.isdigit() else 9600

        return DeviceConfig(
            transport=self.transport_combo.currentText(),
            device_name=self.device_name_input.text().strip(),
            device_address=self.address_input.text().strip(),
            port=self.port_input.currentText().strip(),
            baud_rate=baud_rate,
            protocol=self.protocol_combo.currentText(),
            data_bits=int(self.data_bits_combo.currentText()),
            parity=self.parity_combo.currentText(),
            stop_bits=self.stop_bits_combo.currentText(),
            flow_control=self.flow_control_combo.currentText(),
            terminator=self.terminator_combo.currentText(),
            timeout_ms=self.timeout_input.value(),
            can_bitrate=self.can_bitrate_input.value(),
            can_identifier=self.can_identifier_input.text().strip() or "0x100",
            can_extended_id=self.can_extended_checkbox.isChecked(),
            bluetooth_characteristic_uuid=self.ble_characteristic_input.text().strip(),
        )

    def connect_device(self) -> None:
        config = self._build_config()
        self.state.device_config = config
        self.stream_console.append("--- connecting ---")
        self.connection_service.connect_device(config)

    def disconnect_device(self) -> None:
        self.connection_service.disconnect_device()

    def _on_connection_changed(self, connected: bool, message: str) -> None:
        self.state.connection_status = "connected" if connected else "disconnected"
        self.status_label.setText(message)
        if not connected:
            self.stream_console.append("--- disconnected ---")

    def refresh_ports(self) -> None:
        ports = self.connection_service.preferred_serial_ports()
        current_value = self.port_input.currentText().strip() or "auto"
        self.port_input.blockSignals(True)
        self.port_input.clear()
        self.port_input.addItem("auto")
        if ports:
            self.port_input.addItems(ports)
        if current_value in [self.port_input.itemText(i) for i in range(self.port_input.count())]:
            self.port_input.setCurrentText(current_value)
        elif ports:
            self.port_input.setCurrentText(ports[0])
        else:
            self.port_input.setCurrentText("auto")
        self.port_input.blockSignals(False)

        if ports:
            self.log_label.setText(f"Found ports: {', '.join(ports[:3])}")
        else:
            self.log_label.setText("No serial ports detected. Using auto/mock.")

    def read_sample(self) -> None:
        try:
            self.connection_service.fetch_sample()
        except Exception as exc:
            self.log_label.setText(f"Read failed: {exc}")
            return

    def _on_raw_data_received(self, raw_text: str) -> None:
        self.stream_console.append(raw_text)

    def _on_measurement_received(self, sample) -> None:
        self.state.measurements.append(sample)
        self.log_label.setText(
            f"Sample saved: id={sample.sample_id}, distance={sample.slope_distance_m:.3f} m, angle={sample.vertical_angle_deg:.3f} deg"
        )

    def save_recorded_data(self) -> None:
        payload = self.stream_console.toPlainText().strip()
        if not payload:
            self.log_label.setText("No recorded device data to save")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"device_data_{timestamp}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save recorded device data",
            default_name,
            "Text files (*.txt);;All files (*)",
        )
        if not file_path:
            return

        target = Path(file_path)
        try:
            target.write_text(payload + "\n", encoding="utf-8")
        except OSError as exc:
            self.log_label.setText(f"Save failed: {exc}")
            return

        self.log_label.setText(f"Recorded data saved: {target.name}")

    def save_structured_measurements_csv(self) -> None:
        payload = self.stream_console.toPlainText().strip()
        if not payload:
            self.log_label.setText("No recorded device data to structure")
            return

        rows = self._parse_stream_to_structured_rows(payload)
        if not rows:
            self.log_label.setText("No measurable rows found in stream")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"structured_measurements_{timestamp}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save structured measurements",
            default_name,
            "CSV files (*.csv);;All files (*)",
        )
        if not file_path:
            return

        target = Path(file_path)
        fieldnames = [
            "record_no",
            "packet_code",
            "packet_arg",
            "field_1_code",
            "field_1_sign",
            "field_1_value_raw",
            "field_1_value",
            "field_2_code",
            "field_2_sign",
            "field_2_value_raw",
            "field_2_value",
            "field_3_code",
            "field_3_sign",
            "field_3_value_raw",
            "field_3_value",
            "parse_status",
            "raw_line",
        ]

        try:
            with target.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        except OSError as exc:
            self.log_label.setText(f"CSV save failed: {exc}")
            return

        ok_count = sum(1 for row in rows if row["parse_status"] == "ok")
        partial_count = len(rows) - ok_count
        self.log_label.setText(
            f"Structured CSV saved: {target.name} | rows={len(rows)} ok={ok_count} partial={partial_count}"
        )

    def _parse_stream_to_structured_rows(self, payload: str) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        packet_re = re.compile(r"^(\d{6})([+-][A-Za-z0-9?.]{8})$")
        value_re = re.compile(r"^([0-9?.]{6})([+-])(\d{8})$")

        for line in payload.splitlines():
            raw_line = line.strip()
            if not raw_line or raw_line.startswith("---"):
                continue

            tokens = raw_line.split()
            if not tokens:
                continue

            row = {
                "record_no": "",
                "packet_code": "",
                "packet_arg": "",
                "field_1_code": "",
                "field_1_sign": "",
                "field_1_value_raw": "",
                "field_1_value": "",
                "field_2_code": "",
                "field_2_sign": "",
                "field_2_value_raw": "",
                "field_2_value": "",
                "field_3_code": "",
                "field_3_sign": "",
                "field_3_value_raw": "",
                "field_3_value": "",
                "parse_status": "partial",
                "raw_line": raw_line,
            }

            first = tokens[0]
            packet_match = packet_re.match(first)
            if packet_match:
                row["record_no"] = packet_match.group(1)
                row["packet_arg"] = packet_match.group(2)
                if row["packet_arg"]:
                    row["packet_code"] = row["packet_arg"][0:2]
            elif len(first) >= 6 and first[:6].isdigit():
                row["record_no"] = first[:6]
                row["packet_arg"] = first[6:]
                row["packet_code"] = row["packet_arg"][0:2] if len(row["packet_arg"]) >= 2 else ""

            parsed_values = 0
            for index, token in enumerate(tokens[1:4], start=1):
                value_match = value_re.match(token)
                if not value_match:
                    continue

                code = value_match.group(1)
                sign = value_match.group(2)
                value_raw = value_match.group(3)
                numeric = float(value_raw) / 100000.0
                if sign == "-":
                    numeric = -numeric

                row[f"field_{index}_code"] = code
                row[f"field_{index}_sign"] = sign
                row[f"field_{index}_value_raw"] = value_raw
                row[f"field_{index}_value"] = f"{numeric:.5f}"
                parsed_values += 1

            if parsed_values >= 1 and row["record_no"]:
                row["parse_status"] = "ok"

            rows.append(row)

        return rows

    def scan_ble_devices(self) -> None:
        devices = self.connection_service.scan_bluetooth_devices(timeout_s=4.0)
        if not devices:
            self.log_label.setText("No BLE devices found")
            return

        name, address = devices[0]
        self.device_name_input.setText(name)
        self.address_input.setText(address)
        preview = ", ".join(f"{dev_name} ({dev_addr})" for dev_name, dev_addr in devices[:3])
        self.log_label.setText(f"BLE devices: {preview}")
