.PHONY: up test smoke

up:
	pip install -r requirements.txt

test:
	pytest -q

smoke:
	python -m serve.prefix_cache