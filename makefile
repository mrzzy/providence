#
# Providence
# Makefile
#

.PHONY := all fmt lint
.DEFAULT_GOAL := all

define PHONY_RULE
.PHONY += $(1)-$(2)
$(1): $(1)-$(2)
endef

define PYTHON_RULES
$(eval $(call PHONY_RULE,fmt,$(1)))
fmt-$(1): $(2)
	black $$<

$(eval $(call PHONY_RULE,lint,$(1)))
lint-$(1): $(2)
	black --check $$<

$(eval $(call PHONY_RULE,test,$(1)))
test-$(1): $(2)
	cd $$< && pytest
endef

all: deps fmt lint build test

# SimplyGo source
SIMPLYGO_DIR := sources/simplygo

define SIMPLYGO_RULE
$(call PHONY_RULE,$(1),simplygo)
$(1)-simplygo: $$(SIMPLYGO_DIR)
	cd $$< && $(2)
endef

$(eval $(call SIMPLYGO_RULE,fmt,cargo fmt))
$(eval $(call SIMPLYGO_RULE,lint,cargo fmt --check && cargo clippy))
$(eval $(call SIMPLYGO_RULE,build,cargo build))
$(eval $(call SIMPLYGO_RULE,test,cargo test))

# YNAB source
YNAB_DIR := sources/ynab

$(eval $(call PHONY_RULE,deps,ynab))
deps-ynab: $(YNAB_DIR)
	cd $< && pip install -r requirements-dev.txt

$(eval $(call PYTHON_RULES,ynab,$(YNAB_DIR)))

# Pandas ETL transform
PANDAS_ETL_DIR := transforms/pandas-etl

$(eval $(call PHONY_RULE,deps,pandas-etl))
deps-pandas-etl: $(PANDAS_ETL_DIR)
	cd $< && pip install -r requirements-dev.txt

$(eval $(call PYTHON_RULES,pandas-etl,$(PANDAS_ETL_DIR)))

# DBT transform
DBT_DIR := transforms/dbt

$(eval $(call PHONY_RULE,deps,dbt))
deps-dbt: $(PANDAS_ETL_DIR)
	cd $< && pip install -r requirements-dev.txt

$(eval $(call PHONY_RULE,fmt,$(1)))
fmt-dbt: $(DBT_DIR)
	cd $< && sqlfmt .
	cd $< && sqlfluff fix .

$(eval $(call PHONY_RULE,lint,$(1)))
lint-dbt: $(DBT_DIR)
	cd $< && sqlfmt --check .
	cd $< && sqlfluff lint .

# Airflow Pipelines
# NOTE: run 'airflow db init' before running 'make test-pipeline'
PIPELINES_DIR := pipelines

$(eval $(call PHONY_RULE,deps,pipelines))
deps-pipelines: $(PIPELINES_DIR)
	cd $< && pip install -r requirements-dev.txt
	airflow db init

$(eval $(call PYTHON_RULES,pipelines,$(PIPELINES_DIR)))
