# Makefile — leads-pipeline/draft-cron
#
# Mirrors the steps that .github/workflows/leads-ci.yml runs on
# every PR, so a developer can validate locally before pushing:
#
#   make help        Show all targets
#   make install     Set up .venv/ with the runtime + test deps
#   make test        Run all 6 test modules (matches CI order)
#   make lint        flake8 against the modified source files
#   make docker-build  Build the container image
#   make docker-run    Smoke test the built image
#   make ci          Shortcut: install + test + lint + docker-build
#
# Environment:
#   PY        — Python interpreter (default: .venv/bin/python)
#   AVILX_DB_HOST/PORT/NAME/USER/PASSWORD — same vars as CI
#
# Test schema:
#   `make schema` applies db/schema.sql to $AVILX_DB_NAME. The CI
#   runs this in its Init test schema step; locally we assume you've
#   already got a database (the project's docker-compose starts one
#   on :5433).

HERE       := $(shell pwd)
PY         ?= $(HERE)/.venv/bin/python
VENV       := $(HERE)/.venv
IMAGE      := leads-pipeline:local
# Read the in-tree VERSION (managed by release-please). Fall back
# to "0.0.0+local" if the file is missing — e.g. first-time clone
# before release-please has run.
VERSION    := $(shell test -f $(HERE)/VERSION && tr -d '[:space:]' < $(HERE)/VERSION || echo 0.0.0+local)
DB_HOST    ?= localhost
DB_PORT    ?= 5433
DB_NAME    ?= avilx_leads
DB_USER    ?= avilx
DB_PASS    ?= avilx

# Match the exact module order from .github/workflows/leads-ci.yml
TEST_MODULES := \
    test_dedup_key \
    test_dedup \
    test_parser \
    test_resume_tailor \
    test_better_email \
    test_bounce_deny_persistence \
    test_backfill_cover_letters \
    test_mark_reply

LINT_FILES := \
    find_more_leads.py find_clients.py refine_pipeline.py \
    backfill_emails.py cover_letter.py dashboard.py \
    bin/loop_status.py bin/loop_bounce_sync.py \
    bin/mark_reply.py bin/reply_metrics.py \
    state/bounce_deny_store.py \
    resume_tailor.py

.PHONY: help install schema test lint reply metrics docker-build docker-run docker-shell docker-healthcheck ci clean

help:           ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:        ## Create .venv and install deps
	@test -x $(PY) || python3 -m venv $(VENV)
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet -r requirements.txt flake8

schema:         ## Apply db/schema.sql to $AVILX_DB_NAME
	@echo "Applying schema to $(DB_NAME)@$(DB_HOST):$(DB_PORT)"
	PGPASSWORD=$(DB_PASS) psql -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -d $(DB_NAME) -f db/schema.sql

test:           ## Run all test modules (matches CI order)
	@echo "Running $(words $(TEST_MODULES)) test modules"
	@for t in $(TEST_MODULES); do \
	    echo "===> $$t"; \
	    PYTHONPATH=. $(PY) -m tests.$$t || exit 1; \
	done

lint:           ## flake8 the modified source files
	$(PY) -m flake8 --max-line-length 110 --extend-ignore E501,W503,E731 $(LINT_FILES) || \
	    echo "::warning::lint advisories (non-fatal)"

docker-build:   ## Build the container image (tag: leads-pipeline:local)
	@echo "Building $(IMAGE) with VERSION=$(VERSION)"
	docker build --build-arg VERSION=$(VERSION) -t $(IMAGE) .

docker-run:     ## Smoke test the built image
	docker run --rm --entrypoint python $(IMAGE) \
	    -c "import db.lead_store, find_more_leads, resume_tailor; print('OK; HAVE_DOCX=', resume_tailor.HAVE_DOCX)"

docker-healthcheck:  ## Run the in-image healthcheck script
	@echo "Running healthcheck against $(IMAGE)"
	docker run --rm --entrypoint /bin/sh \
	    -e AVILX_DB_HOST=$(DB_HOST) -e AVILX_DB_PORT=$(DB_PORT) \
	    $(IMAGE) /usr/local/bin/docker-healthcheck.sh \
	    && echo "✅ healthcheck OK" \
	    || (echo "::error::healthcheck failed"; exit 1)

docker-shell:   ## Open a shell in the built image
	docker run --rm -it --entrypoint bash $(IMAGE)

reply:          ## Mark a reply / meeting: make reply Q="Tailscale" REPLIED=1 AT=2026-10-12 VIA=email
	@if [ -z "$(Q)" ]; then echo "Usage: make reply Q=\"<company-substring>\" [REPLIED=1] [MEETING=1] [AT=YYYY-MM-DD] [VIA=email|x_dm|linkedin|platform|inbound|other] [NOTES='...']"; exit 1; fi
	$(PY) bin/mark_reply.py "$(Q)" \
	    $(if $(REPLIED),--replied) \
	    $(if $(MEETING),--meeting) \
	    $(if $(AT),--at $(AT)) \
	    $(if $(VIA),--via $(VIA)) \
	    $(if $(NOTES),--notes "$(NOTES)")

reply-list:     ## Show the reply state of every lead in the most recent drop
	$(PY) bin/mark_reply.py --list

metrics:        ## Weekly reply / conversion KPIs (override DAYS=N for a longer window)
	$(PY) bin/reply_metrics.py $(if $(DAYS),--days $(DAYS)) $(if $(CHANNEL),--by-channel) $(if $(JSON),--json)

ci: install lint test docker-build docker-run docker-healthcheck   ## Run every CI step locally
	@echo ""
	@echo "✅ local CI simulation passed"
	@echo "   Next: git push to trigger the real leads-ci workflow"

clean:          ## Remove local build artifacts (NOT .venv, NOT .tailored_resumes)
	rm -rf $(HERE)/__pycache__ $(HERE)/*/__pycache__
	find $(HERE) -name '*.pyc' -delete
	find $(HERE) -name '*.pyo' -delete
