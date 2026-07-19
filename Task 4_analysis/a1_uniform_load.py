"""
a1_uniform_load.py

Assignment Task 4 - Experiment A-1

Launch 10,000 async requests against the load balancer with N=3 server
containers running, and report the request count handled by each server
instance in a bar chart.

Usage:
    python a1_uniform_load.py

Assumes the LB + 3 server replicas are already up (e.g. via
`make up` / `docker-compose up` from the project root) and reachable at
http://localhost:5000.
"""

import argparse
import asyncio
from collections import Counter

import matplotlib.pyplot as plt

from lb_client import fire_requests, get_replicas, scale_to
import aiohttp

NUM_REQUESTS = 10_000
TARGET_N = 3


async def main(output_file: str, label_suffix: str):
    async with aiohttp.ClientSession() as session:
        replicas = await scale_to(session, TARGET_N)
        print(f"Confirmed N={replicas['N']} replicas: {replicas['replicas']}")

    print(f"Firing {NUM_REQUESTS} async requests at N={TARGET_N}...")
    elapsed, results = await fire_requests(NUM_REQUESTS)

    errors = [r for r in results if r.startswith("ERROR")]
    counts = Counter(r for r in results if not r.startswith("ERROR"))

    print(f"\nCompleted in {elapsed:.2f}s ({NUM_REQUESTS/elapsed:.1f} req/s)")
    print(f"Errors: {len(errors)}")
    print("Per-server counts:")
    for server_id, count in sorted(counts.items()):
        pct = 100 * count / NUM_REQUESTS
        print(f"  Server {server_id}: {count} ({pct:.1f}%)")

    # --- Bar chart ---
    labels = sorted(counts.keys())
    values = [counts[l] for l in labels]
    expected = NUM_REQUESTS / TARGET_N

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar([f"Server {l}" for l in labels], values, color="#4C72B0")
    ax.axhline(expected, color="red", linestyle="--", label=f"Ideal even split ({expected:.0f})")
    ax.set_ylabel("Requests handled")
    ax.set_title(f"A-1: Request distribution across N={TARGET_N} servers ({NUM_REQUESTS} requests){label_suffix}")
    ax.legend()

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + NUM_REQUESTS * 0.01,
                 str(val), ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    print(f"\nSaved chart to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="a1_load_distribution.png",
                         help="Output PNG filename")
    parser.add_argument("--label", default="",
                         help="Extra text appended to the chart title, "
                              "e.g. ' (modified hash functions)' for A-4")
    args = parser.parse_args()
    asyncio.run(main(args.output, args.label))
