# 40-ai-side-hustle — make targets.

PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip

.PHONY: help demo test stream-1 stream-2 stream-3 dashboard clean install

help:                       ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:                    ## pip install -r requirements.txt
	$(PIP) install -r requirements.txt

demo:                       ## run all 3 streams + print dashboard
	$(PYTHON) scripts/run_factory.py

stream-1:                   ## run only the SEO content engine
	$(PYTHON) scripts/run_factory.py --stream seo

stream-2:                   ## run only the SaaS scaffolder
	$(PYTHON) scripts/run_factory.py --stream saas

stream-3:                   ## run only the digital product factory
	$(PYTHON) scripts/run_factory.py --stream product

dashboard:                  ## render dashboard from current ledger.db
	$(PYTHON) -c "import sys; sys.path.insert(0,'src'); from dashboard import print_dashboard; print_dashboard()"

test:                       ## run unit tests
	$(PYTHON) -m pytest tests/ -v

clean:                      ## delete ledger.db and output/
	rm -f ledger.db
	rm -rf output
