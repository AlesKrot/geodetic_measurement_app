from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DeviceConfig:
    transport: str = "RS-232"
    device_name: str = ""
    device_address: str = ""
    port: str = "auto"
    baud_rate: int = 9600
    protocol: str = "ASCII"
    data_bits: int = 8
    parity: str = "None"
    stop_bits: str = "1"
    flow_control: str = "None"
    terminator: str = "CRLF"
    timeout_ms: int = 1000
    can_bitrate: int = 500000
    can_identifier: str = "0x100"
    can_extended_id: bool = False
    bluetooth_characteristic_uuid: str = ""
    bluetooth_scan_timeout_s: float = 4.0
