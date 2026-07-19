"""
lb_client.py

Shared helpers for talking to the Load Balancer container over HTTP,
per the API contract defined in the assignment spec:

    GET    /rep        -> {"message": {"N": int, "replicas": [str, ...]}, "status": ...}
    POST   /add        -> body {"n": int, "hostnames": [str, ...]}
    DELETE /rm         -> body {"n": int, "hostnames": [str, ...]}
    GET    /<path>     -> routed to a server replica (e.g. /home)

These scripts don't care how Task 3 is implemented internally -- they
only assume the LB is reachable at BASE_URL and honours this contract.
"""

import asyncio
import re
import time

import aiohttp

BASE_URL = "http://localhost:5000"

SERVER_ID_RE = re.compile(r"Server:\s*([^\"]+)")


async def get_replicas(session: aiohttp.ClientSession) -> dict:
    """Call GET /rep and return the parsed message dict: {N, replicas}."""
    async with session.get(f"{BASE_URL}/rep") as resp:
        data = await resp.json()
        return data["message"]


async def add_servers(session: aiohttp.ClientSession, n: int, hostnames=None) -> dict:
    """Call POST /add to scale up by n instances."""
    payload = {"n": n}
    if hostnames:
        payload["hostnames"] = hostnames
    async with session.post(f"{BASE_URL}/add", json=payload) as resp:
        return await resp.json()


async def remove_servers(session: aiohttp.ClientSession, n: int, hostnames=None) -> dict:
    """Call DELETE /rm to scale down by n instances."""
    payload = {"n": n}
    if hostnames:
        payload["hostnames"] = hostnames
    async with session.request("DELETE", f"{BASE_URL}/rm", json=payload) as resp:
        return await resp.json()


async def scale_to(session: aiohttp.ClientSession, target_n: int, retries: int = 3) -> dict:
    """
    Scale the currently-managed replica set up or down to exactly target_n
    servers, using /rep to check current count first.

    Retries a few times if a scale-up/down silently doesn't reach the
    target (e.g. a transient container-spawn failure), and prints a
    warning if it still hasn't converged after all retries -- so callers
    don't silently plot the wrong N.
    """
    for attempt in range(1, retries + 1):
        current = await get_replicas(session)
        current_n = current["N"]

        if current_n == target_n:
            return current

        if target_n > current_n:
            result = await add_servers(session, target_n - current_n)
        else:
            result = await remove_servers(session, current_n - target_n)

        if result.get("status") != "successful":
            print(f"    [warn] scale attempt {attempt} to N={target_n} "
                  f"returned: {result}")

        # give the LB a moment to finish spawning/removing containers
        await asyncio.sleep(2)

    final = await get_replicas(session)
    if final["N"] != target_n:
        print(f"    [warn] could not reach N={target_n} after {retries} "
              f"attempts, stuck at N={final['N']}. Results for this N "
              f"will be skipped.")
    return final


def _extract_server_id(response_json: dict) -> str:
    """
    Pull the server identifier out of a routed response, e.g.
    {"message": "Hello from Server: 3", "status": "successful"} -> "3"
    """
    message = response_json.get("message", "")
    match = SERVER_ID_RE.search(message)
    return match.group(1) if match else "UNKNOWN"


async def _fire_one(session: aiohttp.ClientSession, path: str, sem: asyncio.Semaphore):
    async with sem:
        try:
            async with session.get(f"{BASE_URL}{path}") as resp:
                data = await resp.json()
                return _extract_server_id(data)
        except Exception as exc:  # noqa: BLE001
            return f"ERROR:{exc}"


async def fire_requests(num_requests: int, path: str = "/home", concurrency: int = 200):
    """
    Fire `num_requests` concurrent async GET requests at the LB's routed
    endpoint and return (elapsed_seconds, list_of_server_ids).

    concurrency caps how many requests are in flight at once so we don't
    exhaust local sockets / overwhelm the LB unrealistically.
    """
    sem = asyncio.Semaphore(concurrency)
    connector = aiohttp.TCPConnector(limit=concurrency)

    async with aiohttp.ClientSession(connector=connector) as session:
        start = time.perf_counter()
        tasks = [_fire_one(session, path, sem) for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

    return elapsed, results