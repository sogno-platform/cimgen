
DIR := $(shell pwd)

all: build cimpp run

cimpp:
	mkdir cimpp

cimpy:
	mkdir cimpy

build:
	docker build -t cim-codebase-generator .

build-python: cimpy
	docker build -t cim-codebase-generator-python -f Dockerfile.python .
	docker run -v ${DIR}/cimpy:/cim-codebase-generator/main/cgmes_v2_4_15 \
		   -v ${DIR}/cgmes_schema/cgmes_v2_4_15_schema:/cgmes_schema/cgmes_v2_4_15_schema \
	           cim-codebase-generator-python

run:
	docker run -v ${DIR}/cimpp:/cim-codebase-generator/main/cgmes_v2_4_15 -v ${DIR}/cgmes_schema/cgmes_v2_4_15_schema:/cgmes_schema/cgmes_v2_4_15_schema cim-codebase-generator
	cd cimpp && find . -iname "*.hpp" | grep -v Folders | grep -v Task | grep -v IEC61970 | sed "s/\.\///" | sed "s/\(.*\)/#include \"\1\"/" > IEC61970.hpp

.PHONY:
	build build-python run
