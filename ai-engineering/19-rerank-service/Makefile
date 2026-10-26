.PHONY: up api test smoke

up:
\tpip install -r requirements.txt

api:
\tuvicorn service.app:app --reload --port 8090

test:
\tpytest -q

smoke:
\tcurl -s http://localhost:8090/healthz
