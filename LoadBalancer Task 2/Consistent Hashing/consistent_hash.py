"""
Implements a Consistent Hash Ring using virtual servers.

Number of slots (M) = 512
Physical servers (N) = 3
Virtual servers per server (K) = 9

Request Hash:
H(i) = i² + 2i + 17

Virtual Server Hash:
Φ(i,j) = i² + j² + 2j + 25
"""

from server import Server

class ConsistentHash:
    """
    Implements a consistent hash ring.
    """

    def __init__(self, slots=512, virtual_servers=9):
        """
        Initialize the hash ring.

        Parameters
        ----------
        slots : int
            Total slots in the ring.

        virtual_servers : int
            Number of virtual servers per physical server.
        """

        self.slots = slots
        self.virtual_servers = virtual_servers

        # Circular hash ring
        self.ring = [None] * slots

        # Dictionary of physical servers
        self.servers = {}

    # -------------------------------------------------
    # Hash Functions
    # -------------------------------------------------

    def request_hash(self, request_id):
        """
        Hash a client request.

        H(i)=i²+2i+17
        """

        return (request_id ** 2 + 2 * request_id + 17) % self.slots

    def server_hash(self, server_id, replica):
        """
        Hash a virtual server.

        Φ(i,j)=i²+j²+2j+25
        """

        return (
            server_id ** 2
            + replica ** 2
            + 2 * replica
            + 25
        ) % self.slots

    # -------------------------------------------------
    # Collision Resolution
    # -------------------------------------------------

    def linear_probe(self, index):
        """
        Resolve collisions using linear probing.
        """

        start = index

        while self.ring[index] is not None:
            index = (index + 1) % self.slots

            if index == start:
                raise Exception("Hash ring is full.")

        return index

    # -------------------------------------------------
    # Add Server
    # -------------------------------------------------

    def add_server(self, server_id):
        """
        Add a physical server and its virtual servers.
        """

        if server_id in self.servers:
            print(f"Server {server_id} already exists.")
            return

        server = Server(server_id)

        self.servers[server_id] = server

        for replica in range(self.virtual_servers):

            index = self.server_hash(server_id, replica)

            if self.ring[index] is not None:
                index = self.linear_probe(index)

            self.ring[index] = (server_id, replica)

    # -------------------------------------------------
    # Remove Server
    # -------------------------------------------------

    def remove_server(self, server_id):
        """
        Remove a server and all its virtual servers.
        """

        if server_id not in self.servers:
            print("Server does not exist.")
            return

        for i in range(self.slots):

            if self.ring[i] is not None:

                sid, replica = self.ring[i]

                if sid == server_id:
                    self.ring[i] = None

        del self.servers[server_id]

    # -------------------------------------------------
    # Find Responsible Server
    # -------------------------------------------------

    def get_server(self, request_id):
        """
        Find the server responsible for a request.
        """

        request_slot = self.request_hash(request_id)

        index = request_slot

        while self.ring[index] is None:
            index = (index + 1) % self.slots

            if index == request_slot:
                return None

        server_id, replica = self.ring[index]

        return server_id

    # -------------------------------------------------
    # Utility Methods
    # -------------------------------------------------

    def display_servers(self):
        """
        Display physical servers.
        """

        print("\nPhysical Servers")

        for server in self.servers.values():
            print(server)

    def display_virtual_servers(self):
        """
        Print every occupied slot.
        """

        print("\nVirtual Servers")

        for slot in range(self.slots):

            if self.ring[slot] is not None:

                server_id, replica = self.ring[slot]

                print(
                    f"Slot {slot:3} "
                    f"-> Server {server_id} "
                    f"(Replica {replica})"
                )

    def occupied_slots(self):
        """
        Return occupied slots.
        """

        return sum(
            1
            for slot in self.ring
            if slot is not None
        )

    def ring_load(self):
        """
        Percentage utilization.
        """

        return (
            self.occupied_slots()
            / self.slots
        ) * 100