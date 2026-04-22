from __future__ import annotations

from geodetic_app.models.device_config import DeviceConfig
from geodetic_app.services.connection_service import ConnectionService


def test_connection_service_connect_disconnect() -> None:
    service = ConnectionService()
    service.connect_device(DeviceConfig(transport="bluetooth"))
    assert service.is_connected is True
    service.disconnect_device()
    assert service.is_connected is False
