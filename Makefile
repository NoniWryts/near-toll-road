PY ?= python3
SNAP ?= $(shell ls -d data/snapshots/20* 2>/dev/null | sort | tail -1)

.PHONY: setup refresh tables model check report dashboard serve all clean-cache

setup:            ## install dependencies
	$(PY) -m pip install -r requirements.txt

refresh:          ## pull live data from every keyless source into data/snapshots/<today>/
	$(PY) -m pipeline.fetch_all

tables:           ## derive reports/tables/ and kpis.json from the latest snapshot
	$(PY) -m analysis.build --snapshot $(SNAP)

model: tables     ## run the breakeven + scenario model on the latest snapshot
	$(PY) -m models.breakeven --snapshot $(SNAP)

check:            ## re-verify every claim in the ledger against the latest snapshot
	$(PY) -m checks.run_ledger --snapshot $(SNAP)
	$(PY) -m checks.predictions --snapshot $(SNAP)
	$(PY) -m pytest -q checks

report: model check ## regenerate tables, figures, dashboard and THESIS.md from the snapshot
	$(PY) -m dashboard.build --snapshot $(SNAP)
	$(PY) -m thesis.render --snapshot $(SNAP)

dashboard:
	$(PY) -m dashboard.build --snapshot $(SNAP)

serve:            ## open the dashboard on http://localhost:5300
	cd dashboard && $(PY) -m http.server 5300

all: refresh report
