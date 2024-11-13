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
	
# Simplygo SDK, source & transform
SIMPLYGO_SRC:= sources/simplygo
$(eval $(call PYTHON_RULES,simplygo-src,$(SIMPLYGO_SRC)))

$(eval $(call PHONY_RULE,deps,simplygo-src))
deps-simplygo-src: $(SIMPLYGO_SRC)
	cd $< && pip install -r requirements-dev.txt

test-simplygo-src: $(SIMPLYGO_SRC)
	# do nothing for now

# DBT transform
DBT_DIR := transforms/dbt
DBT_TARGET := dev

$(eval $(call PHONY_RULE,deps,dbt))
deps-dbt: $(DBT_DIR)
	cd $< && pip install -r requirements-dev.txt
	cd $< && dbt deps

$(eval $(call PHONY_RULE,fmt,dbt))
fmt-dbt: $(DBT_DIR)
	cd $< && sqlfluff fix -f .
	cd $< && sqlfmt .

$(eval $(call PHONY_RULE,lint,dbt))
lint-dbt: $(DBT_DIR)
	cd $< && sqlfluff lint .
	cd $< && sqlfmt --check .

$(eval $(call PHONY_RULE,build,dbt))
build-dbt: $(DBT_DIR)
	cd $< && dbt build --target $(DBT_TARGET)

# Prefect Pipelines
PIPELINES_DIR := pipelines
$(eval $(call PYTHON_RULES,pipelines,$(PIPELINES_DIR)))

$(eval $(call PHONY_RULE,deps,pipelines))
deps-pipelines: $(PIPELINES_DIR)
	cd $< && pip install -r requirements-dev.txt
	cd $(DBT_DIR) && dbt deps
