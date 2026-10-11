.PHONY: up test smoke run dashboard check

up:
	pip install -r requirements.txt

test:
	pytest -q

smoke:
	python -m bot.smoke

run:
	python -m bot.main

dashboard:
	python -m bot.dashboard

check:
	python -m bot.dashboard --check
