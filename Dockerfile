from alpine
run apk update
run apk add python3 git py3-pip py3-lxml file
run pip3 install --upgrade pip
run pip3 install xmltodict chevron

run mkdir -p /cim-codebase-generator/langPack/
copy langPack /cim-codebase-generator/langPack/
run mkdir -p /cim-codebase-generator/main/
copy cimCodebaseGenerator.py cpp_header_template.mustache cpp_object_template.mustache /cim-codebase-generator/main/
run echo $'import main.cimCodebaseGenerator' >> /cim-codebase-generator/main/__init__.py
run echo $\
'import main\n\
from langPack import langPackCpp\n\
path_to_rdf_files = "/cgmes_schema/cgmes_v2_4_15_schema"\n\
main.cimCodebaseGenerator.cim_generate(path_to_rdf_files, "cgmes_v2_4_15", langPackCpp)\n' >> /cim-codebase-generator/createClasses.py
run cat /cim-codebase-generator/createClasses.py
workdir /cim-codebase-generator
cmd python3 createClasses.py cgmes_v2_4_15
