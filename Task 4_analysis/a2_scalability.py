"""
a2_scalability.py

Assignment Task 4 - Experiment A-2

Increment N from 2 to 6. At each increment, launch 10,000 requests and
report the average load of the servers in a line chart, along with the
standard deviation across servers (a measure of how evenly the hash ring
is balancing load as N grows).

Usage:
    python a2_scalability.py
"""

import argparse
import asyncio
import statistics
from collections import Counter

import aiohttp
import matplotlib.pyplot as plt

from lb_client import fire_requests, scale_to

NUM_REQUESTS = 10_000
N_VALUES = [2, 3, 4, 5, 6]


async def run_for_n(n: int):
    async with aiohttp.ClientSession() as session:
        replicas = await scale_to(session, n)
        actual_n = replicas["N"]

    if actual_n != n:
        print(f"\n--- N={n} SKIPPED (LB stuck at N={actual_n}) ---")
        return None

    print(f"\n--- N={actual_n} ---")
    elapsed, results = await fire_requests(NUM_REQUESTS)
    counts = Counter(r for r in results if not r.startswith("ERROR"))

    per_server_counts = list(counts.values())
    avg_load = statistics.mean(per_server_counts) if per_server_counts else 0
    stdev_load = statistics.pstdev(per_server_counts) if len(per_server_counts) > 1 else 0

    print(f"  Servers observed: {len(counts)} (expected {actual_n})")
    print(f"  Avg load/server: {avg_load:.1f}  |  Std dev: {stdev_load:.1f}")
    print(f"  Throughput: {NUM_REQUESTS/elapsed:.1f} req/s")

    return actual_n, avg_load, stdev_load


async def main(output_file: str, label_suffix: str):
    ns, avgs, stdevs = [], [], []

    for n in N_VALUES:
        result = await run_for_n(n)
        if result is None:
            continue
        actual_n, avg_load, stdev_load = result
        ns.append(actual_n)
        avgs.append(avg_load)
        stdevs.append(stdev_load)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.plot(ns, avgs, marker="o", color="#4C72B0")
    ax1.set_xlabel("N (number of server containers)")
    ax1.set_ylabel("Average requests handled per server")
    ax1.set_title(f"A-2: Average load vs. N{label_suffix}")
    ax1.grid(True, alpha=0.3)

    ax2.plot(ns, stdevs, marker="o", color="#C44E52")
    ax2.set_xlabel("N (number of server containers)")
    ax2.set_ylabel("Std. dev. of load across servers")
    ax2.set_title(f"A-2: Load balance quality vs. N{label_suffix}")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    print(f"\nSaved chart to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="a2_scalability.png")
    parser.add_argument("--label", default="",
                         help="Extra text appended to chart titles, "
                              "e.g. ' (modified hash functions)' for A-4")
    args = parser.parse_args()
    asyncio.run(main(args.output, args.label))