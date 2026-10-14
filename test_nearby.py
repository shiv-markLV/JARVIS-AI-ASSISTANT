import asyncio

from nearby.device_manager import DeviceManager


async def main():

    jarvis = DeviceManager(
        device_name="JARVIS Desktop",
        device_type="desktop",
    )

    print()
    print("================================")
    print("     JARVIS NEARBY SCANNER")
    print("================================")
    print()

    print("Scanning nearby JARVIS devices...")

    devices = await jarvis.scan()

    if not devices:

        print("No JARVIS devices found.")
        return

    print()
    print("Devices found:")
    print()

    for i, device in enumerate(devices, 1):

        print(
            f"{i}. "
            f"{device['device_name']} "
            f"({device['ip']})"
        )

    print()
    print("Sending connection requests...")

    results = await jarvis.request_all()

    for result in results:

        print(
            result["device_id"],
            "=>",
            result["result"],
        )


if __name__ == "__main__":
    asyncio.run(main())