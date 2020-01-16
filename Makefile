
DIR := $(shell pwd)

all: build cimpp run

cimpp:
	mkdir cimpp

build:
	docker build -t cim-codebase-generator .

run:
	docker run -v ${DIR}/cimpp:/cim-codebase-generator/main/cgmes_v2_4_15 -v ${DIR}/cgmes_schema/cgmes_v2_4_15_schema:/cgmes_schema/cgmes_v2_4_15_schema cim-codebase-generator

.PHONY:
	build run
