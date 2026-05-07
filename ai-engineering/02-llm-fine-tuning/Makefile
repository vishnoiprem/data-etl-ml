.PHONY: install demo data lora dpo eval test clean

PYTHON := python3

install:
	$(PYTHON) -m pip install -r requirements.txt

demo: data lora dpo eval

data:
	@echo "═══ Step 1: Build instruction-tuning JSONL ═══"
	$(PYTHON) scripts/prepare_data.py

lora:
	@echo ""
	@echo "═══ Step 2: LoRA-style fine-tuning demo ═══"
	$(PYTHON) scripts/train_lora.py

dpo:
	@echo ""
	@echo "═══ Step 3: DPO preference-tuning demo ═══"
	$(PYTHON) scripts/train_dpo.py

eval:
	@echo ""
	@echo "═══ Step 4: Pre vs post fine-tune evaluation ═══"
	$(PYTHON) scripts/evaluate.py

test:
	$(PYTHON) -m pytest tests/ -v

clean:
	rm -rf data/processed __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
