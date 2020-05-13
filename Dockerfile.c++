from alpine
run apk update
run apk add python3 git py3-pip py3-lxml file
run pip3 install --upgrade pip
run pip3 install xmltodict chevron

copy cpp/ /CIMgen/cpp/
copy CIMgen.py build.py cpp/templates/ /CIMgen/
workdir /CIMgen.py
cmd python3 build.py cgmes_v2_4_15 /CIMgen/cgmes_schema/cgmes_v2_4_15_schema cpp
