.PHONY: up test smoke

up:
\tpip install -r requirements.txt

test:
\tpytest -q

smoke:
\tpython agent/scorer.py
