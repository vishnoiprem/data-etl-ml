.PHONY: install demo ingest query api eval test clean

PYTHON := python3

install:
	$(PYTHON) -m pip install -r requirements.txt

demo: ingest
	@echo ""
	@echo "═══ Asking sample questions ═══"
	$(PYTHON) scripts/query.py "What is our PTO policy for new hires?"
	@echo ""
	$(PYTHON) scripts/query.py "How do I rotate an EBS volume's KMS key?"
	@echo ""
	$(PYTHON) scripts/query.py "What happens if I miss the open-enrollment window?"
	@echo ""
	@echo "═══ Running evaluation ═══"
	$(PYTHON) scripts/evaluate.py

ingest:
	$(PYTHON) scripts/ingest.py

query:
	$(PYTHON) scripts/query.py "$(Q)"

api:
	$(PYTHON) -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

eval:
	$(PYTHON) scripts/evaluate.py

test:
	$(PYTHON) -m pytest tests/ -v

clean:
	rm -rf data/index data/cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
