
DIR := $(shell pwd)
OUTPUT_DIR ?= ${DIR}/cimpp

all: build-cpp run

cimpy:
	mkdir cimpy

${DIR}/cimpp:
	mkdir cimpp

build-cpp:
	docker build -t cim-codebase-generator . -f Dockerfile.c++

build-python: cimpy
	docker build -t cim-codebase-generator-python -f Dockerfile.python .
	docker run -v ${DIR}/cimpy:/cim-codebase-generator/main/cgmes_v2_4_15 \
		-v ${DIR}/cgmes_schema/cgmes_v2_4_15_schema:/cgmes_schema/cgmes_v2_4_15_schema \
		cim-codebase-generator-python

clean:
	find ${OUTPUT_DIR} -type f -iname "*.hpp" -exec rm -f {} \;
	find ${OUTPUT_DIR} -type f -iname "*.h" -exec rm -f {} \;
	find ${OUTPUT_DIR} -type f -iname "*.cpp" -exec rm -f {} \;
	rmdir ${OUTPUT_DIR}/IEC61970

run: ${OUTPUT_DIR}
	cp -a ../static/* ${OUTPUT_DIR}
	docker run -v ${OUTPUT_DIR}:/cim-codebase-generator/main/cgmes_v2_4_15 -v ${DIR}/cgmes_schema/cgmes_v2_4_15_schema:/cgmes_schema/cgmes_v2_4_15_schema cim-codebase-generator

.PHONY:
	build-cpp build-python clean run
