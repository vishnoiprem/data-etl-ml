.PHONY: up api test smoke

up:
\tdocker compose up -d

api:
\tuvicorn control_plane.api:app --reload --port 8080

test:
\tpytest -q

smoke:
\tpython -c "import requests; r = requests.get('http://localhost:8080/healthz'); print(r.json())"
\tpython -c "import requests; r = requests.post('http://localhost:8080/run', json={'workflow': 'linear'}); print(r.json())"
