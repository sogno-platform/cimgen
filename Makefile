
DIR := $(shell pwd)

all: build cimpp run

cimpp:
	mkdir cimpp
build:
	docker build -t cimgen .

run:
	docker run -v ${DIR}/cimpp:/cimgen/cimpy/cgmes_v2_4_15 -v ${DIR}/cgmes_schema/cgmes_v2_4_15_schema:/cgmes_schema/cgmes_v2_4_15_schema cimgen

.PHONY:
	build run
