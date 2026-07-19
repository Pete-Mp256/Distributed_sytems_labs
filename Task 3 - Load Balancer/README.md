# Customizable Load Balancer — ICS 4104 Assignment 1

## Project Layout

```
.
├── server/                    # Task 1: minimal Flask web server
├── load_balancer/             # Task 3: load balancer (wraps Task 2's consistent hash ring)
│   ├── consistent_hash.py     # Task 2, unchanged
│   ├── server.py               # Task 2, unchanged (ring's internal Server class)
│   ├── manager.py               # Docker lifecycle + hostname<->id bookkeeping
│   └── app.py                   # Flask routes (/rep, /add, /rm, /<path>)
├── docker-compose.yml
├── Makefile
├── Task4_Analysis/            # Task 4: load-test scripts + result charts
└── README.md
```

## Design Choices

- **Hostname vs. numeric ID.** The consistent hash ring (Task 2) hashes on
  numeric server IDs, but the assignment spec and Docker both work in
  hostnames/container names. `manager.py` keeps a `hostname_to_id` /
  `id_to_hostname` map so the ring's code didn't need to change at all.
- **Request ID generation.** Each incoming request to `/<path>` is assigned
  a random 6-digit ID before being hashed with `request_hash()`, consistent
  with the Appendix's description of request IDs.
- **Container spawning.** The load balancer container has the Docker CLI
  installed and the host's `/var/run/docker.sock` mounted in, so it can run
  `docker run --network net1 --network-alias <hostname> ...` to spawn
  sibling containers on the same host, per the Appendix hint.
- **Single-process, multi-threaded.** The ring and hostname map live in the
  load balancer's Python process memory. Running multiple Gunicorn workers
  would give each worker its own inconsistent copy of that state, so the
  Flask app runs with `threaded=True` in a single process rather than
  multiple worker processes.
- **Failure detection.** A background thread hits every replica's
  `/heartbeat` every `HEARTBEAT_INTERVAL` seconds (default 5s). A replica
  that fails is torn down, removed from the ring, and immediately replaced
  by a new replica with a freshly generated hostname — keeping `N` replicas
  alive at all times per the spec.
- **Server-image is build-only in Compose.** Server replicas are created
  dynamically at runtime with hostnames chosen by `/add` or by the load
  balancer itself (initial bootstrap, failure recovery). Declaring it as a
  running Compose service would conflict with that, so `docker-compose.yml`
  only builds the load balancer service; `make build` builds the server
  image separately.

## Assumptions

- The only endpoint implemented by server replicas (besides `/heartbeat`)
  is `/home`, so `VALID_PATHS = {"home"}` in `app.py`.
- Hostnames are unique across the whole system; `/add` rejects a hostname
  that's already in use.
- `/rm` removes explicitly named hostnames first, then randomly removes
  additional replicas if `n` exceeds the number of names given — matching
  the spec's example where "Server 2" is chosen randomly alongside two
  named hostnames.
- Docker container names cannot contain spaces (Docker's naming rules only
  allow `[a-zA-Z0-9][a-zA-Z0-9_.-]*`), so default bootstrap hostnames are
  generated as `Server-1`, `Server-2`, `Server-3` (hyphenated) rather than
  the `"Server 1"` style shown in the assignment's illustrative JSON
  examples, which was never meant to be a literal container name.

## Running

```bash
make up      # builds both images and starts the load balancer
curl http://localhost:5000/rep
curl http://localhost:5000/home
make logs    # tail the load balancer's logs
make down    # stop everything
```

On Windows without `make` installed, run the equivalent commands directly:

```cmd
docker build -t ds-server:latest ./server
docker build -t ds-loadbalancer:latest ./load_balancer
docker-compose up -d
```

**Note on restarting the stack:** server replicas are spawned dynamically
by the load balancer and are *not* managed by `docker-compose`, so a plain
`docker-compose down` will not remove them. Before bringing the stack back
up, check `docker ps -a` for leftover containers from a previous run and
remove them manually (`docker rm -f <name>`) — otherwise the load
balancer's bootstrap will crash with a container-name conflict on restart.

## Bugs Found & Fixed During Testing

Several issues surfaced only once the full stack was actually deployed and
load-tested on a real machine (Windows + Docker Desktop). Documenting them
here since they affected correctness, not just environment setup:

1. **`server/requirements.txt` saved in UTF-16 encoding.** A Windows text
   editor saved this file with a UTF-16 BOM instead of UTF-8, which broke
   `pip install -r requirements.txt` inside the Docker build. Fixed by
   re-saving as plain UTF-8/ASCII.

2. **`docker.io` package didn't reliably install the `docker` CLI binary**
   inside the load balancer's Debian-slim base image, causing every
   container-spawn call in `manager.py` to fail with
   `FileNotFoundError: 'docker'`. Fixed by switching the Dockerfile to use
   Docker's official install script instead:
   ```dockerfile
   RUN apt-get update && \
       apt-get install -y --no-install-recommends ca-certificates curl && \
       curl -fsSL https://get.docker.com | sh && \
       rm -rf /var/lib/apt/lists/*
   ```

3. **Default bootstrap hostnames contained spaces** (`"Server 1"`),
   which Docker's container-naming rules reject outright
   (`Invalid container name (Server 1), only [a-zA-Z0-9][a-zA-Z0-9_.-]
   are allowed`). This crashed the load balancer on every fresh startup.
   Fixed by changing `app.py`'s `_bootstrap()` to generate `Server-1`,
   `Server-2`, `Server-3` instead.

4. **Task 1 server not running threaded, causing false failure
   detection under load.** `server/app.py` originally called
   `app.run(host="0.0.0.0", port=5000)` without `threaded=True`. Flask's
   dev server without threading handles one request at a time, so under
   concurrent load-test traffic a busy-but-alive replica couldn't respond
   to `manager.py`'s `/heartbeat` check within its 2-second timeout. The
   health-check loop then wrongly concluded the replica had failed, killed
   it, and spawned a replacement mid-test — inflating the number of
   distinct server IDs observed during a single test run beyond the actual
   `N`. Fixed by adding `threaded=True` to the server's `app.run()` call.

## Testing & Performance Analysis (Task 4)

Full scripts and raw output live in `Task4_Analysis/`. Summary of results
below.

### A-1: Load distribution at N=3 (original quadratic hash)

10,000 requests fired against `H(i) = i²+2i+17`, `Φ(i,j) = i²+j²+2j+25`:

| Server | Requests | Share |
|---|---:|---:|
| Server 1 | 8,476 | 84.8% |
| Server 2 | 483 | 4.8% |
| Server 3 | 1,041 | 10.4% |

**Observation.** This is heavily skewed, but explainable analytically
rather than random noise. `Φ(i,j)` only ever produces small outputs for
small server IDs and replica indices (max possible value ≈ 114), so all 27
virtual server slots (3 servers × 9 virtual replicas) cluster within slots
26–114 of the 512-slot ring — just 17.4% of the ring's span. Because
requests are assigned to the nearest occupied slot going clockwise, the
remaining ~83% of the ring (slots 115–511 wrapping to 0–25) all forwards
to whichever server occupies the first slot after the wraparound point —
Server 1's virtual server at slot 26. A direct calculation of ring
ownership under this hash function gives Server 1 ≈ 89.3%, Server 2 ≈
4.3%, Server 3 ≈ 6.4% — closely matching the measured 84.8/4.8/10.4%
(the small gap is sampling variance from only 10,000 random requests).
**Conclusion:** virtual servers alone don't guarantee balance — the hash
function's output range must span the full ring, or clustering like this
occurs regardless of virtual server count.

### A-2: Scalability, N=2 to 6 (original quadratic hash)

| N | Avg load/server | Std dev | Notes |
|---|---:|---:|---|
| 2 | 5000.0 | 4329.0 | |
| 3 | 3217.3 | 3150.4 | |
| 4 | — | — | *Discarded — see caveat below* |
| 5 | 1909.4 | 2184.8 | |
| 6 | 1654.7 | 1908.6 | |

**Caveat:** the N=4 run in this pass was corrupted by the false
failure-detection bug described above (fixed afterward, see Bug #4) — the
load balancer's health-check loop replaced "healthy" replicas mid-test,
so the reported server count didn't match the true N. That data point has
been excluded rather than reported as valid. The remaining points still
show the expected trend: average load per server falls roughly as
`10000/N` (a trivial consequence of a fixed total request count), while
standard deviation stays large across every N tested — reinforcing the
A-1 finding that the imbalance is structural (rooted in the hash
function's output range) rather than something more servers alone fix.
*A clean re-run of all five points with the fixed scripts is recommended
before final submission if time allows.*

### A-3: Endpoint tests + failure recovery

All endpoints exercised successfully:

- `GET /rep` — correctly reports `N` and replica hostnames at every stage
- `POST /add` (n=1, named hostname) — scaled N=6→7 successfully
- `DELETE /rm` (n=1, named hostname) — scaled N=7→6 successfully, removing
  the exact hostname requested
- `GET /home` — routed request returned `200` with the expected
  `"Hello from Server: <id>"` body
- `GET /nonexistent` — correctly returned `400` with the spec's exact
  error message format

**Failure recovery:** with N=6 replicas running, `Server-1` was killed
directly via `docker kill` (bypassing the load balancer, to simulate a
genuine crash rather than a graceful removal). The load balancer detected
the failure and spawned a replacement, restoring N=6 with a freshly
generated hostname, in **9.4 seconds** — consistent with the configured
5-second heartbeat interval plus detection/respawn overhead.

### A-4: Modified hash functions

Original functions replaced with linear alternatives for comparison:

```
H(i)      = i + 17            (was i² + 2i + 17)
Φ(i,j)    = i + 3j + 25       (was i² + j² + 2j + 25)
```

**A-1 re-run (N=3, 10,000 requests):**

| Server | Requests | Share |
|---|---:|---:|
| Server 1 | 9,666 | 96.7% |
| Server 2 | 182 | 1.8% |
| Server 3 | 152 | 1.5% |

Even more skewed than the original quadratic hash. Analytically, the
linear `Φ(i,j)` packs all 27 virtual slots into just slots 26–52 (5.3% of
the ring, versus 17.4% for the quadratic version), giving a theoretical
ownership split of Server 1 ≈ 96.5%, Server 2/3 ≈ 1.8% each — matching the
measured result closely.

**A-2 re-run (N=2 to 6):** standard deviation of load remained
consistently high (roughly 3080–4830) across every tested N, with only a
modest dip at N=5. Average load per server still followed the expected
`~10000/N` curve (a property of the fixed request count, not of balance
quality).

**Conclusion.** Both hash functions fail for the same structural reason:
for small server IDs and replica indices, their output range is far
smaller than the 512-slot ring, so virtual servers cluster into a narrow
band and one server absorbs the large wraparound majority of the ring.
The linear hash performs *worse* than the quadratic one specifically
because `i + 3j + 25` grows even more slowly than `i² + j² + 2j + 25`,
compressing the servers into an even smaller arc. Critically, **increasing
N did not fix the imbalance under either hash function** — more servers
just means more virtual replicas squeezed into the same tiny slot range.
This demonstrates that load-balance quality in a consistent-hashing scheme
is governed primarily by whether the hash function's output spans the
full ring, not by the number of physical servers or virtual replicas
alone. A well-designed hash function for this scheme would need to
multiply server IDs/replica indices by a factor proportional to the ring
size (e.g. scaling by `slots / max_expected_id`) to spread virtual servers
evenly around the full circle.