.PHONY: install demo single batch test clean
PYTHON := python3

install:
	$(PYTHON) -m pip install -r requirements.txt

demo: batch

single:
	$(PYTHON) scripts/run_application.py

batch:
	$(PYTHON) scripts/run_batch.py

test:
	$(PYTHON) -m pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
