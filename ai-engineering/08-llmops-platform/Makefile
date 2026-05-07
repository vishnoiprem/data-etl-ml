.PHONY: install demo test clean
PYTHON := python3

install:
	$(PYTHON) -m pip install -r requirements.txt

demo:
	$(PYTHON) scripts/run_pipeline.py

test:
	$(PYTHON) -m pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
