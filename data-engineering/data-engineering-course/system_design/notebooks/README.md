# Notebooks

> Optional Jupyter playbooks for hands-on analysis of the running services.

Each notebook assumes a service is already running on its default port
(see `01_url_shortener/code/app.py` and friends). The notebooks are
*exploratory* — they're for the learner who wants to look at the data,
not the engineer who wants to extend the system.

## List

| Notebook | What it does |
|---|---|
| `01_url_shortener_load.ipynb` | Plots p50/p95/p99 latencies for the URL shortener. Uses `01_url_shortener/code/loadtest.py` and reads the service's `/metrics` endpoint. |
| `02_trie_walk.ipynb` | Visualizes the typeahead trie and shows how `top_k` is precomputed. |
| `03_redis_vs_inproc.ipynb` | Compares our in-process TTLCache/LRUCache to a `redis-py` baseline (skipped if Redis isn't installed). |

## How to use

```bash
pip install jupyter matplotlib pandas
jupyter notebook
```

If you don't want to install Jupyter, the same logic lives in plain
`.py` files alongside each notebook — open them in any editor.
