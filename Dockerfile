from alpine
run apk update
run apk add python3 git py3-pip py3-lxml file
run pip3 install --upgrade pip
run pip3 install xmltodict chevron

run mkdir -p /cimgen/cimpy
copy cimCodebaseGenerator.py cpp_header_template.mustache /cimgen/cimpy/
run echo $'import cimpy.cimCodebaseGenerator' >> /cimgen/cimpy/__init__.py
run echo $\
'import cimpy\n\
path_to_rdf_files = "/cgmes_schema/cgmes_v2_4_15_schema"\n\
cimpy.cimCodebaseGenerator.cim_generate(path_to_rdf_files, "cgmes_v2_4_15_schema", "[ { \\\"filename\\\": \\\"cpp_header_template.mustache\\\", \\\"ext\\\": \\\".hpp\\\" } ]")\n' >> /cimgen/createClasses.py
run cat /cimgen/createClasses.py
workdir /cimgen
cmd python3 createClasses.py cimgen_v2_4_15
