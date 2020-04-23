
DIR := $(shell pwd)

all: build-cpp cimpp run

cimpp:
	mkdir cimpp

cimpy:
	mkdir cimpy

build-cpp:
	docker build -t cim-codebase-generator . -f Dockerfile.c++

build-python: cimpy
	docker build -t cim-codebase-generator-python -f Dockerfile.python .
	docker run -v ${DIR}/cimpy:/cim-codebase-generator/main/cgmes_v2_4_15 \
		   -v ${DIR}/cgmes_schema/cgmes_v2_4_15_schema:/cgmes_schema/cgmes_v2_4_15_schema \
	           cim-codebase-generator-python

clean:
	find cimpp -type f -exec rm -f {} \;

run:
	docker run -v ${DIR}/../src:/cim-codebase-generator/main/cgmes_v2_4_15 -v ${DIR}/cgmes_schema/cgmes_v2_4_15_schema:/cgmes_schema/cgmes_v2_4_15_schema cim-codebase-generator

.PHONY:
	build-cpp build-python clean run

