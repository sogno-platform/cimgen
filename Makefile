LANGUAGES=python modernpython java javascript cpp

SCHEMA?=CGMES_2.4.15_27JAN2020

ifndef BUILD_IN_DOCKER
	CIMGEN=cimgen
else
	CIMGEN=docker run --volume "$(shell pwd)/output:/cimgen/output" cimgen
	LANGUAGE_DEPS = image
endif

all: $(LANGUAGES)

$(LANGUAGES): $(LANGUAGE_DEPS)
	$(CIMGEN) \
		--outdir=output/$@/$(SCHEMA) \
		--schemadir=cgmes_schema/$(SCHEMA) \
		--langdir=$@

image:
	docker build -t cimgen -f Dockerfile .

.PHONY: all image python modernpython java javascript
