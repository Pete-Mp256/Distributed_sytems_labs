# A-4: Modified Hash Functions

Experiment A-4 asks you to swap out H(i) and Φ(i,j), then re-run A-1 and
A-2 and compare the observations.

## 1. The functions to swap

Your Task 2 module (`consistent_hash.py`) currently defines:

```python
def request_hash(self, request_id):
    return (request_id ** 2 + 2 * request_id + 17) % self.slots

def server_hash(self, server_id, replica):
    return (server_id ** 2 + replica ** 2 + 2 * replica + 25) % self.slots
```

For A-4, temporarily replace them with a **deliberately weaker** pair of
functions to see how much distribution quality depends on the hash
function's spread. A simple, commonly-used comparison is a plain linear
hash instead of the quadratic one:

```python
def request_hash(self, request_id):
    # A-4: linear hash instead of quadratic -- clusters more, spreads less
    return (request_id + 17) % self.slots

def server_hash(self, server_id, replica):
    # A-4: linear hash instead of quadratic
    return (server_id + replica * 3 + 25) % self.slots
```

Whoever owns Task 3 needs to apply this same change to whatever copy of
`consistent_hash.py` the load balancer container actually imports, then
rebuild/redeploy (`make down && make up`, or equivalent).

## 2. Re-run A-1 and A-2 with new output files

Once the LB is redeployed with the modified hash functions:

```bash
python a1_uniform_load.py --output a4_a1_modified_hash.png --label " (modified hash)"
python a2_scalability.py  --output a4_a2_modified_hash.png --label " (modified hash)"
```

This keeps your original A-1/A-2 charts (`a1_load_distribution.png`,
`a2_scalability.png`) intact for comparison against the modified-hash
versions.

## 3. What to write up in the README

Compare the two sets of charts and discuss:

- **Distribution evenness**: did the standard deviation across servers
  (from A-2's second chart) go up or down with the modified hash?
  A weaker/more linear hash function tends to cluster nearby request IDs
  into nearby slots, which can concentrate load unevenly if your test
  request IDs aren't uniformly random.
- **Collision rate**: did more virtual servers collide during ring
  construction (check how often `linear_probe` was triggered)?
- **Scalability trend**: does the average-load-vs-N line still follow
  the expected ~10000/N curve, or does it degrade at higher N?

There's no single "correct" outcome here -- the point of A-4 is to show
you understand *why* the quadratic hash functions in the original spec
were chosen (better spread, fewer collisions) by contrasting them with a
weaker alternative.
