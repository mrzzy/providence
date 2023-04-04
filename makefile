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
deps-ynab:
	cd $$< && pip install -r requirements-dev.txt

$(eval $(call PYTHON_RULES,ynab,$(YNAB_DIR)))

# Airflow Pipelines
# NOTE: run 'airflow db init' before running 'make test-pipeline'
PIPELINES_DIR := pipelines

$(eval $(call PHONY_RULE,deps,pipelines))
deps-pipeline: $(PIPELINES_DIR)
	airflow db init
	cd $$< && pip install -r requirements-dev.txt

$(eval $(call PYTHON_RULES,pipelines,$(PIPELINES_DIR)))
