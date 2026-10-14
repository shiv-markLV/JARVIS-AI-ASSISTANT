import asyncio
import json
import uuid


class JarvisConnection:

    def __init__(self):
        self.connections = {}

    async def send_request(self, device):

        reader = None
        writer = None

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    device["ip"],
                    device["port"],
                ),
                timeout=5,
            )

            request = {
                "type": "connection_request",
                "request_id": str(uuid.uuid4()),
                "service": "jarvis",
                "message": "JARVIS wants to connect.",
            }

            writer.write(
                (json.dumps(request) + "\n").encode("utf-8")
            )

            await writer.drain()

            response = await asyncio.wait_for(
                reader.readline(),
                timeout=30,
            )

            if not response:
                return {
                    "success": False,
                    "reason": "No response",
                }

            result = json.loads(
                response.decode("utf-8")
            )

            if result.get("accepted") is True:

                device_id = device["device_id"]

                self.connections[device_id] = {
                    "device": device,
                    "connected": True,
                }

                return {
                    "success": True,
                    "device": device,
                }

            return {
                "success": False,
                "reason": "Request rejected",
            }

        except Exception as e:

            return {
                "success": False,
                "reason": str(e),
            }

        finally:

            if writer:
                writer.close()

                try:
                    await writer.wait_closed()
                except Exception:
                    pass

    def connected_devices(self):

        return [
            item["device"]
            for item in self.connections.values()
            if item.get("connected")
        ]

    def disconnect(self, device_id):

        self.connections.pop(
            device_id,
            None,
        )