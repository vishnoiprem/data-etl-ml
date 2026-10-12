# 40-ai-side-hustle — make targets.

PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip

.PHONY: help install demo stream-1 stream-2 stream-3 stream-4 \
        dashboard simulate-ramp simulate-30d launchkit launchkit-url \
        launchkit-map-template launchkit-map test clean

help:                       ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install:                    ## pip install -r requirements.txt
	$(PIP) install -r requirements.txt

demo:                       ## run all 4 streams + print dashboard
	$(PYTHON) scripts/run_factory.py

stream-1:                   ## run only the SEO content engine
	$(PYTHON) scripts/run_factory.py --stream seo

stream-2:                   ## run only the SaaS scaffolder
	$(PYTHON) scripts/run_factory.py --stream saas

stream-3:                   ## run only the digital product factory
	$(PYTHON) scripts/run_factory.py --stream product

stream-4:                   ## run only the print-on-demand merch stream
	$(PYTHON) scripts/run_factory.py --stream merch

simulate-ramp:              ## run all streams + inject a 14-day ramp scenario
	$(PYTHON) scripts/run_factory.py --simulate-ramp

simulate-30d:               ## run all streams + inject 30 days of synthetic sales
	$(PYTHON) scripts/run_factory.py --simulate-days 30

launchkit:                  ## build Gumroad launch kits (PDF + sales page + tweets + emails) for all products
	$(PYTHON) -m src.launchkit --all

launchkit-url:               ## build kits with a real Gumroad URL injected into every asset
	@if [ -z "$(URL)" ]; then echo "usage: make launchkit-url URL=https://yourname.gumroad.com/l/slug"; exit 1; fi
	$(PYTHON) -m src.launchkit --all --url "$(URL)"

launchkit-map-template:     ## write a starter url-map JSON to fill in after publishing on Gumroad
	@if [ -z "$(FILE)" ]; then FILE=output/url-map.json; fi
	$(PYTHON) -m src.launchkit --write-url-template "$(FILE)"

launchkit-map:              ## build kits using a per-product URL map (one URL per product)
	@if [ -z "$(MAP)" ]; then echo "usage: make launchkit-map MAP=output/url-map.json"; exit 1; fi
	$(PYTHON) -m src.launchkit --all --url-map "$(MAP)"

dashboard:                  ## render dashboard from current ledger.db
	$(PYTHON) -c "import sys; sys.path.insert(0,'src'); from dashboard import print_dashboard; print_dashboard()"

test:                       ## run unit tests
	$(PYTHON) -m pytest tests/ -v

clean:                      ## delete ledger.db and output/
	rm -f ledger.db
	rm -rf output
