FROM alpine:3.19.1
RUN apk update
RUN apk add python3 git py3-pip py3-lxml file
RUN python3 -m pip install --break-system-packages xmltodict chevron pydantic beautifulsoup4

WORKDIR /cimgen
COPY . /cimgen

ENTRYPOINT [ "/usr/bin/python3", "build.py", "--outdir=/cgmes_output", "--schemadir=/cgmes_schema" ]
CMD [ "--langdir=cpp" ]
