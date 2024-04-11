FROM alpine:3.19.1
RUN apk update
RUN apk add python3 git py3-pip py3-lxml file
RUN python3 -m pip install --break-system-packages xmltodict chevron pydantic beautifulsoup4

WORKDIR /cimgen
COPY ./cpp /cimgen/cpp
COPY ./java /cimgen/java
COPY ./javascript /cimgen/javascript
COPY ./modernpython /cimgen/modernpython
COPY ./python /cimgen/python
COPY ./cgmes_schema /cimgen/cgmes_schema
COPY ./build.py /cimgen/build.py
COPY ./CIMgen.py /cimgen/CIMgen.py

ENTRYPOINT [ "/usr/bin/python3", "/cimgen/build.py", "--outdir=/cimgen/cgmes_output", "--schemadir=/cimgen/cgmes_schema" ]
CMD [ "--langdir=/cimgen/cpp" ]
