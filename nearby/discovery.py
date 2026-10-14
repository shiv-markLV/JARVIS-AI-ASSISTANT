import asyncio
import json
import socket
import uuid


DISCOVERY_PORT = 37020
DISCOVERY_MESSAGE = "JARVIS_DISCOVERY"


def get_local_ip():
    """
    Get the local LAN IP address.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        sock.close()


class JarvisDiscoveryProtocol(asyncio.DatagramProtocol):

    def __init__(self, callback):
        self.callback = callback
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            message = json.loads(data.decode("utf-8"))

            if message.get("service") != "jarvis":
                return

            device = {
                "device_id": message.get("device_id"),
                "device_name": message.get("device_name", "Unknown"),
                "device_type": message.get("device_type", "unknown"),
                "ip": addr[0],
                "port": message.get("port", 8765),
            }

            self.callback(device)

        except Exception:
            pass


class DiscoveryService:

    def __init__(
        self,
        device_name="JARVIS",
        device_type="desktop",
        service_port=8765,
    ):
        self.device_id = str(uuid.uuid4())
        self.device_name = device_name
        self.device_type = device_type
        self.service_port = service_port

        self.transport = None
        self.devices = {}

    async def start_listener(self, callback):

        loop = asyncio.get_running_loop()

        transport, _ = await loop.create_datagram_endpoint(
            lambda: JarvisDiscoveryProtocol(callback),
            local_addr=("0.0.0.0", DISCOVERY_PORT),
            allow_broadcast=True,
        )

        self.transport = transport

    async def broadcast(self):

        message = {
            "service": "jarvis",
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "port": self.service_port,
        }

        data = json.dumps(message).encode("utf-8")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_BROADCAST,
                1,
            )

            sock.sendto(
                data,
                ("255.255.255.255", DISCOVERY_PORT),
            )

        finally:
            sock.close()

    async def scan(self, seconds=3):

        found = {}

        def on_device(device):

            if device["device_id"] == self.device_id:
                return

            found[device["device_id"]] = device

        await self.start_listener(on_device)

        await self.broadcast()

        await asyncio.sleep(seconds)

        if self.transport:
            self.transport.close()
            self.transport = None

        return list(found.values())