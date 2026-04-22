from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime, timezone
import random
import threading

from PySide6.QtCore import QObject, Signal

from geodetic_app.models.device_config import DeviceConfig
from geodetic_app.models.measurement import MeasurementRecord

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - optional runtime dependency guard
    serial = None
    list_ports = None

try:
    from bleak import BleakClient, BleakScanner
except ImportError:  # pragma: no cover - optional runtime dependency guard
    BleakClient = None
    BleakScanner = None


SERIAL_TRANSPORTS = {"RS-232", "RS-485", "RS-423A", "RS-422A", "USB"}
BLUETOOTH_TRANSPORTS = {"BLUETOOTH", "BLE"}
NON_DEVICE_PORT_MARKERS = ("bluetooth", "debug", "wlan")


def _serial_parity(parity: str):
    if serial is None:
        return None
    mapping = {
        "None": serial.PARITY_NONE,
        "Even": serial.PARITY_EVEN,
        "Odd": serial.PARITY_ODD,
        "Mark": serial.PARITY_MARK,
        "Space": serial.PARITY_SPACE,
    }
    return mapping.get(parity, serial.PARITY_NONE)


def _serial_stop_bits(stop_bits: str):
    if serial is None:
        return None
    mapping = {
        "1": serial.STOPBITS_ONE,
        "1.5": serial.STOPBITS_ONE_POINT_FIVE,
        "2": serial.STOPBITS_TWO,
    }
    return mapping.get(stop_bits, serial.STOPBITS_ONE)


def _parse_ascii_measurement(line: str) -> MeasurementRecord | None:
    text = line.strip()
    if not text:
        return None

    # Expected examples:
    # "12.345" or "12.345,0.10,20.0,1013.2,50.0"
    # slope_distance[,vertical_angle,temperature,pressure,humidity]
    parts = [part.strip() for part in text.split(",")]
    if not parts:
        return None
    try:
        slope_distance_m = float(parts[0])
        vertical_angle_deg = float(parts[1]) if len(parts) > 1 else 0.0
        temperature_c = float(parts[2]) if len(parts) > 2 else 20.0
        pressure_hpa = float(parts[3]) if len(parts) > 3 else 1013.25
        humidity_percent = float(parts[4]) if len(parts) > 4 else 50.0
    except ValueError:
        return None

    return MeasurementRecord(
        sample_id=f"serial-{int(datetime.now(timezone.utc).timestamp())}",
        slope_distance_m=slope_distance_m,
        vertical_angle_deg=vertical_angle_deg,
        temperature_c=temperature_c,
        pressure_hpa=pressure_hpa,
        humidity_percent=humidity_percent,
    )


class ConnectionService(QObject):
    connection_changed = Signal(bool, str)
    log_message = Signal(str)
    raw_data_received = Signal(str)
    measurement_received = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._connected = False
        self._config = DeviceConfig()
        self._serial_conn = None
        self._ble_client = None
        self._ble_stop = threading.Event()
        self._ble_thread: threading.Thread | None = None
        self._ble_loop: asyncio.AbstractEventLoop | None = None
        self._reader_stop = threading.Event()
        self._reader_thread: threading.Thread | None = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    def available_ports(self) -> list[str]:
        if list_ports is None:
            return []
        return [port.device for port in list_ports.comports()]

    def preferred_serial_ports(self) -> list[str]:
        if list_ports is None:
            return []

        preferred: list[str] = []
        fallback: list[str] = []
        for port in list_ports.comports():
            device = (port.device or "").strip()
            if not device:
                continue

            dev_lower = device.lower()
            desc_lower = (port.description or "").lower()
            hwid_lower = (port.hwid or "").lower()
            if any(marker in dev_lower for marker in NON_DEVICE_PORT_MARKERS):
                continue

            is_usb_candidate = any(token in dev_lower for token in ("usb", "serial", "modem"))
            is_usb_candidate = is_usb_candidate or any(token in desc_lower for token in ("usb", "serial"))
            is_usb_candidate = is_usb_candidate or "usb" in hwid_lower
            is_usb_candidate = is_usb_candidate or (port.vid is not None and port.pid is not None)

            if is_usb_candidate:
                preferred.append(device)
            else:
                fallback.append(device)

        return preferred if preferred else fallback

    def scan_bluetooth_devices(self, timeout_s: float = 4.0) -> list[tuple[str, str]]:
        if BleakScanner is None:
            return []
        timeout_s = max(1.0, timeout_s)
        try:
            devices = asyncio.run(BleakScanner.discover(timeout=timeout_s))
        except Exception:
            return []

        result: list[tuple[str, str]] = []
        for device in devices:
            name = (device.name or "Unknown BLE device").strip()
            address = (device.address or "").strip()
            if not address:
                continue
            result.append((name, address))
        return result

    def _resolve_port(self, requested_port: str) -> str | None:
        if requested_port and requested_port.lower() != "auto":
            return requested_port
        ports = self.preferred_serial_ports()
        return ports[0] if ports else None

    def connect_device(self, config: DeviceConfig) -> None:
        if self._connected:
            self.disconnect_device()

        self._config = config
        summary = (
            f"{config.transport} | port={config.port or 'auto'} | {config.baud_rate}"
            f" {config.data_bits}{config.parity[0] if config.parity else 'N'}{config.stop_bits}"
            f" | flow={config.flow_control}"
        )

        transport_upper = (config.transport or "").upper()

        if transport_upper in SERIAL_TRANSPORTS:
            if serial is None:
                self._connected = False
                self.connection_changed.emit(False, "PySerial is not installed")
                self.log_message.emit("Install dependency: pip install pyserial")
                return

            port_name = self._resolve_port(config.port)
            if not port_name:
                self._connected = False
                self.connection_changed.emit(False, "No serial/USB ports found")
                self.log_message.emit("Connect device first or set explicit port")
                return

            try:
                self._serial_conn = serial.Serial(
                    port=port_name,
                    baudrate=config.baud_rate,
                    bytesize=config.data_bits,
                    parity=_serial_parity(config.parity),
                    stopbits=_serial_stop_bits(config.stop_bits),
                    timeout=config.timeout_ms / 1000.0,
                    rtscts=config.flow_control == "RTS/CTS",
                    xonxoff=config.flow_control == "XON/XOFF",
                )
            except Exception as exc:
                self._serial_conn = None
                self._connected = False
                self.connection_changed.emit(False, "Serial connection failed")
                self.log_message.emit(f"Cannot open {port_name}: {exc}")
                return

            self._connected = True
            self.connection_changed.emit(True, f"Connected via {config.transport}")
            self.log_message.emit(f"Serial connection established: {summary} | active_port={port_name}")
            self._start_reader_thread()
            return

        if transport_upper == "CAN":
            self._connected = True
            self.connection_changed.emit(True, "Connected via CAN (mock)")
            self.log_message.emit(
                f"CAN mock mode: bitrate={config.can_bitrate}, id={config.can_identifier}, ext={config.can_extended_id}"
            )
            return

        if transport_upper in BLUETOOTH_TRANSPORTS:
            if not (config.device_address or "").strip():
                self._connected = True
                self.connection_changed.emit(True, "Connected via Bluetooth (mock)")
                self.log_message.emit("Bluetooth backend is pending; mock mode is active.")
                return
            self._connect_bluetooth(config)
            return

        self._connected = True
        if config.transport.upper() == "CAN":
            summary += (
                f" | can_bitrate={config.can_bitrate}"
                f" | can_id={config.can_identifier}"
                f" | ext_id={'yes' if config.can_extended_id else 'no'}"
            )

        self.connection_changed.emit(True, f"Connected via {config.transport}")
        self.log_message.emit(f"Connection established (mock mode): {summary}")

    def disconnect_device(self) -> None:
        self._stop_ble_thread()
        self._stop_reader_thread()
        if self._serial_conn is not None:
            try:
                self._serial_conn.close()
            except Exception:
                pass
            self._serial_conn = None
        self._connected = False
        self.connection_changed.emit(False, "Disconnected")
        self.log_message.emit("Connection closed.")

    def fetch_sample(self) -> MeasurementRecord:
        if not self._connected:
            raise RuntimeError("Device is not connected")

        if self._serial_conn is not None:
            raw_line = self._serial_conn.readline().decode(errors="ignore")
            parsed = _parse_ascii_measurement(raw_line)
            if parsed is not None:
                self.measurement_received.emit(parsed)
                self.log_message.emit(f"Serial sample read: {raw_line.strip()}")
                return parsed
            raise RuntimeError("No valid measurement received from serial device")

        if self._ble_client is not None:
            raise RuntimeError("Bluetooth stream is active: samples are received automatically")

        sample = MeasurementRecord(
            sample_id=f"mock-{random.randint(1000, 9999)}",
            slope_distance_m=25.0 + random.random(),
            vertical_angle_deg=0.1,
            temperature_c=20.0,
            pressure_hpa=1013.25,
            humidity_percent=50.0,
        )
        self.measurement_received.emit(sample)
        return sample

    def _start_reader_thread(self) -> None:
        if self._serial_conn is None:
            return
        if self._reader_thread is not None and self._reader_thread.is_alive():
            return

        self._reader_stop.clear()
        self._reader_thread = threading.Thread(target=self._serial_read_loop, daemon=True)
        self._reader_thread.start()

    def _stop_reader_thread(self) -> None:
        self._reader_stop.set()
        if self._reader_thread is not None and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=1.0)
        self._reader_thread = None

    def _serial_read_loop(self) -> None:
        while not self._reader_stop.is_set() and self._serial_conn is not None:
            try:
                raw_line = self._serial_conn.readline().decode(errors="ignore")
            except Exception as exc:
                self.log_message.emit(f"Serial read error: {exc}")
                break

            if not raw_line:
                continue

            raw_text = raw_line.strip()
            if not raw_text:
                continue

            self.raw_data_received.emit(raw_text)
            parsed = _parse_ascii_measurement(raw_text)
            if parsed is not None:
                self.measurement_received.emit(parsed)

    def _connect_bluetooth(self, config: DeviceConfig) -> None:
        if BleakClient is None:
            self._connected = False
            self.connection_changed.emit(False, "Bleak is not installed")
            self.log_message.emit("Install dependency: pip install bleak")
            return

        address = (config.device_address or "").strip()
        if not address:
            self._connected = False
            self.connection_changed.emit(False, "Bluetooth address is required")
            self.log_message.emit("Use Scan BLE to fill device address")
            return

        self._ble_stop.clear()
        ready_event = threading.Event()
        ready: dict[str, object] = {"ok": False, "error": ""}

        self._ble_thread = threading.Thread(
            target=self._ble_worker,
            args=(config, ready_event, ready),
            daemon=True,
        )
        self._ble_thread.start()

        wait_timeout = max(2.0, (config.timeout_ms / 1000.0) + 2.0)
        ready_event.wait(timeout=wait_timeout)

        if not ready.get("ok"):
            self._connected = False
            self.connection_changed.emit(False, "Bluetooth connection failed")
            error_message = str(ready.get("error") or "Timeout while connecting")
            self.log_message.emit(f"Bluetooth error: {error_message}")
            self._stop_ble_thread()
            return

        self._connected = True
        self.connection_changed.emit(True, "Connected via Bluetooth")
        self.log_message.emit(f"BLE connected to {address}")

    def _ble_worker(self, config: DeviceConfig, ready_event: threading.Event, ready: dict[str, object]) -> None:
        loop = asyncio.new_event_loop()
        self._ble_loop = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._ble_session(config, ready_event, ready))
        finally:
            with contextlib.suppress(Exception):
                loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            self._ble_loop = None

    async def _ble_session(self, config: DeviceConfig, ready_event: threading.Event, ready: dict[str, object]) -> None:
        address = (config.device_address or "").strip()
        characteristic = (config.bluetooth_characteristic_uuid or "").strip()

        try:
            client = BleakClient(address)
            await client.connect(timeout=max(2.0, config.timeout_ms / 1000.0))
            self._ble_client = client
        except Exception as exc:
            ready["ok"] = False
            ready["error"] = str(exc)
            ready_event.set()
            return

        ready["ok"] = True
        ready_event.set()

        if characteristic:
            try:
                await self._ble_client.start_notify(characteristic, self._on_ble_notification)
                self.log_message.emit(f"BLE notify started on characteristic {characteristic}")
            except Exception as exc:
                self.log_message.emit(f"BLE notify error: {exc}")
        else:
            self.log_message.emit("BLE connected. Set Characteristic UUID to start live notifications.")

        try:
            while not self._ble_stop.is_set():
                await asyncio.sleep(0.2)
        finally:
            if characteristic and self._ble_client is not None:
                with contextlib.suppress(Exception):
                    await self._ble_client.stop_notify(characteristic)
            if self._ble_client is not None:
                with contextlib.suppress(Exception):
                    await self._ble_client.disconnect()
            self._ble_client = None

    def _on_ble_notification(self, _sender, data: bytearray) -> None:
        text = bytes(data).decode(errors="ignore").strip()
        if not text:
            text = bytes(data).hex()
        self.raw_data_received.emit(text)
        parsed = _parse_ascii_measurement(text)
        if parsed is not None:
            self.measurement_received.emit(parsed)

    def _stop_ble_thread(self) -> None:
        self._ble_stop.set()
        if self._ble_loop is not None:
            with contextlib.suppress(Exception):
                self._ble_loop.call_soon_threadsafe(lambda: None)
        if self._ble_thread is not None and self._ble_thread.is_alive():
            self._ble_thread.join(timeout=2.0)
        self._ble_thread = None
        self._ble_client = None

