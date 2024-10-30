LANGUAGES=python modernpython java javascript cpp

SCHEMA?=CGMES_2.4.15_27JAN2020

ifndef BUILD_IN_DOCKER
	CIMGEN=cimgen
else
	CIMGEN=docker run --volume "$(shell pwd)/output:/cimgen/output" cimgen
	LANGUAGE_DEPS = image
endif

# Extract version from SCHEMA (CGMES_2.4.15_27JAN2020 => 2_4_15)
CGMES_VERSION=$(subst .,_,$(wordlist 2,4,$(subst _, ,$(SCHEMA))))

all: $(LANGUAGES)

$(LANGUAGES): $(LANGUAGE_DEPS)
	$(CIMGEN) \
		--outdir=output/$@/$(SCHEMA) \
		--schemadir=cgmes_schema/$(SCHEMA) \
		--langdir=$@ \
		--cgmes_version=cgmes_v$(CGMES_VERSION)

image:
	docker build -t cimgen -f Dockerfile .

.PHONY: all image $(LANGUAGES)
