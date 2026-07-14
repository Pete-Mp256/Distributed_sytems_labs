"""
test_consistent_hash.py

Unit tests for the Consistent Hash implementation.

Run using:

python -m unittest test_consistent_hash.py
"""

import unittest

from consistent_hash import ConsistentHash


class TestConsistentHash(unittest.TestCase):

    def setUp(self):
        """
        Create a fresh hash ring before every test.
        """
        self.hash_ring = ConsistentHash()

    # ----------------------------------------
    # Hash Function Tests
    # ----------------------------------------

    def test_request_hash_range(self):
        """
        Request hash should always be between 0 and 511.
        """

        slot = self.hash_ring.request_hash(123456)

        self.assertGreaterEqual(slot, 0)
        self.assertLess(slot, 512)

    def test_server_hash_range(self):
        """
        Server hash should always be between 0 and 511.
        """

        slot = self.hash_ring.server_hash(1, 0)

        self.assertGreaterEqual(slot, 0)
        self.assertLess(slot, 512)

    # ----------------------------------------
    # Server Tests
    # ----------------------------------------

    def test_add_server(self):
        """
        Test adding a server.
        """

        self.hash_ring.add_server(1)

        self.assertIn(1, self.hash_ring.servers)

    def test_remove_server(self):
        """
        Test removing a server.
        """

        self.hash_ring.add_server(1)

        self.hash_ring.remove_server(1)

        self.assertNotIn(1, self.hash_ring.servers)

    # ----------------------------------------
    # Virtual Server Tests
    # ----------------------------------------

    def test_virtual_servers_created(self):
        """
        One server should create nine virtual servers.
        """

        self.hash_ring.add_server(1)

        count = 0

        for slot in self.hash_ring.ring:

            if slot is not None:

                server_id, replica = slot

                if server_id == 1:
                    count += 1

        self.assertEqual(count, 9)

    # ----------------------------------------
    # Request Mapping
    # ----------------------------------------

    def test_request_mapping(self):
        """
        Requests should map to an existing server.
        """

        self.hash_ring.add_server(1)
        self.hash_ring.add_server(2)
        self.hash_ring.add_server(3)

        server = self.hash_ring.get_server(765432)

        self.assertIn(server, [1, 2, 3])

    # ----------------------------------------
    # Occupied Slots
    # ----------------------------------------

    def test_occupied_slots(self):
        """
        Three servers should occupy 27 slots.
        """

        self.hash_ring.add_server(1)
        self.hash_ring.add_server(2)
        self.hash_ring.add_server(3)

        self.assertEqual(
            self.hash_ring.occupied_slots(),
            27
        )

    # ----------------------------------------
    # Ring Utilization
    # ----------------------------------------

    def test_ring_load(self):
        """
        Ring utilization should be greater than zero.
        """

        self.hash_ring.add_server(1)

        self.assertGreater(
            self.hash_ring.ring_load(),
            0
        )

    # ----------------------------------------
    # Remove All Servers
    # ----------------------------------------

    def test_remove_everything(self):
        """
        Removing all servers should leave the ring empty.
        """

        self.hash_ring.add_server(1)
        self.hash_ring.add_server(2)
        self.hash_ring.add_server(3)

        self.hash_ring.remove_server(1)
        self.hash_ring.remove_server(2)
        self.hash_ring.remove_server(3)

        self.assertEqual(
            self.hash_ring.occupied_slots(),
            0
        )


if __name__ == "__main__":
    unittest.main()