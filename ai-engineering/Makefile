.PHONY: setup clean test all-demos

PYTHON := python3.11
PIP := $(PYTHON) -m pip

PROJECTS := 01-enterprise-rag-platform 02-llm-fine-tuning 03-multi-agent-platform \
            04-fm-evaluation 05-distributed-inference 06-regulated-industry \
            07-prompt-engineering 08-llmops-platform

setup:
	$(PIP) install --upgrade pip
	$(PIP) install -r shared/requirements.txt
	@for p in $(PROJECTS); do \
		echo "→ Installing $$p"; \
		$(PIP) install -r $$p/requirements.txt || true; \
	done

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf */data/index */data/cache 2>/dev/null || true

test:
	@for p in $(PROJECTS); do \
		echo "→ Testing $$p"; \
		(cd $$p && $(PYTHON) -m pytest tests/ -v) || true; \
	done

all-demos:
	@for p in $(PROJECTS); do \
		echo ""; echo "═══ Demo: $$p ═══"; \
		(cd $$p && make demo) || echo "  (demo not yet runnable)"; \
	done
