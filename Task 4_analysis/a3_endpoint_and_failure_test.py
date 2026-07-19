"""
a3_endpoint_and_failure_test.py

Assignment Task 4 - Experiment A-3

Test all endpoints of the load balancer (/rep, /add, /rm, /<path>) and
demonstrate that when a server container fails, the load balancer spawns
a replacement quickly. Requires the `docker` CLI on PATH (this script
kills a container directly to simulate an outage, bypassing the LB).

Usage:
    python a3_endpoint_and_failure_test.py
"""

import asyncio
import subprocess
import time

import aiohttp

from lb_client import add_servers, get_replicas, remove_servers

POLL_INTERVAL = 1.0
POLL_TIMEOUT = 30.0


def docker_kill(container_name: str):
    print(f"  $ docker kill {container_name}")
    subprocess.run(["docker", "kill", container_name], check=False,
                    capture_output=True, text=True)


async def test_rep(session):
    print("\n[1] GET /rep")
    replicas = await get_replicas(session)
    print(f"    N={replicas['N']}  replicas={replicas['replicas']}")
    return replicas


async def test_add(session):
    print("\n[2] POST /add  (n=1, hostnames=['A3TestServer'])")
    result = await add_servers(session, 1, hostnames=["A3TestServer"])
    print(f"    -> {result}")
    return result


async def test_rm(session):
    print("\n[3] DELETE /rm  (n=1, hostnames=['A3TestServer'])")
    result = await remove_servers(session, 1, hostnames=["A3TestServer"])
    print(f"    -> {result}")
    return result


async def test_route(session):
    print("\n[4] GET /home  (routed request)")
    async with session.get("http://localhost:5000/home") as resp:
        data = await resp.json()
        print(f"    -> status={resp.status}  body={data}")


async def test_bad_route(session):
    print("\n[5] GET /nonexistent  (expect 400 error)")
    async with session.get("http://localhost:5000/nonexistent") as resp:
        data = await resp.json()
        print(f"    -> status={resp.status}  body={data}")


async def test_failure_recovery(session):
    print("\n[6] Failure recovery test")
    before = await get_replicas(session)
    print(f"    Before: N={before['N']}  replicas={before['replicas']}")

    if not before["replicas"]:
        print("    No replicas to kill, skipping.")
        return

    victim = before["replicas"][0]
    print(f"    Killing container '{victim}' directly via docker to simulate a crash...")
    kill_time = time.perf_counter()
    docker_kill(victim)

    # Poll /rep until the LB has restored N replicas with a NEW hostname set
    recovered = False
    elapsed = 0.0
    while elapsed < POLL_TIMEOUT:
        await asyncio.sleep(POLL_INTERVAL)
        elapsed = time.perf_counter() - kill_time
        current = await get_replicas(session)
        if current["N"] >= before["N"] and victim not in current["replicas"]:
            recovered = True
            print(f"    Recovered after {elapsed:.1f}s: N={current['N']}  replicas={current['replicas']}")
            break

    if not recovered:
        print(f"    NOT recovered within {POLL_TIMEOUT}s -- check LB's heartbeat/respawn logic.")


async def main():
    async with aiohttp.ClientSession() as session:
        await test_rep(session)
        await test_add(session)
        await test_rep(session)
        await test_rm(session)
        await test_rep(session)
        await test_route(session)
        await test_bad_route(session)
        await test_failure_recovery(session)

    print("\nAll endpoint + failure-recovery tests complete. "
          "Paste this output (or screenshots) into your README under Task 4 / A-3.")


if __name__ == "__main__":
    asyncio.run(main())
