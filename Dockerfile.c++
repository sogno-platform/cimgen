from alpine
run apk update
run apk add python3 git py3-pip py3-lxml file
run pip3 install --upgrade pip
run pip3 install xmltodict chevron

copy cpp/ /cim-codebase-generator/cpp/
copy cpp/build.py cimCodebaseGenerator.py cpp/templates/ /cim-codebase-generator/
workdir /cim-codebase-generator
cmd python3 build.py cgmes_v2_4_15
