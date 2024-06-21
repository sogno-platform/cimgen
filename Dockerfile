# NOSONAR 
FROM python:3.11

# NOSONAR 
COPY ./ /cimgen

WORKDIR /cimgen

RUN pip install .

ENTRYPOINT [ "cimgen" ]
