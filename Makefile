
DIR := $(shell pwd)

all: OUTPUT_DIR ?= ${DIR}/cimpp
all: docker-cpp run

cimpy:
	mkdir cimpy

cimpp:
	mkdir cimpp

docker-cpp: OUTPUT_DIR ?= ${DIR}/cimpp
docker-cpp: cimpp
	docker build -t cim-codebase-generator . -f Dockerfile.c++

docker-python: OUTPUT_DIR ?= ${DIR}/cimpy
docker-python: cimpy
	docker build -t cim-codebase-generator-python -f Dockerfile.python .
	docker run -v ${OUTPUT_DIR}:/cim-codebase-generator/cgmes_v2_4_15 \
		-v ${DIR}/cgmes_schema/cgmes_v2_4_15_schema:/cim-codebase-generator/cgmes_schema/cgmes_v2_4_15_schema \
		cim-codebase-generator-python

clean: OUTPUT_DIR ?= ${DIR}/cimpp
clean:
	find ${OUTPUT_DIR} -type f -iname "*.hpp" -exec rm -f {} \;
	find ${OUTPUT_DIR} -type f -iname "*.h" -exec rm -f {} \;
	find ${OUTPUT_DIR} -type f -iname "*.cpp" -exec rm -f {} \;
	rmdir ${OUTPUT_DIR}/IEC61970

run: ${OUTPUT_DIR}
	cp -a ../static/* ${OUTPUT_DIR}
	docker run -v ${OUTPUT_DIR}:/cim-codebase-generator/cgmes_v2_4_15 \
		-v ${DIR}/cgmes_schema/cgmes_v2_4_15_schema:/cim-codebase-generator/cgmes_schema/cgmes_v2_4_15_schema \
		cim-codebase-generator

build-cpp: OUTPUT_DIR ?= ${DIR}/cimpp
build-cpp:
	cp -a ../static/* ${OUTPUT_DIR}
	python3 build.py ${OUTPUT_DIR} cpp

.PHONY:
	docker-cpp docker-python clean run
