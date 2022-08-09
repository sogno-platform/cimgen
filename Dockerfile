from alpine
run apk update
run apk add python3 git py3-pip py3-lxml file
run pip3 install --upgrade pip
run pip3 install xmltodict chevron

copy cpp/               /CIMgen/cpp/
copy java/              /CIMgen/java/
copy javascript/        /CIMgen/javascript/
copy javascript_react/  /CIMgen/javascript_react/
copy python/            /CIMgen/python/
copy CIMgen.py build.py /CIMgen/
copy CIMgen.py build.py /CIMgen/
workdir /CIMgen
entrypoint [ "/usr/bin/python3", "build.py", "/cgmes_output", "/cgmes_schema" ]
cmd [ "cpp" ]
