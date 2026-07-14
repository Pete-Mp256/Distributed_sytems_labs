"""
main.py

Demonstrates the Consistent Hashing implementation.

Author: Mary Arop
Course: ICS 4104 - Distributed Systems

Run:
    python main.py
"""

import random
from consistent_hash import ConsistentHash


def generate_requests(n):
    """
    Generate random request IDs.

    Parameters
    ----------
    n : int
        Number of requests

    Returns
    -------
    list
        List of random request IDs.
    """

    return [random.randint(100000, 999999) for _ in range(n)]


def main():

    print("=" * 60)
    print("CONSISTENT HASHING DEMONSTRATION")
    print("=" * 60)

    # ------------------------------------------------
    # Create Hash Ring
    # ------------------------------------------------

    ring = ConsistentHash()

    print("\nCreating Consistent Hash Ring...")

    print(f"Number of Slots: {ring.slots}")
    print(f"Virtual Servers per Physical Server: {ring.virtual_servers}")

    # ------------------------------------------------
    # Add Default Servers
    # ------------------------------------------------

    print("\nAdding Physical Servers...")

    for server in range(1, 4):
        ring.add_server(server)
        print(f"Server {server} added.")

    print("\nCurrent Servers")

    ring.display_servers()

    print("\nRing Statistics")

    print(f"Occupied Slots : {ring.occupied_slots()}")

    print(f"Hash Ring Load : {ring.ring_load():.2f}%")

    # ------------------------------------------------
    # Display Virtual Servers
    # ------------------------------------------------

    print("\nVirtual Server Placement")

    ring.display_virtual_servers()

    # ------------------------------------------------
    # Generate Client Requests
    # ------------------------------------------------

    print("\nGenerating Client Requests...\n")

    requests = generate_requests(15)

    for request in requests:

        server = ring.get_server(request)

        print(
            f"Request {request} "
            f"--> Server {server}"
        )

    # ------------------------------------------------
    # Remove Server
    # ------------------------------------------------

    print("\nRemoving Server 2...")

    ring.remove_server(2)

    ring.display_servers()

    print("\nRequests After Removing Server 2\n")

    for request in requests:

        server = ring.get_server(request)

        print(
            f"Request {request}"
            f" --> Server {server}"
        )

    # ------------------------------------------------
    # Add New Server
    # ------------------------------------------------

    print("\nAdding Server 4...")

    ring.add_server(4)

    ring.display_servers()

    print("\nRequests After Adding Server 4\n")

    for request in requests:

        server = ring.get_server(request)

        print(
            f"Request {request}"
            f" --> Server {server}"
        )

    print("\nDemo Completed Successfully.")


if __name__ == "__main__":
    main()