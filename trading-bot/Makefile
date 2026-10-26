.PHONY: up test smoke smoke-alerts smoke-fixes run dashboard check

up:
	pip install -r requirements.txt

test:
	pytest -q

smoke:
	python -m bot.smoke

smoke-alerts:
	python -m bot.alerts_smoke

smoke-fixes:
	python -m bot.fixes_smoke

run:
	python -m bot.main

dashboard:
	python -m bot.dashboard

check:
	python -m bot.dashboard --check
