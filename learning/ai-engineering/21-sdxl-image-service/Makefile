.PHONY: up test smoke

up:
\tpip install -r requirements.txt

test:
\tpytest -q

smoke:
\tpython service/pipeline.py
\tpython service/safety.py
