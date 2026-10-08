.PHONY: install ingest query api eval demo test clean

PYTHON := python3

install:
	$(PYTHON) -m pip install -r requirements.txt

demo: ingest
	@echo ""
	@echo "═══ Single-hop question (all strategies should answer) ═══"
	$(PYTHON) scripts/query.py "What is our PTO policy for new hires?" --strategy vector
	@echo ""
	@echo "═══ Two-hop money shot (graph + hybrid should win) ═══"
	$(PYTHON) scripts/query.py "I'm a new hire about to travel internationally for a client visit. What is the approval path?" --strategy vector
	@echo ""
	$(PYTHON) scripts/query.py "I'm a new hire about to travel internationally for a client visit. What is the approval path?" --strategy hybrid
	@echo ""
	@echo "═══ Running evaluation ═══"
	$(PYTHON) scripts/evaluate.py

ingest:
	$(PYTHON) scripts/ingest.py

query:
	$(PYTHON) scripts/query.py "$(Q)" --strategy $(if $(STRATEGY),$(STRATEGY),hybrid)

eval:
	$(PYTHON) scripts/evaluate.py

test:
	LLM_MODE=mock $(PYTHON) -m pytest tests/ -v

clean:
	rm -rf data/* __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
