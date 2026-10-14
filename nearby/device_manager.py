import asyncio

from .discovery import DiscoveryService
from .connection import JarvisConnection
from .permissions import PermissionManager
from .security import SecurityManager


class DeviceManager:

    def __init__(
        self,
        device_name="JARVIS",
        device_type="desktop",
    ):

        self.discovery = DiscoveryService(
            device_name=device_name,
            device_type=device_type,
            service_port=8765,
        )

        self.connection = JarvisConnection()
        self.security = SecurityManager()
        self.permissions = PermissionManager()

        self.devices = {}

    async def scan(self):

        devices = await self.discovery.scan(
            seconds=3
        )

        for device in devices:

            device_id = device["device_id"]

            self.devices[device_id] = device

        return devices

    async def request_connection(
        self,
        device_id,
    ):

        device = self.devices.get(device_id)

        if not device:
            return {
                "success": False,
                "reason": "Device not found",
            }

        result = await self.connection.send_request(
            device
        )

        if result.get("success"):

            self.permissions.create_permissions(
                device_id
            )

        return result

    async def request_all(self):

        results = []

        for device_id in list(self.devices):

            result = await self.request_connection(
                device_id
            )

            results.append({
                "device_id": device_id,
                "result": result,
            })

        return results

    def connected_devices(self):

        return self.connection.connected_devices()

    def get_device_info(self, device_id):

        return self.devices.get(device_id)

    def get_permissions(self, device_id):

        return self.permissions.get_permissions(
            device_id
        )

    def disconnect(self, device_id):

        self.connection.disconnect(
            device_id
        )