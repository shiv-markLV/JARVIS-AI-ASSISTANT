import asyncio
import json
import socket
import platform
import uuid
from datetime import datetime

from .discovery import DISCOVERY_PORT


class JarvisReceiver:

    def __init__(
        self,
        device_name="JARVIS Device",
        device_type="phone",
        service_port=8765,
    ):
        self.device_id = str(uuid.uuid4())
        self.device_name = device_name
        self.device_type = device_type
        self.service_port = service_port

        self.running = False
        self.connected_devices = {}

    # -------------------------------------------------
    # DEVICE INFORMATION
    # -------------------------------------------------

    def get_device_info(self):

        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "hostname": socket.gethostname(),
            "online": True,
            "last_seen": datetime.now().isoformat(),
        }

    # -------------------------------------------------
    # DISCOVERY RESPONSE
    # -------------------------------------------------

    async def discovery_listener(self):

        loop = asyncio.get_running_loop()

        transport, _ = await loop.create_datagram_endpoint(
            lambda: DiscoveryProtocol(self),
            local_addr=("0.0.0.0", DISCOVERY_PORT),
            allow_broadcast=True,
        )

        print(
            f"[DISCOVERY] Listening on UDP {DISCOVERY_PORT}"
        )

        return transport

    async def respond_to_discovery(
        self,
        requester_address,
    ):

        message = {
            "service": "jarvis",
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "port": self.service_port,
        }

        data = json.dumps(message).encode("utf-8")

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        try:
            sock.sendto(
                data,
                requester_address,
            )

        finally:
            sock.close()

    # -------------------------------------------------
    # TCP REQUEST SERVER
    # -------------------------------------------------

    async def start_server(self):

        server = await asyncio.start_server(
            self.handle_client,
            "0.0.0.0",
            self.service_port,
        )

        addresses = ", ".join(
            str(sock.getsockname())
            for sock in server.sockets
        )

        print(
            f"[RECEIVER] Listening on {addresses}"
        )

        return server

    # -------------------------------------------------
    # HANDLE CONNECTION REQUEST
    # -------------------------------------------------

    async def handle_client(
        self,
        reader,
        writer,
    ):

        address = writer.get_extra_info(
            "peername"
        )

        print()
        print(
            "========================================"
        )
        print(
            "      INCOMING JARVIS REQUEST"
        )
        print(
            "========================================"
        )
        print(
            f"Device: {address}"
        )

        try:

            data = await asyncio.wait_for(
                reader.readline(),
                timeout=10,
            )

            if not data:
                writer.close()
                return

            request = json.loads(
                data.decode("utf-8")
            )

            if request.get("type") != "connection_request":

                await self.send_response(
                    writer,
                    {
                        "accepted": False,
                        "reason": "Invalid request",
                    },
                )

                writer.close()
                return

            print()
            print(
                "JARVIS wants to connect to this device."
            )

            print()
            print(
                "Allow connection?"
            )
            print(
                "[A] Accept"
            )
            print(
                "[R] Reject"
            )

            # Input ko blocking thread me run karna
            answer = await asyncio.to_thread(
                input,
                "Your choice: ",
            )

            answer = answer.strip().lower()

            if answer in ("a", "accept", "y", "yes"):

                print()
                print(
                    "[JARVIS] Connection ACCEPTED."
                )

                await self.send_response(
                    writer,
                    {
                        "accepted": True,
                        "device_info":
                            self.get_device_info(),
                    },
                )

                device_id = request.get(
                    "request_id",
                    str(uuid.uuid4()),
                )

                self.connected_devices[
                    device_id
                ] = {
                    "address": address,
                    "connected_at":
                        datetime.now().isoformat(),
                }

                print(
                    "[JARVIS] Device connected."
                )

                # Connection open rakho
                await self.keep_connection(
                    reader,
                    writer,
                )

            else:

                print()
                print(
                    "[JARVIS] Connection REJECTED."
                )

                await self.send_response(
                    writer,
                    {
                        "accepted": False,
                        "reason": "User rejected request",
                    },
                )

                writer.close()

        except asyncio.TimeoutError:

            print(
                "[JARVIS] Request timed out."
            )

            writer.close()

        except Exception as e:

            print(
                f"[RECEIVER ERROR] {e}"
            )

            writer.close()

        finally:

            try:
                await writer.wait_closed()
            except Exception:
                pass

    # -------------------------------------------------
    # SEND RESPONSE
    # -------------------------------------------------

    async def send_response(
        self,
        writer,
        response,
    ):

        data = (
            json.dumps(response)
            + "\n"
        ).encode("utf-8")

        writer.write(data)

        await writer.drain()

    # -------------------------------------------------
    # KEEP CONNECTION
    # -------------------------------------------------

    async def keep_connection(
        self,
        reader,
        writer,
    ):

        while True:

            try:

                data = await reader.readline()

                if not data:
                    break

                message = json.loads(
                    data.decode("utf-8")
                )

                message_type = message.get(
                    "type"
                )

                if message_type == "device_info":

                    await self.send_response(
                        writer,
                        {
                            "type":
                                "device_info",
                            "data":
                                self.get_device_info(),
                        },
                    )

                elif message_type == "ping":

                    await self.send_response(
                        writer,
                        {
                            "type": "pong",
                            "time":
                                datetime.now()
                                .isoformat(),
                        },
                    )

            except Exception:
                break

        print(
            "[JARVIS] Device disconnected."
        )


# -----------------------------------------------------
# UDP DISCOVERY PROTOCOL
# -----------------------------------------------------

class DiscoveryProtocol(
    asyncio.DatagramProtocol
):

    def __init__(self, receiver):

        self.receiver = receiver
        self.transport = None

    def connection_made(
        self,
        transport,
    ):

        self.transport = transport

    def datagram_received(
        self,
        data,
        addr,
    ):

        try:

            message = json.loads(
                data.decode("utf-8")
            )

            if message.get(
                "service"
            ) != "jarvis":

                return

            # Apne hi broadcast ko ignore karo
            if (
                message.get("device_id")
                == self.receiver.device_id
            ):
                return

            print()
            print(
                f"[DISCOVERY] JARVIS found at "
                f"{addr[0]}"
            )

            asyncio.create_task(
                self.receiver.respond_to_discovery(
                    addr
                )
            )

        except Exception:
            pass


# -----------------------------------------------------
# RUN RECEIVER
# -----------------------------------------------------

async def main():

    receiver = JarvisReceiver(
        device_name="JARVIS Receiver",
        device_type="desktop",
        service_port=8765,
    )

    print()
    print(
        "========================================"
    )
    print(
        "       J.A.R.V.I.S RECEIVER"
    )
    print(
        "========================================"
    )

    print(
        f"Device Name : {receiver.device_name}"
    )

    print(
        f"Device ID   : {receiver.device_id}"
    )

    print(
        f"Device Type : {receiver.device_type}"
    )

    print()

    discovery_transport = (
        await receiver.discovery_listener()
    )

    server = await receiver.start_server()

    receiver.running = True

    print()
    print(
        "[JARVIS] Receiver is ONLINE."
    )

    print(
        "[JARVIS] Waiting for nearby devices..."
    )

    print()

    try:

        async with server:

            await server.serve_forever()

    except KeyboardInterrupt:

        pass

    finally:

        discovery_transport.close()

        print(
            "[JARVIS] Receiver stopped."
        )


if __name__ == "__main__":

    asyncio.run(main())