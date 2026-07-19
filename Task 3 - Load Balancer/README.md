# Customizable Load Balancer — ICS 4104 Assignment 1

## Project Layout

```
.
├── server/            # Task 1: minimal Flask web server
├── load_balancer/      # Task 3: load balancer (wraps Task 2's consistent hash ring)
│   ├── consistent_hash.py   # Task 2, unchanged
│   ├── server.py             # Task 2, unchanged (ring's internal Server class)
│   ├── manager.py            # NEW: Docker lifecycle + hostname<->id bookkeeping
│   └── app.py                 # NEW: Flask routes (/rep, /add, /rm, /<path>)
├── docker-compose.yml
├── Makefile
└── README.md
```

## Design Choices

- **Hostname vs. numeric ID.** The consistent hash ring (Task 2) hashes on
  numeric server IDs, but the assignment spec and Docker both work in
  hostnames/container names. `manager.py` keeps a `hostname_to_id` /
  `id_to_hostname` map so the ring's code didn't need to change at all.
- **Request ID generation.** Each incoming request to `/<path>` is assigned
  a random 6-digit ID before being hashed with `request_hash()`, consistent
  with the Appendix's description of request IDs and with the approach
  already used in `main.py`/`demo.py`.
- **Container spawning.** The load balancer container has the Docker CLI
  installed and the host's `/var/run/docker.sock` mounted in, so it can run
  `docker run --network net1 --network-alias <hostname> ...` to spawn
  sibling containers on the same host, per the Appendix hint.
- **Single-process, multi-threaded.** The ring and hostname map live in the
  load balancer's Python process memory. Running multiple Gunicorn workers
  would give each worker its own inconsistent copy of that state, so the
  Flask app runs with `threaded=True` in a single process rather than
  multiple worker processes. This is sufficient for the assignment's load
  tests (10,000 async requests) since Flask's dev server can serve many
  concurrent requests when threaded.
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
  is `/home`, so `VALID_PATHS = {"home"}` in `app.py`. If more server
  endpoints are added, extend this set.
- Hostnames are unique across the whole system; `/add` rejects a hostname
  that's already in use.
- `/rm` removes explicitly named hostnames first, then randomly removes
  additional replicas if `n` exceeds the number of names given — matching
  the spec's example where "Server 2" is chosen randomly alongside two
  named hostnames.

## Running

```bash
make up      # builds both images and starts the load balancer
curl http://localhost:5000/rep
curl http://localhost:5000/home
make logs    # tail the load balancer's logs
make down    # stop everything
```

## Testing & Performance Analysis (Task 4)

Fill in after running the experiments:

- **A-1 (10,000 requests, N=3):** bar chart of request count per server +
  observations on distribution evenness.
- **A-2 (N=2..6, 10,000 requests each):** line chart of average load per
  server across increasing N + scalability discussion.
- **A-3 (failure recovery):** exercise `/rep`, `/add`, `/rm`, then kill a
  replica container directly (`docker kill <hostname>`) and show `/rep`
  reflecting a fresh replacement shortly after.
- **A-4 (modified hash functions):** re-run A-1/A-2 with altered
  `H(i)`/`Φ(i,j)` in `consistent_hash.py` and compare distributions.
