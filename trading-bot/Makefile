.PHONY: up test smoke run

up:
	pip install -r requirements.txt

test:
	pytest -q

smoke:
	python -m bot.smoke

run:
	python -m bot.main
