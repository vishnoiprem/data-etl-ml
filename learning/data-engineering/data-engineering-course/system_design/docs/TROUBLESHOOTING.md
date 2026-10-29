# Troubleshooting

Common issues and fixes when running the system design course.

---

## "ModuleNotFoundError: No module named 'code'"

Each module's `code/` and `tests/` need `__init__.py` (which is created
on scaffold). If you somehow deleted one, recreate it:

```bash
touch 01_url_shortener/code/__init__.py
touch 01_url_shortener/tests/__init__.py
```

## "ModuleNotFoundError: No module named 'common'"

The `common/` directory must be on `sys.path` when the service runs.
Two options:

**Option A** (recommended): run from the system_design directory:
```bash
cd data-engineering-course/system_design
python3 01_url_shortener/code/app.py
```

**Option B**: install the course as a package:
```bash
cd data-engineering-course
pip install -e .
```

## Port already in use

Each service uses a different default port (8001, 8002, ...). If you
have a port conflict, set the env var:
```bash
PORT=9001 python3 01_url_shortener/code/app.py
```

## Sample data missing

The services that need sample data:
- `02_typeahead` — `sample_data/dictionary.jsonl`
- `03_instagram`, `04_twitter`, `05_newsfeed`, `29_slack` — `users.jsonl`
- `06_yt_or_netflix` — `videos.jsonl`
- `04_twitter` — `tweets.jsonl`

Regenerate with:
```bash
cd data-engineering-course/system_design
python3 scripts/seed_data.py
```

## Tests fail with "KeyValueStore" path issues

Some tests use `tempfile.mkdtemp()` for clean state. If you see
permission errors, the var/ directory might have been created by
another user. Fix:
```bash
rm -rf */code/var */tests/var
```

## "Permission denied" on `run_all_smoke_tests.sh`

```bash
chmod +x scripts/run_all_smoke_tests.sh
```

## How to start a single service in the background

```bash
nohup python3 01_url_shortener/code/app.py > var/logs/01.log 2>&1 &
```

Logs go to `var/logs/<service>.log`. Stop with:
```bash
pkill -f "code/app.py"
```

## The sample data is too small

Regenerate with bigger corpora — edit `scripts/seed_data.py` and
change the constants (e.g. `n=10_000` instead of `n=2_000`).

## I want to add a new module

Use the scaffolder:
```bash
python3 scripts/scaffold.py --module 40_my_system "My Cool System"
```

This creates design/, code/, tests/ skeletons. Fill them in.

## Tests are slow

The integration tests are designed to be fast (in-memory). If they're
slow, check that your `KeyValueStore` `persist_path` points to a
slow disk (e.g. network mount). For tests, pass
`persist_path=None` to disable disk writes.

## I'm seeing "Snowflake" ID collisions

By design, the IDs include the machine_id. Different machine_ids
produce different ID spaces. In tests, the same process reuses
machine_id, so IDs are still unique. If you start a fresh service,
you'll see a jump in IDs but no collisions.
