"""
demo.py

A simplified demonstration of the Consistent Hashing implementation.

This file is intended for presentations and screenshots.
"""

from consistent_hash import ConsistentHash


def main():

    print("=" * 60)
    print("CONSISTENT HASHING DEMO")
    print("=" * 60)

    # Create the hash ring
    ring = ConsistentHash()

    # Add the default servers
    print("\nAdding Physical Servers")

    for server_id in [1, 2, 3]:
        ring.add_server(server_id)
        print(f"✓ Server {server_id} added")

    print("\nCurrent Physical Servers")
    ring.display_servers()

    print("\nHash Ring Statistics")
    print(f"Total Slots      : {ring.slots}")
    print(f"Occupied Slots   : {ring.occupied_slots()}")
    print(f"Ring Utilization : {ring.ring_load():.2f}%")

    print("\nSample Request Mapping")
    print("-" * 35)

    requests = [
        123456,
        234567,
        345678,
        456789,
        567890
    ]

    for request in requests:

        server = ring.get_server(request)

        print(
            f"Request {request} "
            f"→ Server {server}"
        )

    print("\nRemoving Server 2...")

    ring.remove_server(2)

    print("\nUpdated Servers")
    ring.display_servers()

    print("\nRequest Mapping After Removal")
    print("-" * 35)

    for request in requests:

        server = ring.get_server(request)

        print(
            f"Request {request} "
            f"→ Server {server}"
        )

    print("\nAdding Server 4...")

    ring.add_server(4)

    print("\nUpdated Servers")
    ring.display_servers()

    print("\nFinal Request Mapping")
    print("-" * 35)

    for request in requests:

        server = ring.get_server(request)

        print(
            f"Request {request} "
            f"→ Server {server}"
        )

    print("\nDemo Complete!")


if __name__ == "__main__":
    main()