"""
manager.py

Bridges the Task 2 ConsistentHash ring with real Docker containers:

  - Spawns/removes server containers via the Docker CLI (talking to the
    host's Docker daemon through the mounted socket).
  - Keeps a hostname <-> numeric server_id map, since the ring only deals
    in numeric IDs but Docker/the HTTP API deal in hostnames.
  - Runs a background heartbeat loop that detects failed replicas and
    spawns replacements, keeping N replicas alive at all times.
"""

import os
import time
import random
import string
import subprocess
import threading

import requests

from consistent_hash import ConsistentHash


class ServerManager:

    def __init__(self):
        self.network = os.environ.get("NETWORK_NAME", "net1")
        self.image = os.environ.get("SERVER_IMAGE", "ds-server:latest")
        self.heartbeat_interval = int(os.environ.get("HEARTBEAT_INTERVAL", "5"))

        self.ring = ConsistentHash(slots=512, virtual_servers=9)

        self.hostname_to_id = {}
        self.id_to_hostname = {}
        self._next_id = 1

        # RLock: health_check_loop calls add_servers(), which also
        # acquires this lock, from a different call site than where the
        # lock is released, so re-entrancy needs to be safe.
        self.lock = threading.RLock()


    # Docker lifecycle


    def _spawn_container(self, hostname, server_id):
        cmd = [
            "docker", "run",
            "--name", hostname,
            "--network", self.network,
            "--network-alias", hostname,
            "-e", f"SERVER_ID={server_id}",
            "-d", self.image,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[Manager] failed to start {hostname}: {result.stderr.strip()}")
            return False
        return True

    def _remove_container(self, hostname):
        subprocess.run(["docker", "stop", hostname], capture_output=True, text=True)
        subprocess.run(["docker", "rm", hostname], capture_output=True, text=True)

    def _random_hostname(self):
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"S{suffix}"


    #public API used by the Flask routes


    def get_replicas(self):
        with self.lock:
            return list(self.hostname_to_id.keys())

    def add_servers(self, n, hostnames=None):
        hostnames = hostnames or []
        if len(hostnames) > n:
            raise ValueError("Length of hostname list is more than newly added instances")

        with self.lock:
            for i in range(n):
                hostname = hostnames[i] if i < len(hostnames) else self._random_hostname()

                if hostname in self.hostname_to_id:
                    raise ValueError(f"hostname '{hostname}' is already in use")

                server_id = self._next_id
                self._next_id += 1

                if not self._spawn_container(hostname, server_id):
                    raise RuntimeError(f"could not spawn container '{hostname}'")

                self.ring.add_server(server_id)
                self.hostname_to_id[hostname] = server_id
                self.id_to_hostname[server_id] = hostname

            return list(self.hostname_to_id.keys())

    def remove_servers(self, n, hostnames=None):
        hostnames = hostnames or []
        if len(hostnames) > n:
            raise ValueError("Length of hostname list is more than removable instances")

        with self.lock:
            requested = [h for h in hostnames if h in self.hostname_to_id]
            remaining_needed = n - len(requested)

            candidates = [h for h in self.hostname_to_id if h not in requested]
            random.shuffle(candidates)
            extra = candidates[:max(remaining_needed, 0)]

            to_remove = requested + extra

            for hostname in to_remove:
                server_id = self.hostname_to_id.pop(hostname, None)
                if server_id is not None:
                    self.id_to_hostname.pop(server_id, None)
                    self.ring.remove_server(server_id)
                self._remove_container(hostname)

            return list(self.hostname_to_id.keys())

    def route_request(self, path):
        """
        Pick a server for this request via the consistent hash ring and
        forward the GET request to it.

        Returns (response, error_message). error_message is None on success.
        """
        with self.lock:
            if not self.hostname_to_id:
                return None, "no server replicas are currently available"

            request_id = random.randint(100000, 999999)
            server_id = self.ring.get_server(request_id)
            hostname = self.id_to_hostname.get(server_id)

        if hostname is None:
            return None, "no server replicas are currently available"

        try:
            resp = requests.get(f"http://{hostname}:5000/{path}", timeout=3)
            return resp, None
        except requests.RequestException as exc:
            return None, f"replica '{hostname}' is unreachable ({exc})"


    # Failure detection/self-healing


    def health_check_loop(self):
        while True:
            time.sleep(self.heartbeat_interval)

            with self.lock:
                hosts = list(self.hostname_to_id.keys())

            for hostname in hosts:
                if self._is_alive(hostname):
                    continue

                print(f"[Manager] {hostname} failed heartbeat check, replacing it")

                with self.lock:
                    server_id = self.hostname_to_id.pop(hostname, None)
                    if server_id is not None:
                        self.id_to_hostname.pop(server_id, None)
                        self.ring.remove_server(server_id)

                self._remove_container(hostname)

                try:
                    self.add_servers(1)
                except RuntimeError as exc:
                    print(f"[Manager] failed to respawn replacement for {hostname}: {exc}")

    def _is_alive(self, hostname):
        try:
            resp = requests.get(f"http://{hostname}:5000/heartbeat", timeout=2)
            return resp.status_code == 200
        except requests.RequestException:
            return False
