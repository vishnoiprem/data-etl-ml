# 39-revenue-pipeline — make targets.
#
# Usage:
#   make demo         # run end-to-end on sample data, print dashboard
#   make test         # 11 unit tests, no network, no API key
#   make dashboard    # render the dashboard from the current pipeline.db
#   make reset        # delete pipeline.db + sample_data/signals.json
#   make clean        # delete pipeline.db only

PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip

.PHONY: help demo test dashboard reset clean install

help:                       ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:                    ## pip install -r requirements.txt
	$(PIP) install -r requirements.txt

demo:                       ## run one end-to-end pass on sample data
	$(PYTHON) scripts/run_loop.py

test:                       ## run unit tests
	$(PYTHON) -m pytest tests/ -v

dashboard:                  ## render the dashboard from pipeline.db
	$(PYTHON) -c "import sys; sys.path.insert(0,'src'); from dashboard import print_dashboard; print_dashboard()"

reset: clean                ## delete all generated state
	rm -f sample_data/signals.json

clean:                      ## delete pipeline.db
	rm -f pipeline.db
