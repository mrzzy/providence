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

# Airflow Pipelines
PIPELINES_DIR := pipelines

$(eval $(call PHONY_RULE,deps,pipelines))
deps-pipelines: $(PIPELINES_DIR)
	cd $< && pip install -r requirements-dev.txt

$(eval $(call PHONY_RULE,fmt,pipelines))
fmt-pipelines: $(PIPELINES_DIR)
	black $<

$(eval $(call PHONY_RULE,lint,pipelines))
lint-pipelines: $(PIPELINES_DIR)
	black --check $<

$(eval $(call PHONY_RULE,test,pipelines))
test-pipelines: $(PIPELINES_DIR)
	airflow db init
	cd $< && pytest
