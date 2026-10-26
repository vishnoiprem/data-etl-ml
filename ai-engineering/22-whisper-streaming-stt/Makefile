.PHONY: up test smoke

up:
\tpip install -r requirements.txt

test:
\tpytest -q

smoke:
\tpython service/vad.py
\tpython service/streaming.py
