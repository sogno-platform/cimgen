
DIR := $(shell pwd)

all: OUTPUT_DIR ?= ${DIR}/cimpp
all: SCHEMA_DIR ?= cgmes_schema/CGMES_2.4.15_27JAN2020
all: docker-cpp run

cimpy:
	mkdir cimpy

cimpp:
	mkdir cimpp

docker-cpp: SCHEMA_DIR ?= cgmes_schema/CGMES_2.4.15_27JAN2020
docker-cpp: OUTPUT_DIR ?= ${DIR}/cimpp
docker-cpp: cimpp
	docker build -t CIMgen . -f Dockerfile.c++

docker-python: SCHEMA_DIR ?= cgmes_schema/CGMES_2.4.15_27JAN2020
docker-python: OUTPUT_DIR ?= ${DIR}/cimpy
docker-python: cimpy
	docker build -t CIMgen-python -f Dockerfile.python .
	docker run -v ${OUTPUT_DIR}:/CIMgen/cgmes_v2_4_15 \
		-v ${DIR}/${SCHEMA_DIR}:/CIMgen/cgmes_schema/cgmes_v2_4_15_schema \
		CIMgen-python

clean: OUTPUT_DIR ?= ${DIR}/cimpp
clean:
	find ${OUTPUT_DIR} -type f -iname "*.hpp" -exec rm -f {} \;
	find ${OUTPUT_DIR} -type f -iname "*.h" -exec rm -f {} \;
	find ${OUTPUT_DIR} -type f -iname "*.cpp" -exec rm -f {} \;
	rmdir ${OUTPUT_DIR}/IEC61970

run: ${OUTPUT_DIR} ${SCHEMA_DIR}
	cp -a ../static/* ${OUTPUT_DIR}
	docker run -v ${OUTPUT_DIR}:/CIMgen/cgmes_v2_4_15 \
		-v ${DIR}/${SCHEMA_DIR}:/CIMgen/cgmes_schema/cgmes_v2_4_15_schema \
		CIMgen

build-cpp: OUTPUT_DIR ?= ${DIR}/cimpp
build-cpp: SCHEMA_DIR ?= cgmes_schema/CGMES_2.4.15_27JAN2020
build-cpp:
	cp -a ../static/* ${OUTPUT_DIR}
	python3 build.py ${OUTPUT_DIR} ${SCHEMA_DIR} cpp

.PHONY:
	docker-cpp docker-python clean run
